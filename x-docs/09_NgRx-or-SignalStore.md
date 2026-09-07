ただし、今後以下が増えるなら従来NgRxが有利です。
- 他featureからDashboardを更新する
- 更新元や更新理由をAction履歴で追跡したい
- 楽観更新やロールバックが多数ある
- 複数APIの成功・失敗を連携させる
- チーム全体が従来NgRxで統一されている

---

1. 他featureからDashboardを更新する

NgRxのボイラープレートをfeature外へ出す、という意味ではありません。
Dashboardのstateを更新するReducerやEffectは、引き続きDashboard feature配下に置きます。

※但し、依存経路が錯雑になる

別featureは、Dashboardのstateを直接触らずActionを通知します。

```text
Lot feature
  └─ lotStatusUpdated をdispatch
          ↓
Dashboard feature
  ├─ Effectが必要なら再取得
  └─ ReducerがDashboard stateを更新
```

たとえば業務イベントを共有します。

```ts
this.store.dispatch(
  LotActions.statusUpdated({
    lotName,
    status,
  }),
);
```

Dashboard側がそれを受け取ります。

```ts
on(LotActions.statusUpdated, (state, { lotName, status }) => ({
  ...state,
  items: state.items.map((item) =>
    item.lotName === lotName ? { ...item, status } : item,
  ),
}));
```

ただし、他featureからの更新が1、2個しかないならSignal Storeでも公開メソッドを呼べます。更新元が多数になり、feature間の直接依存が絡み始めたとき、Actionをイベントとして使う価値が出ます。

---

2. Action履歴とは

変化した項目をアプリのstateへ別途保存する、という意味ではありません。

Redux DevToolsでは、dispatchされたActionと、その前後のstateを開発時に確認できます。

```text
[Dashboard] Polling Started
[Dashboard] Load Requested
[Dashboard] Load Succeeded
[Lot Editor] Status Updated
[Dashboard] Load Requested
[Dashboard] Load Failed
```

これにより「なぜこの値になったのか」をAction単位で追えます。

ただし、これは基本的に開発用のデバッグ履歴です。業務監査ログとして永続保存したい場合は、バックエンドへ明示的に履歴を記録する必要があります。

---

3. 楽観更新とロールバックの例

現在のDashboardは参照中心なので、まだ必要ありません。

たとえばDashboardからLotのステータスを変更できる場合です。

```text
1. ユーザーが「完了」を押す
2. API完了を待たず、画面を即座に「完了」へ変更
3. API成功 → そのまま確定
4. API失敗 → 元の「処理中」へ戻してエラー表示
```

ほかには次のような操作があります。

- 行の削除
- 担当者の割り当て
- 並び替え
- お気に入り切り替え
- 複数行の一括更新

こうした操作が多数あると、「更新前の値」「処理中」「成功」「失敗」「元に戻す」という状態遷移が増えるため、ActionとReducerによる明示的な管理が効いてきます。

---

4. 複数APIの連携とは

`mergeMap` で複数APIを呼ぶこと自体ではなく、API間の成功・失敗によって状態遷移が分岐する場合です。

例えばDashboard表示に3つのAPIが必要なケースです。

```text
Lot一覧API ────── 成功
アラームAPI ──── 失敗
権限API ──────── 成功
        ↓
全体をエラーにする？
Lot一覧だけ表示する？
アラームだけ再試行する？
古いアラームを残す？
```

単純に全部揃ってから表示するなら、完了するHTTPでは `forkJoin` が分かりやすいです。

```ts
forkJoin({
  lots: this.lotApi.getLots(),
  alarms: this.alarmApi.getAlarms(),
  permissions: this.permissionApi.getPermissions(),
});
```

処理に順序があるなら `concatMap`、古い要求をキャンセルしたいなら `switchMap`、実行中の重複を無視するなら現在使っている `exhaustMap` です。

重要なのは演算子の数ではなく、部分成功・再試行・キャンセル・依存関係などの状態が増えることです。

---

5. チーム全体を従来NgRxで統一することについて

従来NgRxで統一すること自体は悪手ではありません。複雑さを先に受け入れて、どのfeatureも同じ読み方・テスト方法・デバッグ方法に揃える選択です。

ただし、単純な画面にも必ず、

```text
Action → Effect → Action → Reducer → Selector
```

を要求する運用は、現在なら過剰になりやすいです。昔に導入された「何でもNgRx」のプロジェクトがそのまま続いているケースもあります。

大規模案件では、次のように選択基準を統一するほうが現実的です。

- ローカルなUI状態：Component Signal
- feature内の共有状態：Signal Store
- featureをまたぐ重要な業務イベント：従来NgRx
- サーバーが正本の単純な取得結果：ServiceまたはSignal Store
- 永続的な業務履歴：バックエンド

今回のDashboardは、現状ならSignal Storeがちょうどよいです。将来feature間イベントが増えた時点で、従来NgRxへの移行を検討すればよく、最初からすべてをAction化する必要はないと思います。

---
---
---

> SignalStoreってまだ若いですよね。大規模案件の長年組はなかなか手付かずなのでは?

はい、相対的にはかなり若いです。

Signal StoreはNgRx v17（2023年11月）で登場し、v18（2024年7月）でDeveloper Previewを抜けてproduction-readyになりました。2026年時点でも、従来NgRx Storeに比べれば実運用の蓄積は短いです。[NgRx v17発表](https://dev.to/ngrx/announcing-ngrx-v17-introducing-ngrx-signals-operators-performance-improvements-workshops-and-more-55e4)、[NgRx Signals v18発表](https://dev.to/ngrx/announcing-ngrx-signals-v18-state-encapsulation-private-store-members-enhanced-entity-management-and-more-2lo6)

長期運用中の大規模案件が手を付けにくいのも、その通りだと思います。

- 従来NgRxがすでに安定稼働している
- 数百のAction・Reducer・Effectを移行する効果が薄い
- チームの設計規約、テスト、研修がNgRx前提
- 移行中に2種類の状態管理が混在する
- Signal Storeには従来Storeほど長い実績やDevTools統合がない

特に「コード量を減らすためだけの全面移行」は、費用に対して得られるものが小さいです。動いている従来NgRxを無理に書き換える必要はありません。NgRx公式もSignal Storeを従来Storeの後継として置き換えるのではなく、それぞれ継続する位置づけにしています。

現実的にはこうなりそうです。

```text
既存の中核機能
  → 従来NgRxを維持

新しいfeature・独立性の高い画面
  → Signal Storeを試す

単純なローカル状態
  → Angular Signal
```

そして利用実績が溜まったら、既存featureを一括ではなくfeature単位で移行します。

つまり、長年運用されている大規模案件で従来NgRxが今も健在なのは、単なる時代遅れではありません。移行メリットより安定性を選んだ合理的な判断も多いはずです。一方、今回のような新規featureでSignal Storeを採用し、比較・評価するのは非常に良い導入方法です。公式もSignal Storeをローカル／グローバル双方に提供できる設計として案内しています。[Signal Store公式ガイド](https://ngrx.io/guide/signals/signal-store)

---
---
---

> SignalStore導入すれば、新規参画者の学習難易度も重くなるしね

そこが大きな隠れコストですね。

既存案件へSignal Storeを導入すると、新規参画者は結局両方を覚える必要があります。

```text
従来NgRx
Action / Reducer / Effect / Selector / Store

Signal Store
withState / patchState / withMethods
withComputed / withHooks / rxMethod
```

さらに厄介なのは、技術そのものより「このfeatureはなぜ従来NgRxで、こちらはなぜSignal Storeなのか」という判断規則まで理解する必要がある点です。

混在させるなら、少なくとも境界を明文化しないとつらくなります。

- 既存featureは従来NgRxのまま維持
- 新規featureは原則Signal Store
- featureをまたぐ業務イベントは従来NgRx
- Signal Storeから従来Storeを直接更新しない
- 各方式の標準テンプレートを用意する
- 同一feature内では方式を混在させない

それでも、新規参画者が両方読む事実は変わりません。

なので長期案件では、「Signal Storeのコードが短い」だけでは導入理由として弱いです。移行期間中の学習コスト、レビュー基準、テスト方針、障害調査まで含めて、それでも得かを見る必要があります。

私なら既存の大規模NgRx案件では、Signal Storeをいきなり標準採用せず、今回のDashboardのような独立featureを1つ実証対象にします。その結果、保守性や開発速度に明確な差がなければ、無理に混在させません。技術選定では「新しい方式が良いか」より、「チーム全体の概念数を増やす価値があるか」のほうが重要ですね。