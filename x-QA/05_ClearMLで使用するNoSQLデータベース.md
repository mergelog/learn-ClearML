# ClearMLで使用するNoSQLデータベース

## このプロジェクトではNoSQLデータベースを使用していますか？

使用しています。メインのデータベースは、ドキュメント指向のNoSQLデータベースであるMongoDBです。

また、ClearML Serverはデータの用途に応じて、次のデータストアを使用します。

| データストア | 種類 | 主な用途 |
| --- | --- | --- |
| MongoDB 8.0.15 | ドキュメント指向NoSQLデータベース | プロジェクト、タスク、Dataset、Modelなどのメタデータ |
| Elasticsearch 8.19.9 | 分散検索・分析エンジン | 実験ログ、スカラー指標、検索用データ |
| Redis 8.2.3 | インメモリ型キーバリューストア | キャッシュや一時的な処理データ |
| ClearML File Server | ファイルストレージ | 画像、モデルファイル、Artifact、Datasetの実ファイル |

PostgreSQLやMySQLなどのリレーショナルデータベースは、このプロジェクトのClearML Server構成では使用していません。

構成は `infra/clearml/compose.yaml` で確認できます。
