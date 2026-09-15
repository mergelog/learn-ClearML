import type {Page, Route} from '@playwright/test';

interface MockTask {
  id: string;
  name: string;
  project: {id: string; name: string};
  company: {id: string; name: string};
  user: {id: string; name: string};
  status: string;
  type: string;
  runtime: Record<string, never>;
  last_change: string;
  last_update: string;
  system_tags: string[];
  tags: string[];
  script?: {
    repository: string;
    entry_point: string;
    working_dir: string;
    binary: string;
    branch: string;
    requirements: {pip: string[]};
    diff: string;
  };
  execution?: {queue: null};
  container?: {image: string; arguments: string};
  output: {destination: string};
}

const project = {id: 'execution-project', name: 'Execution project'};
const company = {id: 'test-company', name: 'Test company'};
const user = {id: 'test-user', name: 'Test User', company};

function buildTask(id: string, name: string, repository?: string): MockTask {
  return {
    id,
    name,
    project,
    company,
    user,
    status: 'completed',
    type: 'training',
    runtime: {},
    last_change: '2026-09-05T00:00:00Z',
    last_update: '2026-09-05T00:00:00Z',
    system_tags: [],
    tags: [],
    ...(repository ? {
      script: {
        repository,
        entry_point: 'train.py',
        working_dir: '.',
        binary: 'python',
        branch: 'main',
        requirements: {pip: [`package-${id}`]},
        diff: ''
      },
      execution: {queue: null},
      container: {image: `image-${id}`, arguments: `--task=${id}`}
    } : {}),
    output: {destination: `s3://${id}`}
  };
}

export const executionTasks = [
  buildTask('task-a', 'Task A', 'repository-task-a'),
  buildTask('task-b', 'Task B', 'repository-task-b'),
  buildTask('task-empty', 'Task without execution')
];

function responseData(endpoint: string, route: Route): Record<string, unknown> {
  const body = route.request().postDataJSON() as {id?: string[]};

  switch (endpoint) {
    case 'login.supported_modes':
      return {authenticated: true};
    case 'users.get_current_user':
      return {user};
    case 'users.get_preferences':
      return {
        preferences: {
          version: 1,
          views: {neverShowPopupAgain: ['tip-of-the-day']}
        }
      };
    case 'projects.get_user_names':
      return {users: []};
    case 'projects.get_task_tags':
    case 'projects.get_model_tags':
      return {tags: []};
    case 'projects.get_task_parents':
      return {parents: []};
    case 'projects.get_all_ex':
      return {projects: [project]};
    case 'tasks.get_types':
      return {types: []};
    case 'tasks.get_by_id_ex':
      return {
        tasks: [executionTasks.find(task => task.id === body.id?.[0]) ?? executionTasks[0]]
      };
    case 'tasks.get_all_ex':
      return {tasks: executionTasks, scroll_id: null};
    case 'tasks.get_configuration_names':
      return {configurations: [{task: body.id?.[0], names: []}]};
    default:
      return {};
  }
}

export async function mockClearmlApi(page: Page): Promise<void> {
  await page.route('https://api.github.com/**', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: '{}'
  }));

  await page.route('**/service/**', route => {
    const endpoint = new URL(route.request().url()).pathname.split('/').at(-1) ?? '';

    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        meta: {result_code: 200},
        data: responseData(endpoint, route)
      })
    });
  });
}
