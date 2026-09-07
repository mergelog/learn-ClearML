基本的には不要です。

`takeUntilDestroyed()` を使って、

`observable.pipe(takeUntilDestroyed()).subscribe(...)`

としているなら、コンポーネントやディレクティブ等が破棄されたタイミングで購読が自動解除されるため、

`const sub = ...`
`sub.unsubscribe()`

のように `Subscription` を保持しておく必要は通常ありません。

つまり、Angularではかなり単純化すると、

`subscribe()`
→ `Subscription` は返る

ただし

`takeUntilDestroyed()`
→ Angularの破棄タイミングで自動的に unsubscribe 相当の処理が走る

なので、戻り値の `Subscription` を受け取らず、そのまま

`this.api.getUsers()
  .pipe(takeUntilDestroyed())
  .subscribe(users => {
    this.users = users;
  });`

で問題ありません。

ただし例外があります。コンポーネントが破棄される前に「今すぐこの購読だけ止めたい」という要件があるなら、`Subscription` を保持して `unsubscribe()` する意味があります。

たとえば、

`this.subscription = observable
  .pipe(takeUntilDestroyed())
  .subscribe(...);`

としておいて、途中で

`this.subscription.unsubscribe();`

とするケースです。

なので整理すると、

**「コンポーネント破棄時のunsubscribe漏れを防ぎたい」**
→ `takeUntilDestroyed()` があるので `Subscription` 保持は不要

**「任意のタイミングで途中停止したい」**
→ `Subscription` を保持することがある

という理解で大丈夫です。

Angularの実務コードでは、単なるライフサイクル管理目的なら

`Subscription` をフィールドに持つより `takeUntilDestroyed()` の方が今はかなり自然です。
