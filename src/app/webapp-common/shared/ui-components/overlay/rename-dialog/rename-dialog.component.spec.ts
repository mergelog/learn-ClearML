import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RenameDialogComponent } from './rename-dialog.component';
import {MAT_DIALOG_DATA, MatDialogRef} from '@angular/material/dialog';

describe('RenameDialogComponent', () => {
  let component: RenameDialogComponent;
  let fixture: ComponentFixture<RenameDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RenameDialogComponent],
      providers: [
        {provide: MatDialogRef, useValue: {close: vi.fn()}},
        {
          provide: MAT_DIALOG_DATA,
          useValue: {
            name: 'Original name',
            minLength: 3,
            iconClass: '',
            header: 'Rename',
            pattern: '',
            patternError: ''
          }
        }
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(RenameDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
