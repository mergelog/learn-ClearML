# `06_users_sample` データフロー全経路

対象は `06_users_sample`（Angular 22 + NgRx 22 / standalone / signal 読み取り）。
**ボタンを 1 回押したときに、何が、どの順で起きるか**を時系列 1 本で追う。経路上のコードは全文を[付録](#appendix)に置いてあるので、ファイルを開き直す必要はない。

パスはすべて `06_users_sample/src/` からの相対。`ファイル:行` 形式なので、確認したいときだけ飛べばよい。

## 結論

- 実行時の流れは **1 本のループ**。`ボタン → action → reducer → 画面 → effect → API → action → reducer → 画面` で閉じる
- **1 回の押下で画面は 2 回描き変わる**。1 回目はローディング表示、2 回目は一覧表示。ここを 1 回だと思って読むと、effect がどこで動くのか分からなくなる
- **コードを読む向きは、実行順の逆**。「`users()` は何の値か」を知りたいときは時系列ではなく[逆引き](#lookup)から入る
- `selectUsers` を定義しているコードはどこにも無い。**`createFeature` が state のキーから自動生成する**（[→ 3-2](#generated)）
- 一番の読み間違いは **`loadUsers` が component のメソッドと action creator の 2 つある**こと（[→ 4-1](#trap-name)）
- 実行時に関わるのは、起動用の `main.ts` を除いて **8 ファイル + JSON 1 件**。`user.model.ts` は型だけ、`app.css` / `styles.css` は経路に無関係

<a id="timeline-table"></a>

## 早見表: ボタンを 1 回押すと起きること

| # | 起きること | 場所 | 画面 |
|---|---|---|---|
| ① | ボタンがクリックされる | `app.html:7` | — |
| ② | component のメソッドが action を dispatch | `app.ts:17-19` | — |
| ③ | **reducer** が `isLoading: true` にする | `users.reducer.ts:19` | — |
| ④ | **同じ action が effect にも届く**（③ の後） | `users.effects.ts:10` | — |
| ⑤ | 変更検知が走り **1 回目の再描画** | `app.html:7-13` | 「読み込み中...」／ボタン disabled |
| ⑥ | API 呼び出し（`delay(1000)` で 1 秒待つ） | `users.api.ts:11` | 待ち |
| ⑦ | 結果を `loadUsersSuccess` に変換 → NgRx が自動 dispatch | `users.effects.ts:12` | — |
| ⑧ | **reducer** が `users` を差し替え、`isLoading: false` | `users.reducer.ts:20-24` | — |
| ⑨ | **2 回目の再描画** | `app.html:15-24` | 一覧が出る／ボタン活性 |

---

<a id="timeline"></a>

## 1. 時系列: 押してから一覧が出るまで

### 全体図

```
[クリック]
app.html:7           (click)="loadUsers()"
    ↓ テンプレートの識別子は必ず App クラスのメンバ
app.ts:17            loadUsers() { this.store.dispatch(loadUsers()) }
    ↓ 引数側の loadUsers() は import した action creator（同名の別物）
users.actions.ts:4   { type: "[Users] Load" }
    │
    ├─(先) users.reducer.ts:19   isLoading: true
    │          ↓ signal が変化 → 変更検知
    │      app.html              再描画 1 回目 =「読み込み中...」
    │
    └─(後) users.effects.ts:10   ofType(loadUsers) が通す
               ↓
           users.api.ts:11       GET /api/users.json → delay(1000)
               ↓
           public/api/users.json 3 件の配列
               ↓
           users.effects.ts:12   map で loadUsersSuccess({ users }) に変換
               ↓ createEffect が返した action は NgRx が自動 dispatch
users.actions.ts:6   { type: "[Users] Load Success", users: [...] }
    ↓
users.reducer.ts:20  users を差し替え / isLoading: false
    ↓ signal が変化 → 変更検知
app.html             再描画 2 回目 = 一覧表示
```

### 1-1. クリックから dispatch まで（① ②）

```html
<button type="button" (click)="loadUsers()" [disabled]="isLoading()">
```

```ts
protected loadUsers(): void {
  this.store.dispatch(loadUsers());   // ← 引数の loadUsers は action creator
}
```

- テンプレートの `loadUsers()` は **component のメソッド**（テンプレートは暗黙に `this.`）
- `dispatch()` の中の `loadUsers()` は **import した action creator**。呼ぶと `{ type: "[Users] Load" }` というただのオブジェクトが返る
- 同名だが、メソッド側は `this.` が付かないと参照されないので衝突しない（[→ 4-1](#trap-name)）
- **この時点では通信は起きていない**。「押された」という事実を値にして Store に渡しただけ

### 1-2. reducer と effect のどちらが先か（③ ④）

Store は action を受け取ると、**先に reducer を全部走らせ、その後で `actions$` に流す**。だから effect が動き出す時点で state はもう `isLoading: true` になっている。

```ts
on(loadUsers, (state): UsersState => ({ ...state, isLoading: true })),
```

- reducer は `{ ...state }` で **新しいオブジェクトを作って返す**。既存 state は書き換えない
- reducer がやるのは `isLoading` を立てることだけ。**通信はしない**（reducer に副作用を書かない、という原則どおり）
- 戻り値に `: UsersState` を明示しているので、キーの綴り間違いはここで型エラーになる

```ts
actions$.pipe(
  ofType(loadUsers),                        // "[Users] Load" だけを通す
  switchMap(() => usersApi.getUsers()),
  map((users) => loadUsersSuccess({ users })),
)
```

- `actions$` は **アプリ全体に流れた action のストリーム**。ここが effect の入口
- `switchMap` は内側の Observable を平坦化し、**新しい値が来たら前の購読を破棄する**。連打すると先行リクエストの結果は捨てられる

### 1-3. 1 回目の再描画（⑤）

③ で変わったのは state オブジェクトと `isLoading` だけ。`state.users` は `...state` でコピーされた**同じ配列参照**なので、`selectUsers` の結果は変わらず `users` signal は通知しない。変化を出しているのは `isLoading` のほうだけである。

画面上の変化はこの 2 つ。

```html
<button ... [disabled]="isLoading()">      <!-- true → disabled -->
  {{ isLoading() ? "読み込み中..." : "ユーザーを取得" }}

@if (users().length === 0 && !isLoading()) {   <!-- false → 空メッセージが消える -->
```

タイミングの順序に注意。**④ の effect が HTTP を始めるほうが、⑤ の描画より先**。`dispatch()` はクリックハンドラの中で同期的に完了し、描画はハンドラを抜けたあとの変更検知で起きるためである。

### 1-4. API と、結果の action 化（⑥ ⑦）

```ts
getUsers(): Observable<User[]> {
  return this.http.get<User[]>("/api/users.json").pipe(delay(1000));
}
```

- `delay(1000)` は **ローディング表示を見せるための演出**。業務要件ではない
- 取得先は `public/api/users.json`（`public/` 配下はビルド時にそのまま配信される）。**サーバー実装は無い**
- `UsersApi` は action も Store も import していない。**API 層は NgRx を知らない**

結果は effect の `map` で action に変換される。

```ts
map((users) => loadUsersSuccess({ users })),
```

- ここで `dispatch` は書かない。**`createEffect` が返した action を NgRx が自動で dispatch する**
- `loadUsersSuccess` の payload の形は `props<{ users: User[] }>()` が決めている

### 1-5. 2 回目の再描画（⑧ ⑨）

```ts
on(loadUsersSuccess, (state, { users }): UsersState => ({
  ...state,
  users,
  isLoading: false,
})),
```

今度は `users` が**別の配列参照に差し替わる**ので、`users` signal も `isLoading` signal も通知する。

```html
@if (users().length > 0) {
  <ul class="user-list">
    @for (user of users(); track user.id) {
```

`users()` の `()` は **Signal の読み取り**。Signal は「呼ぶと現在値を返し、同時に “今この値を読んだ” を記録する関数」で、記録があるので値が変わるとこのテンプレートだけが再描画される。

- `async` パイプは無い。**Observable ではなく Signal だから不要**
- `subscribe` も無い。`selectSignal` は component 側に購読を作らないので、解除のコードも要らない

**effect の出口（`loadUsersSuccess`）が、そのまま reducer の入口に戻る。** ループはここで閉じる。

---

<a id="store-shape"></a>

## 2. Store の形

Store 全体はこうなっている。`selectUsers` が読んでいるのは **`state.users.users`**（外側が feature 名、内側が state のキー）。

```ts
{
  users: {          // ← usersFeature.name = "users"
    users: [],      // ← UsersState.users
    isLoading: false,
  },
}
```

この形を決めているのは `users.reducer.ts` の `UsersState` と `createFeature({ name: "users", ... })` の 2 つ、root に載せているのが `app.config.ts` の `provideStore` である。

```ts
provideStore({ [usersFeature.name]: usersFeature.reducer }),   // キーは "users" に解決される
```

`app.config.ts` の各行は、無いとこうなる。

| 行 | 無いとどうなるか |
|---|---|
| `provideStore({ ... })` | `state.users` が存在せず、selector が undefined を踏む |
| `provideEffects(usersEffects)` | dispatch しても API が呼ばれない（reducer だけ動き、`isLoading` が true のまま） |
| `provideHttpClient(withFetch())` | `HttpClient` を inject できず DI エラー |
| `UsersApi` | 同上。`@Injectable()` に `providedIn` が無いので、ここでの登録が要る |

`main.ts` は `bootstrapApplication(App, appConfig)` の 1 行だけ。読む必要はほぼ無い。

---

<a id="lookup"></a>

## 3. 逆引き: 画面の識別子から定義へ

ここからは**実行順とは逆向き**。「画面に出ているこれは何なのか」を辿る。

| 見えているもの | 正体 | 定義 | 次の行き先 |
|---|---|---|---|
| `users()` | Signal の読み取り | `app.ts:14` | `UsersSelectors.selectUsers` |
| `isLoading()` | Signal の読み取り | `app.ts:15` | `UsersSelectors.selectIsLoading` |
| `loadUsers()`（テンプレート内） | component のメソッド | `app.ts:17` | `store.dispatch(loadUsers())` |
| `loadUsers()`（`app.ts` の dispatch 内） | **import した action creator** | `users.actions.ts:4` | reducer と effect の両方 |
| `user.name` / `user.email` | `@for` のループ変数のプロパティ | `user.model.ts:1` | 型定義のみ。実体は JSON |
| `/api/users.json` | 静的スタブ | `public/api/users.json` | 配信元。サーバー実装は無い |

ジャンプ先は**規約で決まる**。`UsersSelectors` と書いてあれば `features/users/store/users.selectors.ts`、それ以外の場所には無い。

### 3-1. `users()` の定義を最後まで辿る

```
app.html:17          users()
    ↓ 同じクラスのプロパティを読む
app.ts:14            protected readonly users = store.selectSignal(UsersSelectors.selectUsers)
    ↓ 定数オブジェクトのプロパティ
users.selectors.ts:8 UsersSelectors.selectUsers  ── 4 行目の selectUsers を再公開しているだけ
    ↓
users.selectors.ts:4 const selectUsers = usersFeature.selectUsers
    ↓ ここで定義行が途切れる（自動生成）
users.reducer.ts:15  createFeature({ name: "users", reducer: ... })
    ↓ 生成のもとになる state の形
users.reducer.ts:5   interface UsersState { users: User[]; isLoading: boolean }
```

`app.ts` の書き方から読み取れることは以下。

| 書いてあるもの | 意味 |
|---|---|
| `protected` | **テンプレートから参照できる最小の可視性**。`private` はテンプレート型チェックで弾かれる。外部コンポーネントからは触れない |
| `private readonly store` | テンプレートから `store` は触らせない、という意思表示 |
| `selectSignal(...)` | selector の結果を読み取り専用の Signal にして返す。**component 側に購読が生まれない** |
| 型注釈が無い | `Signal<User[]>` / `Signal<boolean>` が selector から推論される。型を知りたければ selector を見る |

`users.selectors.ts` については 2 点。

- `UsersSelectors` は **クラスではなく、selector を束ねた定数オブジェクト**
- `selectIsLoading` の `createSelector` は現状 **素通し**（`usersFeature.selectIsLoading` と結果は同じ）。加工が増えたときの置き場所を空けてある形と読む

component が feature の内部を直接見ず `UsersSelectors` 経由で読む形にしておくと、あとで state の持ち方を変えても component 側は無傷で済む。

<a id="generated"></a>

### 3-2. `usersFeature.selectUsers` の定義が見つからない

**`createFeature` が state のキーから自動生成している。grep しても定義行は出てこない。**

| `usersFeature` が持つもの | 中身 | 由来 |
|---|---|---|
| `.name` | `"users"` | `name` に書いた文字列 |
| `.reducer` | reducer 本体 | `reducer` に渡したもの |
| `.selectUsersState` | feature 全体を返す selector | `select` + name + `State` |
| `.selectUsers` | `state.users.users` | **state のキー `users`** |
| `.selectIsLoading` | `state.users.isLoading` | **state のキー `isLoading`** |

つまり **`UsersState` にキーを 1 つ足すと、同名の selector が 1 つ増える**。逆に「この selector はどこ？」と探して見つからないときは、`createFeature` の自動生成を疑えばよい。

---

## 4. 読み間違えやすい 2 か所

<a id="trap-name"></a>

### 4-1. `loadUsers` が 2 つある

```ts
import { loadUsers } from "./features/users/store/users.actions";   // ← action creator

protected loadUsers(): void {          // ← component のメソッド
  this.store.dispatch(loadUsers());    // ← ここの loadUsers() は import した action の方
}
```

同じスコープに同名が 2 つあるが、**メソッド側は `this.` が付かないと参照されない**ので衝突しない。

| 書かれている場所 | どちらか |
|---|---|
| `app.html` の `(click)="loadUsers()"` | component のメソッド（テンプレートは暗黙に `this.`） |
| `app.ts` の `this.store.dispatch(loadUsers())` | import した action creator |
| `users.reducer.ts` / `users.effects.ts` の `loadUsers` | action creator |

### 4-2. 「1 回押して 1 回描画」だと思ってしまう

reducer が 2 回動くので、描画も 2 回起きる（[→ 1 節](#timeline)）。`loadUsers` の reducer を「何もしていない」と読み飛ばすと、ローディング表示がどこから出ているか分からなくなる。

---

## 5. 変更したいとき

| ファイル | 責務 | 主な export | ここに書かないもの |
|---|---|---|---|
| `app/app.html` | 表示 | — | 分岐以上のロジック、購読 |
| `app/app.ts` | Store との接続 | `App` | 業務ロジック、通信、`subscribe` |
| `app/app.config.ts` | DI と NgRx の登録 | `appConfig` | 業務ロジック |
| `features/users/store/users.actions.ts` | 出来事の定義 | `loadUsers`, `loadUsersSuccess` | 処理 |
| `features/users/store/users.reducer.ts` | state の形と更新 | `UsersState`, `usersFeature` | 通信、時間、乱数 |
| `features/users/store/users.selectors.ts` | state の公開窓口 | `UsersSelectors` | 更新処理 |
| `features/users/store/users.effects.ts` | 副作用 | `usersEffects` | state の直接更新 |
| `features/users/data-access/users.api.ts` | HTTP | `UsersApi` | Store の知識（action / state） |
| `features/users/data-access/user.model.ts` | 型 | `User` | 実装 |

### 逆引き

| やりたいこと | 触る場所 | 連鎖して直す場所 |
|---|---|---|
| 表示項目を増やす（例: `age`） | `user.model.ts` | JSON、`app.html` |
| 一覧を絞り込んで表示する | `users.selectors.ts` に `createSelector` を足す | `app.ts` で新 selector を `selectSignal` |
| 通信先を変える | `users.api.ts` | なし |
| エラー表示を出す | `users.actions.ts` に failure、`users.effects.ts` に `catchError`、`users.reducer.ts` に `on`、state に `error` | selector は自動生成、`app.ts`、`app.html` |
| 別画面から同じ一覧を出す | 新 component で `UsersSelectors` を `selectSignal` | なし（Store は共有） |
| 連打時の挙動を変える | `users.effects.ts` の `switchMap` を `exhaustMap` などに | なし |

---

<a id="gap"></a>

## 6. このサンプルに無いもの

読んでいて「どこ？」となったときのために、**最初から実装されていないもの**を挙げておく。

- **失敗系**: `loadUsersFailure` も `catchError` も無い。通信が失敗すると effect のストリームがエラーで終わり、NgRx が再購読して次の action を待てる状態には戻る。ただし **`isLoading` を false に戻す action が無い**ため true のまま残り、ボタンが disabled のままになる
- **ルーティング**: `provideRouter` は無い。画面は `App` 1 枚
- **feature 単位の遅延登録**: `provideState(usersFeature)` ではなく `provideStore` で root に直接登録している。画面が増えたら feature routes 側へ移すのが通例
- **テスト**: spec ファイルは無い
- **`@ngrx/entity`**: `users` は素の配列。ID 引きが要るようになったら `createEntityAdapter` を検討する

---

<a id="appendix"></a>

## 付録. 経路上のコード全文

### `app/app.html`

```html
<main class="page">
  <section class="card">
    <p class="eyebrow">Angular 22 + NgRx</p>
    <h1>ユーザー一覧</h1>
    <p class="flow">ボタン → loadUsers → Effect → API → loadUsersSuccess → Reducer → Store</p>

    <button type="button" (click)="loadUsers()" [disabled]="isLoading()">
      {{ isLoading() ? "読み込み中..." : "ユーザーを取得" }}
    </button>

    @if (users().length === 0 && !isLoading()) {
      <p class="empty">ボタンを押すと、Action から Store 保存までの流れが動きます。</p>
    }

    @if (users().length > 0) {
      <ul class="user-list">
        @for (user of users(); track user.id) {
          <li>
            <strong>{{ user.name }}</strong>
            <span>{{ user.email }}</span>
          </li>
        }
      </ul>
    }
  </section>
</main>
```

### `app/app.ts`

```ts
import { Component, inject } from "@angular/core";
import { Store } from "@ngrx/store";
import { loadUsers } from "./features/users/store/users.actions";
import { UsersSelectors } from "./features/users/store/users.selectors";

@Component({
  selector: "app-root",
  templateUrl: "./app.html",
  styleUrl: "./app.css",
})
export class App {
  private readonly store = inject(Store);

  protected readonly users = this.store.selectSignal(UsersSelectors.selectUsers);
  protected readonly isLoading = this.store.selectSignal(UsersSelectors.selectIsLoading);

  protected loadUsers(): void {
    this.store.dispatch(loadUsers());
  }
}
```

### `app/app.config.ts`

```ts
import { provideHttpClient, withFetch } from "@angular/common/http";
import { ApplicationConfig, provideBrowserGlobalErrorListeners } from "@angular/core";
import { provideEffects } from "@ngrx/effects";
import { provideStore } from "@ngrx/store";
import { UsersApi } from "./features/users/data-access/users.api";
import { usersEffects } from "./features/users/store/users.effects";
import { usersFeature } from "./features/users/store/users.reducer";

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideHttpClient(withFetch()),
    provideStore({ [usersFeature.name]: usersFeature.reducer }),
    provideEffects(usersEffects),
    UsersApi,
  ],
};
```

### `features/users/store/users.actions.ts`

```ts
import { createAction, props } from "@ngrx/store";
import { User } from "../data-access/user.model";

export const loadUsers = createAction("[Users] Load");

export const loadUsersSuccess = createAction(
  "[Users] Load Success",
  props<{ users: User[] }>(),
);
```

- `"[Users] Load"` は **action の識別子**。DevTools に出る文字列であり、`ofType` / `on` の照合キー
- `props<{ users: User[] }>()` は **payload の型宣言**。`loadUsersSuccess({ users })` と呼ぶ形が確定する

### `features/users/store/users.reducer.ts`

```ts
import { createFeature, createReducer, on } from "@ngrx/store";
import { User } from "../data-access/user.model";
import { loadUsers, loadUsersSuccess } from "./users.actions";

export interface UsersState {
  users: User[];
  isLoading: boolean;
}

const initialState: UsersState = {
  users: [],
  isLoading: false,
};

export const usersFeature = createFeature({
  name: "users",
  reducer: createReducer(
    initialState,
    on(loadUsers, (state): UsersState => ({ ...state, isLoading: true })),
    on(loadUsersSuccess, (state, { users }): UsersState => ({
      ...state,
      users,
      isLoading: false,
    })),
  ),
});
```

### `features/users/store/users.selectors.ts`

```ts
import { createSelector } from "@ngrx/store";
import { usersFeature } from "./users.reducer";

const selectUsers = usersFeature.selectUsers;
const selectIsLoading = createSelector(usersFeature.selectIsLoading, (isLoading) => isLoading);

export const UsersSelectors = {
  selectUsers,
  selectIsLoading,
};
```

### `features/users/store/users.effects.ts`

```ts
import { inject } from "@angular/core";
import { Actions, createEffect, ofType } from "@ngrx/effects";
import { map, switchMap } from "rxjs";
import { UsersApi } from "../data-access/users.api";
import { loadUsers, loadUsersSuccess } from "./users.actions";

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

| 部品 | 読み方 |
|---|---|
| `{ functional: true }` | クラスではなく関数として書く方式。依存はデフォルト引数の `inject()` で受ける（[→ 04_functionalEffects.md](./04_functionalEffects.md)） |
| `actions$` | **アプリ全体に流れた action のストリーム**。ここが effect の入口 |
| `ofType(loadUsers)` | `"[Users] Load"` だけを通す |
| `switchMap` | 内側の Observable を平坦化し、**新しい値が来たら前の購読を破棄する** |
| `map(...)` | HTTP の結果を `loadUsersSuccess` **action に変換**している。ここで dispatch は書かない |
| 戻り値 | `createEffect` が返した action を **NgRx が自動で dispatch する** |
| `export const usersEffects = { loadUsers$ }` | `provideEffects()` に渡すオブジェクト。effect を足したらこのオブジェクトに追加する |

### `features/users/data-access/users.api.ts`

```ts
import { HttpClient } from "@angular/common/http";
import { Injectable, inject } from "@angular/core";
import { Observable, delay } from "rxjs";
import { User } from "./user.model";

@Injectable()
export class UsersApi {
  private readonly http = inject(HttpClient);

  getUsers(): Observable<User[]> {
    return this.http.get<User[]>("/api/users.json").pipe(delay(1000));
  }
}
```

### `features/users/data-access/user.model.ts`

```ts
export interface User {
  id: number;
  name: string;
  email: string;
}
```

`app.html` の `user.name` / `user.email` の根拠はここ。

### `public/api/users.json`

```json
[
  { "id": 1, "name": "田中", "email": "tanaka@example.com" },
  { "id": 2, "name": "佐藤", "email": "sato@example.com" },
  { "id": 3, "name": "鈴木", "email": "suzuki@example.com" }
]
```

## 関連資料

- [00_ngrx.md](./00_ngrx.md) — NgRx の API 早見表
- [01_rxjs.md](./01_rxjs.md) — `switchMap` などの演算子
- [02_pipeOfHtml.md](./02_pipeOfHtml.md) — テンプレートの `|`
- [03_subscribe.md](./03_subscribe.md) — なぜ component に `subscribe` を書かないか
- [04_functionalEffects.md](./04_functionalEffects.md) — `{ functional: true }`
