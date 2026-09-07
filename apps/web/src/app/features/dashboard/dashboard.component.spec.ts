import { ComponentFixture, TestBed } from '@angular/core/testing';
import {vi} from 'vitest';
import type {Mock} from 'vitest';
import { NO_ERRORS_SCHEMA, signal } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { Store } from '@ngrx/store';
import { of, Subject, EMPTY } from 'rxjs';

import { DashboardComponent } from './dashboard.component';
import { initSearch } from '@common/common-search/common-search.actions';
import { selectActiveSearch } from '@common/common-search/common-search.reducer';
import {
  selectCurrentUser,
  selectShowOnlyUserWork
} from '@common/core/reducers/users-reducer';
import { selectFirstLogin } from '@common/core/reducers/view.reducer';
import {
  getRecentExperiments,
  getRecentProjects,
  getRecentReports
} from '@common/dashboard/common-dashboard.actions';
import { selectRecentTasks } from '@common/dashboard/common-dashboard.reducer';
import { firstLogin } from '@common/core/actions/layout.actions';
import { setDeep } from '@common/core/actions/projects.actions';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;

  let store: Store<object> & {select: Mock; selectSignal: Mock; dispatch: Mock};
  let router: Router & {navigate: Mock; navigateByUrl: Mock};
  let dialog: MatDialog & {open: Mock};
  let activatedRoute: ActivatedRoute;

  let activeSearch$: Subject<boolean>;
  let showOnlyUserWork$: Subject<boolean>;
  let currentUser$: Subject<{id: string}>;
  let firstLogin$: Subject<boolean>;
  let recentTasks$: Subject<unknown[]>;

  beforeEach(async () => {
    activeSearch$ = new Subject<boolean>();
    showOnlyUserWork$ = new Subject<boolean>();
    currentUser$ = new Subject<{id: string}>();
    firstLogin$ = new Subject<boolean>();
    recentTasks$ = new Subject<unknown[]>();

    store = {
      select: vi.fn((selector: unknown) => {
        switch (selector) {
          case selectActiveSearch:
            return activeSearch$.asObservable();
          case selectShowOnlyUserWork:
            return showOnlyUserWork$.asObservable();
          case selectCurrentUser:
            return currentUser$.asObservable();
          case selectFirstLogin:
            return firstLogin$.asObservable();
          case selectRecentTasks:
            return recentTasks$.asObservable();
          default:
            return EMPTY;
        }
      }),
      selectSignal: vi.fn(() => signal([])),
      dispatch: vi.fn()
    } as unknown as Store<object> & {select: Mock; selectSignal: Mock; dispatch: Mock};

    router = {
      navigate: vi.fn(),
      navigateByUrl: vi.fn()
    } as unknown as Router & {navigate: Mock; navigateByUrl: Mock};
    activatedRoute = {} as ActivatedRoute;

    dialog = {open: vi.fn()} as unknown as MatDialog & {open: Mock};
    dialog.open.mockReturnValue({
      afterClosed: () => of(null)
    });

    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        { provide: Store, useValue: store },
        { provide: Router, useValue: router },
        { provide: ActivatedRoute, useValue: activatedRoute },
        { provide: MatDialog, useValue: dialog }
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should dispatch initSearch in the constructor', () => {
    expect(store.dispatch).toHaveBeenCalledWith(initSearch({payload: 'Search for all'}));
  });

  it('should navigate to search when active search becomes true', () => {
    activeSearch$.next(false);
    activeSearch$.next(true);
    expect(router.navigate).toHaveBeenCalledWith(
      ['search'],
      {relativeTo: activatedRoute, queryParamsHandling: 'preserve'}
    );
  });

  it('should dispatch recent entities actions when user and showOnlyUserWork are set', async () => {
    const initialDispatchCount = store.dispatch.mock.calls.length;

    showOnlyUserWork$.next(true);
    currentUser$.next({id: 'user-1'});

    await new Promise(resolve => window.setTimeout(resolve, 110));

    expect(store.dispatch.mock.calls.length).toBeGreaterThan(initialDispatchCount);
    expect(store.dispatch).toHaveBeenCalledWith(getRecentProjects());
    expect(store.dispatch).toHaveBeenCalledWith(getRecentExperiments());
    expect(store.dispatch).toHaveBeenCalledWith(getRecentReports());
  });

  it('should show welcome dialog on first login and dispatch firstLogin(false) after closing', () => {
    firstLogin$.next(true);

    expect(dialog.open).toHaveBeenCalled();
    expect(store.dispatch).toHaveBeenCalledWith(firstLogin({first: false}));
  });

  it('should dispatch setDeep(false) on init', () => {
    expect(store.dispatch).toHaveBeenCalledWith(setDeep({deep: false}));
  });

  it('should navigate to workers and queues on redirectToWorkers', () => {
    component.redirectToWorkers();
    expect(router.navigateByUrl).toHaveBeenCalledWith('/workers-and-queues');
  });
});
