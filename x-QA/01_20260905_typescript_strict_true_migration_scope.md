# TypeScriptで`strict: true`にする場合の変更箇所

## 結論

現時点で`apps/web`を一括して`strict: true`へ変更するのは、設定1行だけで完了する作業ではない。

実測では、アプリ本体で4,495件・435ファイルにTypeScriptエラーが発生した。Report Widgetsでは、共有コードとの重複を含めて840件・62ファイルにstrict固有のエラーがあり、Widgetsだけに存在するファイルも4ファイルある。

変更対象は合計で少なくとも439ファイルになる。この件数はTypeScriptコンパイラーによる初回診断の下限であり、型修正によって後続の型推論が変わるほか、Angularテンプレート検査で追加エラーが見つかる可能性もある。

一括変更ではなく、API境界と共有コードから段階的に修正し、最後に全体の`strict: true`を有効化する方針を推奨する。

## 調査条件

調査時の主要バージョンは次のとおり。

| 対象 | バージョン |
| --- | --- |
| Angular | 22.1系 |
| TypeScript | 6.0.3 |
| ClearML Web | 2.5.0ベース |

TypeScript 6では`strict`のデフォルト値が`true`へ変更された。現在は既存コードとの互換性を保つため、次の2ファイルで`strict: false`を明示している。

- `apps/web/tsconfig.json`
- `apps/web/src/tsconfig.json`

最終的にstrict化する場合は、両方を`strict: true`へ変更する必要がある。Report Widgetsの`tsconfig.app.json`は`apps/web/src/tsconfig.json`を継承している。

調査には次のコマンドを使用した。

```bash
cd apps/web

corepack pnpm exec tsc \
  -p tsconfig.app.json \
  --noEmit \
  --strict \
  --pretty false

corepack pnpm exec tsc \
  -p src/app/webapp-common/clearml-applications/report-widgets/tsconfig.app.json \
  --noEmit \
  --strict \
  --pretty false
```

`tsconfig`は変更せず、コマンドラインでstrictを一時的に有効化して調査した。

## エラー総数

### アプリ本体

| 項目 | 件数 |
| --- | ---: |
| TypeScriptエラー | 4,495 |
| 影響ファイル | 435 |

### Report Widgets

Widgetsはアプリ本体の共有コードを多数参照するため、アプリ本体と重複するエラーがある。

| 項目 | 件数 |
| --- | ---: |
| strict固有エラー | 840 |
| strict固有エラーの影響ファイル | 62 |
| アプリ本体に含まれないWidgets固有ファイル | 4 |

Widgets固有の変更対象は次の4ファイル。

- `report-widgets/src/app/app.component.ts`
- `report-widgets/src/app/app.effects.ts`
- `report-widgets/src/app/app.reducer.ts`
- `report-widgets/src/environments/base.ts`

なお、Widgetsの`tsc`単体実行では、TypeScript 6の`rootDir`デフォルト変更による`TS6059`が別途427件発生する。AngularによるWidgetsのproduction buildは成功しているため、これはstrict化固有の件数には含めていない。strict化時にはWidgetsの`rootDir`も明示する必要がある。

## エラーコード別の変更内容

アプリ本体の主要エラーは次のとおり。

| エラー | 件数 | 主な原因 | 主な修正方法 |
| --- | ---: | --- | --- |
| `TS2322` | 796 | 代入元に`null`や`undefined`を含む | 型定義と初期値を一致させる |
| `TS2345` | 679 | optional値を必須引数へ渡している | 呼び出し前のguard、デフォルト値、API契約修正 |
| `TS7006` | 645 | コールバック引数が暗黙の`any` | 引数型を明示するか上流の型推論を改善する |
| `TS2564` | 508 | クラスプロパティがコンストラクターで未初期化 | 初期値、optional型、Signal query、保証できる場合のみ`!` |
| `TS2532` | 452 | 値が`undefined`の可能性を持つ | guard、optional chaining、状態モデル修正 |
| `TS18048` | 413 | 参照対象が`undefined`の可能性を持つ | guardまたは型の絞り込み |
| `TS7053` | 268 | 型のない動的キーでオブジェクトへアクセス | `Record`、`keyof`、判別可能なキー型を使用 |
| その他 | 734 | overload、`never`、未初期化変数など | 上流型を直した後に個別対応 |

機械的に`!`、`as`、`any`を追加するだけでは、strict化の安全性を失う。特に`TS2322`、`TS2345`、`TS2532`、`TS18048`は、実際の`null/undefined`処理を確認して修正する必要がある。

## モジュール別の変更箇所

アプリ本体の影響が大きいモジュールを、エラー件数順に示す。

| モジュール | エラー | 影響ファイル |
| --- | ---: | ---: |
| `webapp-common/shared` | 1,304 | 153 |
| `webapp-common/experiments` | 652 | 49 |
| `webapp-common/experiments-compare` | 647 | 36 |
| `webapp-common/models` | 264 | 23 |
| `business-logic/api-services` | 169 | 13 |
| `webapp-common/serving` | 158 | 11 |
| `webapp-common/core` | 140 | 16 |
| `webapp-common/tasks` | 131 | 1 |
| `webapp-common/pipelines-controller` | 114 | 7 |
| `webapp-common/dashboard-search` | 101 | 5 |
| `webapp-common/reports` | 101 | 11 |
| `webapp-common/settings` | 81 | 10 |
| `webapp-common/workers-and-queues` | 79 | 12 |
| `webapp-common/projects` | 68 | 6 |
| `webapp-common/debug-images` | 49 | 4 |
| `webapp-common/angular-notifier` | 40 | 5 |
| `webapp-common/layout` | 40 | 8 |
| `features/experiments-compare` | 35 | 4 |
| `webapp-common/project-workloads` | 28 | 2 |
| `webapp-common/project-info` | 27 | 3 |
| その他 | 267 | 52 |

`shared`、`experiments`、`experiments-compare`だけで全エラーの半数を超える。共有型を先に直さず各featureを個別修正すると、同じ型不整合を複数箇所で修正することになる。

## エラー数の多いファイル

優先的な調査対象は次のとおり。

| ファイル | エラー |
| --- | ---: |
| `webapp-common/tasks/tasks.utils.ts` | 131 |
| `webapp-common/experiments-compare/jsonToDiffConvertor.ts` | 96 |
| `webapp-common/shared/single-graph/single-graph.component.ts` | 84 |
| `webapp-common/shared/ui-components/data/table/table.component.ts` | 82 |
| `webapp-common/pipelines-controller/pipeline-controller-info/pipeline-controller-info.component.ts` | 79 |
| `webapp-common/experiments-compare/containers/experiment-compare-base.ts` | 56 |
| `webapp-common/experiments/effects/common-experiments-view.effects.ts` | 56 |
| `webapp-common/experiments-compare/containers/experiment-compare-metric-values/experiment-compare-metric-values.component.ts` | 55 |
| `webapp-common/shared/ui-components/data/table/overrideFilterFunc.ts` | 54 |
| `webapp-common/dashboard-search/dashboard-search.effects.ts` | 52 |
| `webapp-common/experiments-compare/containers/experiment-compare-metric-charts/experiment-compare-scalar-charts.component.ts` | 50 |
| `webapp-common/shared/experiment-graphs/experiment-graphs.component.ts` | 50 |
| `business-logic/api-services/tasks.service.ts` | 48 |
| `webapp-common/serving/serving.effects.ts` | 48 |
| `webapp-common/experiments-compare/dumbs/parallel-coordinates-graph/parallel-coordinates-graph.component.ts` | 47 |

`tasks.utils.ts`のような共有処理は多数のfeatureから利用されるため、型修正後の回帰テスト範囲も広くなる。

## 推奨する移行順序

### 1. API生成コードとサーバー契約

`business-logic/api-services`には169件ある。生成コードを手作業で直すと再生成時に消えるため、OpenAPI定義または生成テンプレートをstrict対応させる。

特に確認する項目は次のとおり。

- 必須・任意パラメータ
- `null`と`undefined`の使い分け
- APIレスポンスのoptional項目
- `Record<string, unknown>`で表現すべき動的データ

### 2. Domain、Store、共通Utility

Stateの初期値として`null`を使う場合は、State interface側にも`null`を含める。空配列や空オブジェクトで意味が一致する場合だけ初期値を置き換える。

`shared`と`tasks.utils.ts`を先に直し、下流featureの連鎖エラーを減らす。

### 3. Angularコンポーネント

コンポーネントでは次の順に対応する。

1. `input()`、Store selector、Observableの戻り型を正す
2. 初期表示前に存在しない値はoptional型にする
3. 必須のView queryはAngularの`viewChild.required()`を検討する
4. ライフサイクル上必ず設定されることを証明できる箇所だけ`!`を使う
5. テンプレート側ではguard後に参照する

### 4. Feature単位の移行

依存の下流から、次の単位で型検査と画面回帰を行う。

1. Projects、Dashboard
2. Experiments、Tasks
3. Models、Reports、Datasets
4. Pipelines、Serving
5. Workers and Queues
6. Experiments Compare、Graphs

### 5. Report Widgets

共有コードのstrict化後、Widgets固有4ファイルを修正する。同時にWidgets用`tsconfig`へ適切な`rootDir`を明示する。

### 6. 全体有効化

すべての段階が完了してから、次を変更する。

```json
{
  "compilerOptions": {
    "strict": true
  }
}
```

変更対象は`apps/web/tsconfig.json`と`apps/web/src/tsconfig.json`の両方。その後、本体とWidgetsのproduction build、主要画面のE2Eを必須確認とする。

## 段階移行で使用するstrictオプション

一度に`strict: true`へ変更しない場合は、次の順で個別オプションを有効化する。

1. `noImplicitAny`
2. `strictBindCallApply`
3. `strictFunctionTypes`
4. `strictNullChecks`
5. `strictPropertyInitialization`
6. `useUnknownInCatchVariables`
7. 最後に`strict: true`

`strictPropertyInitialization`は`strictNullChecks`を前提とする。各段階で新規エラーを増やさないCIチェックを追加する。

## メリット

- `null`、`undefined`による実行時エラーをコンパイル時に検出しやすくなる
- NgRx State、selector、action間の契約が明確になる
- APIレスポンスの未設定値を安全に処理できる
- リファクタリング時の影響箇所をIDEとコンパイラーが検出できる
- 暗黙の`any`が減り、補完と型推論の精度が上がる
- AngularのSignal、必須Input、View queryと状態モデルの整合性を高められる
- TypeScript 6以降の標準設定と一致し、将来の更新で設定差が生じにくい

## デメリット

- 初期対応が少なくとも4,495件・435ファイル規模になる
- 共有型の変更が多数のfeatureへ波及する
- 機械的な`!`や型アサーションを増やすと、見かけ上だけエラーが消えて安全性が下がる
- API生成コードは生成元を直さないと再生成のたびに修正が失われる
- `null`と`undefined`の契約変更はClearML Server APIとの確認が必要になる
- 移行中はstrict対応済み領域と未対応領域が混在し、レビュー基準が複雑になる
- 型修正だけでは保証できない挙動があるため、主要画面の回帰テストが必要になる
- 長期間の一括ブランチにすると、通常開発との競合が増える

## 判断

strict化そのものには長期的な価値があるが、現時点で`strict: true`だけを先に設定するのは推奨しない。

まずAPI生成処理、State、共有Utilityをstrict対応し、feature単位でエラー0件と画面回帰を確認する。その完了後に全体設定を`strict: true`へ切り替えるのが安全である。

## 参考資料

- [TypeScript 6.0 Release Notes](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html)
- [ClearML Web公式リポジトリ](https://github.com/clearml/clearml-web)
