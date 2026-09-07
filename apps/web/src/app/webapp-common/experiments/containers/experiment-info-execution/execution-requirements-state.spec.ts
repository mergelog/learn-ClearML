import type {IExecutionForm} from '~/features/experiments/shared/experiment-execution.model';
import {createExecutionRequirementsState} from './execution-requirements-state';

const buildExecution = (requirements: IExecutionForm['requirements']): IExecutionForm => ({
  source: {
    repository: 'https://example.test/repository.git',
    entry_point: 'train.py',
    working_dir: '.',
    binary: 'python',
    scriptType: 'branch' as IExecutionForm['source']['scriptType'],
    branch: 'main'
  },
  requirements,
  diff: '',
  output: {destination: 's3://example/output'},
  queue: null
});

describe('createExecutionRequirementsState', () => {
  it('clears task-specific state while execution data is unavailable', () => {
    expect(createExecutionRequirementsState(undefined, 'conda')).toEqual({
      options: [],
      selected: 'pip',
      editable: true,
      resetTooltip: ''
    });
  });

  it('creates ordered options and preserves an available selection', () => {
    const state = createExecutionRequirementsState(buildExecution({
      pip: 'numpy',
      orgPip: 'numpy==1.0',
      conda: 'python=3.12',
      orgConda: 'python=3.11'
    }), 'conda');

    expect(state.options).toEqual([
      {value: 'pip', label: 'PIP'},
      {value: 'orgPip', label: 'Original PIP'},
      {value: 'conda', label: 'Conda'},
      {value: 'orgConda', label: 'Original Conda'}
    ]);
    expect(state.selected).toBe('conda');
    expect(state.editable).toBe(false);
    expect(state.resetTooltip).toBe(
      'Set packages to originally recorded values (original-pip / original-conda)'
    );
  });

  it('falls back to pip when the next task does not contain the previous selection', () => {
    const state = createExecutionRequirementsState(
      buildExecution({pip: '', orgPip: 'recorded-package'}),
      'conda'
    );

    expect(state.options).toEqual([
      {value: 'pip', label: 'PIP'},
      {value: 'orgPip', label: 'Original PIP'}
    ]);
    expect(state.selected).toBe('pip');
    expect(state.editable).toBe(true);
    expect(state.resetTooltip).toBe(
      'Set packages to originally recorded values (original-pip)'
    );
  });

  it('represents a task with no package metadata without retaining previous options', () => {
    expect(createExecutionRequirementsState(buildExecution({}), 'pip')).toEqual({
      options: [],
      selected: 'pip',
      editable: true,
      resetTooltip: 'Set packages to originally recorded values ()'
    });
  });
});
