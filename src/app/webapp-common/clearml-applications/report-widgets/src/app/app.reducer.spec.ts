import {
  reportsPlotlyReady,
  setNoPermissions,
  setPlotData,
  setSignIsNeeded,
  setTaskData
} from './app.actions';
import {appFeature, initialState} from './app.reducer';

describe('report widgets reducer', () => {
  it('returns the initial state for an unknown action', () => {
    const state = appFeature.reducer(undefined, {type: '[Test] unknown'});

    expect(state).toEqual(initialState);
  });

  it('stores plot data without changing unrelated readiness flags', () => {
    const plotData = [{metric: 'loss', variant: 'training'}];
    const state = appFeature.reducer(
      initialState,
      setPlotData({data: plotData as never})
    );

    expect(state.plotData).toBe(plotData);
    expect(state.plotlyReady).toBe(false);
    expect(state.signIsNeeded).toBe(false);
    expect(state.noPermissions).toBe(false);
  });

  it('accumulates independent status and task-data updates', () => {
    const readyState = appFeature.reducer(initialState, reportsPlotlyReady());
    const signState = appFeature.reducer(readyState, setSignIsNeeded());
    const permissionState = appFeature.reducer(signState, setNoPermissions());
    const state = appFeature.reducer(permissionState, setTaskData({
      sourceProject: 'project-1',
      sourceTasks: ['task-1', 'task-2'],
      appId: 'app-1'
    }));

    expect(state).toMatchObject({
      plotlyReady: true,
      signIsNeeded: true,
      noPermissions: true,
      taskData: {
        sourceProject: 'project-1',
        sourceTasks: ['task-1', 'task-2'],
        appId: 'app-1'
      }
    });
  });
});
