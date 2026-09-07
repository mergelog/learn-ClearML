
RxJSは関数がかなり多いですが、Angular / NgRxの既存コードを読む目的なら、全部暗記する必要はありません。まず下の★★★を押さえれば、かなり読めます。

RxJS公式でも、Operatorを「Transformation / Filtering / Joining / Error Handling / Utility」などに分類しています。([RxJS][1])

### RxJS 実務向け関数・Operator一覧

| 分類   | 関数・クラス                   | 何をするか                               | よくある用途                   | 重要度 |
| ---- | ------------------------ | ----------------------------------- | ------------------------ | --- |
| 生成   | `of()`                   | 普通の値からObservableを作る                 | `of(data)`、モック値、エラー時の代替値 | ★★★ |
| 生成   | `from()`                 | Promise・配列などからObservableを作る         | Promise → Observable     | ★★☆ |
| 生成   | `fromEvent()`            | DOMイベントなどをObservable化               | click、input、scroll       | ★★☆ |
| 生成   | `interval()`             | 一定間隔で値を流す                           | ポーリング、タイマー               | ★★☆ |
| 生成   | `timer()`                | 指定時間後に値を流す                          | 遅延処理、ポーリング開始             | ★★☆ |
| 生成   | `defer()`                | subscribeされた瞬間にObservableを生成        | 実行時の最新状態を使う              | ★★☆ |
| 生成   | `throwError()`           | エラーObservableを作る                    | エラーを意図的に返す               | ★★☆ |
| 変換   | `map()`                  | 流れてきた値を別の値へ変換                       | DTO → ViewModel          | ★★★ |
| 変換   | `switchMap()`            | 新しい処理が来たら前の処理をキャンセル                 | 検索、画面切替、API再取得           | ★★★ |
| 変換   | `mergeMap()`             | 複数処理を並列実行                           | 独立したAPI処理                | ★★★ |
| 変換   | `concatMap()`            | 1件ずつ順番に処理                           | 更新APIを順番に実行              | ★★★ |
| 変換   | `exhaustMap()`           | 処理中の新しい要求を無視                        | 二重送信防止、ログインボタン           | ★★★ |
| 変換   | `scan()`                 | 過去の値を蓄積しながら計算                       | 簡易State、累積値              | ★★☆ |
| 変換   | `pairwise()`             | 前回値と今回値をセットで取得                      | 値の変化比較                   | ★★☆ |
| フィルタ | `filter()`               | 条件に合う値だけ通す                          | `null`除外、状態判定            | ★★★ |
| フィルタ | `take()`                 | 指定回数だけ受信して終了                        | `take(1)` が特に多い          | ★★★ |
| フィルタ | `takeUntil()`            | 別Observableが発火したら終了                 | 古典的unsubscribe管理         | ★★★ |
| フィルタ | `takeWhile()`            | 条件を満たす間だけ受信                         | 条件付き監視                   | ★★☆ |
| フィルタ | `first()`                | 最初の値だけ取得                            | 最初のイベント待ち                | ★★☆ |
| フィルタ | `skip()`                 | 最初のN件を無視                            | 初期値を無視                   | ★★☆ |
| フィルタ | `debounceTime()`         | 一定時間入力が止まるまで待つ                      | 検索ボックス                   | ★★★ |
| フィルタ | `throttleTime()`         | 一定時間内の連続イベントを制限                     | scroll、click             | ★★☆ |
| フィルタ | `distinctUntilChanged()` | 前回と同じ値なら流さない                        | 検索文字、State監視             | ★★★ |
| 結合   | `combineLatest()`        | 複数Observableの最新値を組み合わせる             | 複数Stateから画面データ生成         | ★★★ |
| 結合   | `withLatestFrom()`       | メインObservable発火時に別Observableの最新値を取得 | Action + State           | ★★★ |
| 結合   | `forkJoin()`             | 全Observable完了後にまとめて結果取得             | 複数APIの一括取得               | ★★★ |
| 結合   | `merge()`                | 複数Observableを1本にまとめる                | 複数イベントを同じ処理へ             | ★★☆ |
| 結合   | `concat()`               | Observableを順番に実行                    | A完了 → B開始                | ★★☆ |
| 結合   | `zip()`                  | 各Observableの1件目同士、2件目同士を組み合わせる      | 同期的ペア処理                  | ★☆☆ |
| 初期値  | `startWith()`            | 最初に指定値を流す                           | loading初期値など             | ★★★ |
| 副作用  | `tap()`                  | 値を変更せず途中処理を行う                       | ログ、デバッグ、一時的副作用           | ★★★ |
| 終了処理 | `finalize()`             | complete/error/unsubscribe時に実行      | loading解除                | ★★★ |
| エラー  | `catchError()`           | エラーを捕捉する                            | APIエラー処理                 | ★★★ |
| エラー  | `retry()`                | エラー時に再実行                            | 一時的通信障害                  | ★★☆ |
| 時間   | `delay()`                | 値の通知を遅らせる                           | UI演出、テスト                 | ★☆☆ |
| 時間   | `timeout()`              | 指定時間以内に来なければエラー                     | APIタイムアウト                | ★★☆ |
| 集約   | `toArray()`              | completeまでの値を配列にまとめる                | バッチ処理                    | ★★☆ |
| 集約   | `reduce()`               | 最終結果を累積計算                           | 合計など                     | ★☆☆ |
| 共有   | `share()`                | 複数subscriberでObservable実行を共有        | 重複処理防止                   | ★★☆ |
| 共有   | `shareReplay()`          | 結果を共有し、直近値も再利用                      | API結果キャッシュ               | ★★★ |

特に重要なのが、この4兄弟です。RxJS公式でも `concatMap / mergeMap / switchMap / exhaustMap` は、Observableの中から別のObservableを作って「平坦化する」代表的なOperatorとして整理されています。([RxJS][1])

| Operator     | 新しい要求が来たら | イメージ       | Angularでの代表例 |
| ------------ | --------- | ---------- | ------------ |
| `switchMap`  | 前をキャンセル   | **最新だけ**   | 検索API        |
| `mergeMap`   | 前も新しいのも実行 | **全部並列**   | 独立した複数処理     |
| `concatMap`  | 前が終わるまで待つ | **順番待ち**   | 更新処理         |
| `exhaustMap` | 新しい要求を捨てる | **処理中は無視** | 二重クリック防止     |

ここはかなり重要です。

例えば検索欄なら、

`a`入力 → API A
`ab`入力 → API B
`abc`入力 → API C

となった場合、

`switchMap`

なら

`A キャンセル → B キャンセル → Cだけ採用`

です。

一方で `mergeMap` なら、

`A・B・C全部実行`

になるので、検索APIでは古いAのレスポンスが最後に返ってきて画面を書き換える危険があります。

逆に保存処理なら `concatMap` が、

`保存1 → 完了 → 保存2 → 完了 → 保存3`

と順序を保証するので向いています。

そして送信ボタンなら `exhaustMap`。

`クリック1 → API通信中 → クリック2・3は無視`

になります。公式の挙動も「inner Observableの実行中に新しく来た値を無視する」というものです。([RxJS][1])

NgRxを読むなら、さらにこの組み合わせが非常によく出ます。

| よく見る形                                             | 意味              |
| ------------------------------------------------- | --------------- |
| `pipe(map(...))`                                  | データ変換           |
| `pipe(filter(...))`                               | 不要データ除外         |
| `pipe(switchMap(...))`                            | 最新APIへ切替        |
| `pipe(concatMap(...))`                            | APIを順番に処理       |
| `pipe(exhaustMap(...))`                           | 二重実行防止          |
| `pipe(catchError(...))`                           | エラー処理           |
| `pipe(tap(...))`                                  | 副作用             |
| `pipe(finalize(...))`                             | 最後に必ず処理         |
| `pipe(debounceTime(...), distinctUntilChanged())` | 検索入力            |
| `combineLatest([a$, b$])`                         | 複数Stateを合成      |
| `withLatestFrom(state$)`                          | イベント発生時のState取得 |
| `forkJoin([api1$, api2$])`                        | APIを並列実行して全部待つ  |
| `take(1)`                                         | 1回だけ取得          |
| `shareReplay(1)`                                  | 最後の結果をキャッシュ・共有  |

NgRx Effectsになると、例えば概念的には、

`Action`
→ `filter的に対象Actionを選択`
→ `exhaustMap / switchMap / concatMap`
→ `API`
→ `map`
→ `成功Action`
→ `catchError`
→ `失敗Action`

という流れになります。

なので、ClearMLのような既存Angular + NgRxコードを読む目的なら、優先順位はまず

**`map` → `filter` → `tap` → `switchMap` → `mergeMap` → `concatMap` → `exhaustMap` → `catchError` → `combineLatest` → `withLatestFrom` → `take` → `debounceTime` → `distinctUntilChanged`**

くらいで十分です。

なお、以前話していたAngularの `takeUntilDestroyed()` は少し別物です。これは純粋なRxJSのOperatorではなく、AngularがRxJS連携用に提供している `@angular/core/rxjs-interop` の機能です。RxJSの `takeUntil()` をAngular向けにかなり楽にしたもの、と捉えると分かりやすいです。

次にやるなら、上の表の中でも特に混乱しやすい **`switchMap / mergeMap / concatMap / exhaustMap` を、同じAPI処理を4通りに書いて比較**すると、一気にRxJSが見えるようになります。([RxJS][2])

[1]: https://rxjs.dev/guide/operators?utm_source=chatgpt.com "RxJS - RxJS Operators"
[2]: https://rxjs.dev/guide/overview?utm_source=chatgpt.com "RxJS - Introduction"
