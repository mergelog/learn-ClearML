import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { ActivatedRoute } from '@angular/router';
import { ApiTasksService } from '~/business-logic/api-services/tasks.service';

import { ModelInfoPlotsComponent } from './model-info-plots.component';
import {initViewState} from '@common/core/reducers/view.reducer';
import {modelsInitialState} from '@common/models/reducers/models-view.reducer';

describe('ModelInfoPlotComponent', () => {
  let component: ModelInfoPlotsComponent;
  let fixture: ComponentFixture<ModelInfoPlotsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ModelInfoPlotsComponent],
      providers: [
        provideMockStore({
          initialState: {
            models: {view: modelsInitialState, info: {plots: []}},
            views: initViewState,
            rootProjects: {selectedProject: null, deep: false}
          }
        }),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { params: {}, queryParams: {}, data: {}, routeConfig: {data: {}} }
          }
        },
        { provide: ApiTasksService, useValue: {} }
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ModelInfoPlotsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
