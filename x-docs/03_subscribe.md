# NgRx を使う大規模案件での `subscribe` 作法

## 結論

- **画面に出すための `subscribe` は 0 にできる。0 にすべき**。購読は Angular（`async` / `selectSignal`）と NgRx（`createEffect`）に任せる
- **残るのは「NgRx の外の世界」との境界だけ**。外部ライブラリ、DOM、SDK、テスト。ここは無理に消さない
- 書く場合は **`takeUntilDestroyed()` とセットで、橋渡し 1 行に留める**。`subscribe` の中で分岐やロジックを書き始めたら設計を疑う

判断の軸は「その `subscribe` は**値を見たいのか**、**外の世界を動かしたいのか**」。前者なら消せる。後者なら残ってよい。

## 早見表

| やりたいこと | `subscribe` | 代わりに書くもの | 詳細 |
|---|---|---|---|
| state を画面に出す | ✗ | `store.selectSignal()` / `async` パイプ | [→](#alt) |
| API を叩く | ✗ | `createEffect` + `switchMap` | [→](#why) |
| debounce・throttle して state を更新 | ✗ | `createEffect`（時間も副作用） | [→](#why) |
| 通信結果でトーストを出す・画面遷移する | ✗ | `createEffect(..., { dispatch: false })` | [→](#uc-04) |
| state を外部ライブラリのメソッドに流す | △ | まず `effect()`、無理なら subscribe | [→](#uc-01) |
| フォームの入力を action に変換する | △ | `toSignal` + `effect()` か subscribe | [→](#uc-02) |
| WebSocket・online/offline を state に取り込む | ✗ | `createEffect`（source は `Actions` でなくてよい） | [→](#uc-03) |
| ダイアログの結果を待つ | △ | effect 内で `switchMap`。component 起点なら subscribe | [→](#uc-05) |
| トークン更新・アイドル監視を常駐させる | ✗ | root の effect | [→](#uc-06) |
| SDK のリスナを張る／外す | ○ | subscribe（`finalize` で後始末） | [→](#uc-07) |
| テストで値を検証する | ○ | subscribe / marble | [→](#uc-09) |
| state を読んで `if` 分岐したい | ✗ | selector か `concatLatestFrom` | [→](#ng) |
| component で state を購読して dispatch | ✗ | それは effect の仕事 | [→](#ng) |

## 書く前の 4 つの質問

1. **画面に出すだけか？** → `selectSignal` / `async`。ここで subscribe したら負け
2. **通信・時間・乱数・履歴操作が絡むか？** → effect。component には書かない
3. **NgRx の外のもの（DOM・ライブラリ・SDK）を動かすのか？** → 橋渡しの subscribe は可。ただし [必須ルール](#rules) を守る
4. **1 回だけ値が欲しいのか？** → `firstValueFrom` か `take(1)`。購読を張りっぱなしにしない

---

以下、詳細。

<a id="why"></a>

## 1. なぜ NgRx だと `subscribe` が消えるのか

自前で RxJS の store を組むと、**ストリームを回し続ける主体**を自分で持つことになる。だから購読も自分で始めて自分で終わらせる必要がある。

```ts
// RxJS 手組みの store（04 のサンプル）
this.reload$
  .pipe(
    switchMap(() => this.animalsApi.loadAnimals().pipe(...)),
    takeUntilDestroyed(this.destroyRef),   // ← 寿命管理も自分
  )
  .subscribe((partial) => this.patch(partial));   // ← 購読も自分
```

NgRx はこの 3 つの責任を全部引き取る。

| 自前で持っていたもの | NgRx では |
|---|---|
| ストリームを購読する主体 | `EffectsModule`（`createEffect` の戻り値を購読するのは NgRx） |
| 購読の寿命管理 | `provideEffects()` を書いたルート／インジェクタの寿命 |
| 画面への配信 | `store.selectSignal()` / `async` パイプ（購読は Angular） |

結果、**アプリケーションコードに購読の面倒を見る理由が残らない**。

```ts
// NgRx（05 のサンプル）。subscribe はどこにもない
const loadAnimals = createEffect(
  (actions$ = inject(Actions), animalsApi = inject(AnimalsApi)) =>
    actions$.pipe(
      ofType(AnimalListPageActions.opened, AnimalListPageActions.reloadClicked),
      switchMap(() => animalsApi.loadAnimals().pipe(...)),
    ),
  { functional: true },
);
```

ここで重要なのが、**effect の入力は `Actions` でなくてよい**という点。`createEffect` は「Observable を返す関数」であればよく、`Actions` はその代表例にすぎない。これを知っていると、常駐監視の subscribe はほぼ全部 effect に畳める（[2-3](#uc-03), [2-6](#uc-06)）。

<a id="usecases"></a>

## 2. それでも `subscribe` が必要になるユースケース

大規模案件で実際に残るものを、出現頻度の高い順に並べる。

<a id="uc-01"></a>

### 2-1. 命令的な外部ライブラリへ state を流し込む

**状況** — AG Grid、Google Maps、Chart.js、Monaco Editor、動画プレイヤー、canvas。「値をバインドする」のではなく「メソッドを呼べ」という API を持つライブラリ。

```ts
constructor() {
  this.store
    .select(AnimalsSelectors.selectKeyword)
    .pipe(takeUntilDestroyed())
    .subscribe((keyword) => this.gridApi.setGridOption("quickFilterText", keyword));
}
```

**先に検討すべきこと** — 入力プロパティでバインドできないか。AG Grid なら `[quickFilterText]="keyword()"` で済むし、Angular 側で `toSignal` + `effect()` にも書き換えられる。

```ts
private readonly keyword = this.store.selectSignal(AnimalsSelectors.selectKeyword);

constructor() {
  effect(() => this.gridApi.setGridOption("quickFilterText", this.keyword()));
}
```

**判断** — 新規なら `effect()` が第一候補。ただし「初回は流さない」「前回値と比較する」「デバウンスする」といった条件が付くと RxJS の方が素直なので、そこは subscribe でよい。

<a id="uc-02"></a>

### 2-2. Reactive Forms の `valueChanges` を action に変換する

**状況** — 検索条件フォーム、明細行の一括編集。フォームは Angular が持つ独自の状態で、NgRx の外にある。

```ts
constructor() {
  this.searchForm.valueChanges
    .pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed())
    .subscribe((value) => this.store.dispatch(SearchFormActions.changed({ value })));
}
```

**注意** — これは「component で subscribe して dispatch」だが、[3 章](#ng) の禁止パターンとは**別物**。禁止なのは *store の値* を subscribe して dispatch するケース（action の連鎖が DevTools から切れる）。こちらは *NgRx の外のイベント源* を action の入口に変換しているので、むしろ正しい位置にある。

**先に検討すべきこと** — debounce を effect 側に持てるなら、component は生の値を dispatch するだけにできる（05 のサンプルがこの形）。フォームの状態そのものを NgRx に載せるかどうかは別問題で、**載せない方が普通**（`@ngrx/forms` 系が定着しなかったのはそのため）。

<a id="uc-03"></a>

### 2-3. NgRx の外のイベント源を state に取り込む

**状況** — WebSocket、SSE、`BroadcastChannel`、`online`/`offline`、`visibilitychange`、`storage` イベント、Service Worker からの通知。

**これは subscribe ではなく effect にできる。** `Actions` を入力にしない effect を書けばよい。

```ts
const trackNetworkStatus = createEffect(
  () =>
    merge(fromEvent(window, "online"), fromEvent(window, "offline")).pipe(
      map(() => NetworkActions.statusChanged({ online: navigator.onLine })),
    ),
  { functional: true },
);

const receiveNotifications = createEffect(
  (socket = inject(NotificationSocket)) =>
    socket.messages$.pipe(map((message) => NotificationApiActions.received({ message }))),
  { functional: true },
);
```

大規模で「外部イベントの購読があちこちの component に散っている」のは、この形を知らないことが原因であることが多い。**外から来る出来事も action にする**のが NgRx の一貫した書き方。

**subscribe が残るのは** — 受け取った値を state に載せず、その場で外部ライブラリに渡すだけのとき（[2-1](#uc-01) に合流する）。

<a id="uc-04"></a>

### 2-4. state に載せない一過性の処理

**状況** — CSV / PDF ダウンロード、印刷、クリップボードコピー、トースト表示、画面遷移。結果が状態にならず、誰も後から参照しない処理。

**第一候補は `dispatch: false` の effect。**

```ts
const downloadCsv = createEffect(
  (actions$ = inject(Actions), exportApi = inject(ExportApi)) =>
    actions$.pipe(
      ofType(AnimalListPageActions.csvDownloadClicked),
      exhaustMap(() => exportApi.downloadCsv()),   // 連打しても 1 回だけ
      tap((blob) => saveAs(blob, "animals.csv")),
    ),
  { functional: true, dispatch: false },
);
```

`dispatch: false` を付ける限り、**購読は NgRx 側**なので subscribe は書かない。`exhaustMap` による二重送信防止や、失敗時の action 化がタダで付いてくるのが effect にする利点。

**subscribe（または `firstValueFrom`）が現実解になるのは** — 開発者ツールのような画面固有の使い捨て処理で、action を 1 つ増やす方が読み手のコストになる場合だけ。**大規模では原則こちらを選ばない。**

<a id="uc-05"></a>

### 2-5. ダイアログ・確認モーダルの結果待ち

**状況** — 「本当に削除しますか？」→ OK なら削除 action。

**effect 起点にできるなら** subscribe は不要。

```ts
const confirmDelete = createEffect(
  (actions$ = inject(Actions), dialog = inject(MatDialog)) =>
    actions$.pipe(
      ofType(AnimalListPageActions.deleteClicked),
      exhaustMap(({ animalId }) =>
        dialog
          .open(ConfirmDialog)
          .afterClosed()
          .pipe(
            filter((confirmed): confirmed is true => confirmed === true),
            map(() => AnimalsDialogActions.deleteConfirmed({ animalId })),
          ),
      ),
    ),
  { functional: true },
);
```

**subscribe が残るのは** — ダイアログを開くのが component 側の都合（フォームの入力値を渡す、開いた位置を保持する等）で、結果だけを dispatch する構成にしたとき。`afterClosed()` は 1 回で complete するので `takeUntilDestroyed()` は必須ではないが、**付けておいた方が事故が少ない**（ダイアログを閉じる前に画面が破棄されるケース）。

<a id="uc-06"></a>

### 2-6. アプリ常駐の監視処理

**状況** — アクセストークンの自動更新、アイドルタイムアウトによる強制ログアウト、定期ポーリング、セッション切れ検知。

**これも root の effect に置ける。**

```ts
const refreshToken = createEffect(
  (auth = inject(AuthService)) =>
    timer(0, TOKEN_REFRESH_INTERVAL_MS).pipe(
      exhaustMap(() => auth.refresh()),
      map((token) => AuthApiActions.tokenRefreshed({ token })),
      catchError(() => of(AuthApiActions.sessionExpired())),
    ),
  { functional: true },
);
```

**注意点** — root で `provideEffects` した effect は**アプリの寿命と同じ**なので止まらない。ポーリングを画面の表示中だけにしたいなら、`opened` / `closed` の action で `switchMap` + `takeUntil` を組む。

```ts
actions$.pipe(
  ofType(DashboardPageActions.opened),
  switchMap(() =>
    timer(0, POLLING_INTERVAL_MS).pipe(
      takeUntil(actions$.pipe(ofType(DashboardPageActions.closed))),
      ...
    ),
  ),
)
```

<a id="uc-07"></a>

### 2-7. サードパーティ SDK のリスナ管理

**状況** — 決済 SDK、地図 SDK、WebRTC、分析 SDK。`addListener` / `removeListener` のような後始末が必要で、しかも Observable を返してこないもの。

```ts
const marker$ = new Observable<MarkerEvent>((subscriber) => {
  const handler = (event: MarkerEvent) => subscriber.next(event);
  sdk.addListener("markerClick", handler);
  return () => sdk.removeListener("markerClick", handler);   // ← 後始末をここに閉じる
});
```

こう包んでしまえば、あとは [2-3](#uc-03) と同じで effect に流せる。**「SDK のイベントを Observable に包む層」を 1 枚作る**のが大規模での定石で、これをやらないと SDK の解除漏れが component 全体に散る。

<a id="uc-08"></a>

### 2-8. アプリ境界（マイクロフロントエンド / Web Components / iframe）

**状況** — 別チームのアプリに state を渡す、`postMessage` で受け取る、カスタムエレメントのプロパティに値を書き込む。

境界の向こう側は NgRx を知らないので、**受け渡しは必ず命令的**になる。ここは subscribe（または `effect()`）で橋渡しするしかない。渡す形は selector で作った ViewModel に固定し、**state の内部構造をそのまま外へ出さない**。

<a id="uc-09"></a>

### 2-9. テストコード

制限なし。reducer と selector は同期関数なのでそのまま呼べるが、effect のテストは subscribe か marble になる。

```ts
it("失敗したら loadAnimalsFailed を流す", () => {
  const actions$ = of(AnimalListPageActions.opened());
  const api = { loadAnimals: () => throwError(() => new HttpErrorResponse({ status: 500 })) };

  loadAnimals(actions$, api as AnimalsApi).subscribe((action) => {
    expect(action.type).toBe("[Animals API] Load Animals Failed");
  });
});
```

`{ functional: true }` の effect は**ただの関数**なので、DI を経由せず引数で差し替えられる。これが functional effect の一番の利点で、テストのために `TestBed` を組む必要がない。

<a id="uc-10"></a>

### 2-10. レガシーとの共存（移行期）

NgRx 導入前の `BehaviorSubject` サービスが残っている期間。両方から読むために subscribe が必要になる。

**必ず期限を決める。** 恒久的に残すと「state の正が 2 つある」状態が固定化し、NgRx を入れた意味がなくなる。移行中は **NgRx → レガシー の一方向**（NgRx を正とし、レガシー側へ流し込むだけ）に限定すると壊れにくい。

<a id="uc-11"></a>

### 番外. 特定の action を 1 回だけ待つ

```ts
this.actions$
  .pipe(ofType(AnimalsApiActions.saveSucceeded), take(1), takeUntilDestroyed())
  .subscribe(() => this.dialogRef.close());
```

component（特にダイアログ）で「保存が終わったら閉じる」をやりたいときに出てくる形。`take(1)` があるので購読は残らないが、**同じことは effect でも書ける**（`dispatch: false` + `tap` で `dialogRef.close()`）。ダイアログの参照を effect から触りたくない、という理由でのみ許容する。

<a id="ng"></a>

## 3. 書いたら設計ミスのサイン

| 書き方 | 何が壊れるか | 正しい置き場所 |
|---|---|---|
| component で **store を** subscribe して dispatch | action の連鎖が DevTools から切れ、再現手順が追えなくなる | effect |
| `createEffect` の中で `subscribe()` | NgRx と二重購読になる。`catchError` の位置もずれて再試行が死ぬ | `pipe` で完結させる |
| `store.select(...).subscribe(v => { if (v) ... })` | 判定ロジックが画面に散る。テストに TestBed が必要になる | selector、または effect の `concatLatestFrom` |
| subscribe の中で subscribe | 解除漏れ・実行順の非決定・エラーの握り潰し | `switchMap` / `concatMap` / `exhaustMap` |
| `store.subscribe()`（Store 自体を購読） | state 全体に反応するので、無関係な更新で毎回動く | 必要な slice の selector |
| API サービスの中で subscribe | 呼び出し側が結果を受け取れず、エラーも伝播しない | Observable を返して effect に任せる |
| `takeUntilDestroyed()` の無い subscribe | 画面遷移のたびに購読が積み上がる。長時間運用で顕在化する | [4 章](#rules) |

特に 1 行目は、**NgRx を入れた価値がそこだけ消える**ので優先的に潰す。

<a id="rules"></a>

## 4. どうしても書くときの必須ルール

**1. `takeUntilDestroyed()` を必ず付ける**

```ts
// constructor / field 初期化なら引数なしでよい（注入コンテキスト内）
.pipe(takeUntilDestroyed())

// ngOnInit など注入コンテキストの外では DestroyRef を渡す
private readonly destroyRef = inject(DestroyRef);
.pipe(takeUntilDestroyed(this.destroyRef))
```

`take(1)` や `first()` で必ず complete する場合も、**付けておく方を既定**にする。「complete するはず」の前提はレビューでは検証できない。

**2. 単発なら購読を張らない**

```ts
const animals = await firstValueFrom(this.store.select(AnimalsSelectors.selectAnimals));
```

**3. `subscribe` の中身は 1 動作に留める**

橋渡し以上のことを書き始めたら、それは effect か selector に移す対象。

**4. `error` コールバックを省かない**

```ts
.subscribe({
  next: (value) => this.gridApi.setGridOption("quickFilterText", value),
  error: (error: unknown) => this.logger.error(error),
});
```

`next` だけを渡す形だとエラーが未処理例外になり、**その購読はそこで死ぬ**（以後 next が来ない）。値の流し込みが静かに止まる、という一番調査しづらい障害になる。

**5. ローディング解除は `finalize`**

`next` 側に書くと、エラー時に解除されずスピナーが回りっぱなしになる。

<a id="alt"></a>

## 5. 代替手段の使い分け

| 手段 | 使いどころ | 購読するのは誰か |
|---|---|---|
| `store.selectSignal(selector)` | テンプレートに出す。既定はこれ | Angular |
| `async` パイプ | テンプレートに出す（signal 化しない方針のとき） | Angular |
| `toSignal(obs$)` | NgRx 外の Observable をテンプレートに出す | Angular |
| `effect(() => ...)`（Angular の signal effect） | signal の変化を外部 API に流す | Angular |
| `createEffect` | 通信・時間・外部イベント。state を動かす副作用すべて | NgRx |
| `createEffect(..., { dispatch: false })` | state を動かさない副作用（遷移・保存・トースト） | NgRx |
| `firstValueFrom` / `take(1)` | 命令的な処理の途中で 1 回だけ値が欲しい | 呼び出し側（すぐ終わる） |
| `subscribe` | 上のどれにも当てはまらない境界 | 自分（＝ルールが要る） |

**`effect()` と `createEffect` の使い分け** — 名前が紛らわしいが別物。前者は Angular の signal API で **描画側の副作用**（DOM・ライブラリ操作）、後者は NgRx の **状態遷移の副作用**（通信・action 発行）。`effect()` の中で dispatch したくなったら、それは `createEffect` に置くべき処理。

<a id="ops"></a>

## 6. チーム運用

**レビュー観点は 3 つだけ**にすると回る。

1. その `subscribe` は境界か？（[2 章](#usecases) のどれに当たるか言えるか）
2. `takeUntilDestroyed()` が付いているか
3. 中身は橋渡し 1 行か

**Lint で機械的に落とす。** `eslint-plugin-rxjs-angular` の `prefer-takeuntil` で 2 番は自動化できる。`@ngrx/eslint-plugin` にも effect 内での dispatch 禁止など規約系のルールが入っているので、導入バージョンで `npx eslint --print-config <file>` を見て有効なものを確認しておく。

**新規参画者への説明**は「subscribe 禁止」ではなく **「購読は Angular と NgRx の仕事。あなたが書くのは境界だけ」** と伝える。禁止だと理由が伝わらず、`take(1)` を付けて隠すような回避が始まる。

<a id="sample"></a>

## 付録. このリポジトリでの実例

| サンプル | `.subscribe(` の数 | 内訳 |
|---|---|---|
| `03_large-scale-structure`（NgRx） | 0 | — |
| `04_hello-http-rxjs`（RxJS 手組み） | 2 | `animals.store.ts` の HTTP 接続と debounce 接続 |
| `05_hello-http-ngrx`（NgRx） | 0 | 04 の 2 つがそのまま `createEffect` になった |

04 → 05 の差分がそのまま「[1 章](#why) で消えた 2 つの subscribe」に対応している。逆に、05 でクイックフィルタを `[quickFilterText]` バインドではなく `gridApi.setGridOption()` で当てる設計にしていたら、[2-1](#uc-01) の subscribe が 1 つ増えていた。

**つまり、subscribe の数はライブラリではなく境界の設計で決まる。** NgRx を入れれば消えるのではなく、「バインドで済ませられる形にしたか」で決まる。
