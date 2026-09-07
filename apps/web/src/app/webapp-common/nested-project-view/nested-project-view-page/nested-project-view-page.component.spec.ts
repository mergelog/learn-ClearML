import {Component, input, output} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {By} from '@angular/platform-browser';
import {provideMockStore} from '@ngrx/store/testing';
import {Project} from '~/business-logic/model/projects/project';
import {ProjectCardMenuComponent} from '@common/shared/ui-components/panel/project-card-menu/project-card-menu.component';
import {ProjectsHeaderComponent} from '@common/projects/dumb/projects-header/projects-header.component';

import {NestedProjectViewPageComponent, ProjectTypeEnum} from './nested-project-view-page.component';

@Component({
  selector: 'sm-projects-header',
  template: '<ng-content />',
})
class ProjectsHeaderStubComponent {
  sortByField = input<string>();
  sortOrder = input();
  enableTagsFilter = input(true);
  tags = input<string[]>();
  orderByChanged = output<string>();
}

describe('NestedProjectViewPageComponent', () => {
  let fixture: ComponentFixture<NestedProjectViewPageComponent>;

  const project = {
    id: 'project-id',
    name: 'Project',
    basename: 'Project',
    company: {id: 'company-id'},
    sub_projects: [],
  } as Project;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NestedProjectViewPageComponent],
      providers: [provideMockStore({})],
    })
      .overrideComponent(NestedProjectViewPageComponent, {
        remove: {imports: [ProjectsHeaderComponent]},
        add: {imports: [ProjectsHeaderStubComponent]},
      })
      .compileComponents();

    fixture = TestBed.createComponent(NestedProjectViewPageComponent);
    fixture.componentRef.setInput('projectsList', [project]);
    fixture.componentRef.setInput('entityType', ProjectTypeEnum.pipelines);
    fixture.componentRef.setInput('searching', false);
    fixture.componentRef.setInput('noMoreProjects', true);
    fixture.componentRef.setInput('projectsOrderBy', 'basename');
    fixture.componentRef.setInput('projectsTags', []);
    fixture.detectChanges();
  });

  it('forwards a nested-card delete action', () => {
    const deleteSpy = vi.fn();
    fixture.componentInstance.deleteProjectClicked.subscribe(deleteSpy);

    const menu = fixture.debugElement.query(By.directive(ProjectCardMenuComponent))
      .componentInstance as ProjectCardMenuComponent;

    expect(menu.actions()).toEqual(['delete']);

    menu.deleteProjectClicked.emit(project);

    expect(deleteSpy).toHaveBeenCalledWith(project);
  });
});
