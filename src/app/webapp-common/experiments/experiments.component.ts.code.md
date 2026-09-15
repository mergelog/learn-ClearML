# experiments.component.ts 解説

対象: [experiments.component.ts](src/app/webapp-common/experiments/experiments.component.ts)

````ts
import {
  ChangeDetectionStrategy,                                  // OnPush を指定するための列挙。Angular22ではデフォルトなので本来は省略可
  Component,
  computed,                                                  // 他のsignalから派生値を作る
  effect,                                                    // signalの変化に反応して副作用（dispatch等）を走らせる
  OnDestroy,
  signal,                                                    // 書き換え可能な状態。ここでは「ハイライト行」の保持に使う
  viewChild                                                  // テンプレート内の子コンポーネントのインスタンスをsignalとして取得
} from '@angular/core';
import {
  selectActiveParentsFilter,                                 // 以下は experiments feature の NgRx セレクタ群。全てstoreの読み取り口
  selectCompareSelectedMetrics,                              // 比較モードで選択中のメトリクス
  selectCustomColumns,                                       // ユーザーが追加したカスタム列
  selectExperimentsList,                                     // 一覧テーブルの行データ本体
  selectExperimentsParents,                                  // 親タスクのフィルタ候補
  selectExperimentsTableColsOrder,                           // 列の並び順（プロジェクト単位で保存される）
  selectExperimentsTags,
  selectExperimentsTypes,
  selectFilteredTableCols,                                   // 表示対象に絞り込まれた列定義
  selectHyperParamsOptions,
  selectHyperParamsVariants,
  selectIsExperimentInEditMode,                              // 編集中か。編集中は自動リフレッシュ等を抑止する用途
  selectMetricVariantForView,
  selectMetricVariants,
  selectNoMoreExperiments,                                   // 無限スクロールの打ち止めフラグ
  selectSelectedExperiments,                                 // チェックボックスで選択された複数行
  selectSelectedExperimentsDisableAvailable,                 // 選択内容に対する各メニュー項目の活性/非活性の集計結果
  selectSelectedTableExperiment,                             // テーブル上で「今見ている」1行
  selectShowAllSelectedIsActive,                             // 「選択済みのみ表示」トグル
  selectShowCompareScalarSettings,
  selectSplitSize,                                           // 左右分割の幅
  selectTableCompareView,
  selectTableFilters,
  selectTableMode,                                           // 'table' | 'info' | 'compare' の表示モード
  selectTableRefreshSessionList,
  selectTableSortFields
} from './reducers';
import {
  selectCompanyTags,                                         // 会社全体のタグ候補
  selectRouterProjectId,                                     // URLから読んだprojectId（ルータstate由来）
  selectSelectedProjectId,                                   // storeが保持する選択中projectId
  selectTagsFilterByProject
} from '../core/reducers/projects.reducer';
import {ColHeaderTypeEnum, ISmCol, TableSortOrderEnum} from '../shared/ui-components/data/table/table.consts';   // 列定義の型と列ヘッダ種別
import {isEqual} from 'lodash-es';                           // 列定義の深い比較に使う（参照比較では毎回変化扱いになるため）
import {selectRouterParams} from '../core/reducers/router-reducer';                                             // :experimentId などのURLパラメータ
import {debounceTime, distinctUntilChanged, filter, map, skip, switchMap, tap} from 'rxjs/operators';
import {combineLatest, Observable} from 'rxjs';
import {selectBackdropActive} from '../core/reducers/view.reducer';                                             // メニュー背面の暗幕
import {initSearch, resetSearch} from '../common-search/common-search.actions';                                 // ヘッダ共通検索ボックスの初期化/解除
import {selectSearchQuery} from '../common-search/common-search.reducer';
import {ITableExperiment} from './shared/common-experiment-model.model';                                         // テーブル1行分のタスクモデル
import * as experimentsActions from './actions/common-experiments-view.actions';                                // 一覧画面用アクションを名前空間で束ねて使う
import {resetAceCaretsPositions, setAutoRefresh} from '../core/actions/layout.actions';                         // コードエディタのカーソル位置リセット / 自動更新
import {
  getProjectUsers,                                           // フィルタ用のユーザー一覧取得
  setArchive as setProjectArchive,                           // アーカイブ表示モードの切替（名前衝突回避のためリネーム）
  setBreadcrumbsOptions,
  setDeep                                                    // サブプロジェクトまで潜って表示する「deep」モード
} from '../core/actions/projects.actions';
import {
  createCompareMetricColumn,                                 // 比較ビュー用のメトリクス列を生成
  createMetricColumn,                                        // 通常テーブル用のメトリクス列を生成
  decodeColumns,                                             // URLクエリ文字列 -> 列定義へ復元
  decodeFilter,                                              // URLクエリ文字列 -> フィルタへ復元
  decodeOrder,                                               // URLクエリ文字列 -> ソート順へ復元
  decodeURIComponentSafe                                     // 不正なエスケープでも例外を投げないdecodeURIComponent
} from '../shared/utils/tableParamEncode';
import {BaseEntityPageComponent} from '../shared/entity-page/base-entity-page';                                 // 一覧画面の共通基底。store/route/router/dialog等をinject済み
import {groupHyperParams} from '../shared/utils/shared-utils';                                                  // hyperparamsをsection単位にグルーピング
import {
  ProjectsGetTaskParentsResponseParents
} from '~/business-logic/model/projects/projectsGetTaskParentsResponseParents';                                  // 自動生成されたAPIモデル（~ はfeature層へのエイリアス）
import {FilterMetadata, SortMeta} from 'primeng/api';         // テーブル実体はPrimeNGなので、その型を借用
import {EntityTypeEnum} from '~/shared/constants/non-common-consts';                                             // experiment / model / dataset など画面種別
import {ShowItemsFooterSelected} from '../shared/entity-page/footer-items/show-items-footer-selected';           // 以下、複数選択時の下部バーの各ボタン定義クラス
import {CompareFooterItem} from '../shared/entity-page/footer-items/compare-footer-item';
import {DividerFooterItem} from '../shared/entity-page/footer-items/divider-footer-item';                        // 見た目の区切り線
import {ArchiveFooterItem} from '../shared/entity-page/footer-items/archive-footer-item';
import {SelectedTagsFooterItem} from '../shared/entity-page/footer-items/selected-tags-footer-item';
import {DeleteFooterItem} from '../shared/entity-page/footer-items/delete-footer-item';
import {ResetFooterItem} from '../shared/entity-page/footer-items/reset-footer-item';
import {PublishFooterItem} from '../shared/entity-page/footer-items/publish-footer-item';
import {MoveToFooterItem} from '../shared/entity-page/footer-items/move-to-footer-item';
import {EnqueueFooterItem} from '../shared/entity-page/footer-items/enqueue-footer-item';
import {AbortFooterItem} from '../shared/entity-page/footer-items/abort-footer-item';
import {addTag} from './actions/common-experiments-menu.actions';                                                 // タグ付与だけはメニュー側のアクションを使う
import {
  CountAvailableAndIsDisableSelectedFiltered,                // 「何件に適用可能か / 無効か」を表す集計型
  MenuItems,                                                 // メニュー項目のID列挙
  selectionDisabledAbort,                                    // 以下は「この選択でこの操作が可能か」を判定する純関数群
  selectionDisabledAbortAllChildren,
  selectionDisabledArchive,
  selectionDisabledDelete,
  selectionDisabledDequeue,
  selectionDisabledEnqueue,
  selectionDisabledMoveTo,
  selectionDisabledPipelineRun,
  selectionDisabledPublishExperiments,
  selectionDisabledQueue,
  selectionDisabledReset,
  selectionDisabledRetry,
  selectionDisabledViewWorker
} from '../shared/entity-page/items.utils';
import {ExperimentsTableComponent} from './dumb/experiments-table/experiments-table.component';                   // 表示専用（dumb）のテーブル
import {DequeueFooterItem} from '../shared/entity-page/footer-items/dequeue-footer-item';
import {HasReadOnlyFooterItem} from '../shared/entity-page/footer-items/has-read-only-footer-item';               // 読み取り専用が混ざっている旨の表示
import {encodeHyperParameter, filterArchivedExperiments} from './shared/common-experiments.utils';
import {AbortAllChildrenFooterItem} from '../shared/entity-page/footer-items/abort-all-footer-item';
import {
  ExperimentMenuExtendedComponent
} from '@features/experiments/containers/experiment-menu-extended/experiment-menu-extended.component';           // 右クリックメニュー本体をラップした拡張コンポーネント
import {INITIAL_EXPERIMENT_TABLE_COLS} from './experiment.consts';                                                // 初期列定義の定数
import {selectIsPipelines} from '@common/experiments-compare/reducers';                                           // このページがパイプライン用途で使われているか
import {isReadOnly} from '@common/shared/utils/is-read-only';                                                      // 例示プロジェクト等の読み取り専用判定
import {rootProjectsPageSize} from '@common/constants';
import {
  SelectionEvent
} from '@common/experiments/dumb/select-metric-for-custom-col/select-metric-for-custom-col.component';            // メトリクス列追加ダイアログからのイベント型
import {
  CreateExperimentDialogComponent
} from '@common/experiments/containers/create-experiment-dialog/create-experiment-dialog.component';
import {RetryFooterItem} from '@common/shared/entity-page/footer-items/retry-footer-item';
import {computedPrevious} from 'ngxtension/computed-previous';                                                     // signalの「1つ前の値」を保持するユーティリティ
import {takeUntilDestroyed, toSignal} from '@angular/core/rxjs-interop';                                           // Observable購読の自動解除 / Observable -> signal 変換
import {setExperiment} from '@common/experiments/actions/common-experiments-info.actions';                         // 詳細パネル側のstateクリアに使う
import {selectMetricsLoading, selectSelectedExperiment} from '@features/experiments/reducers';
import {ProjectsGetUserNamesRequest} from '~/business-logic/model/projects/projectsGetUserNamesRequest';
import {distinctParamsUntilChanged$} from '@common/projects/common-projects.utils';                                // 「前回値つき」で変化だけを流すカスタムオペレータ
import {SplitAreaComponent, SplitComponent} from 'angular-split';                                                  // 左右リサイズ可能な分割レイアウト
import {RouterOutlet} from '@angular/router';                                                                      // 右ペインに詳細/比較の子ルートを描画
import {OverlayComponent} from '@common/shared/ui-components/overlay/overlay/overlay.component';
import {ExperimentHeaderComponent} from '@common/experiments/dumb/experiment-header/experiment-header.component';
import {EntityFooterComponent} from '@common/shared/entity-page/entity-footer/entity-footer.component';
import {PushPipe} from '@ngrx/component';                                                                          // async の代替。ZonelessでもOKな | ngrxPush
import {TooltipDirective} from '@common/shared/ui-components/indicators/tooltip/tooltip.directive';
import {MatButton} from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import {concatLatestFrom} from '@ngrx/operators';                                                                  // withLatestFromの遅延評価版。必要になるまでsourceを購読しない


@Component({
  selector: 'sm-common-experiments',
  templateUrl: './experiments.component.html',                // テンプレートは別ファイル（インライン禁止の方針どおり）
  styleUrls: ['./experiments.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,            // 入力/signalの変化時だけ再描画。Angular22ではデフォルト
  imports: [                                                  // standaloneコンポーネントなのでNgModuleでなくここで依存を宣言
    SplitComponent,
    SplitAreaComponent,
    RouterOutlet,
    ExperimentsTableComponent,
    ExperimentMenuExtendedComponent,
    OverlayComponent,
    ExperimentHeaderComponent,
    EntityFooterComponent,
    MatIconModule,
    PushPipe,
    TooltipDirective,
    MatButton
  ]
})
export class ExperimentsComponent extends BaseEntityPageComponent implements OnDestroy {   // [■観点:継承] 一覧画面の共通処理は基底クラス、タスク固有だけをここに書く
  protected get tableCols() {                                 // getterにしているのは、派生クラス（pipelines等）が別の列定義へ差し替えられるようにするため
    return INITIAL_EXPERIMENT_TABLE_COLS;
  }

  public entityTypeEnum = EntityTypeEnum;                     // テンプレートから列挙を参照するための橋渡し
  public tableSortOrder$: Observable<TableSortOrderEnum>;
  public readOnlySelection: boolean;                          // 選択行に読み取り専用が1つでも含まれるか
  public contextMenuActive: boolean;                          // 右クリックメニューが開いているか
  public singleRowContext: boolean;                           // 右クリックが「1行に対して」か「選択済み全体に対して」か
  public firstExperiment: ITableExperiment;                   // 一覧の先頭行。詳細を自動オープンする際の既定値
  public menuBackdrop: boolean;
  protected setTableModeAction = experimentsActions.setTableMode;   // 基底のabstractを実装。基底からモード変更をdispatchできるようにする
  private sortFields: SortMeta[];                             // 列削除時に該当ソートを解除するため、最新値をここに保持

  protected override splitSize = this.store.selectSignal(selectSplitSize);              // 基底のSignal<number>をタスク用セレクタで上書き
  protected override showAllSelectedIsActive$ = this.store.select(selectShowAllSelectedIsActive);

  protected isPipeline$ = this.store.select(selectIsPipelines);
  protected tableSortFields$ = this.store.select(selectTableSortFields).pipe(tap(field => this.sortFields = field));   // [■観点:tapで副作用] 購読ついでにフィールドへ写している。テンプレートが購読していないと更新されない点に注意
  protected backdropActive$ = this.store.select(selectBackdropActive);
  protected noMoreExperiments$ = this.store.select(selectNoMoreExperiments);
  protected tableFilters$ = this.store.select(selectTableFilters);
  protected selectedExperimentsDisableAvailable$ = this.store.select(selectSelectedExperimentsDisableAvailable);
  protected selectedExperimentsHasUpdate$ = this.store.select(selectTableRefreshSessionList);
  protected checkedExperiments$ = this.store.select(selectSelectedExperiments)
    .pipe(tap((selectedExperiments: ITableExperiment[]) => {
      this.checkedExperiments = selectedExperiments;          // 基底が参照するフィールドへ同期
      this.readOnlySelection = this.checkedExperiments.some(exp => isReadOnly(exp));    // 1つでも読み取り専用なら編集系を止める
    }));
  protected searchQuery$ = this.store.select(selectSearchQuery);
  protected parents$ = this.store.select(selectExperimentsParents).pipe(tap(parents => this.parents = parents));
  protected activeParentsFilter$ = this.store.select(selectActiveParentsFilter);
  protected types$ = this.store.select(selectExperimentsTypes);
  protected tags$ = this.store.select(selectExperimentsTags);
  protected tagsFilterByProject$ = this.store.select(selectTagsFilterByProject);
  protected companyTags$ = this.store.select(selectCompanyTags);
  protected tableColsOrder$ = this.store.select(selectExperimentsTableColsOrder);
  protected metricVariants$ = this.store.select(selectMetricVariants);
  protected metricLoading$ = this.store.select(selectMetricsLoading);
  protected hyperParamsOptions$ = this.store.select(selectHyperParamsOptions);
  protected hyperParams$ = this.store.select(selectHyperParamsVariants).pipe(
    map(hyperParams => groupHyperParams(hyperParams.filter(hp => hp.section !== 'properties' || hp.name !== 'version')))   // properties.version は内部管理用なので候補から除外
  );

  protected experiments$ = combineLatest([                    // combineLatestだが配列要素は1つだけ。過去に複数ソースだった名残
    this.store.select(selectExperimentsList)
  ])
    .pipe(
      filter(([experiments, ]) => experiments !== null),       // 未取得（null）は下流に流さない。空配列[]とは区別する
      // lil hack for hiding archived task after they have been archived from task info or footer...
      map(([experiments, ]) => filterArchivedExperiments(experiments, this.inArchivedMode()))   // 再取得を待たず、アーカイブ済み行をクライアント側で即座に消す
    );

  protected filteredTableCols$ = this.store.select(selectFilteredTableCols);


  protected tableCols$ = this.filteredTableCols$.pipe(
    distinctUntilChanged((a, b) => isEqual(a, b)),             // [■観点:深い比較] 列定義は毎回別オブジェクトで来るため、isEqualで内容比較しないと無駄な再描画が走る
    map(cols => cols.filter(col => !col.hidden))               // 非表示列を落として実際に描く列だけにする
  );
  override tableMode = this.store.selectSignal(selectTableMode);     // 基底ではSignal<...>の宣言のみ。ここで実体を与える
  // .pipe(tap(tableMode => this.tableMode = tableMode));
  protected showCompareScalarSettings$ = this.store.select(selectShowCompareScalarSettings);
  protected compareSelectedMetricsScalars$ = this.store.select(selectCompareSelectedMetrics('scalars'));           // セレクタファクトリ。引数違いで別インスタンスを生成
  protected compareSelectedMetricsPlots$ = this.store.select(selectCompareSelectedMetrics('plots'));
  protected selectedExperiment$ = this.store.select(selectSelectedExperiment);                                      // 右ペインに出している詳細対象
  protected selectedTableExperiment = toSignal(this.store.select(selectSelectedTableExperiment)
    .pipe(distinctUntilChanged((a, b) => a?.id === b?.id)));   // idが同じなら同一視。オブジェクト差し替えだけでは反応させない
  private previousTableExperiment = computedPrevious(this.selectedTableExperiment);                                 // 選択が外れた直後に「直前の行」を復元するため
  protected selectionState = computed(() => ({                 // [■観点:computedの中でsignalを作る] 選択対象が変わるたびにハイライト用signalを作り直している
    prevExperiment: this.previousTableExperiment(),
    highlited: signal(this.selectedTableExperiment() ?? this.previousTableExperiment())    // 現在値が無ければ直前値でハイライトを維持
  }));
  protected highlited = computed(() => this.tableMode() === 'compare' ? null : this.selectionState().highlited());  // 比較モードでは単一行のハイライトを出さない


  table = viewChild(ExperimentsTableComponent);               // CSVダウンロード等で子テーブルのAPIを直接叩くため
  contextMenuExtended = viewChild.required(ExperimentMenuExtendedComponent);                                        // requiredなので未配置ならエラーになる
  public contextMenu = computed(() => this.contextMenuExtended().contextMenu());                                    // 拡張コンポーネントがさらに内包する実メニューまで掘り下げる

  // public tableMode: 'table' | 'info' | 'compare';
  private previousSelectedIds: string;                        // 比較モードの初回だけ選択を復元するためのガード
  public metricsVariants$ = this.store.selectSignal(selectMetricVariantForView);                                    // 命名は$だがsignal。selectSignalなので実体はSignal
  public tableCompareView = this.store.selectSignal(selectTableCompareView);

  protected showColorsInCards = computed(() => {               // 比較モードのときだけカードに系列色を出す
    return this.tableMode() === 'compare';
  });


  override get selectEditMode() {                             // 基底が「編集中か」を知るためのセレクタを、タスク用に差し替える
    return selectIsExperimentInEditMode;
  }

  protected override get entityType() {                       // 基底の共通処理がこの値で分岐する（パイプライン側は別の値を返す）
    return EntityTypeEnum.experiment;
  }

  constructor() {
    super();
    this.setSplitSizeAction = experimentsActions.setSplitSize;       // 基底のリサイズ処理が使うアクションを注入
    this.addTag = addTag;                                            // 同じく、基底のタグ付与が使うアクション
    this.syncAppSearch();                                            // ヘッダの共通検索ボックスと一覧を結線

    this.store.dispatch(getProjectUsers({                            // 「User」列のフィルタ候補を取得
      projectId: this.selectedProjectId,
      entity: ProjectsGetUserNamesRequest.EntityEnum.Task
    }));
    this.store.dispatch(experimentsActions.setTableCols({cols: this.tableCols}));    // 初期列定義をstoreへ投入。以降の列操作は全てstore基準

    // effect(() => {
    //   this.shouldOpenDetails = this.tableMode() !== 'table';
    // });

    this.store.select(selectRouterParams)
      .pipe(
        takeUntilDestroyed(),                                        // [■観点:自動unsubscribe] constructor内（injection context）なのでDestroyRef省略で書ける
        map(params => this.getParamId(params)))
      .subscribe(() =>
        this.store.dispatch(resetAceCaretsPositions()));             // 別タスクへ移ったらコードエディタのカーソル位置を初期化

    distinctParamsUntilChanged$(combineLatest([                      // [■観点:URL is the source of truth] URLクエリを正としてstoreを再構築する中核
      this.store.select(selectRouterProjectId),
      this.route.queryParams,
      this.store.select(selectCustomColumns)
    ]))
      .subscribe(([prevProjectId, projectId, params]) => {           // 第1要素が「前回のprojectId」。オペレータが前回値を先頭に付けて流す
        if (projectId !== prevProjectId && Object.keys(params || {}).length === 0) {
          this.emptyUrlInit();                                       // プロジェクト切替かつクエリ無し = 素の遷移。既定状態をURLへ書き戻す
        } else {
          if ((projectId === prevProjectId || prevProjectId === null) && this.entityType === this.entityTypeEnum.experiment) {
            this.setupHeaderTabs('tasks', params.archive === 'true');         // 同一プロジェクト内の遷移か初回のみヘッダタブを構築
          }
          if (params.columns) {
            const [cols, metrics, hyperParams, , allIds] = decodeColumns(params.columns, this.tableCols);   // 4番目は未使用なので空スロットで飛ばしている
            this.store.dispatch(experimentsActions.setVisibleColumnsForProject({
              visibleColumns: cols,
              projectId: this.projectId()
            }));
            this.store.dispatch(experimentsActions.setExtraColumns({                    // 標準列以外（メトリクス列・ハイパラ列）を復元
              projectId: this.selectedProjectId,
              columns: metrics.map(metricCol => createMetricColumn(metricCol, projectId))
                .concat(hyperParams.map(param => this.createParamColumn(decodeURIComponentSafe(param), projectId)))
            }));
            this.columnsReordered(allIds, false);                    // falseでURL再書き込みを抑止。URL由来の復元なので書き戻すと無限ループになる
          }
          if (params.order) {
            const orders = decodeOrder(params.order);
            this.store.dispatch(experimentsActions.setTableSort({orders, projectId}));
          }
          if (params.filter != null) {                               // != null は undefined も拾う。空文字''は有効な値として扱いたいので !params.filter にはしない
            const filters = decodeFilter(params.filter);
            this.store.dispatch(experimentsActions.setTableFilters({filters, projectId: this.selectedProjectId}));
          } else {
            if (params.order) {
              this.store.dispatch(experimentsActions.setTableFilters({filters: [], projectId}));   // ソート指定だけのURLなら、残っているフィルタは消す
            }
          }
          if (params.deep) {
            this.store.dispatch(setDeep({deep: true}));              // サブプロジェクトまで含めて一覧する
          }
          this.store.dispatch(setProjectArchive({archive: params.archive === 'true'}));
          this.store.dispatch(experimentsActions.getExperiments());  // 上でstoreを整えてから一覧取得。Effects側が最新のstoreを読んでリクエストを組む
        }
      });

    this.createFooterItemsRunner();


    this.selectExperimentFromUrl();                                  // URLの:experimentIdと一覧データの突き合わせを開始
    this.store.dispatch(experimentsActions.getParents({searchValue: null}));
    effect(() => {                                                   // [■観点:effect] projectIdが変わるたびにタグ/タイプの候補を取り直す
      if (this.projectId()) {
        this.store.dispatch(experimentsActions.getTags({}));
        this.store.dispatch(experimentsActions.getProjectTypes({}));
      }
    });
  }

  createFooterItemsRunner = () => this.createFooterItems({            // アロー関数フィールドなのでthisが束縛済み。setTimeout等から呼んでも安全
    entitiesType: this.entityType,
    showAllSelectedIsActive$: this.showAllSelectedIsActive$,
    selected$: this.checkedExperiments$,
    tags$: this.tags$,
    data$: this.selectedExperimentsDisableAvailable$,
    companyTags$: this.companyTags$,
    projectTags$: this.store.select(selectSelectedProjectId).pipe(switchMap(id =>
      id === '*' ? this.companyTags$ : this.tags$                    // 「全プロジェクト」表示では会社タグ、通常はプロジェクトタグを候補にする
    )),
    tagsFilterByProject$: this.tagsFilterByProject$
  });

  protected emptyUrlInit() {
    this.store.dispatch(experimentsActions.updateUrlParams());        // 現在のstore状態をURLへ反映（リロード・共有可能にする）
    this.shouldOpenDetails = true;                                    // 素の遷移なので先頭行の詳細を開いてよい、というフラグ
  }

  getSelectedEntities() {                                             // 基底のabstract実装。共通フッタ処理が対象行を取るための口
    return this.checkedExperiments;
  }

  override createFooterItems(config: {
    entitiesType: EntityTypeEnum;
    selected$: Observable<ITableExperiment[]>;
    showAllSelectedIsActive$: Observable<boolean>;
    tags$: Observable<string[]>;
    data$?: Observable<Record<string, CountAvailableAndIsDisableSelectedFiltered>>;
    companyTags$: Observable<string[]>;
    projectTags$: Observable<string[]>;
    tagsFilterByProject$: Observable<boolean>;
  }) {
    super.createFooterItems(config);                                  // 先に基底でfooterState$等の共通配線を作る
    this.footerItems = [                                              // その上でタスク画面固有のボタン並びを定義（順序＝表示順）
      new ShowItemsFooterSelected(config.entitiesType),
      new CompareFooterItem(config.entitiesType),
      new DividerFooterItem(),
      new ArchiveFooterItem(config.entitiesType),
      new DeleteFooterItem(),
      new DividerFooterItem(),
      new EnqueueFooterItem(),
      new RetryFooterItem(),
      new DequeueFooterItem(),
      new ResetFooterItem(config.entitiesType),
      new AbortFooterItem(config.entitiesType),
      new AbortAllChildrenFooterItem(),
      new PublishFooterItem(this.entityType),
      new DividerFooterItem(),

      new SelectedTagsFooterItem(this.entityType),
      new DividerFooterItem(),

      new MoveToFooterItem(),
      new HasReadOnlyFooterItem()
    ];
  }

  onFooterHandler({emitValue, item}) {                                // フッタボタン押下の一括ハンドラ。基底のabstract実装
    this.singleRowContext = false;                                    // フッタ経由＝選択済み全体が対象
    window.setTimeout(() => {                                         // [■観点:setTimeout] 上のフラグ更新をメニュー側が読み終えてから実行させるためのマクロタスク送り
      switch (item.id) {
        case MenuItems.showAllItems:
          this.showAllSelected(!emitValue);                           // トグルなので現在値を反転
          break;
        case MenuItems.compare:
          this.compareExperiments();
          break;
        case MenuItems.archive:
          this.contextMenu().restoreArchive(item.entitiesType);       // 実処理は右クリックメニューのコンポーネントに集約し、フッタからも呼び出す
          break;
        case MenuItems.reset:
          this.contextMenu().resetPopup();
          break;
        case MenuItems.publish:
          this.contextMenu().publishPopup();
          break;
        case MenuItems.retry:
          this.contextMenu().retryPopup();
          break;
        case MenuItems.enqueue:
          this.contextMenu().enqueuePopup();
          break;
        case MenuItems.dequeue:
          this.contextMenu().dequeuePopup();
          break;
        case MenuItems.delete:
          this.contextMenu().deleteExperimentPopup();
          break;
        case MenuItems.abort:
          this.contextMenu().stopPopup();
          break;
        case MenuItems.abortAllChildren:
          this.contextMenu().stopAllChildrenPopup();
          break;
        case MenuItems.moveTo:
          this.contextMenu().moveToProjectPopup();
          break;
      }
    });
  }

  onAddTag(tag: string, contextExperiment: ITableExperiment) {
    this.store.dispatch(addTag({
      tag,
      experiments: this.singleRowContext ? [contextExperiment] : this.checkedExperiments.filter(_selected => !isReadOnly(_selected))   // 1行操作なら対象1件、一括なら読み取り専用を除外
    }));
    this.store.dispatch(experimentsActions.addProjectsTag({tag}));    // タグ候補リストにも新タグを追加しておく
  }

  setContextMenuStatus(menuStatus: boolean) {
    this.contextMenuActive = menuStatus;
  }

  override ngOnDestroy(): void {
    super.ngOnDestroy();
    this.store.dispatch(experimentsActions.resetExperiments({}));     // [■観点:後始末] 一覧stateを破棄。残すと別プロジェクトへ遷移した際に前の行が一瞬見える
    this.store.dispatch(setExperiment({experiment: null}));           // 詳細パネル側のstateもクリア
    this.stopSyncSearch();
  }

  stopSyncSearch() {
    this.store.dispatch(resetSearch());                               // ヘッダ検索ボックスを共通状態へ戻す
    this.store.dispatch(experimentsActions.resetGlobalFilter());
  }

  syncAppSearch() {
    this.store.dispatch(initSearch({payload: 'Search for tasks'}));   // プレースホルダを指定してヘッダ検索を有効化

    this.searchQuery$
      .pipe(
        takeUntilDestroyed(),
        skip(1),                                                      // 購読直後に流れる現在値を捨てる。初期化時に余計な検索を走らせない
        filter(query => query !== null)
      )
      .subscribe(query => this.store.dispatch(experimentsActions.globalFilterChanged(query)));
  }

  selectExperimentFromUrl() {                                         // [■観点:URLと一覧の突き合わせ] URLのidと、取得済み一覧の両方が揃ってはじめて選択を確定できる
    combineLatest([
      this.store.select(selectRouterParams).pipe(map(params => this.getParamId(params))),
      this.experiments$
    ])
      .pipe(
        takeUntilDestroyed(),
        debounceTime(0),                                              // 同一タスク内で両者が連続発火するのを1回にまとめる
        concatLatestFrom(() => this.store.select(selectTableMode)),    // 現在モードを「必要になった時に」取りに行く
        map(([[experimentId, experiments], mode]) => {
          this.firstExperiment = experiments?.[0];
          this.entities = experiments;                                // 基底が参照する一覧実体へ同期
          const experimentsIds = (this.route.snapshot.firstChild?.firstChild ?? this.route.snapshot.firstChild)?.params?.ids?.split(',').filter(id => !!id);   // 比較ルートの ids=a,b,c を取り出す。ネストが1段深い場合に備えて??で降りる
          if (this.getTableModeFromURL() === 'compare' && experimentsIds?.length > 0 && this.checkedExperiments?.length === 0 && !this.previousSelectedIds) {
            this.store.dispatch(experimentsActions.getSelectedExperiments({ids: experimentsIds}));   // 比較URLを直接開いた初回だけ、URLのidsから選択を復元
          }
          this.previousSelectedIds = experimentsIds;                  // 2回目以降は上の条件が偽になるようマーク
          if (!experimentId && this.shouldOpenDetails && this.firstExperiment && mode === 'info') {
            this.shouldOpenDetails = false;
            this.store.dispatch(experimentsActions.experimentSelectionChanged({           // infoモードなのにid未指定なら先頭行を開く
              experiment: this.firstExperiment,
              project: this.selectedProjectId
            }));
          } else if (mode !== 'compare' || ![EntityTypeEnum.experiment, EntityTypeEnum.controller].includes(this.entityType)) {
            this.store.dispatch(experimentsActions.setTableMode({mode: this.getTableModeFromURL()}));   // 比較を持たない画面種別はURL通りのモードにするだけ
          } else if (this.shouldOpenDetails) {
            this.modeChanged(mode);                                   // 比較モードで初回表示なら、比較ビューの準備込みで切り替える
            this.shouldOpenDetails = false;
          } else if (this.getTableModeFromURL() !== mode) {
            this.modeChanged(this.getTableModeFromURL());             // URLとstoreがずれていたらURLに合わせる
          }
          this.shouldOpenDetails = false;                             // どの分岐を通っても最終的にフラグは落とす
          return experiments.find(experiment => experiment.id === experimentId);
        }),
        distinctUntilChanged()                                        // 同じ行オブジェクトなら下流のdispatchを省く
      )
      .subscribe((selectedExperiment) => {
          // this.tableMode = this.getTableModeFromURL();
          this.store.dispatch(experimentsActions.setTableMode({mode: this.tableMode()}));
          this.store.dispatch(experimentsActions.setSelectedExperiment({experiment: selectedExperiment}));
        }
      );
  }

  public getTableModeFromURL() {                                      // [■観点:ルート形状からモードを判定] 子ルートの有無とpathで 'table'/'info'/'compare' を決める
    if (!this.route.snapshot.firstChild) {
      return 'table';                                                 // 子ルート無し = 一覧のみ
    }
    return this.route.snapshot.firstChild?.url[0].path === 'compare' ? 'compare' :
      this.route.snapshot.firstChild?.routeConfig.path === undefined ? 'table' : 'info';   // path未定義（空パスの通過ルート）はtable扱い
  }

  getNextExperiments() {                                              // 無限スクロールの続き読み
    this.store.dispatch(experimentsActions.getNextExperiments());
  }

  experimentsSelectionChanged(experiments: ITableExperiment[]) {      // チェックボックスによる複数選択の変更
    this.store.dispatch(experimentsActions.setSelectedExperiments({experiments}));
    if (this.getTableModeFromURL() === 'compare') {
      this.router.navigate(['compare'], {relativeTo: this.route, queryParamsHandling: 'preserve'});   // 比較中は選択変更のたびに比較ルートを引き直す。preserveでフィルタ等のクエリは維持
    }
  }

  experimentSelectionChanged({experiment, openInfo, origin}: {        // 単一行のクリック。originでテーブル全体由来か行由来かを区別
    experiment: ITableExperiment;
    openInfo?: boolean;
    origin: 'table' | 'row'
  }) {
    if (experiment) {
      if (this.minimizedView() || openInfo) {
        this.store.dispatch(experimentsActions.experimentSelectionChanged({              // 詳細ペインが出ている状態なら中身を差し替える
          experiment: experiment,
          project: this.selectedProjectId
        }));
      } else if (origin === 'row') {
        this.selectionState().highlited.update(current => current?.id === experiment.id ? null : experiment);   // 同じ行の再クリックでハイライト解除（トグル）
      }
    }
  }

  sortedChanged(event: { isShift: boolean; colId: ISmCol['id'] }) {   // isShiftで複数列ソートかを判断するのはreducer側
    this.store.dispatch(experimentsActions.tableSortChanged(event));
  }

  filterChanged({col, value, andFilter}: { col: ISmCol; value: any; andFilter?: boolean }) {
    this.store.dispatch(experimentsActions.tableFilterChanged({
      filters: [{
        col: col.id,
        value,
        filterMatchMode: col.filterMatchMode || andFilter ? 'AND' : undefined   // ||の優先順位により (col.filterMatchMode || andFilter) が条件。列指定があればAND固定になる挙動
      }], projectId: this.projectId()
    }));
  }

  compareExperiments() {
    this.router.navigate(
      [
        `compare-tasks`,
        {ids: this.checkedExperiments.map(experiment => experiment.id).join(',')}        // matrix parameter形式でidsを渡す
      ],
      {relativeTo: this.route.parent.parent});                        // 比較画面は一覧の2階層上にあるので親の親を基準にする
  }

  afterArchiveChanged() {                                             // 基底のabstract実装。アーカイブ操作後の後処理
    this.store.dispatch(experimentsActions.showOnlySelected({active: false, projectId: this.projectId()}));   // 対象が一覧から消えるので「選択のみ表示」を解除しておく
  }

  showAllSelected(active: boolean) {
    this.store.dispatch(experimentsActions.showOnlySelected({active, projectId: this.projectId()}));
  }

  selectedTableColsChanged(col: ISmCol) {                             // 列の表示/非表示トグル
    this.store.dispatch(experimentsActions.toggleColHidden({columnId: col.id, projectId: this.projectId()}));
  }

  toggleSelectedMetricHidden(col: ISmCol) {                           // 比較ビュー側のメトリクス表示トグル
    this.store.dispatch(experimentsActions.toggleSelectedMetricCompare({
      columnId: col.id,
      projectId: this.projectId()
    }));
  }

  getMetricsToDisplay() {
    if (this.getTableModeFromURL() !== 'compare') {                   // 比較モードでは別経路で取得するので二重取得を避ける
      this.store.dispatch(experimentsActions.getCustomMetrics({hideLoader: true}));   // hideLoaderでスピナーを出さずに裏で取得
      this.store.dispatch(experimentsActions.getCustomHyperParams());
    }
  }

  selectedMetricToShow(event: SelectionEvent) {                       // メトリクス列の追加/削除
    if (!event.valueType) {
      return;                                                         // min/max/last など集計種別が未選択なら何もしない
    }
    const variantCol = createMetricColumn({                           // hash群から一意な列idを組み立てる
      metricHash: event.variant.metric_hash,
      variantHash: event.variant.variant_hash,
      valueType: event.valueType,
      metric: event.variant.metric,
      variant: event.variant.variant
    }, this.projectId());
    if (event.addCol) {
      this.store.dispatch(experimentsActions.addColumn({col: variantCol}));
    } else {
      this.store.dispatch(experimentsActions.removeCol({id: variantCol.id, projectId: variantCol.projectId}));
    }
    this.store.dispatch(experimentsActions.updateUrlParams());        // 列構成が変わったのでURLへ反映し、共有・リロード可能にする
  }

  compareSelectedMetricToShow(event: SelectionEvent) {                // 比較ビュー側は列ではなく「選択メトリクス」として保持する
    const variantCol = createCompareMetricColumn(event.variant);
    if (event.addCol) {
      this.store.dispatch(experimentsActions.addSelectedMetric({col: variantCol, projectId: this.projectId()}));
    } else {
      this.store.dispatch(experimentsActions.removeSelectedMetric({id: variantCol.id, projectId: this.projectId()}));
    }
  }

  createParamColumn(param: string, projectId?: string): ISmCol {      // ハイパーパラメータ列の定義を動的生成
    return {
      id: param,                                                      // 'hyperparams.General.lr' のようなフルパスがそのままid
      getter: encodeHyperParameter(param),                            // 行データから値を取り出すためのパス（エスケープ済み）
      headerType: ColHeaderTypeEnum.sortFilter,                       // ソートとフィルタ両方のUIを出すヘッダ
      sortable: true,
      filterable: true,
      header: decodeURIComponentSafe(param.replace('hyperparams.', '')),   // 表示名からは接頭辞を落とす
      hidden: false,
      projectId: projectId || this.projectId(),
      isParam: true,                                                  // 標準列と区別するフラグ。URLエンコード時の扱いが変わる
      style: {width: '200px'},
      searchableFilter: true,
      asyncFilter: true,                                              // 候補値はサーバから都度取得する
      paginatedFilterPageSize: rootProjectsPageSize
    };
  }

  selectedHyperParamToShow(event: { param: string; addCol: boolean }) {
    const variantCol = this.createParamColumn(event.param);
    if (event.addCol) {
      this.store.dispatch(experimentsActions.addColumn({col: variantCol}));
    } else {
      this.store.dispatch(experimentsActions.removeCol({id: variantCol.id, projectId: variantCol.projectId}));
    }
    this.store.dispatch(experimentsActions.updateUrlParams());
  }

  removeColFromList(colId: string) {
    const sortIndex = this.sortFields.findIndex(field => field.field === colId);
    if (sortIndex > -1) {
      this.store.dispatch(experimentsActions.resetSortOrder({sortIndex, projectId: this.projectId()}));   // [■観点:整合性] 消す列でソートしていたら、そのソート条件も外す
    }
    this.store.dispatch(experimentsActions.removeCol({id: colId, projectId: this.projectId()}));
    this.store.dispatch(experimentsActions.updateUrlParams());
  }

  compareRemoveColFromList(colId: string) {
    this.store.dispatch(experimentsActions.removeSelectedMetric({id: colId, projectId: this.projectId()}));
  }

  columnResized(event: { columnId: string; widthPx: number }) {       // 列幅もプロジェクト単位で永続化する
    this.store.dispatch(experimentsActions.setColumnWidth({
      ...event,
      projectId: this.projectId()
    }));
  }

  refreshList(isAutoRefresh: boolean) {                               // 基底のabstract実装
    this.store.dispatch(experimentsActions.refreshExperiments({
      hideLoader: isAutoRefresh,                                      // 自動更新ではスピナーを出さず画面のちらつきを避ける
      autoRefresh: isAutoRefresh
    }));
  }

  setAutoRefresh($event: boolean) {
    this.store.dispatch(setAutoRefresh({autoRefresh: $event}));
  }

  clearSelection() {
    this.store.dispatch(experimentsActions.clearHyperParamsCols({projectId: this.projectId()}));   // 追加したハイパラ列を一括で消す
  }

  columnsReordered(cols: string[], updateUrl = true) {
    this.store.dispatch(experimentsActions.setColsOrderForProject({
      cols: Array.from(new Set([...cols, 'project.name'])),           // Setで重複除去しつつ、project.name列は必ず含める
      projectId: this.projectId()
    }));
    if (updateUrl) {
      this.store.dispatch(experimentsActions.updateUrlParams());      // URL復元経路からはfalseで呼ばれ、ここを通らない
    }
  }

  refreshTagsList() {
    this.store.dispatch(experimentsActions.getTags({}));
  }

  refreshTypesList() {
    this.store.dispatch(experimentsActions.getProjectTypes({}));
  }

  protected getParamId(params) {                                      // 基底のabstract実装。この画面のURLパラメータ名を教える
    return params?.experimentId;
  }

  clearTableFiltersHandler(tableFilters: Record<string, FilterMetadata>, others?: Record<string, string>) {
    const filters = Object.keys(tableFilters).map(col => ({col, value: []}));   // 全列を「値なし」に潰したリストを作る
    this.store.dispatch(experimentsActions.setTableFilters({filters: [], projectId: this.selectedProjectId}));   // store上のフィルタを空に
    this.store.dispatch(experimentsActions.tableFilterChanged({filters, projectId: this.selectedProjectId,       // 併せてURL/再取得も走らせる
      others: others || {}
    }));
  }

  clearTableFiltersAndSearchHandler(tableFilters: Record<string, FilterMetadata>) {
    this.clearTableFiltersHandler(tableFilters, {
      q: null,                                                        // othersでクエリ文字列のqも消す = 検索語もクリア
    });
  }

  onContextMenuOpen({x, y, single, backdrop}: { x: number; y: number; single?: boolean; backdrop?: boolean }) {
    this.singleRowContext = single;                                   // 以降のタグ付与等が「1行だけ」を対象にするかの判断材料
    this.menuBackdrop = !!backdrop;
    this.contextMenu().openMenu({x, y});                              // viewChild経由で子のメソッドを直接呼ぶ
  }

  getSingleSelectedDisableAvailable(experiment): Record<string, CountAvailableAndIsDisableSelectedFiltered> {   // 1行右クリック時の各操作の可否を、選択集計と同じ形にして返す
    return {
      [MenuItems.abort]: selectionDisabledAbort([experiment]),        // 単一でも配列に包むことで、複数選択時と同じ判定関数を使い回せる
      [MenuItems.abortAllChildren]: selectionDisabledAbortAllChildren([experiment]),
      [MenuItems.publish]: selectionDisabledPublishExperiments([experiment]),
      [MenuItems.reset]: selectionDisabledReset([experiment]),
      [MenuItems.delete]: selectionDisabledDelete([experiment]),
      [MenuItems.moveTo]: selectionDisabledMoveTo([experiment]),
      [MenuItems.enqueue]: selectionDisabledEnqueue([experiment]),
      [MenuItems.retry]: selectionDisabledRetry([experiment]),
      [MenuItems.dequeue]: selectionDisabledDequeue([experiment]),
      [MenuItems.queue]: selectionDisabledQueue([experiment]),
      [MenuItems.viewWorker]: selectionDisabledViewWorker([experiment]),
      [MenuItems.archive]: selectionDisabledArchive([experiment]),
      [MenuItems.run]: selectionDisabledPipelineRun([experiment])
    };
  }

  modeChanged(mode: 'info' | 'table' | 'compare') {                   // [■観点:モード遷移の集約] 3モード間の切替に伴う副作用をここ1か所に集める
    if (this.tableMode() !== mode) {
      this.store.dispatch(experimentsActions.setTableMode({mode}));
    }
    setTimeout(() => this.createFooterItemsRunner(), 100);            // レイアウト確定後にフッタを作り直す。100msはアニメーション待ちの経験値
    if (mode === 'info') {
      this.store.dispatch(experimentsActions.experimentSelectionChanged({
        experiment: this.selectionState().highlited() || this.checkedExperiments?.[0] || this.firstExperiment,   // ハイライト→選択1件目→先頭行、の優先順で開く対象を決める
        project: this.selectedProjectId
      }));
      return Promise.resolve();                                       // 他分岐がPromiseを返すので戻り値の型を揃える
    } else if (mode === 'compare') {
      setTimeout(() => {                                              // ルート遷移が反映されたあとのsnapshotを読む必要があるため次タスクへ送る
        const experimentsIds = (this.route.snapshot.firstChild?.firstChild ?? this.route.snapshot.firstChild)?.params?.ids?.split(',').filter(id => !!id);
        this.store.dispatch(experimentsActions.getSelectedExperiments({ids: experimentsIds}));
      })
      return this.compareView();                                      // 基底が持つ比較ビューへの遷移
    } else {
      return this.closePanel();                                       // tableモード = 右ペインを閉じる
    }
  }

  newExperiment() {
    this.dialog.open(CreateExperimentDialogComponent, {
      width: '800px',
      disableClose: true                                              // 背景クリックやESCで閉じさせない
    }).afterClosed()
      .pipe(filter(res => !!res))                                     // キャンセル（undefined）は流さない
      .subscribe(data => this.store.dispatch(experimentsActions.createExperiment({data})));
  }

  downloadTableAsCSV() {
    this.table().table().downloadTableAsCSV(`ClearML ${this.selectedProject().id === '*' ? 'All' : this.selectedProject()?.basename?.substring(0, 60)} Experiments`);   // 画面に読み込み済みの行だけをCSV化。ファイル名が長くなりすぎないよう60文字で切る
  }

  downloadFullTableAsCSV() {
    this.store.dispatch(experimentsActions.prepareTableForDownload({entityType: 'task'}));   // 全件はサーバ側で用意させる
  }

  override setupBreadcrumbsOptions() {
    effect(() => {                                                    // selectedProjectの変化に追従してパンくずを組み直す
      const selectedProject = this.selectedProject();
      if (selectedProject) {
        this.store.dispatch(setBreadcrumbsOptions({
          breadcrumbOptions: {
            showProjects: !!selectedProject,
            featureBreadcrumb: {
              name: 'PROJECTS',
              url: 'projects'
            },
            ...(this.projectDeepMode() && selectedProject?.id !== '*' && {                  // [■観点:条件付きスプレッド] falseをスプレッドしても何も足されない性質を使った分岐
              subFeatureBreadcrumb: {
                name: 'All Tasks'
              }
            }),
            projectsOptions: {
              basePath: 'projects',
              filterBaseNameWith: null,
              compareModule: null,
              showSelectedProject: selectedProject?.id !== '*',                             // '*' は「全プロジェクト」の疑似ID
              ...(selectedProject && {
                selectedProjectBreadcrumb: {
                  name: selectedProject?.id === '*' ? 'All Tasks' : selectedProject?.basename,
                  url: `projects/${selectedProject?.id}/projects`
                }
              })
            }
          }
        }));
      }
    });
  }

  showCompareSettingsChanged() {
    this.store.dispatch(experimentsActions.toggleCompareScalarSettings());
  }

  compareViewChanged(compareView: 'scalars' | 'plots') {
    this.store.dispatch(experimentsActions.setCompareView({mode: compareView}));
    return this.router.navigate(['compare'], {relativeTo: this.route, queryParamsHandling: 'preserve'});
  }

  override filterSearchChanged({colId, value}: { colId: string; value: { value: string; loadMore?: boolean } }) {   // 列フィルタの候補検索。列の種類ごとに取得経路が違うので分岐する
    super.filterSearchChanged({colId, value});                        // 共通列（user/project等）は基底が処理する
    if (colId === 'parent.name') {
      // No pagination in BE - setting same list will set noMoreOptions to true
      if (value.loadMore) {
        this.store.dispatch(experimentsActions.setParents({parents: [...this.parents]}));   // 同じ配列を入れ直すことで「これ以上無い」とUIに伝える回避策
      } else {
        this.store.dispatch(experimentsActions.resetTablesFilterParentsOptions());          // 検索語が変わったので候補を一旦空に
        this.store.dispatch(experimentsActions.getParents({searchValue: value.value}));
      }
    } else if (colId.startsWith('hyperparams.')) {
      if (!value.loadMore) {
        this.store.dispatch(experimentsActions.hyperParamSelectedInfoExperiments({          // 新規検索時のみ、既存の候補・ページ位置をリセット
          col: {id: colId},
          loadMore: false,
          values: null
        }));
        this.store.dispatch(experimentsActions.setHyperParamsFiltersPage({page: 0}));
      }
      this.store.dispatch(experimentsActions.hyperParamSelectedExperiments({
        col: {id: colId, getter: `${colId}.value`},                   // ハイパラは {value, section, ...} 構造なので .value まで指定する
        searchValue: value.value
      }));
    }
  }
}
````

---

## 全体像

このコンポーネントは ClearML の「タスク一覧画面」の**コンテナ（smart）コンポーネント**。役割は3つに絞られる。

1. URL（クエリパラメータ・子ルート）と NgRx store の同期
2. 子コンポーネント（テーブル・ヘッダ・フッタ・コンテキストメニュー）から上がってきたイベントを**アクションに変換して dispatch する**
3. 3つの表示モード（`table` / `info` / `compare`）の切り替え制御

ビジネスロジックそのものは持たない。実際の API 呼び出しは Effects、状態計算は reducer/selector 側にある。

## 観点1: 継承による共通化

`BaseEntityPageComponent` を継承している。タスク・モデル・データセットなど**一覧画面が複数ある**ため、共通部分を基底に寄せている。

| 基底が持つもの | このクラスがすること |
| --- | --- |
| `store` / `route` / `router` / `dialog` の `inject` | そのまま使う |
| `abstract getParamId(params)` | `params.experimentId` を返す |
| `abstract onFooterHandler()` | タスク固有のメニュー処理に振り分け |
| `abstract refreshList()` | タスク一覧の再取得を dispatch |
| `protected get entityType()` | `EntityTypeEnum.experiment` を返す |
| `setSplitSizeAction` / `addTag` フィールド | コンストラクタでタスク用アクションを代入 |

`get tableCols()` や `get entityType()` が**プロパティでなく getter** なのは、派生クラス（パイプライン画面など）が `override` で差し替えるため。プロパティ初期化だと基底のコンストラクタ実行時にまだ値が入っていない、という順序問題も避けられる。

## 観点2: Observable と Signal の混在

このファイルは Angular の移行期の書き方がそのまま残っており、**同じ store から 2 通りの読み方**をしている。

```ts
protected tableFilters$ = this.store.select(selectTableFilters);     // Observable。テンプレートで | ngrxPush
override  tableMode     = this.store.selectSignal(selectTableMode);  // Signal。this.tableMode() で同期的に読める
```

使い分けの実態はこうなっている。

- **`select`（Observable）** … テンプレートへ流すだけのもの。`PushPipe` で購読
- **`selectSignal`（Signal）** … `getTableModeFromURL()` との比較など、**TypeScript コード中から同期的に現在値が欲しい**もの

新規に書くなら `selectSignal` に寄せるのがベストプラクティス。`tableSortFields$` のように `tap` で副作用的にフィールドへ写している箇所は、**テンプレートがその Observable を購読していないと `this.sortFields` が永久に `undefined` のまま**という危うさがある。Signal ならこの依存が消える。

## 観点3: URL を正とする状態復元

この画面の一番の肝。`constructor` 内の `distinctParamsUntilChanged$(combineLatest([...]))` がそれ。

```
URL クエリ (?columns=...&order=...&filter=...&archive=true)
        ↓ decodeColumns / decodeOrder / decodeFilter
      store へ dispatch（列・ソート・フィルタ・アーカイブ）
        ↓
   getExperiments() … 整えた store を Effects が読んでリクエストを組む
```

逆方向は `updateUrlParams()` で、ユーザー操作（列追加・並べ替え等）のたびに store の状態を URL へ書き戻す。これにより**リロードしても URL 共有しても同じ画面が再現される**。

無限ループを避ける仕掛けが `columnsReordered(allIds, false)` の第2引数。URL 由来の復元時は `updateUrl = false` で書き戻しを止めている。

## 観点4: viewChild で子を直接叩く

```ts
contextMenuExtended = viewChild.required(ExperimentMenuExtendedComponent);
public contextMenu  = computed(() => this.contextMenuExtended().contextMenu());
```

簡単にいうと、**子コンポーネントのインスタンスを掴んでメソッドを直接呼ぶ**ための仕組み。ポップアップを開く・閉じるといった「状態というより命令」は store を経由させると逆に複雑になるため、この形になっている。

`viewChild.required` は未配置ならエラーになる版。`computed` で 1 段掘っているのは、ラッパーコンポーネントの中にさらに実メニューがあるため。

イベント処理（`onFooterHandler`）でフッタボタンもコンテキストメニューも**同じ `this.contextMenu()` のメソッドを呼んでいる**のがポイント。処理の実体を 1 か所に集約し、呼び出し口だけ 2 つ用意している形。

## 観点5: signal を computed の中で作る

```ts
protected selectionState = computed(() => ({
  prevExperiment: this.previousTableExperiment(),
  highlited: signal(this.selectedTableExperiment() ?? this.previousTableExperiment())
}));
```

`computed` の中で `signal()` を新規生成している、やや変則的な書き方。意図は「**選択対象が変わったらハイライト状態をリセットしたいが、ハイライト自体はユーザー操作で書き換えたい**」という要求で、

- store 由来の選択が変わる → `computed` が再評価され、新しい `signal` ができる（＝リセット）
- 行クリック → `this.selectionState().highlited.update(...)` で書き換え（＝トグル操作）

を両立させている。ただし可読性は低く、一般には `linkedSignal`（Angular 19+）で書くほうが意図が明確になる。

## 観点6: setTimeout の使われ方

3 か所で使われており、それぞれ理由が違う。

| 箇所 | 理由 |
| --- | --- |
| `onFooterHandler` の `window.setTimeout` | 直前の `this.singleRowContext = false` をメニュー側が読み終えてから処理させる |
| `modeChanged` の `setTimeout(..., 100)` | 分割レイアウトのアニメーション完了後にフッタを組み直す |
| `modeChanged` の compare 分岐 | ルート遷移が `route.snapshot` に反映されてから ids を読む |

いずれも**タイミング依存の回避策**であり、設計としてはきれいではない。特に 100ms のマジックナンバーは、アニメーション時間が変わると壊れる。

## 観点7: 演算子の選択

```ts
filter(([experiments, ]) => experiments !== null)
```
`null`（未取得）と `[]`（0件）を区別している。`!experiments` にすると 0 件時に「読み込み中」表示のままになる。

```ts
distinctUntilChanged((a, b) => isEqual(a, b))
```
列定義は selector が毎回新しい配列を返すため、参照比較では常に「変化あり」になる。`lodash` の深い比較で無駄な再描画を止めている。

```ts
concatLatestFrom(() => this.store.select(selectTableMode))
```
`withLatestFrom` と違い、**source が発火するまで引数の Observable を購読しない**。不要な購読を避けるための NgRx 製オペレータ。

```ts
skip(1)
```
`syncAppSearch` で、購読直後に流れてくる「現在値」を捨てる。これが無いと画面表示と同時に検索アクションが 1 回無駄に走る。

## 観点8: 条件付きスプレッド

```ts
...(this.projectDeepMode() && selectedProject?.id !== '*' && {
  subFeatureBreadcrumb: {name: 'All Tasks'}
}),
```

`false` や `undefined` をスプレッドしても何も追加されない、という JavaScript の性質を利用したイディオム。オブジェクトリテラルの中で条件分岐したいときの定番。`if` を書くために一旦変数へ切り出す必要がなくなる。

## 気になる点

学習教材として読むなら、以下は「真似しないほうがよい」箇所として押さえておくとよい。

- **要素 1 個の `combineLatest`**（`experiments$`）… 過去に複数ソースだった名残。分割代入の `[experiments, ]` の余分なカンマもその痕跡
- **コメントアウトされた旧コード**が複数箇所に残っている（`// public tableMode: ...` など）
- **`filterMatchMode: col.filterMatchMode || andFilter ? 'AND' : undefined`** … `||` と三項演算子の優先順位により、実際には `(col.filterMatchMode || andFilter) ? 'AND' : undefined` と解釈される。`col.filterMatchMode` に何が入っていても結果が `'AND'` になるため、意図した式かどうか疑わしい
- **`tap` による副作用でのフィールド同期**（`sortFields` / `parents` / `checkedExperiments`）… テンプレートの購読有無に暗黙に依存する
- **`setTimeout` のマジックナンバー**（100ms）

--- chat

作成しました → experiments.component.ts.code.md

構成:

コードブロック（866行全文 + 末尾解説コメント）

import 群は「何のためのものか」を1行ずつ。セレクタ群・フッタアイテム群・判定関数群といった塊単位で意味が分かるように
クラス本体は全メソッド・全フィールドに解説を付与
特に重要な箇所には [■観点:...] を付けた（継承 / tapで副作用 / 深い比較 / computedの中でsignalを作る / 自動unsubscribe / URL is the source of truth / URLと一覧の突き合わせ / ルート形状からモードを判定 / 整合性 / モード遷移の集約 / 後始末 / 条件付きスプレッド）
解説セクション（8観点）

継承による共通化 — 基底の abstract と、このクラスが埋める対応表
Observable と Signal の混在 — select と selectSignal の使い分けの実態
URL を正とする状態復元 — この画面の中核。無限ループ回避の updateUrl = false
viewChild で子を直接叩く — フッタとコンテキストメニューが同じメソッドを共有する構造
computed の中で signal() を作る変則パターンの意図
setTimeout 3箇所それぞれの理由
演算子の選択（filter(!== null) / isEqual / concatLatestFrom / skip(1)）
条件付きスプレッド
最後に「気になる点」として、真似しないほうがよい箇所を5点挙げました。特に filterChanged の


filterMatchMode: col.filterMatchMode || andFilter ? 'AND' : undefined
は演算子の優先順位により (col.filterMatchMode || andFilter) ? 'AND' : undefined と解釈されます。col.filterMatchMode が truthy なら中身に関係なく 'AND' になるため、意図した式ではない可能性が高いです（ただし本件は解説対象外のため、コードは変更していません）。
