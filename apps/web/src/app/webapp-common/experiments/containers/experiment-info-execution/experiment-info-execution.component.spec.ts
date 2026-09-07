import {ComponentFixture, TestBed} from '@angular/core/testing';
import {MatDialog} from '@angular/material/dialog';
import {ActivatedRoute} from '@angular/router';
import {MockStore, provideMockStore} from '@ngrx/store/testing';
import {IExecutionForm, sourceTypesEnum} from '~/features/experiments/shared/experiment-execution.model';
import {selectIsExperimentEditable, selectShowExtraDataSpinner} from '~/features/experiments/reducers';
import {selectBackdropActive, selectHideRedactedArguments} from '@common/core/reducers/view.reducer';
import {CommonExperimentConverterService} from '@common/experiments/shared/services/common-experiment-converter.service';
import {
  selectExperimentExecutionInfoData,
  selectIsExperimentSaving,
  selectIsSelectedExperimentInDev
} from '../../reducers';
import {ExperimentInfoExecutionComponent} from './experiment-info-execution.component';

const buildExecution = (
  repository: string,
  requirements: IExecutionForm['requirements'] = {pip: ''}
): IExecutionForm => ({
  source: {
    repository,
    entry_point: 'train.py',
    working_dir: '.',
    binary: 'python',
    scriptType: sourceTypesEnum.Branch,
    branch: 'main'
  },
  requirements,
  diff: '',
  output: {destination: `s3://output/${repository}`},
  queue: null,
  container: {
    image: `image-${repository}`,
    arguments: `--task=${repository}`
  }
});

describe('ExperimentInfoExecutionComponent', () => {
  let fixture: ComponentFixture<ExperimentInfoExecutionComponent>;
  let component: ExperimentInfoExecutionComponent;
  let store: MockStore;
  let executionSelector: ReturnType<MockStore['overrideSelector']>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ExperimentInfoExecutionComponent],
      providers: [
        provideMockStore({
          selectors: [
            {selector: selectExperimentExecutionInfoData, value: undefined},
            {selector: selectShowExtraDataSpinner, value: false},
            {selector: selectIsExperimentEditable, value: false},
            {selector: selectIsSelectedExperimentInDev, value: false},
            {selector: selectIsExperimentSaving, value: false},
            {selector: selectBackdropActive, value: false},
            {selector: selectHideRedactedArguments, value: false}
          ]
        }),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              routeConfig: {data: {minimized: true}}
            }
          }
        },
        {
          provide: MatDialog,
          useValue: {open: vi.fn()}
        },
        {
          provide: CommonExperimentConverterService,
          useValue: {convertRequirements: vi.fn(value => value)}
        }
      ]
    }).compileComponents();

    store = TestBed.inject(MockStore);
    executionSelector = store.overrideSelector(selectExperimentExecutionInfoData, undefined);
    fixture = TestBed.createComponent(ExperimentInfoExecutionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('renders safely before execution data is available', () => {
    expect(component.formData).toBeUndefined();
    expect(component.requirementsOptions).toEqual([]);
    expect(fixture.nativeElement.textContent).not.toContain('task-a-repository');
  });

  it('replaces task A execution data with task B on the same component instance', () => {
    executionSelector.setResult(buildExecution('task-a-repository', {
      pip: 'task-a-package',
      conda: 'task-a-conda'
    }));
    store.refreshState();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('task-a-repository');
    component.requirementChanged('conda');

    executionSelector.setResult(buildExecution('task-b-repository', {
      pip: 'task-b-package'
    }));
    store.refreshState();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('task-b-repository');
    expect(fixture.nativeElement.textContent).not.toContain('task-a-repository');
    expect(component.selectedRequirement).toBe('pip');
    expect(component.requirementsOptions).toEqual([{value: 'pip', label: 'PIP'}]);
  });

  it('clears the previous task when the selected task has no execution data', () => {
    executionSelector.setResult(buildExecution('task-with-execution'));
    store.refreshState();
    fixture.detectChanges();

    executionSelector.setResult(undefined);
    store.refreshState();
    fixture.detectChanges();

    expect(component.formData).toBeUndefined();
    expect(component.requirementsOptions).toEqual([]);
    expect(fixture.nativeElement.textContent).not.toContain('task-with-execution');
  });

  it('stops updating execution state after destroy', () => {
    const taskB = buildExecution('task-b-before-destroy');
    executionSelector.setResult(taskB);
    store.refreshState();
    fixture.detectChanges();

    fixture.destroy();
    executionSelector.setResult(buildExecution('task-c-after-destroy'));
    store.refreshState();

    expect(component.formData).toBe(taskB);
  });
});
