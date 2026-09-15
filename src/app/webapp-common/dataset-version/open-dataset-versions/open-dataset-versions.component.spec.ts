import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { StoreModule } from '@ngrx/store';
import { EffectsModule } from '@ngrx/effects';
import { ApiEventsService } from '~/business-logic/api-services/events.service';
import { ApiProjectsService } from '~/business-logic/api-services/projects.service';
import { ActivatedRoute} from '@angular/router';
import { ApiTasksService } from '~/business-logic/api-services/tasks.service';
import { of } from 'rxjs';

import { OpenDatasetVersionsComponent } from './open-dataset-versions.component';
import {CommonExperimentsInfoEffects} from '@common/experiments/effects/common-experiments-info.effects';
import {initViewState} from '@common/core/reducers/view.reducer';
import {initUsers} from '@common/core/reducers/users-reducer';
import {experimentsViewInitialState} from '@common/experiments/reducers/experiments-view.reducer';
import {ColorHashService} from '@common/shared/services/color-hash/color-hash.service';

describe('SimpleDatasetVersionsComponent', () => {
  let component: OpenDatasetVersionsComponent;
  let fixture: ComponentFixture<OpenDatasetVersionsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        OpenDatasetVersionsComponent,
        StoreModule.forRoot({}),
        EffectsModule.forRoot([])
      ],
      providers: [
        provideMockStore({
          initialState: {
            rootProjects: {
              selectedProject: null,
              users: [],
              allUsers: [],
              extraUsers: [],
              deep: false
            },
            projects: { selectedProject: null },
            view: { projectType: 'datasets' },
            views: initViewState,
            users: initUsers,
            commonSearch: {
              isSearching: false,
              searchQuery: {query: '', regExp: false},
              placeholder: null,
              active: false,
              initiated: false
            },
            experiments: {
              view: experimentsViewInitialState,
              info: {},
              output: {}
            }
          }
        }),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
                params: { projectId: 'test' },
                queryParams: {},
                data: {},
                firstChild: { firstChild: { routeConfig: { path: '' } } }
            },
            parent: {
                snapshot: { params: { projectId: 'test' } }
            }
          }
        },
        { provide: ApiEventsService, useValue: {} },
        { provide: ApiProjectsService, useValue: {} },
        { provide: ApiTasksService, useValue: { tasksGetAllEx: () => of({ tasks: [] }) } },
        { provide: CommonExperimentsInfoEffects, useValue: {} },
        { provide: ColorHashService, useValue: {getColorForString: () => '#000000'} }
      ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(OpenDatasetVersionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
