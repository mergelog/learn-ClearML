まずは「AWSのこのサービスは、Azureだとだいたい何に当たるか」という対応だけ押さえるなら、これで十分です。

| AWS                 | Azure                                         | ざっくり何をするものか                 |
| ------------------- | --------------------------------------------- | --------------------------- |
| **S3**              | **Azure Blob Storage**                        | ファイル・画像・ログ・学習データなどのオブジェクト保存 |
| **EC2**             | **Azure Virtual Machines**                    | 仮想サーバー                      |
| **EBS**             | **Azure Managed Disks**                       | VMに付ける仮想ディスク                |
| **RDS**             | **Azure SQL Database / Azure Database系**      | マネージドDB                     |
| **DynamoDB**        | **Azure Cosmos DB**                           | NoSQLデータベース                 |
| **VPC**             | **Azure Virtual Network（VNet）**               | クラウド内の仮想ネットワーク              |
| **IAM**             | **Microsoft Entra ID + Azure RBAC**           | ユーザー認証・権限制御                 |
| **ELB**             | **Azure Load Balancer / Application Gateway** | 負荷分散                        |
| **Route 53**        | **Azure DNS**                                 | DNS管理                       |
| **CloudWatch**      | **Azure Monitor**                             | 監視・メトリクス・ログ                 |
| **CloudTrail**      | **Azure Activity Log**                        | 「誰が何を操作したか」の監査ログ            |
| **Lambda**          | **Azure Functions**                           | サーバーレス関数                    |
| **ECS**             | **Azure Container Apps / AKS**                | コンテナ実行                      |
| **EKS**             | **AKS（Azure Kubernetes Service）**             | Kubernetes                  |
| **ECR**             | **Azure Container Registry（ACR）**             | Dockerイメージ保管                |
| **Secrets Manager** | **Azure Key Vault**                           | パスワード・APIキー・証明書管理           |
| **CloudFront**      | **Azure Front Door / Azure CDN**              | CDN、Web配信高速化                |
| **SQS**             | **Azure Service Bus Queue / Storage Queue**   | メッセージキュー                    |
| **SNS**             | **Azure Service Bus Topics / Event Grid**     | Pub/Sub、イベント通知              |
| **API Gateway**     | **Azure API Management**                      | API公開・認証・制御                 |

今回のClearML案件との関連だけに絞るなら、最初はこの8個を押さえるとよいです。

**AWS → Azure**

* S3 → **Blob Storage**
* EC2 → **Virtual Machines**
* VPC → **VNet**
* IAM → **Entra ID + RBAC**
* EKS → **AKS**
* ECR → **ACR**
* CloudWatch → **Azure Monitor**
* Secrets Manager → **Key Vault**

特に最重要なのは、

**S3 ≒ Azure Blob Storage**

です。

ClearMLで「Dataset」「Artifact」「Model」「ログファイル」などをクラウドストレージに置く場合、AWSならS3、AzureならBlob Storage、という理解でまず問題ありません。

たとえばイメージは、

`ClearML`
→ 学習データ
→ **Azure Blob Storage**

`ClearML Agent`
→ コンテナを取得
→ **Azure Container Registry**

`ClearML Server`
→ Kubernetesで稼働
→ **AKS**

`ユーザー認証`
→ **Microsoft Entra ID**

`ログ・監視`
→ **Azure Monitor**

という形です。

ただし、AWSとAzureは完全な1対1対応ではありません。特に **IAM ↔ Entra ID + RBAC** や **ECS ↔ Container Apps / AKS** は設計思想が少し違うので、「同じもの」ではなく「役割が近いもの」と捉えるのが正確です。
