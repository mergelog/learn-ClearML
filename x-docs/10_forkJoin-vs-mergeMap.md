`forkJoin` と `mergeMap` は、そもそも役割がかなり違います。

一言でいうと、

* `forkJoin` → 「複数のObservableをまとめて、全部終わるのを待つ」
* `mergeMap` → 「値を受け取るたびに別Observableを開始し、並列で流す」

たとえばAPI通信で見ると分かりやすいです。

`forkJoin` はこういう用途です。

```ts
forkJoin({
  users: this.api.getUsers(),
  products: this.api.getProducts(),
  settings: this.api.getSettings(),
}).subscribe(result => {
  console.log(result.users);
  console.log(result.products);
  console.log(result.settings);
});
```

3つのAPIは並列で実行されます。

そして、

```text
getUsers()     ─────完了
getProducts()  ─────────完了
getSettings()  ────完了

                    ↓
              全部終わった
                    ↓
               next が1回
```

という動きです。

つまり `forkJoin` は、

> 「A・B・C全部の結果が揃ったら次へ進みたい」

ときに使います。

一方、`mergeMap` はこうです。

```ts
of(1, 2, 3).pipe(
  mergeMap(id =>
    this.api.getUser(id)
  )
).subscribe(user => {
  console.log(user);
});
```

これは、

```text
1 → getUser(1) ─────────
2 → getUser(2) ────
3 → getUser(3) ──────
```

のように、3つのAPIを同時進行させます。

そして完了した順に、

```text
user2
user3
user1
```

のように結果が流れてくる可能性があります。

重要なのは、`mergeMap` は「全部揃うまで待つ」のではないということです。

比較するとこうなります。

|        | `forkJoin`        | `mergeMap`                  |
| ------ | ----------------- | --------------------------- |
| 主目的    | 複数Observableをまとめる | Observableから別Observableへつなぐ |
| 並列実行   | できる               | できる                         |
| 結果     | 全部完了後にまとめて1回      | 完了したものから順次                  |
| 順序     | 結果のキー・配列順を維持      | 完了順になる可能性あり                 |
| よくある用途 | 画面初期表示で複数API取得    | IDごとにAPIを呼ぶ                 |
| 分類     | Observable生成・結合   | flattening operator         |

この2つは競合するものではなく、一緒に使うこともあります。

```ts
this.route.params.pipe(
  mergeMap(params =>
    forkJoin({
      user: this.api.getUser(params['id']),
      orders: this.api.getOrders(params['id']),
    })
  )
)
```

これは、

```text
URLのidを取得
  ↓
mergeMap
  ↓
そのidを使って
 ├─ getUser()
 └─ getOrders()
      ↓
   forkJoin
      ↓
両方揃ったら結果を返す
```

という構造です。

なので覚え方としては、

> `mergeMap` = 「次の非同期処理を開始する」
> `forkJoin` = 「複数の非同期処理が全部終わるのを待つ」

くらいに分けるとかなり整理しやすいです。

なお `forkJoin` には重要な注意点があって、**全Observableが `complete` しないと結果を出しません**。`HttpClient` のAPI通信は通常1回レスポンスを返して完了するので、`forkJoin` と非常に相性がいいです。
