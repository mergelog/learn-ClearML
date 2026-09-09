# stackup

ClearML WebをAngular 22へ更新し、ローカルのClearML Serverと接続して動かすためのプロジェクトです。

## 公式docs

公式Web UI全体解説: https://clear.ml/docs/latest/docs/webapp/webapp_overview/
Projects画面: https://clear.ml/docs/latest/docs/webapp/webapp_projects_page/
Project Overview画面: https://clear.ml/docs/latest/docs/webapp/webapp_project_overview/
Datasets画面: https://clear.ml/docs/latest/docs/webapp/datasets/webapp_dataset_page/
Workers・Queues画面: https://www.clear.ml/docs/latest/docs/webapp/webapp_workers_queues/

## 構成

```text
.
├── apps/web/             # Angular 22版 ClearML Web
├── infra/clearml/        # ClearML Server用Docker Compose
├── ml/                   # 登録済みDatasetを使う学習コード
├── tools/                # 上流データ準備（テストデータ作成）スクリプト
├── .env.example          # 環境変数のサンプル
└── package.json          # プロジェクト共通コマンド
```

## 使用バージョン

- Node.js 24
- pnpm 10
- Angular 22.1
- ClearML Server 2.4.0
- Docker Compose v2

## 初回セットアップ

環境変数ファイルを作成します。

```bash
cp .env.example .env
cp apps/web/.env.example apps/web/.env
```

PrimeUIのライセンスキーは `apps/web/.env` に設定します。

```dotenv
PRIMEUI_LICENSE=取得したライセンスキー
```

この値はAngularのブラウザ向けバンドルに含まれます。`apps/web/.env` にはPrimeUIライセンスキー以外の秘密情報を設定しないでください。

依存パッケージをインストールします。

```bash
corepack pnpm install
```

## 起動方法

### 1. ClearML Serverを起動する

Dockerデーモンを起動してから、次を実行します。

```bash
corepack pnpm backend:up
```

起動状態を確認します。

```bash
corepack pnpm backend:status
```

ClearML APIの疎通確認は次のコマンドで行えます。

```bash
curl http://localhost:8008/debug.ping
```

ClearML Server全体の件数と、このプロジェクトで使用する半導体学習データの登録状態を確認します。このコマンドはデータを変更しません。

```bash
corepack pnpm backend:data:status
```

### 2. 上流データを準備する

学習に使うデータは上流工程で用意し、ClearML Datasetとして登録しておきます。次の手順3の学習コマンドはDatasetの生成を行いません。

#### 最小の疎通確認データ

`stackup/test` プロジェクトと `hello-stackup` タスクを作成します。
同じコマンドを複数回実行してもデータは重複しません。

```bash
corepack pnpm seed
```

#### 半導体の機械学習データ

製造条件からウェハの良品・不良品を予測する、架空の表形式データを作成します。画像は使用しません。

初回だけPythonの仮想環境と依存パッケージを準備します。

```bash
corepack pnpm python:setup
```

Datasetだけを登録して、実験がない状態から学習を始める場合は次を実行します。

```bash
corepack pnpm seed:semiconductor:dataset
```

このコマンドが登録するのはDataset 2バージョンだけです。実験TaskやModelは登録しません。
登録されるDatasetは、`Semiconductor Quality Prediction` プロジェクトの `semiconductor-quality-data` です。Versionは `1.0.0` と `2.0.0` の2つで、`2.0.0`は`1.0.0`を親Datasetとします。

比較用データを一括で用意する場合は、従来の全件seedを実行します。

```bash
corepack pnpm seed:semiconductor
```

全件seedはDataset 2バージョンに加えて、モデル比較・パラメータ比較用の実験20件と代表モデル3件を登録します。ClearML Webを空に近い状態から学習したい場合は実行しないでください。

生成元のCSVは `.generated/semiconductor/datasets/` に作成されます。全件seedでは評価結果とモデルも `.generated/semiconductor/artifacts/` に作成されます。`.generated/semiconductor/` はGit管理対象外です。

どちらのseedも登録済みのDatasetを再利用します。全件seedを再実行した場合は登録済みの実験も再利用され、重複しません。

### 3. 登録済みDatasetで学習する

`ml/semiconductor_quality/` は、登録済みのClearML Datasetを取得してRandomForestを学習し、実行内容をClearML Taskとして残す独立したコマンドです。

実行前提は次の3つです。

- 手順1でClearML Serverが起動していること
- `corepack pnpm python:setup` を実行済みであること
- 手順2で学習対象のDataset Versionが登録済みであること

Dataset Versionは必ず明示します。名前だけで最新版を暗黙に選ぶことはありません。

```bash
corepack pnpm ml:train -- --dataset-version 1.0.0
```

1回の実行につき、過去のTaskを再利用しない新しいClearML Taskが1件作成されます。

主なオプションは次のとおりです。

| オプション | 既定値 | 説明 |
| --- | --- | --- |
| `--dataset-version` | 必須 | 学習に使う登録済みDatasetのVersion |
| `--dataset-project` | `Semiconductor Quality Prediction` | Datasetが属するプロジェクト |
| `--dataset-name` | `semiconductor-quality-data` | 登録済みDatasetの名称 |
| `--dataset-csv-path` | `semiconductor_quality.csv` | Datasetルートからの相対パスで指定するCSV |
| `--task-project` | `Semiconductor Quality Prediction/Training` | 学習Taskを作成するプロジェクト |
| `--task-name` | `random-forest-quality-classifier` | 学習Taskの名称 |
| `--train-ratio` | `0.6` | 学習に使う行の割合 |
| `--validation-ratio` | `0.2` | 設定確認に使う行の割合 |
| `--test-ratio` | `0.2` | 最終評価に使う行の割合 |
| `--n-estimators` | `300` | 決定木の本数 |
| `--max-depth` | 無制限 | 決定木の深さの上限 |
| `--min-samples-leaf` | `4` | 葉に必要な最小サンプル数 |
| `--random-seed` | `20260906` | 分割とRandomForestが共有するseed |

全オプションは次のコマンドで確認できます。

```bash
corepack pnpm ml:train -- --help
```

分割比率の合計は1.0にします。パラメータを変えて再実行すると別Taskとして残り、ClearML Web上で比較できます。

```bash
corepack pnpm ml:train -- --dataset-version 1.0.0 --max-depth 6
```

Dataset Versionの未指定や比率の誤りは、ClearML Taskを作成する前に終了コード2で失敗します。Dataset取得後の失敗は、失敗したTaskとしてClearMLに残ります。

学習が生成するものは次のとおりです。

- ClearML Task 1件（Parameters、Metrics、confusion matrix、Artifact、Output Model）
- 取得したDatasetのread-onlyキャッシュ（`~/.clearml/cache/`）

学習済みモデルは一時ディレクトリを経由してClearMLへuploadされるため、リポジトリにはファイルを残しません。

実行結果はClearML Web（http://localhost:8080）で確認します。学習Taskは `Semiconductor Quality Prediction/Training` プロジェクトにあります。

| 確認したいもの | 確認箇所 |
| --- | --- |
| 実行時の引数と学習設定 | Task → CONFIGURATION → HYPERPARAMETERS の `Dataset` / `Split` / `RandomForest` / `Execution` |
| 実際に解決したDataset IDとVersion | 同 `Resolved Dataset`、および `Datasets` の `training-dataset` |
| 実行したコードと実行環境 | Task → EXECUTION |
| accuracy、precision、recall、F1 | Task → SCALARS（各プロットにvalidationとtestが並びます） |
| confusion matrix | Task → PLOTS |
| データ検証結果と評価結果 | Task → ARTIFACTS の `data_validation` / `evaluation` |
| 学習済みモデル | Task → ARTIFACTS → OUTPUT MODELS の `semiconductor-quality-classifier` |
| 条件を変えた2実行の比較 | Trainingプロジェクトで2 Taskを選択 → COMPARE |

### 4. Angularを起動する

```bash
corepack pnpm web:start
```

Angularは `0.0.0.0:4200` で起動します。

## URL

| 用途 | URL |
| --- | --- |
| Angular 22版 stackup | http://localhost:4200 |
| ClearML標準Web画面 | http://localhost:8080 |
| ClearML API | http://localhost:8008 |
| ClearML File Server | http://localhost:8081 |

別端末から接続する場合は、`localhost` の代わりにWindowsのLAN IPv4を使用します。

## よく使うコマンド

```bash
# Angularの本番ビルド
corepack pnpm web:build

# seedスクリプトのテスト
corepack pnpm test

# 半導体データ生成用Python環境の準備
corepack pnpm python:setup

# 半導体Datasetだけを登録
corepack pnpm seed:semiconductor:dataset

# 半導体Dataset・比較用実験・代表モデルを一括登録
corepack pnpm seed:semiconductor

# 登録済みDatasetで学習（Dataset Versionは必須）
corepack pnpm ml:train -- --dataset-version 1.0.0

# 学習コードのテスト
corepack pnpm ml:test

# AngularのLint
corepack pnpm web:lint

# ClearML Serverのログを表示
corepack pnpm backend:logs

# ClearML Serverと半導体学習データの登録状態を表示
corepack pnpm backend:data:status

# ClearML Serverを停止
corepack pnpm backend:down
```

## 環境変数

`.env` はDocker Compose用です。seedと学習コマンドはシェルの環境変数を読むため、既定値から変える場合はシェルで設定します。ローカルのClearML Serverを既定のポートで動かしている場合、設定は不要です。

| 変数 | 既定値 | 用途 |
| --- | --- | --- |
| `CLEARML_SERVER_IMAGE` | `clearml/server:2.4.0` | `.env`。起動するClearML Serverのイメージ |
| `CLEARML_WEB_PORT` | `8080` | `.env`。Docker Composeが公開するWeb画面のポート |
| `CLEARML_API_PORT` | `8008` | `.env`。同、APIのポート |
| `CLEARML_FILES_PORT` | `8081` | `.env`。同、File Serverのポート |
| `CLEARML_API_HOST` | `http://localhost:8008` | seedと学習コマンドの接続先API |
| `CLEARML_WEB_HOST` | `http://localhost:8080` | 同、Web画面 |
| `CLEARML_FILES_HOST` | `http://localhost:8081` | 同、File Server。学習の生成物のupload先 |
| `CLEARML_API_ACCESS_KEY` | 未設定 | 認証を有効にしたClearML Serverへ接続する場合のみ設定 |
| `CLEARML_API_SECRET_KEY` | 未設定 | 同上。seed・学習コマンドは2つ揃っていない場合にエラーとします |
| `SEMICONDUCTOR_SEED_OUTPUT` | `.generated/semiconductor` | 半導体seedの出力先 |
| `SEMICONDUCTOR_RANDOM_SEED` | `20260904` | 半導体seedが生成するデータのrandom seed |
| `PRIMEUI_LICENSE` | 未設定 | `apps/web/.env`。PrimeUIのライセンスキー |

認証キーは学習コマンドのTask Parametersには記録されません。未設定の場合はClearML SDKの設定ファイル（`~/clearml.conf`）にフォールバックします。

## ポートを変更する

`.env` の値を変更します。

```dotenv
CLEARML_WEB_PORT=8080
CLEARML_API_PORT=8008
CLEARML_FILES_PORT=8081
```

Angularのポートは [apps/web/package.json](apps/web/package.json) の `start` コマンドで設定しています。

## ブラウザに400エラーが表示される場合

通常のChromeでは `users.get_current_user` や `users.set_preferences` が
`400 BAD REQUEST` になり、シークレットモードでは正常に表示できる場合、
ブラウザに古いClearMLの認証情報が残っている可能性があります。

ChromeのDevToolsで `Application`、`Storage` の順に開き、
`Clear site data` を実行してCookieとLocal Storageを削除してから、ページを再読み込みしてください。

開発サーバーの `credentials.json` には、ユーザー名だけでログインするための
ローカル開発用認証情報が含まれます。この認証方式は信頼できるLAN内でのみ使用してください。

## 補足

- Angular開発サーバーからのAPIリクエストは `apps/web/proxy.config.mjs` により `http://localhost:8008` へ転送されます。
- ClearMLのデータはDockerのnamed volumeに保存されます。
- `backend:down` ではデータは削除されません。
