exhaustMap
処理中の新しい要求を無視

switchMap
新しい要求が来たら、古い処理をキャンセル

concatMap
新しい要求を待ち行列に入れて順番に処理

mergeMap
すべて同時に処理

---

map：Observableから流れてきた値を、好きな値・型へ変換する
of：指定した値を流して完了するObservableを作る

from: ofは引数一個ずつ、fromは引数一個だけだが、中身をそれぞれ処理する https://qiita.com/ksh-fthr/items/3f5ecb5bf47ad0216101#from

complete: 厳密には、「最後の値なら処理する」ではなく、Observable 自体が完了したと通知してきたら処理する

---

| Operator     | 新しい要求が来たとき         | イメージ              |
| ------------ | ------------------ | ----------------- |
| `exhaustMap` | 処理中なら新しい要求を無視      | 「今やってるから後は受け付けない」 |
| `switchMap`  | 古い処理を打ち切って新しい要求へ切替 | 「最新だけ欲しい」         |
| `concatMap`  | 待ち行列に積んで順番に処理      | 「全部やる。順番厳守」       |
| `mergeMap`   | 新しい要求もすぐ開始         | 「全部同時にやる」         |

