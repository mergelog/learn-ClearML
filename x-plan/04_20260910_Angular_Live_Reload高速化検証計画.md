# Angular Live Reload高速化検証計画

## 1. 目的

ClearML WebのAngular開発環境において、TypeScript変更後のブラウザ反映が遅い原因を計測で特定し、安全性を維持したまま編集から確認までの待ち時間を短縮する。

本計画では、次の4区間を分離して評価する。

```text
ファイル保存
  ↓ A. 変更検知
Changes detected. Rebuilding...
  ↓ B. Angular incremental rebuild
Application bundle generation complete. [x seconds]
  ↓ C. Vite WebSocketによる更新通知
Page reload sent to client(s).
  ↓ D. ブラウザ全reload後のアプリ起動
Angular bootstrap → Router / NgRx → API取得 → Dashboard描画
```

一般的なJavaScript／TypeScript HMRをAngular CLIがサポートしていないことと、rebuildやページ再起動が過度に遅いことは別問題として扱う。

## 2. 現状

2026-09-10時点で確認できている構成は次のとおりである。

| 項目 | 現状 |
| --- | --- |
| Angular CLI | 22.1.7 |
| Angular | 22.1.5 |
| `@angular/build` | 22.1.7 |
| TypeScript | 6.0.3 |
| build builder | `@angular/build:application` |
| dev-server builder | `@angular/build:dev-server` |
| development source map | 有効 |
| `isolatedModules` | 未設定 |
| Stackupの`preserveSymlinks` | `false` |
| 通常のserve設定 | `liveReload: false` |
| live reload用script | `ng serve --live-reload true` |
| ソース配置 | WSL2のLinux領域 `/home/mtrysd/...` |
| inotify `max_user_watches` | 524288 |
| LAN経由のVite WebSocket | HTTP 101で接続可能 |

Angular CLIのViteはdev serverとして利用され、Angular buildが生成した結果を配信する。一般的なJavaScript HMRは未対応であり、現在のHMR対象はグローバルstyle、Component style、Component templateである。TypeScript変更時のページ全reload自体は現行仕様である。

## 3. 対象範囲

### 3.1 対象

- TypeScript保存からDashboardが操作可能になるまでの時間
- Angular incremental rebuildの時間
- Vite WebSocketによる更新通知
- 全reload後のAngular bootstrap、NgRx初期化、API取得、描画
- `isolatedModules: true`によるAngular 22.1のesbuild transpilation経路
- 変更ファイルの依存coneとbarrel importの影響
- development source mapの影響

### 3.2 対象外

- 一般的なTypeScript HMRを独自実装すること
- Angular CLI内部のVite設定を直接変更すること
- 根拠なく全barrel importを廃止すること
- `node_modules`や`.angular`を定常的に削除する運用
- 変更検知が正常な状態でのpolling導入
- dependency prebundleの無計画な無効化
- productionの最適化設定を開発速度だけを理由に変更すること

## 4. 仮説と優先順位

| 優先度 | 仮説 | 判定方法 |
| --- | --- | --- |
| P0 | 全reload後のClearML起動が重い | F5とlive reload後の表示時間を比較する |
| P0 | `isolatedModules`未設定によりTypeScript emit経路を使用している | baseline取得後に`true`との比較試験を行う |
| P1 | 初回編集時に依存coneが広く再処理される | 同一TSファイルの1回目と2回目を比較する |
| P1 | 共通moduleやbarrelがaffected filesを広げている | 末端Componentと共通ファイルを比較する |
| P2 | source map生成またはブラウザ側解析が重い | development限定でsource map有無を比較する |
| P3 | ファイル監視が遅い | 保存から`Changes detected`までを計測する |

ファイル変更はすでに即座に検知されているため、pollingとinotifyは現時点の主仮説から除外する。

## 5. 測定方法

### 5.1 測定対象

次の時間を別々に記録する。

| 指標 | 始点 | 終点 |
| --- | --- | --- |
| 検知時間 | エディタで保存 | `Changes detected. Rebuilding...` |
| rebuild時間 | `Changes detected. Rebuilding...` | `Application bundle generation complete` |
| 通知時間 | bundle生成完了 | ブラウザがreload開始 |
| アプリ起動時間 | ブラウザreload開始 | Dashboardが操作可能 |
| 合計時間 | エディタで保存 | Dashboardが操作可能 |
| F5時間 | F5実行 | Dashboardが操作可能 |

### 5.2 テスト条件

- 同じPC、同じブラウザ、同じDashboard URLを使用する。
- DevToolsは同じ設定に固定する。
- API serverとネットワーク条件を揃える。
- 初期build直後の1回をwarm-upとして分離する。
- 各ケースを最低3回、可能なら5回測定し、中央値を比較する。
- コードの意味を変えない編集を使用する。コメントまたはdebug用文字列だけを変更する。
- 各比較では一度に1設定だけ変更する。
- Angular再起動が必要な設定変更では、再起動後にブラウザを一度手動更新して新しいVite WebSocket tokenへ接続する。

### 5.3 テストファイル

| ケース | 対象例 | 目的 |
| --- | --- | --- |
| 末端TS | DashboardのカードComponent | 通常のTypeScript rebuildを測る |
| 同一TSの2回目 | 上と同じファイル | 初回依存cone問題を判定する |
| Component HTML | 同Componentのtemplate | template HMRの速度と動作を確認する |
| Component SCSS | 同Componentのstyle | style HMRの速度と動作を確認する |
| 共通TS | 多数から参照されるservice/model | import graphの影響を比較する |
| F5 | コード変更なし | ClearML runtime起動時間を測る |

## 6. 実施手順

### Phase 1: Baseline取得

1. `liveReload: true`または既存の`hmr` scriptでAngularを起動する。
2. ブラウザを手動更新し、Vite WebSocketがHTTP 101で接続されていることを確認する。
3. 末端ComponentのTSを同じ内容の変更方法で2回保存する。
4. 各回のrebuild時間と合計時間を記録する。
5. 同じ画面でF5を3～5回実行し、操作可能になるまでを記録する。
6. HTMLとSCSSも変更し、terminalにComponent updateが出るか確認する。

判定は次のとおりとする。

```text
live reload合計 ≒ F5時間
  → 主因はClearML runtime初期化

live reload合計 ≫ F5時間
かつrebuildが長い
  → 主因はAngular build

1回目のTS変更 ≫ 2回目
  → 初回依存cone問題を疑う

末端TS ≪ 共通TS
  → import graph / barrel dependency coneを疑う
```

### Phase 2: `isolatedModules`比較試験

Phase 1でrebuild時間が無視できない場合に実施する。

1. `apps/web/tsconfig.json`の`compilerOptions`へ`"isolatedModules": true`を追加する。
2. Angularを完全に停止して再起動する。
3. 初期buildが成功することを確認する。
4. Phase 1と同一のTS変更を同じ回数行う。
5. rebuild時間の中央値をbaselineと比較する。
6. typecheck、unit test、development build、production buildを実行する。
7. Dashboard、Projects、主要lazy routeをsmoke testする。
8. runtime error、bundle差異、既存構文との非互換がないか確認する。

Angular 22.1では`isolatedModules: true`により、TypeScriptからJavaScriptへの変換をesbuildへ移せる。ただし、TypeScript emitとesbuild transpilationは完全に同一ではない。速度だけで採用せず、production buildと主要画面のruntime検証を完了条件に含める。

採用条件は次のとおりとする。

- rebuild中央値が明確に改善する。目安は20%以上、または体感待ち時間を継続的に減らせる差がある。
- typecheck、test、development build、production buildが成功する。
- 主要画面で新しいruntime errorが発生しない。
- チームがesbuild transpilation経路の意味とrollback方法を共有できる。

改善が小さい、または安全性を確認できない場合は採用しない。

### Phase 3: 依存cone調査

Phase 1でファイルによるrebuild時間の差、または初回だけ大幅に遅い現象が確認された場合に実施する。

1. 同一ファイルの1回目と2回目のrebuild時間を記録する。
2. 末端Component、feature service、共通service/model、barrel `index.ts`を比較する。
3. 対象ファイルのimport元とre-export経路を`rg`で確認する。
4. 巨大barrelを経由する頻繁な内部importがある場合、feature単位barrelまたは直接importの小規模な比較変更を行う。
5. affected範囲とrebuild時間が改善するか再測定する。

barrel整理はリポジトリ全体へ一括適用せず、計測で影響が確認できた依存境界から段階的に実施する。

### Phase 4: Browser runtime調査

F5とlive reload後の表示時間が同程度の場合に実施する。

1. Chrome Performanceでreloadから操作可能までを記録する。
2. NetworkでAPI requestの本数、直列化、遅いresponseを確認する。
3. main threadのlong task、script evaluation、chart/editor等の初期化を確認する。
4. Angular bootstrap、Router navigation、NgRx Effect、Dashboard描画のどこが支配的か特定する。
5. lazy loading、初期APIの並列化・重複排除、重いwidgetの遅延生成を候補化する。

runtime改善は開発専用hackにせず、productionの初回表示や画面遷移にも有効な改善として別設計・別変更で扱う。

### Phase 5: Source map比較

Phase 2～4で原因が確定しない場合のみ実施する。

1. development設定に限定してsource map無効の比較条件を作る。
2. rebuild時間とブラウザ起動時間を再測定する。
3. 改善量とdebuggability低下を比較する。

source map無効化は最後の候補とし、標準設定として採用する場合も用途別scriptやconfigurationへ分離する。

## 7. 実施しない対策

現時点では次の対策を行わない。

- `--poll`: 変更検知は正常であり、CPUとI/O負荷を増やす可能性がある。
- inotify上限の追加変更: `max_user_watches=524288`へ設定済みである。
- `prebundle: false`: Angular公式ではprebundleはbuild/rebuild改善のため既定で有効である。
- `.angular`の定常削除: current bundleが手動reloadで取得できており、キャッシュ破損を示す証拠がない。
- `preserveSymlinks`変更: Stackup本体ではすでに`false`である。
- `--public-host` / `--disable-host-check`: 現在のAngular CLI 22のserve optionには存在せず、LAN経由WebSocketも接続済みである。

## 8. 記録テンプレート

| Case | 設定 | 試行 | 検知 | Rebuild | Browser起動 | 合計 | 備考 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 末端TS 初回 | baseline | 1 |  |  |  |  |  |
| 末端TS 2回目 | baseline | 1 |  |  |  |  |  |
| HTML | baseline | 1 |  |  |  |  | HMR / full reload |
| SCSS | baseline | 1 |  |  |  |  | HMR / full reload |
| F5 | baseline | 1 | - | - |  |  |  |
| 末端TS 初回 | isolatedModules | 1 |  |  |  |  |  |
| 末端TS 2回目 | isolatedModules | 1 |  |  |  |  |  |

測定単位は秒とし、各Caseの全試行値、中央値、最小値、最大値を残す。結論だけでなくraw dataを保存する。

## 9. 完了条件

次のすべてを満たしたとき、本検証を完了とする。

- 遅延の支配区間が変更検知、rebuild、通知、runtimeのいずれかに分類されている。
- baselineと改善候補を同条件で複数回測定している。
- `isolatedModules`の採否を速度と正しさの両面で判断している。
- 初回依存coneと共通import graphの影響を確認している。
- 採用する設定にtypecheck、test、production build、主要画面の確認結果がある。
- 改善しなかった設定を残していない。
- 開発者向け起動コマンドと期待動作を`AGENTS.local.md`または開発資料へ反映するための結論が出ている。

## 10. 参考資料

- [Angular application build system / HMR](https://angular.dev/tools/cli/build-system-migration#hot-module-replacement)
- [Angular CLI compiler plugin](https://github.com/angular/angular-cli/blob/main/packages/angular/build/src/tools/esbuild/angular/compiler-plugin.ts)
- [Angular CLI Issue #33774: Angular 22.1のtranspilation経路変更](https://github.com/angular/angular-cli/issues/33774)
- [Angular CLI Issue #33619: 初回編集時のdependent cone](https://github.com/angular/angular-cli/issues/33619)
- [Angular CLI Issue #24755: HMR改善議論](https://github.com/angular/angular-cli/issues/24755)
- [Angular CLI Issue #25935: incremental rebuild性能計測](https://github.com/angular/angular-cli/issues/25935)

## 11. 実施結果（2026-09-10）

### 11.1 Angular build計測

`project-card.component.ts`へ意味を変えないコメントを追加・変更・除去し、同一条件で比較した。計測用コメントはすべて除去済みである。

| Case | baseline | `isolatedModules: true` | 改善率 |
| --- | ---: | ---: | ---: |
| 初期development build | 14.100秒 | 11.138秒 | 21.0% |
| 同一TSの初回変更 | 8.994秒 | 7.444秒 | 17.2% |
| 同一TSの2回目 | 1.296秒 | 1.189秒 | 8.3% |
| コメント除去 | 0.904秒 | 0.901秒 | 0.3% |

次を確認した。

- 変更検知は即時であり、WSL2のwatch、inotify、pollingは主因ではない。
- 初回TS変更だけが約7～9秒、同一ファイルのwarm rebuildは約1秒である。
- Angular CLI Issue #33619で報告されている初回dependent cone型の傾向と一致する。
- `isolatedModules`は初期buildと初回変更を改善するが、warm rebuildへの効果は小さい。
- ブラウザのF5時間とreload後の操作可能時間は、実ブラウザで別途計測する必要がある。

### 11.2 採用内容

`isolatedModules: true`は本番buildへ波及させず、`tsconfig.dev.json`とAngularの`development` configurationに限定して採用した。これにより、開発時はesbuild transpilationの高速経路を利用しつつ、productionは従来の`tsconfig.app.json`を使用する。

LAN公開とlive reloadを同時に有効化する起動コマンドを次に統一した。

```bash
pnpm web:hmr
```

内部では次を実行する。

```bash
ng serve --host 0.0.0.0 --port 4200 --live-reload true
```

通常の`pnpm web:start`は従来どおり`liveReload: false`であり、用途に応じて明示的に使い分ける。

### 11.3 検証結果

| 検証 | 結果 |
| --- | --- |
| `tsc -p tsconfig.app.json --noEmit` | 成功 |
| `tsc -p tsconfig.dev.json --noEmit` | 成功 |
| `pnpm web:hmr` initial build | 成功、10.949秒 |
| 最終構成でのTS初回変更 | 成功、7.472秒、page reload通知済み |
| 最終構成での同一TS warm変更 | 成功、1.223秒、page reload通知済み |
| production build | 成功 |
| unit test | 50 files、109 tests成功 |
| widget test | 1 file、3 tests成功 |

production buildには既存のdirect eval、side-effects、SCSS budget警告があるが、失敗および今回変更による新規errorはなかった。unit testにも既存のstderr警告があるが、すべて成功した。

### 11.4 残課題

初回TS変更の約7.4秒は残っている。次の優先調査は、末端Component・共通Service・barrel `index.ts`の初回変更時間を比較し、依存coneの広がりを特定することである。

また、実ブラウザで次を比較し、残りの体感待ち時間がAngular rebuildとClearML runtime初期化のどちらに支配されるか確定する。

1. F5からDashboard操作可能まで
2. TS保存からDashboard操作可能まで
3. HTML変更時に`Component update sent to client(s).`となるか
