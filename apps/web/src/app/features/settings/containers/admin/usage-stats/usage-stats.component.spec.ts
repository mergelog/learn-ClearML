import { ComponentFixture, TestBed } from '@angular/core/testing';
import {provideMockStore} from '@ngrx/store/testing';
import {signal} from '@angular/core';
import {ConfigurationService} from '@common/shared/services/configuration.service';
import {selectAllowed, selectStatsSupported} from '~/core/reducers/usage-stats.reducer';

import { UsageStatsComponent } from './usage-stats.component';

describe('UsageStatsComponent', () => {
  let component: UsageStatsComponent;
  let fixture: ComponentFixture<UsageStatsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UsageStatsComponent],
      providers: [
        provideMockStore({
          selectors: [
            {selector: selectAllowed, value: false},
            {selector: selectStatsSupported, value: true}
          ]
        }),
        {
          provide: ConfigurationService,
          useValue: {configuration: signal({demo: false})}
        }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(UsageStatsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
