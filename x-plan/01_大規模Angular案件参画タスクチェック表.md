# 大規模Angular案件参画タスクチェック表

## 1. この資料の位置付け

この資料は、`01_大規模Angular案件参画に向けた実装と学習プラン.md` の進捗を日々更新するためのチェック表である。

- 学習プラン: 目的、優先順位、実施順序、完了条件を管理する。原則として頻繁に変更しない
- このチェック表: 理解度、実装状況、証跡、次に取り組む項目を管理する。作業のたびに更新する

コードや機能が存在することと、自分が理解して変更できることを分けて記録する。コーディングエージェントによる実装だけでは、Levelを上げない。

## 2. 更新ルール

### 2.1 チェックの条件

| 列 | チェックする条件 |
| --- | --- |
| Agent実装 | コーディングエージェントによる対象実装が完了し、動作確認できた |
| コード読解 | 関係する主要ファイルと責務を特定し、diffを含む対象コードを読んだ |
| 自力説明 | 処理経路、state、API、正常系、失敗系をコードを根拠に説明できた |
| 自力変更 | エージェントの実装とは別の小変更を、自分で設計して完了した |
| テスト | 変更に必要なテストを自分で追加し、意図的に失敗させて検出力も確認した |

チェックを付けるときは、原則として「9. 作業証跡」にコード、テスト、読解記録のいずれかを残す。

### 2.2 Level判定

| Level | 判定基準 |
| --- | --- |
| 0 | 未着手、またはAgent実装だけが完了している |
| 1 | 主要なファイルと責務を特定し、コードを端から端まで追える |
| 2 | 入力、state遷移、API、失敗経路、出力を自分の言葉で説明できる |
| 3 | 自分で小変更し、必要なテストを追加し、影響範囲を説明できる |

Levelは累積条件として判定する。例えば、自力変更だけを先に行っても、Level 1とLevel 2の条件を満たすまではLevel 3にしない。

### 2.3 状態

| 状態 | 意味 |
| --- | --- |
| 未着手 | 対象作業を開始していない |
| Agent実装済み | 実装は存在するが、本人のコード読解が完了していない |
| 読解中 | コードを追っている途中 |
| 説明可能 | Level 2に到達し、自力変更は未完了 |
| 自力変更中 | Level 3に向けた小変更またはテストを実施中 |
| 完了 | Level 3の条件と項目固有の完了条件を満たした |
| 保留 | 外部要因で停止中。理由と再開条件を作業証跡に記録している |

## 3. 進捗サマリー

毎回の作業開始時と終了時に更新する。詳細表と矛盾する場合は、詳細表と証跡を正とする。

| ID | 学習対象 | Level | 状態 | 現在地・次の一手 |
| --- | --- | ---: | --- | --- |
| P0-0 | 学習ベースラインと安全網 | 0 | 読解中 | lint負債を増やさない基準とコード読解テンプレートを確認する |
| P0-1 | Task一覧・詳細 | 0 | 未着手 | routeからAPI、state、UIまでを1本traceする |
| P0-2 | Queue / Agent | 0 | 未着手 | Queue投入からTask status表示までを追う |
| P0-3 | Pipeline | 0 | 未着手 | controller、step、失敗経路を追う |
| P0-4 | Evaluation / Model Registry | 0 | 未着手 | modelからTask、Dataset、評価へ追跡する |
| P0-5 | Serving | 0 | 未着手 | Angular requestからmodel version付きresponseまでを追う |
| P1-1 | Observability | 0 | 未着手 | P0完了後に着手する |
| P1-2 | Error Handling | 0 | 未着手 | P0完了後に着手する |
| P1-3 | Auth / Security | 0 | 未着手 | P0完了後に着手する |
| P1-4 | Data Quality UI | 0 | 未着手 | P0完了後に着手する |
| P2-1 | TypeScript / model境界 | 0 | 未着手 | P1完了後に体系化する |
| P2-2 | Feature / State設計 | 0 | 未着手 | P1完了後に体系化する |
| P2-3 | Routing / DI / Performance | 0 | 未着手 | P1完了後に体系化する |
| P2-4 | Testing / Accessibility | 0 | 未着手 | P1完了後に体系化する |
| P2-5 | 品質負債改善 | 0 | 未着手 | P1完了後に体系化する |
| P3-1 | 設計・所有権・レビュー標準 | 0 | 未着手 | P2完了後に着手する |
| P3-2 | CI/CDとrelease運用 | 0 | 未着手 | P2完了後に着手する |
| P3-3 | Onboardingと運用知識 | 0 | 未着手 | P2完了後に着手する |
| P3-4 | Enterprise基盤との接続 | 0 | 未着手 | P2完了後に着手する |

## 4. 全体習熟度チェック

`Agent実装` は実装手段の記録であり、Level判定には含めない。既存実装を読む項目など、Agent実装が不要な場合は `-` とする。

| ID | 学習対象 | Agent実装 | コード読解 | 自力説明 | 自力変更 | テスト | Level | 状態 |
| --- | --- | :---: | :---: | :---: | :---: | :---: | ---: | --- |
| P0-0 | 学習ベースラインと安全網 | - | [ ] | [ ] | [ ] | [ ] | 0 | 読解中 |
| P0-1 | Task一覧・詳細 | - | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P0-2 | Queue / Agent | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P0-3 | Pipeline | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P0-4 | Evaluation / Model Registry | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P0-5 | Serving | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P1-1 | Observability | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P1-2 | Error Handling | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P1-3 | Auth / Security | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P1-4 | Data Quality UI | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P2-1 | TypeScript / model境界 | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P2-2 | Feature / State設計 | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P2-3 | Routing / DI / Performance | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P2-4 | Testing / Accessibility | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P2-5 | 品質負債改善 | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P3-1 | 設計・所有権・レビュー標準 | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P3-2 | CI/CDとrelease運用 | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P3-3 | Onboardingと運用知識 | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |
| P3-4 | Enterprise基盤との接続 | [ ] | [ ] | [ ] | [ ] | [ ] | 0 | 未着手 |

## 5. P0詳細チェック

### P0-0. 学習ベースラインと安全網

#### 実行基盤

- [x] Python testを再現できる
- [x] Angular unit testを再現できる
- [x] E2E typecheckを再現できる
- [x] Angular production buildを再現できる
- [x] 上記を1つの共通入口から実行できる
- [x] 変更前の実行結果と既知の失敗を記録した
- [x] CIで変更範囲のtest、typecheck、buildを実行できる
- [x] 新規・変更範囲でlint負債を増やさない基準を説明できる
- [x] 既存コード読解用の記録テンプレートを用意した

#### Lint負債を増やさない基準

- 全体baselineは2026-09-08時点で2871 errors / 56 warningsとし、既存負債として記録する
- 新規ファイルはerror / warningともに0件を必須とする
- 既存ファイルの変更では、変更前の同一ファイルと比較してdiagnosticを増やさない
- 変更箇所に起因するdiagnosticは、ファイルに既存違反が残っていても解消する
- `eslint-disable`は対象ruleと理由を局所的に記載し、ファイル全体の無効化に使わない
- 大量の自動修正は機能変更と同じdiffへ混在させない

#### Angular読解

- [ ] 起動処理とroot providersを特定できる
- [ ] root routeから対象featureのlazy routeを追える
- [ ] container componentとpresentational componentを区別できる
- [ ] store providerの登録箇所とscopeを説明できる
- [ ] action、reducer、effect、selector、serviceの配置を説明できる
- [ ] API clientとinterceptorの呼び出しを追える

#### Level 3確認

- [ ] 既存画面の表示項目またはselectorを自分で1つ追加した
- [ ] 対応するunit testを自分で追加した
- [ ] テストを意図的に壊し、想定どおり失敗することを確認した
- [ ] 変更の影響範囲と残るリスクを説明できる

### P0-1. Task一覧・詳細

#### ドメインと画面

- [ ] Task一覧のユースケースを説明できる
- [ ] Task詳細のユースケースを説明できる
- [ ] Task statusの主要状態と遷移を説明できる
- [ ] Task一覧と詳細のrouteを特定できる
- [ ] 最初に生成されるcomponentを特定できる

#### Angular処理経路

- [ ] `Routing -> Component -> Signal / Observable`を追える
- [ ] `Component -> Action -> Effect -> API Client`を追える
- [ ] ClearML APIのrequestとresponse modelを追える
- [ ] `Response -> Reducer / State -> Selector -> Component`を追える
- [ ] Signals、SignalStore、Observableの役割分担を説明できる
- [ ] 使用されているRxJS operatorの選択理由を説明できる
- [ ] requestのcancel条件とsubscriptionの寿命を説明できる
- [ ] API errorの変換箇所を特定できる
- [ ] loading / success / empty / failureのstate表現を説明できる
- [ ] facadeがある場合、componentとstoreの境界を説明できる

#### Level 3確認

- [ ] loading、empty、status selector、error表示、再読込みのいずれかを自分で変更した
- [ ] 多重requestまたはstale responseへの対処を確認した
- [ ] state遷移のunit testを自分で追加した
- [ ] テストを意図的に壊し、想定どおり失敗することを確認した
- [ ] Task一覧または詳細の1経路を、図なしで端から端まで説明できる

### P0-2. Queue / Agent

#### MLOps実装とドメイン

- [ ] Queueとは何か説明できる
- [ ] Agentとは何か説明できる
- [ ] 学習用Dockerfileと`clearml-agent`を用意した
- [ ] ローカル実行とQueue投入で共有する設定contractを説明できる
- [ ] TaskがQueueへ投入される箇所を特定できる
- [ ] AgentがTaskを取得する流れを説明できる
- [ ] Training Containerがどこで起動するか説明できる
- [ ] `train.py`の入力と出力を説明できる
- [ ] Git SHA、image識別子、Dataset ID、Queue名の記録箇所を特定できる
- [ ] Dataset IDがどこから渡るか追える
- [ ] Task IDの生成箇所と保持期間を追える
- [ ] 正常Taskを実行した
- [ ] 代表的な失敗Taskを実行した

#### Angular処理経路

- [ ] Task statusを取得するAPIを特定できる
- [ ] Queue / Worker / Task statusのresponse modelを追える
- [ ] statusのdomain model / view model変換を追える
- [ ] `Action -> Effect -> API`を追える
- [ ] `Response -> Reducer -> Selector -> Component`を追える
- [ ] pollingの開始条件を説明できる
- [ ] pollingの停止条件を説明できる
- [ ] pollingのcancel条件を説明できる
- [ ] 画面破棄後のpolling停止を確認できる
- [ ] 古いrequestのresponseをstateへ反映しない仕組みを説明できる
- [ ] Queue待機中と実行中のstate遷移を説明できる
- [ ] Task成功時のstate遷移を説明できる
- [ ] Task失敗時のstate遷移を説明できる
- [ ] abort時と通信失敗時の表示を区別できる

#### Level 3確認

- [ ] polling間隔、停止条件、status表示のいずれかを自分で変更した
- [ ] 正常系のunit testを自分で追加した
- [ ] 少なくとも1つの失敗系のunit testを自分で追加した
- [ ] テストを意図的に壊し、想定どおり失敗することを確認した
- [ ] `Angular -> ClearML API -> Task -> Queue -> Agent -> Container -> train.py -> Output Model`を説明できる

### P0-3. Pipeline

#### MLOps実装とドメイン

- [ ] `validate dataset -> preprocess -> train -> evaluate -> register candidate`を独立Taskで構成した
- [ ] 各stepの入力、出力、依存関係を説明できる
- [ ] ArtifactとDataset Versionの受け渡しを追える
- [ ] Dataset検証失敗時に後続stepへ進まないことを確認した
- [ ] Pipeline IDと各Task IDの対応を追える

#### Angular処理経路

- [ ] Pipeline一覧、詳細、step表示のrouteを追える
- [ ] 各画面のcomponent構造を説明できる
- [ ] controller取得のaction / effect / APIを追える
- [ ] Pipeline起動のaction / effect / APIを追える
- [ ] Pipeline abortのaction / effect / APIを追える
- [ ] step stateから画面表示への変換を追える
- [ ] 起動中の二重操作防止を説明できる
- [ ] API errorの変換と表示を説明できる
- [ ] `Component -> Action -> Effect -> API Client -> ClearML API -> Pipeline -> Task`を説明できる
- [ ] `Task response -> Reducer / State -> Selector -> Component`を説明できる

#### Level 3確認

- [ ] validation failureを停止step付きで表示する変更を自分で行った
- [ ] または、起動後のTask ID / step status表示を自分で追加した
- [ ] Pipeline正常完了のテストを追加した
- [ ] validation failureのテストを追加した
- [ ] テストを意図的に壊し、想定どおり失敗することを確認した

### P0-4. Evaluation Gate / Model Registry

#### MLOps実装とドメイン

- [ ] recallとF1の最小合格基準を設定化した
- [ ] 基準未達モデルがcandidate以降へ進まないことを確認した
- [ ] candidate / staging / productionの状態遷移を説明できる
- [ ] 承認者、理由、元Task、Dataset ID、評価結果の記録箇所を追える
- [ ] 直前のproduction modelへのrollbackを実行できる

#### Angular処理経路

- [ ] model一覧・詳細のrouteとcomponentを追える
- [ ] model API、state、selectorを追える
- [ ] model metadataから画面表示値への変換を追える
- [ ] modelから元Task、Dataset、評価指標へ追跡できる
- [ ] 昇格、却下、rollbackの操作経路を追える
- [ ] 操作権限と確認ダイアログの責務を説明できる
- [ ] 基準未達とAPI失敗のUI stateを区別できる

#### Level 3確認

- [ ] recall表示、基準未達理由、昇格操作制御のいずれかを自分で変更した
- [ ] model境界の型と変換を保ったまま評価項目を追加できた
- [ ] 正常系と基準未達またはAPI失敗のテストを追加した
- [ ] テストを意図的に壊し、想定どおり失敗することを確認した
- [ ] 変更した評価項目の影響範囲を説明できる

### P0-5. Serving

#### MLOps実装とドメイン

- [ ] production modelを読み込むonline推論APIを用意した
- [ ] request / response schemaを説明できる
- [ ] healthとreadinessの違いを説明できる
- [ ] responseでmodel versionを確認できる
- [ ] 不正入力、timeout、model読込失敗のcontract testがある
- [ ] 新旧modelの切替とrollbackを確認した
- [ ] productionへ昇格したmodelだけが推論に使われることを確認した

#### Angular処理経路

- [ ] form値からrequest modelへの変換を追える
- [ ] response modelから画面表示への変換を追える
- [ ] validation error、server error、timeoutの表示境界を説明できる
- [ ] 実行中の二重送信防止を説明できる
- [ ] requestのcancel条件を説明できる
- [ ] 使用されたmodel versionの表示経路を追える
- [ ] Angular requestからmodel version付きresponseまでを説明できる

#### Level 3確認

- [ ] 入力validationまたは推論結果項目を自分で1つ追加した
- [ ] または、timeout時のretry導線を自分で追加した
- [ ] 正常、4xx、5xx、timeoutのUIテストを追加した
- [ ] テストを意図的に壊し、想定どおり失敗することを確認した
- [ ] 変更のAPI contractとUIへの影響を説明できる

### P0総合演習

- [ ] AngularからPipelineを起動した
- [ ] ClearML APIからPipeline Controllerへの経路を確認した
- [ ] Dataset validationを通過する正常系を確認した
- [ ] Queue / Agentによるtrain / evaluateを確認した
- [ ] Evaluation Gateからcandidate登録までを確認した
- [ ] production昇格後のServingを確認した
- [ ] Angularで状態、評価、model versionを確認した
- [ ] Dataset validation failureまたはAgent failureを意図的に発生させた
- [ ] UIが停止箇所と次の行動を表示することを確認した
- [ ] 一連の操作、通信、state遷移、ドメイン処理を自分の言葉で説明できる

## 6. Angular横断チェック

各セルは、その機能でコードと動作を確認し、自分で説明できた場合にチェックする。

| 項目 | Task | Queue / Agent | Pipeline | Model | Serving |
| --- | :---: | :---: | :---: | :---: | :---: |
| Routeを追える | [ ] | [ ] | [ ] | [ ] | [ ] |
| Componentを特定できる | [ ] | [ ] | [ ] | [ ] | [ ] |
| State所有者を説明できる | [ ] | [ ] | [ ] | [ ] | [ ] |
| Actionを追える | [ ] | [ ] | [ ] | [ ] | [ ] |
| Effectを追える | [ ] | [ ] | [ ] | [ ] | [ ] |
| RxJS operatorの理由を説明できる | [ ] | [ ] | [ ] | [ ] | [ ] |
| API Clientを追える | [ ] | [ ] | [ ] | [ ] | [ ] |
| Response modelを追える | [ ] | [ ] | [ ] | [ ] | [ ] |
| API / domain / view model境界を説明できる | [ ] | [ ] | [ ] | [ ] | [ ] |
| Reducer / State更新を追える | [ ] | [ ] | [ ] | [ ] | [ ] |
| Selectorを追える | [ ] | [ ] | [ ] | [ ] | [ ] |
| loadingを説明できる | [ ] | [ ] | [ ] | [ ] | [ ] |
| emptyを説明できる | [ ] | [ ] | [ ] | [ ] | [ ] |
| failureを説明できる | [ ] | [ ] | [ ] | [ ] | [ ] |
| cancelを説明できる | [ ] | [ ] | [ ] | [ ] | [ ] |
| retryを説明できる | [ ] | [ ] | [ ] | [ ] | [ ] |
| request競合とstale responseを説明できる | [ ] | [ ] | [ ] | [ ] | [ ] |
| subscription / pollingの寿命を説明できる | [ ] | [ ] | [ ] | [ ] | [ ] |
| 自分で変更した | [ ] | [ ] | [ ] | [ ] | [ ] |
| 自分でテストを追加した | [ ] | [ ] | [ ] | [ ] | [ ] |

## 7. P1〜P3詳細チェック

### P1-1. Observability

- [ ] Angular requestにcorrelation IDを付与できる
- [ ] correlation ID、Task ID、Pipeline IDを構造化ログで接続できる
- [ ] request成功率、latency、Queue滞留、Pipeline失敗を確認できる
- [ ] ユーザー向けの原因と運用者向け追跡IDを分けて表示できる
- [ ] API停止、Agent停止、遅延を注入した
- [ ] UIから原因Taskまで追跡できる
- [ ] 障害追跡のテストまたは再現手順を追加した

### P1-2. Error Handling

- [ ] validation / authorization / conflict / timeout / server errorをdomain errorへ変換できる
- [ ] retry可能な失敗と不可能な失敗を区別できる
- [ ] optimistic updateのrollbackを説明し、テストできる
- [ ] stale response、多重click、画面遷移後のresponseを安全に扱える
- [ ] error messageに機密情報やstack traceが含まれないことを確認した
- [ ] 代表的な失敗経路を自分で変更し、テストを追加した

### P1-3. Authentication / Authorization / Security

- [ ] route guard、permission directive、表示制御、API認可を区別できる
- [ ] UIの表示制御とは別にserver側で認可されることを確認した
- [ ] 権限別の許可・拒否をintegration testで確認した
- [ ] token、secret、Task Parameters、logの漏えい境界を確認した
- [ ] dependency / secret / SAST / container scanをCIで実行できる
- [ ] 権限に関する小変更と必要なテストを自分で追加した

### P1-4. Data Quality UI

- [ ] 必須列、型、範囲、欠損率、カテゴリ、クラス比率の契約を追える
- [ ] Dataset Version間のdriftとlineageを追える
- [ ] 検証失敗の項目、期待値、実際値、対処をUIで説明できる
- [ ] 壊したDatasetが学習前に停止することを確認した
- [ ] UIから原本と変換処理へ追跡できる
- [ ] Data Quality表示の小変更と必要なテストを自分で追加した

### P2-1. TypeScriptとmodel境界

- [ ] 対象featureが`strict`で検査される
- [ ] 新規コードで`any`を原則使用していない
- [ ] API / domain / view modelの境界を説明できる
- [ ] `unknown`と型の絞り込みを安全に使用できる
- [ ] discriminated unionとexhaustive checkをstateまたはerrorへ適用できる
- [ ] nullable / optional / absentの意味をcontractとtestで固定できる
- [ ] model境界を保つ小変更とテストを自分で追加した

### P2-2. Feature構造とstate architecture

- [ ] domain単位のfeature境界とpublic APIを説明できる
- [ ] 禁止依存と循環依存を静的に検知できる
- [ ] Effectsが更新対象stateのfeature配下にある
- [ ] local state / Signals / SignalStore / Classic NgRxの選択理由を説明できる
- [ ] facadeを導入する条件を説明できる
- [ ] selectorで導出可能なstateを重複保持していない
- [ ] ID、entity、request state、filter、selectionの所有者を説明できる
- [ ] state設計の小変更とテストを自分で追加した

### P2-3. Routing、DI、Performance

- [ ] Standalone Componentとroute-level providerの境界を説明できる
- [ ] featureがlazy loadingされることを確認できる
- [ ] initial bundleとlazy chunkのbudgetをCIで監視できる
- [ ] change detection、Signals、`track`、selectorの改善をprofiling結果で判断できる
- [ ] pagination、virtualization、request cancel、cacheを検証できる
- [ ] provider scopeによるstate重複生成を説明し、テストできる
- [ ] 計測に基づく小変更とテストを自分で追加した

### P2-4. TestingとAccessibility

- [ ] reducer / selector / effect / adapter / componentの責務ごとにテストを選べる
- [ ] API contract testで破壊的変更を検知できる
- [ ] 主要ユースケースを実ClearML ServerとのE2Eで確認できる
- [ ] loading / empty / failure / permission denied / retry / cancelをcomponent testで確認できる
- [ ] keyboard、focus、label、色以外のstatus表現を検証できる
- [ ] flaky testの原因と再発防止を記録できる
- [ ] accessibility改善と回帰テストを自分で追加した

### P2-5. 段階的な品質負債の解消

- [ ] lint、runtime warning、bundle warningをbaseline化した
- [ ] 新規違反をCIで防止できる
- [ ] 業務featureの変更単位でbaselineを減らせる
- [ ] 移行前にbehaviorを固定するテストを追加できる
- [ ] 自動変換の大量diffと意味のある変更を分離できる
- [ ] 品質負債を1件、自分で安全に解消した

### P3-1. 設計・所有権・レビュー標準

- [ ] C4と主要なAngular / API / ClearMLシーケンスを保守できる
- [ ] state選択、API境界、error model、feature依存をADRに残せる
- [ ] 所有者と横断変更に必要なレビュアーが明確である
- [ ] Definition of DoneとAngular review checklistがある
- [ ] 大きな変更をcontract / state / UI / E2Eへ分割できる

### P3-2. CI/CDとrelease運用

- [ ] test pyramidと必須jobを説明できる
- [ ] unit testと高コストE2Eを適切に分けられる
- [ ] API compatibility、bundle、accessibility、securityをrelease gateにできる
- [ ] feature flag、段階リリース、rollbackの手順を説明できる
- [ ] changelogと非互換変更の周知方法が明確である

### P3-3. Onboardingと運用知識

- [ ] 資料だけで環境構築、debug、test、小改修を実施できる
- [ ] 主要featureごとにコードを読み始める場所が明確である
- [ ] 障害、rollback、API変更、state不整合のrunbookがある
- [ ] postmortemからtest、観測性、プロセスを改善できる

### P3-4. Enterprise基盤との接続

- [ ] dev / staging / productionの設定と権限を分離できる
- [ ] IaC、backup / restore、RPO / RTO、capacity、cost、retentionを説明できる
- [ ] API endpoint、authentication、feature flagの環境差分を追跡できる
- [ ] 環境障害時の劣化運転、復旧、ユーザー通知のcontractがある

## 8. 今回の作業スコープ

コーディングエージェントへ依頼する前に記入し、1回の作業範囲を限定する。

```text
日付: 2026-09-08
対象ID: P0-0
対象ユースケース: 変更前の品質チェックを再現し、安全な変更の出発点を固定する
今回チェックする項目: Python test、Angular unit test、E2E typecheck、Angular production build、既知のwarning、共通実行入口、CI構成
対象外: E2E実行、ClearML Server起動、機能改修、既知warningの解消
代表的な正常条件: 各コマンドが終了コード0で完了する
代表的な失敗条件: test failure、TypeScript error、production build error、依存関係または実行環境の不備
完了条件: 本人が各4系統と共通実行入口を再現し、結果と既知warningの意味を説明できる
```

## 9. 作業証跡

作業単位で追記する。説明できなかった内容は隠さず、次の一手として残す。

```text
日付:
対象ID:
開始時Level:
終了時Level:

Agentが実装した内容:
自分で読んだ主要ファイル:
確認した処理経路:
stateの所有者:
API / domain / view modelの境界:
正常時のstate遷移:
失敗時のstate遷移:
cancel / retry / timeout:

自分で加えた変更:
自分で追加したテスト:
意図的に壊したテストと確認結果:
実行した確認コマンドと結果:

説明できるようになったこと:
まだ説明できないこと:
残る疑問とリスク:
次の一手:
関連するコード・テスト・資料:
```

### 2026-09-08 P0-0 変更前ベースライン

```text
日付: 2026-09-08
対象ID: P0-0
開始時Level: 0
終了時Level: 0

Agentが実装した内容: ルートの `package.json` に共通実行入口 `verify` を追加し、`.github/workflows/quality.yml` にPython / AngularのCI jobを追加
自分で読んだ主要ファイル: 未実施
確認した処理経路: package.json -> apps/web/package.json -> Angular CLI / Vitest / TypeScript / production build
stateの所有者: 未確認
API / domain / view modelの境界: 未確認
正常時のstate遷移: 対象外
失敗時のstate遷移: 対象外
cancel / retry / timeout: 対象外

自分で加えた変更: なし
自分で追加したテスト: なし
意図的に壊したテストと確認結果: 未実施
実行した確認コマンドと結果:
- corepack pnpm test: 16 tests passed
- corepack pnpm ml:test: 199 tests passed
- corepack pnpm web:test: stackup 108 tests / 49 files passed、report-widgets 3 tests / 1 file passed
- corepack pnpm --dir apps/web e2e:typecheck: 終了コード0
- corepack pnpm web:build: 終了コード0
- corepack pnpm verify: 追加後にAgentが実行し、5スクリプトすべて成功（終了コード0）
- .github/workflows/quality.yml: PyYAMLで構文解析成功
- CI対象コマンドのローカル再確認: tools 16 tests、ML 199 tests、E2E typecheckが成功（Angular unit / buildは `verify` で確認済み）

説明できるようになったこと: AgentはルートとAngular側のコマンド境界、変更前の成否を確認した
まだ説明できないこと: 各チェックの対象範囲、Angular起動・route・state・API経路
残る疑問とリスク:
- Angular unit testは成功するが NG01354、NG0318、NG0953、as-split warningが出力される
- production buildは成功するが ngx-markdown-editorのignored importと3ファイルのSCSS budget warningが出力される
- production buildは成功するが、生成bundle内のdirect evalに対するsecurity / minification warningが出力される（発生元は未特定）
- CIはローカル構文検査と対象コマンド検証のみで、GitHub Actions上では未実行
次の一手: 本人がCI差分とjob / step / `&&` の責務の違いを読み、GitHub Actions上の実行結果を確認する
関連するコード・テスト・資料: package.json、apps/web/package.json、apps/web/angular.json、apps/web/vitest.config.ts、apps/web/e2e/tsconfig.json
```

本人による追加確認:

- 2026-09-08: `corepack pnpm test`、`corepack pnpm ml:test`、`corepack pnpm web:test` の正常完了を確認
- 2026-09-08: `corepack pnpm --dir apps/web e2e:typecheck` の正常完了を確認
- 2026-09-08: `corepack pnpm web:build` の正常完了と、direct eval、ignored bare import、SCSS budgetのwarningを確認
- 2026-09-08: `corepack pnpm verify` で全チェックの正常完了と既知warningの再現を本人が確認
- 2026-09-08: GitHub Actions run 34219231984は失敗。Pythonは `Run tools tests`、Angularは `Run Angular unit tests` で終了コード1。後続stepはskip。`actions/setup-python@v5` のNode.js 20 deprecated warningも確認
- Python失敗原因: requirementsを`.venv`へinstallした後、tools testsだけsystem Pythonで実行し、`clearml`と`numpy`をimportできなかった
- Angular失敗原因: pnpmのhoisted配置とAngular workspaceが不整合で、clean install時に`apps/web/node_modules`のasset参照を解決できなかった
- 修正: tools testsのPythonを`.venv/bin/python`に統一、pnpmをisolated linkerに変更、`actions/setup-python@v6`へ更新
- 修正後に`corepack pnpm install --force --frozen-lockfile`と`corepack pnpm verify`が終了コード0
- 2026-09-08: 再実行でPython jobは成功。Angularは`window.YT`のTS2339で失敗
- Angular再失敗原因: アプリが直接使う`@types/youtube`を推移的依存に頼っており、isolated linkerで正しく参照できなくなった
- 修正: `@types/youtube@0.3.0`を`apps/web` の直接devDependencyに追加
- 追加修正後の`corepack pnpm verify`は終了コード0
- 2026-09-08: Angular再実行は`chartjs-plugin-zoom`から`hammerjs`を解決できず失敗（48 / 49 files、107 testsは成功）
- 原因: `preserveSymlinks: true`の環境で、推移的なruntime dependencyの`hammerjs`が`apps/web/node_modules`から解決できなかった
- 修正: `hammerjs@2.0.8`を`apps/web`の直接dependencyに追加
- 修正後の`corepack pnpm web:test`は49 files / 108 testsとreport-widgets 3 testsが成功
- 2026-09-08: Angular jobはunit testとE2E typecheckを通過後、production buildで複数の推移的依存と`apps/web/.env`を解決できず失敗
- 原因: `preserveSymlinks: true`によりpnpm isolated store内のpackage実体を基準に推移的依存を解決できなかった
- 修正: `preserveSymlinks: false`へ変更し、CIで`.env.example`から`.env`を準備するstepを追加。暫定対応だった`hammerjs`の直接dependencyは削除
- 構造修正後の`corepack pnpm verify`は終了コード0
- clean-room `/tmp/tmp.XnTqkhg94W`へnode_modules、.env、build生成物を除外して複製し、`pnpm install --frozen-lockfile`からAngular検証を再現
- clean-room結果: stackup 49 files / 108 tests、report-widgets 3 tests、E2E typecheck、production buildがすべて成功
- clean-roomのPython venv作成はローカルOSに`python3-venv`がないため未実施。ただし同じ修正後のGitHub Python jobは成功済み
- 2026-09-08: 修正後のGitHub ActionsでPython / Angular両jobの成功を本人が確認
- `corepack pnpm web:lint`: 終了コード1、2927 problems（2871 errors / 56 warnings）。既存lint負債のbaselineとして記録
- 既存コード読解用テンプレート: 本資料「9. 作業証跡」を使用

## 10. Level 3昇格前の最終確認

対象項目をLevel 3および完了へ変更する直前に確認する。

- [ ] ユースケースと代表的な失敗条件を説明できる
- [ ] 既存の処理経路を端から端までtraceした
- [ ] state、Effect、API境界の所有者と設計理由を説明できる
- [ ] Agentが作ったdiffを全て読んだ
- [ ] 自分で仕様の異なる小変更を完了した
- [ ] 正常系と代表的な失敗系のテストを追加した
- [ ] テストを意図的に壊して検出力を確認した
- [ ] loading / empty / success / failure / cancelの該当stateを確認した
- [ ] subscription、polling、request cancelの寿命を説明できる
- [ ] API modelから画面表示までの変換を説明できる
- [ ] 変更の影響範囲と残るリスクを説明できる
- [ ] 学び、設計判断、証跡を記録した
