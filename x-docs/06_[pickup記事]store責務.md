
# 06_[pickup記事]store責務

````
■以下前提で読むこと

逆に、大規模でも classic が効いてくる分岐点
users という feature 名のままでも、こうなった瞬間に話が変わります。

受注画面の担当者セレクト、ヘッダのアバター、権限チェックが同じ users を参照し始める
loadUsersSuccess に対して reducer 更新 + アナリティクス送信 + キャッシュ書き込み、と複数の effect が並列に反応する
[Auth] Logout や router action のような横断 action で users も一緒に畳む必要が出る
つまり「users で閉じているか」がそのまま判定条件で、これは案件規模とは独立です。大規模案件でも feature 内で閉じた state は山ほどあります。
````

> ngrx使いすぎ対策で、SignalStoreを使うって感じですか

かなり近い理解です。ただ、正確には「NgRxを使いすぎないためにSignalStoreを使う」というより、

**「Global Store が必要ない状態まで Classic NgRx に載せないために、SignalStoreを使う」**

という考え方です。

NgRx公式も、`@ngrx/store` は基本的にアプリ全体で共有するグローバル状態向けで、ローカルな状態には `@ngrx/signals` を検討する、という整理をしています。現在はローカル状態管理について NgRx Signals が推奨されています。([NgRx][1])

たとえば、今まで何でもClassic NgRxに載せる設計だと、

Component
→ `dispatch(loadUsers)`
→ Effect
→ API
→ `loadUsersSuccess`
→ Reducer
→ State
→ Selector
→ Component

となります。

これは「複数画面から使うユーザー情報」「認証状態」「アプリ全体の権限」「複数機能が依存するデータ」なら非常に強いです。

でも、たとえば半導体案件で「Task一覧画面」があって、

* 現在選択しているTask
* フィルタ条件
* ソート条件
* ページ番号
* ローディング状態
* 画面で取得したTask一覧

くらいしかないなら、Classic NgRxにすると少し大げさになります。

SignalStoreならイメージとしては、

```ts
export const TaskStore = signalStore(
  withState({
    tasks: [],
    selectedTaskId: null,
    loading: false
  }),

  withMethods((store) => ({
    selectTask(id: string) {
      patchState(store, {
        selectedTaskId: id
      });
    }
  }))
);
```

くらいで済みます。

つまり、

```text
Classic NgRx

Component
   ↓ dispatch
Action
   ↓
Effect
   ↓
API
   ↓
Action
   ↓
Reducer
   ↓
Store
   ↓
Selector
   ↓
Component
```

に対して、

```text
SignalStore

Component
   ↓
store.loadTasks()
   ↓
API
   ↓
patchState()
   ↓
Signal
   ↓
Component
```

という、かなり短い経路にできます。

ここが「NgRx使いすぎ対策」に見える理由です。

ただし、SignalStoreもNgRxです。`@ngrx/signals` が提供している正式なNgRxの状態管理方式で、単なるAngular `signal()` のラッパーという位置づけではありません。公式も「fully-featured state management solution」としています。([NgRx][2])

なので、実務ではこう考えるとかなり整理しやすいです。

| 状態                                  | 第一候補                   |
| ----------------------------------- | ---------------------- |
| Component内だけ                        | Angular `signal()`     |
| 画面・Feature内で共有                      | **SignalStore**        |
| 複数Featureをまたぐ重要状態                   | **Classic NgRx Store** |
| Action履歴が重要                         | **Classic NgRx Store** |
| 多数のEffectが連鎖する業務処理                  | **Classic NgRx Store** |
| filter / sort / selection / loading | **SignalStore**        |
| 単純なUI開閉状態                           | `signal()`             |
| 認証・権限などアプリ全体                        | Classic NgRx候補         |

特に重要なのが、

**「状態が複雑だからNgRx Store」ではない**

というところです。

SignalStoreもかなり複雑な状態を扱えます。Entity管理やRxJS連携、イベントベースの状態管理までNgRx Signals側に用意されています。([NgRx][2])

Classic NgRxを選ぶ本当の理由は、

**Actionを中心にシステム全体の状態遷移を明示したいか**

です。

たとえば、

```text
ユーザーが工程変更
    ↓
changeProcessRequested
    ↓
権限確認
    ↓
API更新
    ↓
changeProcessSucceeded
    ↓
Task更新
    ↓
Dataset更新
    ↓
監査ログ更新
    ↓
通知
```

みたいな処理なら、

「何が起きたか」

をActionとして残せるClassic NgRxの価値が大きくなります。

逆に、

```text
Taskをクリック
↓
selectedTaskId = 123
↓
右ペインに詳細表示
```

程度なのに、

```text
selectTask Action
↓
Reducer
↓
Selector
```

まで作ると、まさに「NgRx使いすぎ」です。

なので以前話していたClearML系Angular案件に当てはめるなら、かなり自然なのは、

```text
Angularアプリ

Global
├─ Authentication        Classic NgRx
├─ User / Permission     Classic NgRx候補
└─ Global configuration  Classic NgRx候補

Feature
├─ Task selection        SignalStore
├─ Dataset filter        SignalStore
├─ Experiment table      SignalStore
├─ Artifact selection    SignalStore
└─ Graph UI state        SignalStore

Component
├─ dialogOpen            signal()
├─ selectedTab           signal()
└─ form入力              Reactive Forms等
```

という3階層です。

要するに、

**何でもStore → Classic NgRxの使いすぎ**

から、

**Component固有 → signal()
Feature状態 → SignalStore
アプリ全体・イベント駆動 → Classic NgRx**

と振り分けられるようになった、と捉えるとかなり正確です。

そしてこれは、以前出てきた「Task selectionへのNgRx Signal Store採用」という設計とも非常に相性がいいです。Task選択程度のFeature状態なら、まさにClassic NgRxよりSignalStoreに寄せる合理性があります。([NgRx][3])

[1]: https://ngrx.io/guide/store?utm_source=chatgpt.com "NgRx"
[2]: https://ngrx.io/guide/signals?utm_source=chatgpt.com "NgRx"
[3]: https://ngrx.io/guide/signals/signal-store?utm_source=chatgpt.com "NgRx"
