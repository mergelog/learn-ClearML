# `{ functional: true }` — 関数方式の Effect

## 結論

- `{ functional: true }` は **「この effect をクラスの外に、ただの関数として作る」** という宣言。それ以上の意味はない
- 実装差は **1 行だけ**。`createEffect` が渡された関数を **その場で実行するか、実行せずに持っておくか** が変わる
- 依存は **デフォルト引数の `inject()`** で受け取る。本番は NgRx が引数なしで呼ぶので DI が効き、テストは引数を渡して差し替える
- **新規は全部これ**。クラス方式も現役で動くが、1 つのアプリで混在させない

小さい effect では見た目の差しかない。**効いてくるのはテストと、クラス特有の初期化順序の罠が消える点**。

## 早見表

| | クラス方式 | 関数方式（`functional: true`） |
|---|---|---|
| 定義場所 | `@Injectable()` クラスのプロパティ | モジュールスコープの `const` |
| 依存の受け取り | constructor | デフォルト引数の `inject()` |
| `createEffect` の戻り値 | Observable（**即実行済み**） | **関数そのもの**（未実行） |
| 登録 | `provideEffects(UsersEffects)` | `provideEffects(usersEffects)`（オブジェクト） |
| テスト | `TestBed` の組み立てが要る | 関数を直接呼ぶだけ |
| フィールド初期化順序の罠 | あり（[5-2](#pitfall)） | 原理的に無い |
| 命名の `$` | 付ける（Observable なので） | **付けない**（関数なので）[→](#naming) |
| 方針 | 既存の保守のみ | 新規はこちら |

---

<a id="recap"></a>

## 1. 前提: effect とは何だったか

NgRx では「画面で何かが起きた」を **action** という値で表す。ただし action はただの値なので、それ自体は通信をしない。

**「この action が流れてきたら、この副作用を実行し、結果を別の action にして流し直す」** という担当役が effect である。

```
loadUsers が流れてくる → usersApi.getUsers() を呼ぶ → 結果を loadUsersSuccess にして流す
```

action / reducer / selector の全体像は [00_ngrx.md](./00_ngrx.md)、
「なぜ component に `subscribe` を書かず effect に寄せるのか」は [03_subscribe.md](./03_subscribe.md) を参照。

この資料は **その effect の「書き方」だけ** を扱う。

<a id="two-styles"></a>

## 2. 2 つの書き方

### クラス方式（NgRx 15.1 まではこれしかなかった）

```ts
@Injectable()
export class UsersEffects {
  constructor(
    private actions$: Actions,
    private usersApi: UsersApi,
  ) {}

  loadUsers$ = createEffect(() =>
    this.actions$.pipe(
      ofType(loadUsers),
      switchMap(() => this.usersApi.getUsers()),
      map((users) => loadUsersSuccess({ users })),
    ),
  );
}
```

```ts
provideEffects(UsersEffects)   // クラスを渡す
```

### 関数方式（`{ functional: true }`）

```ts
const loadUsers$ = createEffect(
  (actions$ = inject(Actions), usersApi = inject(UsersApi)) =>
    actions$.pipe(
      ofType(loadUsers),
      switchMap(() => usersApi.getUsers()),
      map((users) => loadUsersSuccess({ users })),
    ),
  { functional: true },
);

export const usersEffects = { loadUsers$ };
```

```ts
provideEffects(usersEffects)   // オブジェクトを渡す
```

> `06_users_sample` の実コードをそのまま載せている。**末尾の `$` は本来付けない方がよい**。理由と、このサンプルで付いてしまっている事情は [6 章](#naming)。

クラス・`@Injectable()`・constructor・`this` が全部消える。

**なぜ `{ functional: true }` を明示する必要があるのか** — `createEffect` に渡されるのはどちらの方式でも「関数」で、受け取った側から見分けが付かない。だから **どちらの方式で書いたかを引数で申告する**。書き忘れるとクラス方式として扱われ、[4 章](#impl) の通りその場で実行されて壊れる。

<a id="default-args"></a>

## 3. `(actions$ = inject(Actions))` の正体

これは NgRx 独自の文法ではなく、**JavaScript のデフォルト引数**そのもの。

```js
function greet(name = "ゲスト") { ... }

greet();         // name は "ゲスト"
greet("山田");   // name は "山田"
```

呼ぶ側が値を渡さなければ `=` の右側が評価される、というだけのルール。effect に当てはめると：

| 呼ぶ人 | 呼び方 | `actions$` の中身 |
|---|---|---|
| NgRx（本番） | `loadUsers()` — 引数なし | `inject(Actions)` の結果＝本物 |
| テストコード | `loadUsers(fakeActions$, fakeApi)` | 渡した偽物 |

NgRx が引数なしで呼んでいることは実装で確認できる（`ngrx-effects.mjs` の `mergeEffects`）。

```js
const observable$ = typeof sourceInstance[propertyName] === 'function'
    ? sourceInstance[propertyName]()      // ← 関数方式。引数なしで呼ぶ
    : sourceInstance[propertyName];       // ← クラス方式。既に Observable
```

この呼び出しは `provideEffects` が仕込む `provideEnvironmentInitializer` の中で起きるため、**Angular の injection context が有効**な状態にある。だからデフォルト引数の `inject()` が成立する。

> **関数の本体で `const actions$ = inject(Actions);` と書いてもいいのでは？**
> 本番は動く（injection context 内なので）。ただし **外から差し替える口が無くなり、テストで `TestBed` が必要になる**。関数方式の利点をそこで捨てることになるので、依存は必ずデフォルト引数で受け取る。

<a id="impl"></a>

## 4. 内部実装は 1 行

`@ngrx/effects` の `createEffect` の中身は実質これだけ。

```js
function createEffect(source, config = {}) {
    const effect = config.functional ? source : source();
    // ... メタデータを生やして返すだけ
}
```

| | 動作 | 戻り値 |
|---|---|---|
| `functional: true` | 渡された関数を **実行せずそのまま保持** | 関数 |
| 指定なし | その場で **`source()` を実行** して Observable を作る | Observable |

型定義もこの通りに分かれている。

```ts
// functional なし
declare function createEffect<...>(source: () => R, config?: C): R & CreateEffectMetadata;
// functional: true
declare function createEffect<Source extends () => Observable<Action>>(
  source: Source, config: EffectConfig & { functional: true },
): FunctionalEffect<Source>;   // = Source & メタデータ ＝ 関数のまま
```

**この 1 行の差が、以降の章の違いを全部生んでいる。**

<a id="benefits"></a>

## 5. 何が嬉しいのか

### 5-1. テストで `TestBed` が要らない

RFC（[ngrx/platform#3668](https://github.com/ngrx/platform/issues/3668)）に挙がっている理由がこれ。

> To test functional effects, we don't need `TestBed` to provide services if we inject all dependencies as effect factory parameters

クラス方式のテストは、Angular の DI 環境を組み立て → 偽の API を provider に登録 → クラスのインスタンスを取得、という手順が要る。関数方式は **ただの関数呼び出し**で済む。

```ts
it("失敗したら loadAnimalsFailed を流す", () => {
  const actions$ = of(AnimalListPageActions.opened());
  const api = { loadAnimals: () => throwError(() => new HttpErrorResponse({ status: 500 })) };

  loadAnimals(actions$, api as AnimalsApi).subscribe((action) => {
    expect(action.type).toBe("[Animals API] Load Animals Failed");
  });
});
```

**effect の数だけ効く差**なので、大規模ほど積み上がる。

<a id="pitfall"></a>

### 5-2. クラス方式の初期化順序の罠が消える

[4 章](#impl) の通り、クラス方式では `createEffect` に渡した関数が **その場で実行される**。つまり `this.actions$` はフィールド初期化の時点で読まれる。

```ts
@Injectable()
export class UsersEffects {
  loadUsers$ = createEffect(() => this.actions$.pipe(...));  // ← ここで this.actions$ を読む
  constructor(private actions$: Actions) {}                   // ← 代入されるのはこの後
}
```

`useDefineForClassFields`（**`target: ES2022` 以降の TypeScript 既定値**。このリポジトリの各 tsconfig も `ES2022`）が有効だと、
**フィールド初期化子は constructor 本体より先に走る**。結果 `this.actions$` が `undefined` のまま `.pipe()` されて実行時エラーになる。

クラス方式で回避するなら、`inject()` を **使う側より上の行**でフィールドとして受ける。

```ts
@Injectable()
export class UsersEffects {
  private actions$ = inject(Actions);                        // ← 先に宣言する必要がある
  loadUsers$ = createEffect(() => this.actions$.pipe(...));
}
```

関数方式は「NgRx が後で呼ぶ」ので、**この順序問題自体が存在しない**。

### 5-3. Angular 全体と書き方が揃う

ガードもインターセプターも既に関数方式になっている（[7 章](#history)）。effect だけクラスのまま残すと、**同じアプリの中に依存の受け取り方が 2 種類混在する**。新規参画者が「どっちで書けばいいのか」を毎回迷うコストの方が、書き換えコストより高い。

### 5-4. 正直な評価

**小さい effect 単体で見れば、得られるのは見た目の簡潔さだけ**。「多くの場面で役立つから追加された」というより、**「effect がクラスである必然性が元々なかったので、周りに合わせて外した」** という整理に近い。

RFC にも明記されている通り、クラス方式が消えるわけではない。

> This feature will not remove the ability to create effects within classes

<a id="naming"></a>

## 6. 命名 — `$` は付けない

Finnish notation の `$` は **「この変数は Observable」** という目印（→ [01_rxjs.md](./01_rxjs.md)）。

[4 章](#impl) の通り、`functional: true` の `createEffect` が返すのは **関数であって Observable ではない**。`$` を付けると型と名前が食い違う。

```ts
const loadUsers$ = createEffect(..., { functional: true });   // ✗ 中身は関数
const loadUsers  = createEffect(..., { functional: true });   // ○
```

`$` を付けたくなるのは「中で `actions$` を扱っているから」だが、**名前が指すのは戻り値の型**であって中の処理ではない。引数側の `actions$` は本物の Observable なので `$` 付きで正しい。

### なぜ `06_users_sample` は `$` 付きなのか

action をフラットに定義していると、**effect 名と action 名がぶつかる**から。

```ts
// users.actions.ts
export const loadUsers = createAction("[Users] Load");

// users.effects.ts
const loadUsers = createEffect(          // ✗ import した action と同名で衝突する
  (actions$ = inject(Actions)) => actions$.pipe(ofType(loadUsers), ...),
);
```

`$` を付ければ回避できるが、それは **action の名付けの問題を effect 側の命名で肩代わりしている**だけ。

正しい解決は **action を `createActionGroup` でまとめる**こと。`03` / `05` はこの形なので衝突が起きず、`$` なしで書けている。

```ts
// animals.actions.ts
export const AnimalListPageActions = createActionGroup({
  source: "Animal List Page",
  events: { Opened: emptyProps(), "Reload Clicked": emptyProps() },
});

// animals.effects.ts
const loadAnimals = createEffect(        // ○ 衝突しない
  (actions$ = inject(Actions), animalsApi = inject(AnimalsApi)) =>
    actions$.pipe(ofType(AnimalListPageActions.opened), ...),
);
```

action group は「どの画面/どの API が発生源か」が type 文字列に出るので、大規模では**どちらにせよこちらが標準**。`$` の要否はその副産物として決まる。

<a id="dispatch"></a>

## 7. `dispatch: false` との併用

effect が流した action を store に dispatch させたくない場合（トースト表示・画面遷移など、状態遷移を伴わない副作用）は併記する。

```ts
const showErrorToast = createEffect(
  (actions$ = inject(Actions), toast = inject(ToastService)) =>
    actions$.pipe(
      ofType(UsersApiActions.loadUsersFailed),
      tap(({ error }) => toast.error(error)),
    ),
  { functional: true, dispatch: false },
);
```

`dispatch: false` を付けると **戻り値が `Observable<Action>` である必要がなくなる**。型定義側も `functional: true` × `dispatch: false` 用のオーバーロードが独立して用意されている。

付け忘れると `tap` が素通しした元の action がもう一度 dispatch され、**無限ループになる**。

<a id="history"></a>

## 8. いつ入ったのか — 背景

関数方式の effect は **NgRx 15.2.0（2023-01-26）** で追加された。公式 CHANGELOG に該当行がある。

```
# [15.2.0] (2023-01-26)
### Features
- effects: add ability to create functional effects (#3669), closes #3668
```

その後 **NgRx 16（2023-05-09）** のリリース発表で目玉機能の 1 つとして紹介され、一般に広まった。

これは NgRx 単独の判断ではなく、**Angular 本体が先に切った舵に追随したもの**。

| 時期 | 何が起きたか |
|---|---|
| 2022-06 Angular 14 | `inject()` が constructor の外でも使えるようになった（土台） |
| 2022-09 Angular 14.2 | ルーターガードの関数方式（`CanActivateFn`） |
| 2022-11 Angular 15 | HTTP インターセプターの関数方式（`withInterceptors`） |
| **2023-01 NgRx 15.2** | **effect の関数方式（`{ functional: true }`）** |
| 2023-05 NgRx 16 | リリース発表で前面に |

同時期に standalone component が標準化されており、**「クラスや NgModule という入れ物を減らす」という一本の流れ**の中の 1 つが関数方式の effect である。`provideEffects()` や `provideState()` のような `provide〜` 系関数も、同じ流れで `NgModule` を置き換えるために生まれている。

## 9. 大規模案件での運用ルール

**配置** — effect は **更新対象の state と同じ feature 配下**に置く。root の `app.effects.ts` に集約しない。

```
features/users/store/
  users.actions.ts
  users.effects.ts     ← ここ
  users.reducer.ts
```

**export はオブジェクト 1 つにまとめる。** 個別 export すると登録側で列挙が増え、追加のたびに 2 ファイル触ることになる。

```ts
export const usersEffects = { loadUsers, showErrorToast };
```

**登録は feature の routes に寄せる。** `app.config.ts` に置くと初期バンドルに引き込まれる。lazy load したい feature は `provideState` とセットでルート配下に置く（`05_hello-http-ngrx/src/app/features/animals/animals.routes.ts` が実例）。

```ts
providers: [
  provideState(animalsFeature),
  provideEffects(animalsEffects),
],
```

**レビュー観点は 4 つ。**

1. `{ functional: true }` が付いているか（付け忘れは実行時に落ちる）
2. 依存を **デフォルト引数**で受けているか（本体で `inject()` していないか）
3. effect 名に `$` を付けていないか（[6 章](#naming)）
4. `tap` で終わる effect に `dispatch: false` が付いているか（[7 章](#dispatch)）

**混在させない。** 既存のクラス方式が残っているなら移行期限を決める。両方式が動くこと自体は問題ないが、「どちらで書くか」の判断がレビューのたびに発生する状態が問題。

## 付録. このリポジトリでの実例

| サンプル | effect ファイル | 登録場所 | 備考 |
|---|---|---|---|
| `01_hello-world-srp1` | `core/store/app.effects.ts` | root | `Actions` / `ofType` の解説コメント付き |
| `02_hello-world` | `features/color/store/color.effects.ts` | root | — |
| `03_large-scale-structure` | `features/products/store/products.effects.ts` | feature | 2 effect を 1 オブジェクトに |
| `05_hello-http-ngrx` | `features/animals/store/animals.effects.ts` | **routes（lazy）** | `catchError` の置き場所の実例 |
| `06_users_sample` | `features/users/store/users.effects.ts` | root | 命名だけ `$` 付きで不統一 |

**全サンプルが関数方式**で、クラス方式は 1 つも無い。新規実装で迷ったらこれらをそのまま写せばよい。
