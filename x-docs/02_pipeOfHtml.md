# Angular テンプレートの Pipe（`|`）

Angular の HTML テンプレートでは、**パイプ（Pipe）構文**を使って表示値を整形できる。

```html
{{ price | currency:'JPY' }}
```

`|` の左にある値を右の Pipe に渡し、Pipe が返した値を画面に表示する。
Unix のパイプと同じく、値を次の処理へ流すイメージで読むと分かりやすい。

> この資料は、このリポジトリで使っている Angular 22 のスタンドアロンコンポーネントを前提にする。

## まず結論

テンプレートの Pipe は、主に次のような **表示のための単純な変換** に使う。

| やりたいこと | 例 |
| --- | --- |
| 日付を見やすくする | `{{ createdAt | date:'yyyy/MM/dd' }}` |
| 数値に桁区切りを付ける | `{{ count | number }}` |
| 金額を通貨表記にする | `{{ price | currency:'JPY' }}` |
| Observable の最新値を表示する | `{{ backgroundColor$ | async }}` |
| 表示専用の小さな変換を共通化する | 独自 Pipe |

一方で、複雑な計算、複数の状態を組み合わせる処理、業務ルール、API 用データの加工は TypeScript 側へ置く。HTML にロジックを詰め込むと、テスト・再利用・デバッグがしづらくなる。

## 構文

### 基本形

```html
{{ 値 | pipe名 }}
```

```html
{{ name | uppercase }}
```

`name` が `"Angular"` のとき、画面には `ANGULAR` と表示される。

### 引数を渡す

```html
{{ 値 | pipe名:引数1:引数2 }}
```

```html
{{ price | currency:'JPY' }}
{{ createdAt | date:'yyyy/MM/dd HH:mm' }}
{{ title | slice:0:20 }}
```

`:` の後ろが Pipe の引数である。文字列は `'JPY'` のようにクォートする。テンプレートの変数や式も引数に渡せる。

```html
{{ title | slice:0:maxLength }}
```

### 複数の Pipe をつなぐ

```html
{{ 値 | pipeA | pipeB }}
```

左から順番に評価される。

```html
{{ name | lowercase | titlecase }}
```

この例は、まず小文字化し、その結果をタイトルケースへ変換する。

`async` も Pipe の一つなので、Observable の値を整形するときは通常 `async` を先に置く。

```html
{{ price$ | async | currency:'JPY' }}
```

流れは次のとおり。

```text
price$（Observable）
  → async（最新の number または null を取り出す）
  → currency:'JPY'（通貨文字列に整形する）
  → 画面へ表示
```

## このリポジトリの `AsyncPipe` の例

`02_hello-world` の `ColorPickerForm` には次の定義がある。

```ts
readonly backgroundColor$ = this.store.select(
  ColorSelectors.selectBackgroundColor,
);
```

変数名の末尾に付く `$` は、**Observable であることを表す慣習**である。TypeScript の文法上の意味はないが、コードを読む人が「値そのものではなく、値を通知するストリームだ」と判断できる。

`store.select()` は Observable を返すため、テンプレートではそのまま文字列として表示できない。そこで `AsyncPipe` を使う。

```html
<dd>{{ backgroundColor$ | async }}</dd>
```

`AsyncPipe` は以下を担当する。

1. `backgroundColor$` を購読する。
2. Observable から新しい値が届くたびに、表示を最新値へ更新する。
3. コンポーネントが破棄されたとき、購読を自動解除する。

したがって、表示だけが目的なら次のような手動購読は通常不要である。

```ts
// 表示のためだけなら、基本的には書かない
backgroundColor = '';

ngOnInit(): void {
  this.store.select(ColorSelectors.selectBackgroundColor)
    .subscribe((color) => {
      this.backgroundColor = color;
    });
}
```

手動で `subscribe()` すると、破棄時の解除、エラー処理、更新先プロパティの管理を自分で考える必要がある。テンプレート表示だけなら `AsyncPipe` の方が短く安全である。

### `AsyncPipe` が返す値と `null`

`AsyncPipe` は、Observable からまだ値が届いていない間は `null` を返しうる。そのため、非同期 API の結果などを直後に別の Pipe で処理する場合は `null` を考慮する。

```html
<!-- 商品がまだない間は何も表示しない -->
@if (product$ | async; as product) {
  <p>{{ product.price | currency:'JPY' }}</p>
}
```

`as product` を使うと、`async` の結果をブロック内で一度だけ受け取り、繰り返し `| async` と書かずに済む。

```html
<!-- 避けたい: 同じ Observable を何度も展開している -->
<p>{{ (product$ | async)?.name }}</p>
<p>{{ (product$ | async)?.price | currency:'JPY' }}</p>
```

上のようなケースは `@if (...; as ...)` で値を受ける方が読みやすい。

### Signal には `async` を使わない

Signal は関数として呼び出すと現在値を読める。

```ts
readonly pickedColor = signal('#ffffff');
```

```html
{{ pickedColor() }}
```

これは Observable ではないので、`{{ pickedColor() | async }}` にはしない。

このリポジトリの `ColorPickerForm` では、比較のために両方が使われている。

| 値 | 種別 | テンプレートでの読み方 |
| --- | --- | --- |
| `pickedColor` | Signal | `{{ pickedColor() }}` |
| `backgroundColor$` | Observable | `{{ backgroundColor$ | async }}` |

Angular / NgRx の新規コードでは、状態を Signal として読む `selectSignal()` を選ぶ場面も多い。その場合は `async` ではなく Signal を呼び出す。

```ts
readonly backgroundColor = this.store.selectSignal(
  ColorSelectors.selectBackgroundColor,
);
```

```html
{{ backgroundColor() }}
```

どちらを採用するかは周辺の設計に合わせる。RxJS の時間系 Operator（例: `debounceTime`）や Observable API と合成するなら Observable が自然であり、同期的に状態を読む画面なら Signal が読みやすい。

## スタンドアロンコンポーネントでの import

Pipe はテンプレートで使う前に、そのコンポーネントから利用可能にする必要がある。スタンドアロンコンポーネントでは、`@Component` の `imports` に追加する。

```ts
import { AsyncPipe, CurrencyPipe, DatePipe } from '@angular/common';
import { Component } from '@angular/core';

@Component({
  selector: 'app-order-summary',
  templateUrl: './order-summary.html',
  styleUrl: './order-summary.css',
  imports: [AsyncPipe, CurrencyPipe, DatePipe],
})
export class OrderSummary {}
```

このリポジトリの `ColorPickerForm` の次の記述は、テンプレートの `| async` を使えるようにするためのもの。

```ts
imports: [AsyncPipe],
```

`CommonModule` を import する方法もある。

```ts
import { CommonModule } from '@angular/common';

@Component({
  imports: [CommonModule],
})
export class OrderSummary {}
```

`CommonModule` には多くの標準ディレクティブ・Pipe が含まれる。ただし、このリポジトリのようにスタンドアロン構成で依存を明確にしたい場合は、`AsyncPipe` や `CurrencyPipe` を個別に import する書き方が分かりやすい。

> `@if`、`@for`、`@switch` は Angular の組み込み制御フロー構文であり、`CommonModule` の import は不要である。一方、`async`、`date`、`currency` などの Pipe は import が必要である。

## よく使う組み込み Pipe

以下は `@angular/common` から個別 import できる代表的な Pipe である。

| Pipe | 例 | 主な用途 | 注意点 |
| --- | --- | --- | --- |
| `AsyncPipe` | `value$ \| async` | Observable / Promise の最新値を表示 | Signal には不要 |
| `DatePipe` | `date:'yyyy/MM/dd'` | 日付・時刻の表示 | タイムゾーン、ロケールに注意 |
| `CurrencyPipe` | `currency:'JPY'` | 金額の表示 | 金額の計算には使わない |
| `DecimalPipe` | `number:'1.0-2'` | 数値、桁区切り、小数桁の整形 | 表示のみ |
| `PercentPipe` | `percent:'1.0-1'` | 割合の表示 | `0.123` は通常 `12.3%` |
| `UpperCasePipe` | `uppercase` | 英字を大文字化 | 日本語には変化がない |
| `LowerCasePipe` | `lowercase` | 英字を小文字化 | 日本語には変化がない |
| `TitleCasePipe` | `titlecase` | 単語の先頭を大文字化 | 英語表示向け |
| `SlicePipe` | `slice:0:20` | 文字列・配列の一部を表示 | 省略記号は自動で付かない |
| `JsonPipe` | `json` | オブジェクトを JSON 表示 | 開発・デバッグ向け。通常の画面には置かない |
| `KeyValuePipe` | `keyvalue` | オブジェクトや Map を列挙 | 並び順が必要なら比較関数を検討 |
| `I18nPluralPipe` | `i18nPlural:messageMap` | 件数に応じた文言変更 | 本格的な多言語化は Angular i18n も検討 |

### `CurrencyPipe` — 金額を表示する

```ts
import { CurrencyPipe } from '@angular/common';
```

```html
{{ price | currency:'JPY' }}
```

`price` が `1200` なら、ロケール設定に従って `￥1,200` のように表示される。

より細かく指定する場合は次の形式を使う。

```html
{{ price | currency:'JPY':'symbol':'1.0-0':'ja-JP' }}
```

引数の意味は以下のとおり。

| 順番 | 引数 | 例 | 意味 |
| --- | --- | --- | --- |
| 1 | 通貨コード | `'JPY'` | ISO 4217 の通貨コード |
| 2 | 表示形式 | `'symbol'` | 記号、コード、独自文字列など |
| 3 | 桁指定 | `'1.0-0'` | 最低整数桁.最低小数桁-最大小数桁 |
| 4 | ロケール | `'ja-JP'` | 表示ルールに使うロケール |

金額を扱う際、Pipe は**見た目を変えるだけ**である。税計算、丸め、合計などの業務ルールを Pipe に隠さず、TypeScript の明示的な関数やドメインロジックとして実装する。

### `DatePipe` — 日付を表示する

```ts
import { DatePipe } from '@angular/common';
```

```html
{{ createdAt | date:'yyyy/MM/dd' }}
{{ createdAt | date:'yyyy/MM/dd HH:mm':'Asia/Tokyo':'ja-JP' }}
```

日付は「どのタイムゾーンの何時か」が重要である。API が UTC を返すか、日時文字列にオフセットを含むか、表示を利用者のローカル時刻にするかを API 境界で決める。

`DatePipe` は画面での書式を整えるために使い、曖昧な日時文字列の解釈に依存しないよう注意する。

### `DecimalPipe` と `PercentPipe` — 数字を読みやすくする

```ts
import { DecimalPipe, PercentPipe } from '@angular/common';
```

```html
{{ total | number }}
{{ score | number:'1.0-2' }}
{{ completionRate | percent:'1.0-1' }}
```

`number:'1.0-2'` の `1.0-2` は、次のルールを意味する。

```text
最低整数桁 . 最低小数桁 - 最大小数桁
  1       .     0     -     2
```

たとえば `12.345` を `number:'1.0-2'` で表示すると、最大 2 桁までの小数表記になる。表示の丸めと、業務上必要な丸めは混同しない。

### `SlicePipe` — 一部だけ表示する

```ts
import { SlicePipe } from '@angular/common';
```

```html
<p>{{ description | slice:0:100 }}{{ description.length > 100 ? '…' : '' }}</p>
```

文字数制限が単なる見た目の都合であれば有用である。ただし「省略文をどう作るか」がプロダクトの仕様なら、独自 Pipe または表示用 ViewModel に切り出す方が意図を表しやすい。

### `KeyValuePipe` — オブジェクトを `@for` で表示する

```ts
import { KeyValuePipe } from '@angular/common';
```

```html
@for (entry of settings | keyvalue; track entry.key) {
  <dt>{{ entry.key }}</dt>
  <dd>{{ entry.value }}</dd>
}
```

動的なキーを持つ設定情報などを表示する場合に使う。UI の表示順が重要なら、オブジェクト任せにせず、最初から表示順を持つ配列へ整形することを優先する。

### `JsonPipe` — デバッグにだけ使う

```ts
import { JsonPipe } from '@angular/common';
```

```html
<pre>{{ state | json }}</pre>
```

状態の確認には便利だが、オブジェクト全体の表示は重くなりやすく、情報漏えいにもつながりうる。リリースする画面には残さない。

## Pipe と TypeScript 側の `pipe()` は別物

Angular / RxJS には、同じ「pipe」という名前で混乱しやすいものが二つある。

| 場所 | 記法 | 正体 | 目的 |
| --- | --- | --- | --- |
| Angular テンプレート | `{{ value \| currency:'JPY' }}` | Angular Pipe | **表示値**を変換する |
| TypeScript / RxJS | `value$.pipe(map(...))` | RxJS のメソッド | Observable の通知を変換・制御する |

たとえば次の 2 行は別の層の処理である。

```ts
readonly price$ = this.product$.pipe(
  map((product) => product.price),
);
```

```html
{{ price$ | async | currency:'JPY' }}
```

前者はデータの流れを作る RxJS、後者は最終的な画面表示を整える Angular Pipe である。

## Pure Pipe と Impure Pipe

独自 Pipe を作るときに知っておくべき設定が `pure` である。

### Pure Pipe（標準、基本はこちら）

```ts
@Pipe({
  name: 'displayName',
  pure: true,
})
```

Pure Pipe は、入力値または引数の**参照が変わったとき**に変換を再実行する。Angular の組み込み Pipe の多くは Pure Pipe である。

利点は、不要な再実行が少なく性能上扱いやすいこと。通常の独自 Pipe は必ず Pure Pipe として設計する。

注意点は、配列やオブジェクトを破壊的に変更しても参照が同じなら再実行対象にならないこと。

```ts
// 避ける: 同じ配列を直接変更している
this.items.push(newItem);

// 推奨: 新しい配列を作る
this.items = [...this.items, newItem];
```

Angular の Signal や NgRx では、もともと不変更新を基本にするため、Pure Pipe と相性がよい。

### Impure Pipe（原則として避ける）

```ts
@Pipe({
  name: 'example',
  pure: false,
})
```

Impure Pipe は変更検知のたびに実行される。入力の内部変更を拾える反面、一覧や複雑な画面では処理回数が増え、性能問題を作りやすい。

検索・フィルタ・ソートのために Impure Pipe を作るのは避ける。代わりに、コンポーネントで Signal の `computed()`、または Observable の `map()` を使って派生値を一度作る。

```ts
readonly visibleProducts = computed(() =>
  this.products().filter((product) => product.isVisible),
);
```

## 独自 Pipe を作る基準

標準 Pipe で表せず、次の条件を満たすなら独自 Pipe が候補になる。

- 入力から表示値への変換が小さく、同期的である
- 副作用がない（HTTP 通信、状態更新、ログ記録などをしない）
- 複数画面で再利用する、またはテンプレートの意図が明確になる
- 業務ルールの本体ではなく、表示の表現を担当する

### 例: 色コードを表示用に整える

`#ffffff` を `#FFFFFF` と表示するだけなら、独自 Pipe は適している。

```ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'colorCode',
})
export class ColorCodePipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    return value?.toUpperCase() ?? '';
  }
}
```

スタンドアロン Pipe としてテンプレートで使うには `standalone: true` を明示できる（現在の Angular では Pipe はデフォルトで standalone）。依存関係を明確にするため、ここでは明示する。

```ts
@Pipe({
  name: 'colorCode',
  standalone: true,
})
export class ColorCodePipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    return value?.toUpperCase() ?? '';
  }
}
```

使うコンポーネントで import する。

```ts
import { ColorCodePipe } from './color-code.pipe';

@Component({
  imports: [ColorCodePipe],
})
export class ColorPickerForm {}
```

```html
{{ backgroundColor$ | async | colorCode }}
```

### 引数を受け取る独自 Pipe

```ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'truncate',
  standalone: true,
})
export class TruncatePipe implements PipeTransform {
  transform(value: string | null | undefined, maxLength: number): string {
    if (!value || value.length <= maxLength) {
      return value ?? '';
    }

    return `${value.slice(0, maxLength)}…`;
  }
}
```

```html
{{ description | truncate:80 }}
```

`transform()` の第 1 引数が `|` の左から渡る値で、第 2 引数以降が `:` で渡す引数となる。

### 独自 Pipe に入れてはいけないこと

以下は Pipe に置かない。

| 処理 | 置き場所の例 | 理由 |
| --- | --- | --- |
| HTTP 通信 | Service / Effect | 表示のたびに実行されうる。副作用がある |
| Store の更新 | Component / Store method / Effect | Pipe は表示を変換するだけにする |
| 複雑な絞り込み・ソート | `computed()` / RxJS `map()` / Selector | 性能とテスト容易性のため |
| 税額計算・権限判定 | ドメイン関数 / Use case | 重要なルールを HTML から隠さない |
| 非同期処理 | Observable / Promise を作る TypeScript | Pipe の責務ではない |

## 可読性を保つ実務上のルール

Pipe は便利だが、長くつなぐと HTML が読みにくくなる。以下を目安にする。

### 1. 1〜2 個の単純な Pipe ならテンプレートに置く

```html
{{ order.total | currency:'JPY' }}
{{ order.createdAt | date:'yyyy/MM/dd' }}
{{ status | titlecase }}
```

これは「何を表示するか」がその場で分かり、テンプレートに置く価値がある。

### 2. `async` の結果を何度も使うなら `@if ... as` で受ける

```html
@if (order$ | async; as order) {
  <h2>{{ order.name }}</h2>
  <p>{{ order.total | currency:'JPY' }}</p>
  <time>{{ order.createdAt | date:'yyyy/MM/dd HH:mm' }}</time>
}
```

### 3. 3 個以上の連結や条件式は TypeScript 側へ切り出す

```html
<!-- 読みにくくなり始める例 -->
{{ (price$ | async) ?? 0 | currency:'JPY':'symbol':'1.0-0':'ja-JP' }}
```

このような表示要件が何か所にも出るなら、ViewModel、`computed()`、RxJS の `map()`、または名前のある独自 Pipe に切り出す。

```ts
readonly displayPrice = computed(() => {
  const price = this.price() ?? 0;
  return formatJapaneseYen(price);
});
```

```html
{{ displayPrice() }}
```

ただし、`formatJapaneseYen()` のような表示用関数をテンプレートから直接何度も呼び出す設計は避ける。Signal の `computed()` や Pipe によって、依存と再計算の意図を明確にする。

### 4. 表示専用の共通変換は独自 Pipe、画面固有の組み立ては ViewModel

| 種別 | 例 | 適した場所 |
| --- | --- | --- |
| 共通の小さな表示変換 | ステータスコードをラベルへ変換 | 独自 Pipe |
| 画面固有の表示モデル | 商品、在庫、権限から購入可否を作る | Component の `computed()` / Selector |
| 複数 Feature にまたがる派生状態 | ログインユーザーと権限からメニューを作る | NgRx Selector |
| 非同期データの変換 | API DTO を画面モデルへ変換 | Service / RxJS `map()` / Effect |

## よくある間違い

### `async` は Observable の変換 Operator ではない

`async` は Angular テンプレート用の Pipe であり、RxJS の `map()` や `switchMap()` の仲間ではない。

```html
{{ backgroundColor$ | async }}
```

は HTML で値を表示するための書き方である。Observable の中身を TypeScript 側で変換したいなら、RxJS の `pipe()` を使う。

```ts
readonly upperColor$ = this.backgroundColor$.pipe(
  map((color) => color.toUpperCase()),
);
```

### Pipe を使うのに import していない

スタンドアロンコンポーネントで以下のようなエラーが出る場合、Pipe を `imports` に追加していない可能性が高い。

```text
No pipe found with name 'currency'
```

```ts
import { CurrencyPipe } from '@angular/common';

@Component({
  imports: [CurrencyPipe],
})
export class ExampleComponent {}
```

### `async` を二重に使う

```html
<!-- 避ける -->
{{ value$ | async | async }}
```

基本的には不要である。最初の `async` が返す値がさらに Observable / Promise という特殊な設計を除き、データ構造を TypeScript 側で整理する。

### Pipe の中で状態を更新する

```ts
// 避ける: transform() の中で store.dispatch() などをしない
transform(value: string): string {
  this.store.dispatch(...);
  return value;
}
```

表示の評価が状態変更を起こすと、予測不能な更新や無限ループの原因になる。Pipe は入力から出力を返すだけの関数として保つ。

### 毎回新しいオブジェクトを返す重い Pipe

Pipe が大量の配列を処理したり、毎回新しい配列・オブジェクトを作ったりすると、リスト描画の性能に影響する。大きなデータの整形は Selector や `computed()` で行い、`@for` では安定した `track` を指定する。

## テスト

Pure な独自 Pipe は、クラスを生成して `transform()` を直接テストできる。

```ts
describe('TruncatePipe', () => {
  const pipe = new TruncatePipe();

  it('長い文字列に省略記号を付ける', () => {
    expect(pipe.transform('abcdefghij', 5)).toBe('abcde…');
  });

  it('短い文字列はそのまま返す', () => {
    expect(pipe.transform('abc', 5)).toBe('abc');
  });
});
```

Pipe に依存性注入や副作用がないほど、このように速く単純にテストできる。

## チェックリスト

テンプレートに Pipe を追加するときは、次を確認する。

- [ ] 表示のための単純な変換か
- [ ] 使用する Pipe をコンポーネントの `imports` に追加したか
- [ ] Observable なら `async`、Signal なら `()` と使い分けたか
- [ ] `async` の未到着時の `null` を考慮したか
- [ ] 同じ `| async` を何度も書かず、必要なら `@if (...; as value)` を使ったか
- [ ] 複雑な処理、業務ルール、副作用を Pipe に入れていないか
- [ ] 独自 Pipe は Pure のまま実装できないか
- [ ] 日付・通貨はロケールとタイムゾーンの要件を確認したか

## 参考

- [Angular: Pipes](https://angular.dev/guide/templates/pipes)
- [Angular API: AsyncPipe](https://angular.dev/api/common/AsyncPipe)
- [Angular API: CurrencyPipe](https://angular.dev/api/common/CurrencyPipe)
- [Angular API: DatePipe](https://angular.dev/api/common/DatePipe)
