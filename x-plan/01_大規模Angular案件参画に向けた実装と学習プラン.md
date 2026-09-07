# 大規模Angular案件参画に向けた実装と学習プラン

この資料のプランでユーザーのスキルアップをフォローすること
完了した項目は、
`01_大規模Angular案件参画タスクチェック表`
に随時マークしていく

## 1. 目的

このプロジェクトを教材として、次の状態を目指す。

> MLOpsドメインを理解し、ClearMLベースの大規模Angularコードを読める・説明できる・安全に変更できるフロントエンドエンジニアになる。

主軸はAngular / TypeScript / RxJS / NgRxである。ClearML、Queue、Agent、Pipeline、Model Registry、Servingは、Angularのボタンの向こうで起きる業務処理を理解するためのドメイン学習と位置付ける。

ゴールは、画面を新規に大量実装することや、機械学習アルゴリズムを深く研究することではない。既存の大規模コードを読解し、責務と変更影響を判断し、テストで安全性を証明しながら小さく改修する力を身につける。

## 2. 学習の優先配分

```text
Angular / TypeScript / RxJS / NgRx  最優先
ClearML / MLOps                    高
Python / ML基盤                   中
MLアルゴリズム                  低
```

目安として、実装・学習時間の50〜60%をAngular / TypeScript / RxJS / NgRxに使う。ClearML / MLOpsは25〜35%、Python / ML基盤は10〜15%とし、MLアルゴリズムの比較や精度改善は、AngularとClearMLの接続理解を妨げない範囲に限る。

## 3. P0〜P3の意味

| Priority | Angularの学習段階 | 到達像 |
| --- | --- | --- |
| P0 | Angularを実務で読んで動かす | 既存の処理経路を追い、小さな機能をテスト付きで変更できる |
| P1 | Angularを運用システムとして扱う | 失敗、遅延、権限、観測性を含めた業務画面として改善できる |
| P2 | Angularを大規模案件の品質へ引き上げる | 型、境界、state、性能、accessibility、テストを体系的に改善できる |
| P3 | チームでAngularを安全に変更し続ける | 設計判断、所有権、レビュー、リリース、運用を標準化できる |

P0とP1にもAngular学習が含まれる。P2で初めてAngularに着手する計画ではない。P0で実コードに必要な要素を都度学び、P2で設計原則と品質基準を体系化する。

## 4. 到達度の判定基準

各機能を次の3段階で評価する。学習済みとみなすのはLevel 3に到達したときである。

```text
Level 1: 読める
  主要なファイルと責務を特定できる

Level 2: 説明できる
  入力、state遷移、API、失敗経路、出力を図なしでも説明できる

Level 3: 壊さず変更できる
  仕様変更を小さな差分で実装し、必要なテストを追加し、影響範囲を説明できる
```

## 5. 実装と学習の進め方

### 5.1 1機能完成→徹底読解→小改修

P0〜P3を一度に実装しない。原則として1〜3日を目安に、独立して実行・確認できる小さな完成単位へ分け、次のループを回す。ただし、日数は達成目標や打ち切り条件にしない。ClearML Webの既存NgRxコードなど、読解に時間が必要な対象は、処理経路と設計理由の理解が浅いまま次の機能へ進まない。完了は日数ではなく、Level 3の到達基準で判定する。

```text
1. 対象ユースケースと完了条件を決める
2. 既存の処理経路と変更境界を探す
3. 設計上の選択肢と理由を確認する
4. コーディングエージェントに1機能だけ実装させる
5. diffをファイルごとに読む
6. 処理経路、state遷移、失敗時の動作を自分の言葉で説明する
7. 自分で別の小変更を加える
8. テストを意図的に壊し、原因を確認して直す
9. 学び、設計理由、未解決事項を短く記録する
```

作業量の目安は、コーディングエージェントによる実装70〜80%、自分による読解・判断・変更20〜30%とする。ただし、次の設計判断は理由を確認せずに採用しない。

- stateをどのfeatureが所有するか
- Classic NgRx、Signals、SignalStore、component local stateをどこで使うか
- Effectの責務と配置先
- API model、domain model、view modelの変換境界
- polling、retry、timeout、cancelの責務
- Task、Pipeline、ModelのIDをどの期間保持するか
- feature間の依存をどの境界で止めるか

### 5.2 常にAngularへ戻る

MLOps機能だけを連続して実装し、Angularを最後に回さない。機能を1つ学ぶたびに、対応するClearML Webの画面とAngularコードへ戻る。

```text
Queue / Agentを動かす
  -> ClearML WebでQueue、Worker、Task statusを確認する
  -> Angularで表示に使うAPI、state、selectorを追う
  -> loading / failure表示を1つ変更する

Pipelineを動かす
  -> ClearML Webでstep、依存関係、停止箇所を確認する
  -> AngularでPipeline取得から表示までを追う
  -> step failureの表示を1つ変更する

Modelを登録・昇格する
  -> ClearML Webでmodel metadataと元Taskを確認する
  -> Angularでmodel取得、表示、操作権限を追う
  -> evaluation resultを1項目追加する
```

### 5.3 新規実装より先に既存コードを読む

ClearML Webに既存機能がある場合は、学習のためだけに同じ画面を作り直さない。まず既存実装をtraceし、学習目標を満たす最小の変更を加える。新規画面は、既存画面で縦スライスを検証できない場合に限る。

## 6. P0: AngularからMLOps基盤までの縦スライス

### P0-0. 学習ベースラインと安全網

**実装**

- 現在のPython test、Angular unit test、E2E typecheck、production buildを1つの共通入口から実行できるようにする
- CIで変更範囲のtest、typecheck、buildが実行される最小構成を用意する
- 新規・変更範囲で既存のlint負債を増やさない基準を決める
- 既存コード読解用の記録テンプレートを用意する

**Angularで読む対象**

- 起動処理、root providers、root routes、lazy route
- 対象featureのrouteからcontainer / presentational componentまで
- store provider、action、reducer、effect、selector、serviceの配置
- 生成API clientまたはserviceとinterceptorの呼び出し

**自分で行う小改修**

- 既存画面の表示項目またはselectorを1つ追加する
- 対応するunit testを追加する

**完了条件**

- 変更前のテスト結果を再現できる
- routeからAPI request、responseから画面までの主要ファイルを特定できる
- Angularの小改修とテストを完了できる

### P0-1. Task一覧・詳細で基本フローを読む

**学習する処理経路**

```text
Routing
  -> Component
  -> Signal / Observable
  -> Store
  -> Action
  -> Effect
  -> API Client
  -> ClearML API
  -> Response
  -> Reducer / State
  -> Selector
  -> Component
```

**Angularの重点**

- Standalone ComponentとDI
- Classic NgRxのaction / reducer / effect / selector
- Signals、SignalStore、Observableの使われ方
- RxJSの主要operatorとcancelの発生条件
- HttpClient、interceptor、API errorの変換
- loading / success / empty / failureのstate表現
- `takeUntilDestroyed`等によるsubscriptionの寿命管理
- facadeがある場合のcomponentとstoreの境界

**自分で行う小改修の候補**

- loadingまたはempty stateの表示改善
- Task status用selectorの追加
- API errorの表示分け
- 再読込み操作と多重request防止

**完了条件**

- Task一覧とTask詳細の少なくとも1経路をコード上で端から端まで追える
- action、effect、API、reducer、selectorの役割を対象コードに即して説明できる
- 小改修に対するstate遷移のunit testを書ける

### P0-2. Queue / AgentとAngularのTask状態表示

**MLOps実装**

- 学習用Dockerfileと`clearml-agent`を用意する
- ローカル実行とQueue投入を同じ設定contractで扱う
- Git SHA、image識別子、Dataset ID、Queue名をTaskへ記録する
- 正常Taskと代表的な失敗Taskを実行する

**Angularで読む・変更する対象**

- Queue / Worker / Task statusのAPI requestとresponse model
- statusのdomain / view model変換
- pollingまたは再取得の開始、停止、cancel条件
- 完了、失敗、abort、通信失敗の表示分け
- Task IDをstateに保持する期間

**自分で行う小改修**

- polling間隔または停止条件の変更
- status表示の1状態追加
- Queue待機中と実行中の表示分け

**完了条件**

- `Angular -> ClearML API -> Task -> Queue -> Agent -> Container -> train.py -> Output Model`を説明できる
- 古いrequestのresponseや画面破棄後のpollingで誤ったstateを表示しない
- 正常系と少なくとも1つの失敗系をtestで確認できる

### P0-3. PipelineとAngularの実行経路

**MLOps実装**

- `validate dataset -> preprocess -> train -> evaluate -> register candidate`を独立Taskとして構成する
- Artifact、Dataset Version、依存関係を明示する
- Dataset検証失敗時は後続stepへ進まないようにする

**Angularで読む・変更する対象**

- Pipeline一覧、詳細、step表示のrouteとcomponent構造
- controller取得、起動、abortのaction / effect / API
- Pipeline IDと各Task IDの対応
- step stateと画面表示の変換
- 起動中の二重操作防止とAPI error handling

**自分で行う小改修**

- validation failureを汎用的な「失敗」ではなく停止step付きで表示する
- Pipeline起動後のTask IDまたはstep statusの表示を追加する

**完了条件**

- `Component -> Action -> Effect -> API Client -> ClearML API -> Pipeline -> Task`を追跡できる
- `Task response -> Reducer / State -> Selector -> Component`を追跡できる
- Pipelineの正常完了とvalidation failureを画面とtestの両方で確認できる

### P0-4. Evaluation Gate / Model RegistryとAngularのモデル表示

**MLOps実装**

- recallとF1の最小合格基準を設定化する
- 基準未達モデルをcandidate以降へ進めない
- candidate / staging / productionの昇格と承認者、理由、元Task、Dataset ID、評価結果を記録する
- 直前のproduction modelへのrollback手順を用意する

**Angularで読む・変更する対象**

- model一覧・詳細のAPI、state、selector、component
- model metadataと画面表示値の変換
- modelから元Task、Dataset、評価指標への導線
- 昇格・却下・rollback操作の権限と確認ダイアログ

**自分で行う小改修**

- F1に加えてrecallを表示する
- 基準未達の理由を表示する
- production昇格不可時の操作制御を追加する

**完了条件**

- 画面のmodelから学習Task、コード、Dataset、評価、承認履歴へ追跡できる
- 基準未達時とAPI失敗時のUIを区別できる
- 評価項目の追加をmodel境界とtestを保って実装できる

### P0-5. ServingとAngularからの利用確認

**MLOps実装**

- production modelを読み込む最小のonline推論APIを作る
- 入出力schema、health / readiness、model versionを明示する
- 不正入力、timeout、model読込失敗のcontract testを用意する
- 新旧modelの切替とrollbackを確認する

**Angularで読む・変更する対象**

- request / response modelとform値の変換
- validation error、server error、timeoutの表示境界
- 実行中の二重送信防止とcancel
- 使用されたmodel versionの表示

**自分で行う小改修**

- 新しい入力validationまたは推論結果項目を1つ追加する
- timeout時のretry導線を追加する

**完了条件**

- productionへ昇格したmodelだけが推論に使われる
- Angular requestからmodel version付きresponseまでを説明できる
- 正常、4xx、5xx、timeoutのUI状態をtestで確認できる

### P0総合演習

次の縦スライスを1回通し、操作、通信、state遷移、ドメイン処理を説明する。

```text
AngularでPipelineを起動
  -> ClearML API
  -> Pipeline Controller
  -> Dataset validation
  -> Queue / Agent
  -> Train / Evaluate
  -> Evaluation Gate
  -> candidate登録
  -> production昇格
  -> Serving
  -> Angularで状態・評価・model versionを確認
```

P0の最終完了条件は、一連の正常系に加え、Dataset validation failureまたはAgent failureのどちらかを発生させ、Angularが「失敗しました」だけでなく停止箇所と次の行動を表示できることとする。

## 7. P1: Angularを運用システムとして扱う

### P1-1. Observabilityと障害追跡

```text
User operation
  -> Angular request / correlation ID
  -> ClearML API
  -> Task ID / Pipeline ID
  -> Queue / Agent
  -> Artifact / Model
```

**実装・学習項目**

- Angularから送るcorrelation IDとTask IDを構造化ログで接続する
- request成功率、latency、Queue滞留、Pipeline失敗を可視化する
- UIにユーザー向けの原因と運用者向けの追跡IDを分けて表示する
- API停止、Agent停止、遅延を注入し、UIから原因Taskへ到達する

### P1-2. Error handlingと復旧可能なUX

**実装・学習項目**

- validation error、authorization error、conflict、timeout、server errorをdomain errorへ変換する
- retry可能な失敗と不可能な失敗を分ける
- optimistic updateを使う場合のrollbackをテストする
- stale response、多重click、画面遷移後のresponseを安全に扱う
- error messageに機密情報や内部stack traceを含めない

### P1-3. Authentication / Authorization / Security

```text
User
  -> Angular
  -> Authentication
  -> Authorization
  -> ClearML API
  -> Audited operation
```

**実装・学習項目**

- route guard、permission directive、画面表示制御、API認可を区別する
- UIでボタンを隠すことを認可の代わりにしない
- 権限別の許可・拒否をintegration testで確認する
- token、secret、Task Parameters、logの漏えい境界を確認する
- dependency / secret / SAST / container scanをCIに追加する

### P1-4. Data Qualityの業務表示

**実装・学習項目**

- 必須列、型、範囲、欠損率、カテゴリ、クラス比率のデータ契約を機械可読にする
- Dataset Version間のdriftとlineageをArtifactに記録する
- Angularで検証失敗の項目、期待値、実際値、対処を表示する
- 壊したDatasetを学習前に停止し、画面から原本と変換処理へ追跡する

### P1完了条件

- ユーザーが画面から失敗の種類、次の行動、問い合わせに必要なIDを判断できる
- 運用者がcorrelation IDからAPI、Task、Agentへ追跡できる
- 画面の表示制御とserver側の認可がそれぞれtestされている

## 8. P2: 大規模Angular開発の品質へ引き上げる

### P2-1. TypeScriptとmodel境界

- feature単位で`strict`へ移行し、新規コードで`any`を原則使わない
- API generated modelをcomponentへ直接流さず、API model / domain model / view modelを必要な境界で変換する
- `unknown`、discriminated union、exhaustive checkをerrorとstate表現に適用する
- nullable / optional / absentの意味を契約とtestで固定する

### P2-2. Feature構造とstate architecture

- domain単位のfeature境界、public API、禁止依存を定義する
- Effectsは更新対象stateのfeature配下に置く
- component local state、Signals、SignalStore、Classic NgRxの選択基準をADR化する
- facadeを導入する条件を明確にし、単なる中継層にしない
- selectorで導出可能なstateを重複保持しない
- ID、entity、request state、filter、selectionの所有者を明示する

### P2-3. Routing、DI、performance

- Standalone Componentとroute-level providerの境界を整理する
- featureごとにlazy loadingし、initial bundleとlazy chunkのbudgetをCIで監視する
- change detection、Signals、`track`、memoized selectorをprofiling結果に基づいて適用する
- 大量データのpagination、virtualization、request cancel、cacheを検証する
- provider scopeの間違いによるstateの重複生成をtestする

### P2-4. Testingとaccessibility

- reducer / selector / effect / adapter / componentの責務に合わせてtestする
- API contract testでAngular clientとClearML APIの破壊的変更を検知する
- 主要ユースケースだけを実ClearML ServerとE2Eで確認する
- loading、empty、failure、permission denied、retry、cancelをcomponent testで確認する
- keyboard操作、focus、label、色以外のstatus表現を自動・手動の両方で検証する
- flaky testは隔離だけで終えず、原因と再発防止を記録する

### P2-5. 段階的な品質負債の解消

- lint、runtime warning、bundle warningをbaseline化し、新規違反をCIで防ぐ
- 一括変更ではなく、業務featureの変更と同じ単位でbaselineを減らす
- 各移行でbehaviorを固定するtestを先に用意する
- 自動変換した大量diffは、意味のある変更と分離する

### P2完了条件

- 変更対象featureがstrict、lint、unit / component test、build budgetを通過する
- API変更が影響するadapter、state、selector、componentを予測できる
- feature間の禁止依存と循環依存を静的に検知できる
- 中規模の仕様変更を分割し、レビュー可能な差分で実装できる

## 9. P3: チームでAngularを安全に扱う

### P3-1. 設計・所有権・レビュー標準

- C4と主要なAngular / API / ClearMLシーケンスを保守する
- state選択、API境界、error model、feature依存をADRに残す
- CODEOWNERS相当の所有者と、横断的変更に必要なレビュアーを決める
- Definition of DoneとAngular review checklistを整備する
- 大きな変更を「contract」「state」「UI」「E2E」に分割する方針を定める

### P3-2. CI/CDとrelease運用

- test pyramidと必須jobを定義し、高コストなE2Eと高速なunit testを分ける
- API compatibility、bundle budget、accessibility、security scanをrelease gateにする
- feature flag、段階リリース、rollback、DB / API compatibilityの手順を決める
- バージョン、changelog、非互換変更の周知方法を決める

### P3-3. Onboardingと運用知識

- 新規参画者が環境構築、デバッグ、test、小改修を行うonboardingを用意する
- 主要featureごとに「どこから読むか」を記録する
- 障害、rollback、API変更、state不整合のrunbookを用意する
- postmortemで個人ではなく、test、観測性、プロセスの欠落を改善する

### P3-4. Enterprise基盤との接続

- dev / staging / productionの設定と権限を分離する
- IaC、backup / restore、RPO / RTO、capacity、cost、retentionを運用要件として定義する
- Angularが依存するAPI endpoint、authentication、feature flagの環境差分を追跡可能にする
- 環境障害時にAngularが劣化運転、復旧、ユーザー通知を行える契約を決める

### P3完了条件

- 6人、10人、20人と開発者が増えても、所有者と変更手順が不明にならない
- 新規参画者が資料だけで対象featureの処理経路を追い、小改修のPR相当を作れる
- 障害とrelease failureをrunbookに沿って切り分け、rollbackできる

## 10. 実施順序

```text
Phase 0: 現在地の固定
  test / typecheck / buildの再現
  Angularのroute -> API -> state -> UIを1本trace

Phase 1: Angular実務読解
  Task一覧・詳細をtrace
  最初の小改修とunit test

Phase 2: Queue / Agentの縦スライス
  Agent実行 -> Webで確認 -> Angularでtrace -> status小改修

Phase 3: Pipelineの縦スライス
  Pipeline実行 -> Webで確認 -> Angularでtrace -> failure小改修

Phase 4: Model lifecycleの縦スライス
  Evaluation Gate / Registry -> Angularでtrace -> evaluation小改修

Phase 5: Servingの縦スライス
  Deploy / Predict / Rollback -> Angularでtrace -> error handling小改修

Phase 6: 運用システム化
  Observability / Error / Security / Data QualityをAngularまで接続

Phase 7: 大規模Angular品質
  strict / model境界 / state / feature依存 / performance / a11y / testing

Phase 8: チーム開発標準
  ADR / ownership / DoD / review / release / onboarding / runbook
```

P0完了前に、モデル比較、HPO、特徴量開発、大規模IaC、lint全件解消へ脱線しない。これらは、縦スライスの理解に必要な不足が明確になった場合に限り、期間と完了条件を決めたスパイクとして扱う。

## 11. 1機能ごとの完了チェックリスト

- [ ] ユースケースと代表的な失敗条件が明文化されている
- [ ] 変更前に既存の処理経路をtraceしている
- [ ] state、Effect、API境界の所有者と理由を説明できる
- [ ] コーディングエージェントが作ったdiffを全て読んでいる
- [ ] 自分で仕様の異なる小変更を1つ完了している
- [ ] 正常系と代表的な失敗系のtestがある
- [ ] loading / empty / success / failure / cancelの該当stateを確認している
- [ ] subscription、polling、request cancelの寿命を説明できる
- [ ] API modelから画面表示までの変換を説明できる
- [ ] 変更の影響範囲と残るリスクを説明できる
- [ ] 学びと設計判断を短い資料に残している

## 12. 各セッションで残す読解記録

1機能につき次の内容を1ページ程度で残す。コードの要約ではなく、次回自分が変更するときの地図とする。

```text
対象ユースケース:
入力と出力:
処理経路:
stateの所有者:
API / domain / view modelの境界:
正常時のstate遷移:
失敗時のstate遷移:
cancel / retry / timeout:
主要なtest:
この設計の理由:
自分で加えた変更:
残る疑問とリスク:
```

## 13. 参画前の最終判定

次の質問に実コードとtestを根拠に回答できれば、参画準備の主目標を達成したと判断する。

1. このrouteから最初に生成されるcomponentは何か。
2. この画面のstateはどこが所有し、どこで導出されるか。
3. このactionを受けるEffectはどこにあり、なぜそこにあるか。
4. API responseはどこでdomain / view modelへ変換されるか。
5. requestの競合、cancel、retry、timeoutはどこで制御されるか。
6. Task ID、Pipeline ID、Model IDはどのstateに、いつまで保持されるか。
7. Dataset validation failureとAPI failureはUIでどう区別されるか。
8. この変更で影響を受けるfeatureとtestは何か。
9. 仕様を1つ変えるとき、最小で安全な変更単位は何か。
10. ボタンの向こうでClearMLのTask、Queue、Agent、Pipeline、Modelがどう状態遷移するか。

最終的な成果はコード量ではない。既存コードを読み、設計理由と業務処理を説明し、小さい差分で安全に変更し、testと運用上の根拠を示せることである。
