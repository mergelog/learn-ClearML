# ClearML Serverデータの初期化方法

## 概要

現在の`infra/clearml/compose.yaml`では、ClearML Serverの永続データをDockerのnamed volumeに保存しています。永続データを保存するbind mountやexternal volumeは使用していません。

この説明は、現在のCompose構成を確認した結果に基づきます。Compose構成を変更してbind mountやexternal volumeを使用した場合、それらのデータは`docker compose down -v`だけでは削除されません。

通常の停止コマンドではnamed volumeが残るため、データは削除されません。

```bash
corepack pnpm backend:down
```

ClearML Serverを学習開始前の状態へ戻す場合は、Docker Composeのサービスと、このCompose構成が管理するnamed volumeを削除してから、ClearML Serverを再起動します。

## 削除されるデータ

初期化すると、ローカルのClearML Serverに登録されている次のデータがすべて削除されます。

- Project
- DatasetとDataset Version
- Taskと実験履歴
- Parameters
- MetricsとPlots
- Model
- Artifact
- ClearML File Serverへアップロードしたファイル

削除したデータは基本的に復元できません。必要なデータがないことを確認してから実行してください。

## ClearML Serverデータを初期化する

プロジェクトルートで次を実行します。

```bash
docker compose -f infra/clearml/compose.yaml down -v
```

このコマンドはClearML Serverを停止し、このCompose構成が管理しているnamed volumeを削除します。bind mountやexternal volumeが将来追加された場合、その保存データはこのコマンドの削除対象になりません。

初期化後、ClearML Serverを再起動します。

```bash
corepack pnpm backend:up
```

コンテナの起動状態を確認します。

```bash
corepack pnpm backend:status
```

ClearML APIの疎通を確認します。

```bash
curl http://localhost:8008/debug.ping
```

正常な応答が返れば、ClearML Serverデータの初期化と再起動は完了です。ClearML標準Web画面は次のURLから確認できます。

```text
http://localhost:8080
```

ClearML Server全体の件数と、半導体学習データが残っていないことを確認します。

```bash
corepack pnpm backend:data:status
```

現在のCompose構成では、ClearML標準サンプルの自動登録を無効にしています。初期化直後は、Server全体と半導体学習データの両方が次の状態であることを確認します。

```text
ClearML Server全体:
- Project: 0件
- Task: 0件
- Model: 0件

判定: 半導体学習データはありません。学習開始前の状態です。
```

## 初期化後の注意点

Datasetだけを登録して、実験がない状態から学習を始める場合は次を実行します。

```bash
corepack pnpm seed:semiconductor:dataset
```

このコマンドが登録するものは次のとおりです。

- Dataset 2バージョン（`1.0.0`、`2.0.0`）
- `2.0.0`から`1.0.0`への親Dataset参照

実験TaskやModelは登録しません。同じコマンドを再実行した場合は、登録済みのDatasetを再利用します。

従来の全件seedは、比較用データを一括で用意する場合に使用します。

```bash
corepack pnpm seed:semiconductor
```

全件seedでは次のデモデータがまとめて登録されます。

- Dataset 2バージョン
- 比較用の実験20件
- 代表モデル3件

ClearML Webを空に近い状態から学習したい場合は、初期化直後に全件seedを実行しないでください。

想定する学習手順は次のとおりです。

```bash
# Python環境を初回だけ準備する
corepack pnpm python:setup

# Datasetだけを登録する
corepack pnpm seed:semiconductor:dataset

# 最初の学習Taskを作成する
corepack pnpm ml:train -- --dataset-version 1.0.0

# 条件を変更した2件目のTaskを作成する
corepack pnpm ml:train -- \
  --dataset-version 1.0.0 \
  --max-depth 6
```

## ローカル生成ファイルについて

半導体seedが作成したローカルファイルは、次のディレクトリに保存されます。

```text
.generated/semiconductor/
```

Dockerのnamed volumeを削除しても、このディレクトリは削除されません。ただし、ここにあるファイルはClearML Webに表示される登録データそのものではないため、ClearML Serverデータの初期化だけが目的であれば削除不要です。

ClearML SDKが取得したDatasetのキャッシュも、通常は次のディレクトリに残ります。

```text
~/.clearml/cache/
```

このキャッシュが残っていても、初期化後のClearML ServerにTaskやDatasetが復元されることはありません。

`~/.clearml/cache/`はグローバルなClearML SDK cacheであり、ほかのプロジェクトや実験でも使用される可能性があります。今回の学習開始時には削除しないでください。確認対象はServer側へ登録されるデータであるため、ClearML Serverのnamed volumeだけを初期化すれば十分です。

## ブラウザに古い状態が残る場合

ClearML Serverを初期化したあともブラウザに古い表示や認証情報が残る場合は、ページを再読み込みします。それでも解消しない場合は、Chrome DevToolsの`Application`、`Storage`から`Clear site data`を実行してください。
