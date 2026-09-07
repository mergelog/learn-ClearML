ClearMLのコードリーディングを想定して、**「何を見たら何だと判断するか」まで含めた表**にします。優先度は、まず読むべき順です。

| 分類             | 関数・クラス                      | 主なimport元                    | 何をするか                            | コードで見たときの意味                         | 優先度 |
| -------------- | --------------------------- | ---------------------------- | -------------------------------- | ----------------------------------- | --- |
| Action         | `createAction()`            | `@ngrx/store`                | Actionを1個定義する                    | 「何かが起きた」というイベントを作っている               | ★★★ |
| Action         | `props()`                   | `@ngrx/store`                | Actionに渡すデータ型を定義                 | API結果やIDなどをActionに載せる               | ★★★ |
| Action         | `emptyProps()`              | `@ngrx/store`                | createActionGroup() でデータなしActionを定義 | 「ロード開始」のように引数不要のイベント                | ★★  |
| Action         | `createActionGroup()`       | `@ngrx/store`                | 関連Actionをまとめて定義                  | Load / Success / Failureなどを一か所に整理   | ★★★ |
| Reducer        | `createReducer()`           | `@ngrx/store`                | State更新ロジックを定義                   | 「Actionを受けてStateをどう変えるか」            | ★★★ |
| Reducer        | `on()`                      | `@ngrx/store`                | 特定Actionに対応する更新処理                | このActionが来たら、このState変更を行う           | ★★★ |
| Feature        | `createFeature()`           | `@ngrx/store`                | Feature単位でReducer・Selector等をまとめる | Modern NgRxでよく見るFeature定義           | ★★★ |
| Selector       | `createSelector()`          | `@ngrx/store`                | Stateから派生値を作る                    | 複数Stateを加工して画面用データを作る               | ★★★ |
| Selector       | `createFeatureSelector()`   | `@ngrx/store`                | Feature State全体を取得               | 古典的NgRxでよく見るFeature入口               | ★★  |
| Store          | `Store`                     | `@ngrx/store`                | Global Store本体                   | ComponentやServiceからNgRxへアクセスする入口    | ★★★ |
| Store          | `store.dispatch()`          | `Store` instance             | Actionを発火する                      | 「処理を開始してくれ」とNgRxへ通知                 | ★★★ |
| Store          | `store.select()`            | `Store` instance             | StateをObservableとして読む            | 従来NgRxの標準的State購読                   | ★★★ |
| Store          | `store.selectSignal()`      | `Store` instance             | StateをSignalとして読む                | Modern AngularとNgRxを直接つなぐ           | ★★★ |
| Provider       | `provideStore()`            | `@ngrx/store`                | Root Storeを登録                    | Standalone AngularでNgRx本体を有効化       | ★★★ |
| Provider       | `provideState()`            | `@ngrx/store`                | Feature Stateを登録                 | Feature単位でReducerをアプリに追加            | ★★★ |
| Effect         | `Actions`                   | `@ngrx/effects`              | 発火したActionのObservable            | EffectがActionを監視する入口                | ★★★ |
| Effect         | `createEffect()`            | `@ngrx/effects`              | 副作用処理を作る                         | API通信などReducerでやらない処理               | ★★★ |
| Effect         | `ofType()`                  | `@ngrx/effects`              | 特定Actionだけ抽出                     | 「このActionのときだけ処理する」                 | ★★★ |
| Provider       | `provideEffects()`          | `@ngrx/effects`              | Effectを登録                        | Standalone構成でEffectを有効化             | ★★★ |
| Operator       | `concatLatestFrom()`        | `@ngrx/operators`            | Actionに最新Stateを付ける               | Effect処理時に現在のStore値も参照する            | ★★★ |
| Operator       | `tapResponse()`             | `@ngrx/operators`            | Observableの成功・失敗処理を整理            | SignalStoreのAPI処理で頻出                | ★★★ |
| Entity         | `createEntityAdapter()`     | `@ngrx/entity`               | Entity操作用Adapterを作る              | 配列ではなくIDベースでデータ管理                   | ★★  |
| Entity         | `adapter.getInitialState()` | Entity Adapter               | Entity State初期値を作る               | `ids` と `entities` を持つStateを初期化     | ★★  |
| Entity         | `adapter.getSelectors()`    | Entity Adapter               | Entity Selectorを自動生成             | 全件取得、ID取得などを自動生成                    | ★★  |
| Entity         | `adapter.addOne()`          | Entity Adapter               | 1件追加                             | 新しいEntityをStoreへ追加                  | ★★  |
| Entity         | `adapter.addMany()`         | Entity Adapter               | 複数追加                             | API取得データを追加する場合など                   | ★★  |
| Entity         | `adapter.setAll()`          | Entity Adapter               | 全Entityを置き換える                    | 一覧API結果でStoreを全更新                   | ★★★ |
| Entity         | `adapter.updateOne()`       | Entity Adapter               | 1件部分更新                           | IDを指定して一部だけ更新                       | ★★  |
| Entity         | `adapter.updateMany()`      | Entity Adapter               | 複数部分更新                           | 一括更新                                | ★★  |
| Entity         | `adapter.upsertOne()`       | Entity Adapter               | あれば更新、なければ追加                     | API結果同期などで便利                        | ★★  |
| Entity         | `adapter.upsertMany()`      | Entity Adapter               | 複数Upsert                         | 大量データ同期                             | ★★  |
| Entity         | `adapter.removeOne()`       | Entity Adapter               | 1件削除                             | ID指定削除                              | ★★  |
| Entity         | `adapter.removeMany()`      | Entity Adapter               | 複数削除                             | 条件付き削除など                            | ★★  |
| Entity         | `adapter.removeAll()`       | Entity Adapter               | 全削除                              | Storeを空に戻す                          | ★★  |
| Router         | `getRouterSelectors()`      | `@ngrx/router-store`         | Router用Selector群を生成              | URLやroute paramをStore経由で読む          | ★★  |
| Router         | `selectUrl`                 | Router selectors             | 現在URL取得                          | Router状態をNgRxから参照                   | ★★  |
| Router         | `selectRouteParam()`        | Router selectors             | URLパラメータ取得                       | `/task/:id` の `id` など               | ★★  |
| Router         | `selectQueryParam()`        | Router selectors             | Query parameter取得                | `?page=3` のような値                     | ★★  |
| SignalStore    | `signalStore()`             | `@ngrx/signals`              | Signal Store本体を定義                | Classic NgRxとは別系統のStore             | ★★★ |
| SignalStore    | `withState()`               | `@ngrx/signals`              | State定義                          | SignalStoreが保持する値を定義                | ★★★ |
| SignalStore    | `withComputed()`            | `@ngrx/signals`              | 派生Signalを定義                      | Stateから計算値を作る                       | ★★★ |
| SignalStore    | `withMethods()`             | `@ngrx/signals`              | Store操作メソッドを追加                   | Componentから呼ぶ処理の入口                  | ★★★ |
| SignalStore    | `withProps()`               | `@ngrx/signals`              | Service等の依存値を追加                  | API ServiceなどをStore内部で利用            | ★★  |
| SignalStore    | `withHooks()`               | `@ngrx/signals`              | init / destroy処理                 | Store生成時・破棄時の処理                     | ★★  |
| SignalStore    | `patchState()`              | `@ngrx/signals`              | Stateを部分更新                       | SignalStore版Reducer的な役割             | ★★★ |
| SignalStore    | `getState()`                | `@ngrx/signals`              | 現在Stateのsnapshot取得               | 現在値全体をその場で読む                        | ★★  |
| SignalStore    | `rxMethod()`                | `@ngrx/signals/rxjs-interop` | RxJSベースのStoreメソッド                | API・検索・非同期処理で重要                     | ★★★ |
| SignalStore    | `signalMethod()`            | `@ngrx/signals`              | Signal変化に応じて処理                   | Signal中心のリアクティブ処理                   | ★★  |
| Signal Entity  | `withEntities()`            | `@ngrx/signals/entities`     | SignalStoreにEntity管理を追加          | SignalStore版Entityの入口               | ★★  |
| Signal Entity  | `addEntity()`               | `@ngrx/signals/entities`     | Entity追加                         | `patchState(store, addEntity(...))` | ★★  |
| Signal Entity  | `setAllEntities()`          | `@ngrx/signals/entities`     | Entity全件置換                       | 一覧API取得後など                          | ★★  |
| Signal Entity  | `updateEntity()`            | `@ngrx/signals/entities`     | Entity更新                         | SignalStore Entityの1件更新             | ★★  |
| Signal Entity  | `removeEntity()`            | `@ngrx/signals/entities`     | Entity削除                         | SignalStore Entityの1件削除             | ★★  |
| ComponentStore | `ComponentStore`            | `@ngrx/component-store`      | Component付近のLocal State管理        | 旧来のLocal Store方式                    | ★   |
| ComponentStore | `setState()`                | ComponentStore               | State全体を変更                       | ComponentStoreでState設定              | ★   |
| ComponentStore | `patchState()`              | ComponentStore               | State部分更新                        | SignalStore版とは別物なので注意               | ★   |
| ComponentStore | `updater()`                 | ComponentStore               | 更新関数を定義                          | Reducerに近い役割                        | ★   |
| ComponentStore | `effect()`                  | ComponentStore               | 副作用処理を定義                         | ComponentStore専用Effect              | ★   |

NgRxを読むうえでは、さらにRxJSがほぼセットです。

| RxJS                     | 役割              | NgRxでよく出る場面               | 優先度 |
| ------------------------ | --------------- | ------------------------- | --- |
| `pipe()`                 | Operatorを連結     | Effect / rxMethod全般       | ★★★ |
| `map()`                  | 値を変換            | API結果→Actionなど            | ★★★ |
| `tap()`                  | 値を変えず副作用        | ログなど                      | ★★★ |
| `filter()`               | 条件で絞る           | 不要データ除外                   | ★★★ |
| `switchMap()`            | 前処理をキャンセルし最新優先  | 検索、条件変更、再取得               | ★★★ |
| `concatMap()`            | 順番に1件ずつ実行       | 更新処理を順序保証したい              | ★★★ |
| `mergeMap()`             | 並列処理            | 独立した複数処理                  | ★★★ |
| `exhaustMap()`           | 実行中は次を無視        | ログイン、保存ボタン連打防止            | ★★★ |
| `catchError()`           | エラー処理           | API失敗→Failure Action      | ★★★ |
| `of()`                   | 値をObservable化   | Success/Failure Actionを返す | ★★★ |
| `EMPTY`                  | 何も流さず終了         | エラー時など                    | ★★  |
| `debounceTime()`         | 一定時間待つ          | 検索入力                      | ★★  |
| `distinctUntilChanged()` | 同じ値を無視          | 検索条件・filter               | ★★  |
| `take()`                 | 指定回数だけ取得        | Stateを1回だけ読む等             | ★★  |
| `combineLatest()`        | 複数Observableを合成 | 複数条件から画面状態を作る             | ★★  |

特に最初は、全部を横並びで覚える必要はありません。

**最優先はこの15個前後です。**

| 順番 | 覚えるもの                 | 理由                |
| -- | --------------------- | ----------------- |
| 1  | `createAction()`      | NgRxのイベント起点       |
| 2  | `props()`             | Actionにデータを載せる    |
| 3  | `createActionGroup()` | 現代的なAction定義      |
| 4  | `createReducer()`     | State更新本体         |
| 5  | `on()`                | ActionとReducerを接続 |
| 6  | `Store`               | NgRxの入口           |
| 7  | `dispatch()`          | Action発火          |
| 8  | `select()`            | State取得           |
| 9  | `createSelector()`    | State加工           |
| 10 | `createEffect()`      | APIなど副作用          |
| 11 | `Actions`             | EffectのAction入力   |
| 12 | `ofType()`            | Actionを絞る         |
| 13 | `switchMap()`         | API通信の中心          |
| 14 | `catchError()`        | API失敗処理           |
| 15 | `concatLatestFrom()`  | Effect + Store連携  |

ここまで分かれば、Classic NgRxはかなり読めます。

その後に、

**`signalStore → withState → withComputed → withMethods → rxMethod → patchState`**

を覚える。

ClearMLを読む前提では、この二系統を頭で分離するとかなり楽です。

| Classic NgRx   | SignalStore             |
| -------------- | ----------------------- |
| `Action`       | method呼び出し              |
| `dispatch()`   | Store method            |
| `Effect`       | `rxMethod()`            |
| `Reducer`      | `patchState()`          |
| `Selector`     | Signal / computed       |
| Global Store中心 | Feature/local Storeにも向く |
| RxJS中心         | Signal + RxJS           |

つまりコードを開いて、

```ts
this.store.dispatch(...)
```

が出たら、

**「Classic NgRxルートだな」**

と判断。

一方、

```ts
patchState(store, ...)
```

や

```ts
rxMethod(...)
```

が出たら、

**「SignalStoreルートだな」**

と判断する。

この判別ができるだけで、大規模コードの見通しがかなり良くなります。
