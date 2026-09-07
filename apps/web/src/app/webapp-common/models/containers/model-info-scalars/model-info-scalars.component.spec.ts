import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { ActivatedRoute } from '@angular/router';
import { ApiTasksService } from '~/business-logic/api-services/tasks.service';

import { ModelInfoScalarsComponent } from './model-info-scalars.component';
import {initViewState} from '@common/core/reducers/view.reducer';
import {modelsInitialState} from '@common/models/reducers/models-view.reducer';

describe('ModelInfoScalarsComponent', () => {
  let component: ModelInfoScalarsComponent;
  let fixture: ComponentFixture<ModelInfoScalarsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ModelInfoScalarsComponent],
      providers: [
        provideMockStore({
          initialState: {
            models: {view: modelsInitialState, info: {}},
            views: initViewState,
            rootProjects: {selectedProject: null, deep: false},
            experiments: {}
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

    fixture = TestBed.createComponent(ModelInfoScalarsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
