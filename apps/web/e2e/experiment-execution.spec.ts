import {expect, test} from '@playwright/test';
import {mockClearmlApi} from './fixtures/clearml-api.fixture';

test.beforeEach(async ({page}) => {
  await mockClearmlApi(page);
});

test('updates Execution when switching tasks and does not retain stale data', async ({page}) => {
  await page.goto('/projects/execution-project/tasks/task-a/execution');

  await expect(page).toHaveURL(/\/tasks\/task-a\/execution/);
  await expect(page.getByText('repository-task-a', {exact: true})).toBeVisible();

  await page.locator('sm-experiments-table').getByText('Task B', {exact: true}).first().click();

  await expect(page).toHaveURL(/\/tasks\/task-b\/execution/);
  await expect(page.getByText('repository-task-b', {exact: true})).toBeVisible();
  await expect(page.getByText('repository-task-a', {exact: true})).toHaveCount(0);

  const navigation = page.locator('sm-experiment-info-navbar');
  await navigation.getByText('CONFIGURATION', {exact: true}).click();
  await expect(page).toHaveURL(/\/tasks\/task-b\/hyper-params/);
  await navigation.getByText('EXECUTION', {exact: true}).click();
  await expect(page.getByText('repository-task-b', {exact: true})).toBeVisible();

  await page.locator('sm-experiments-table')
    .getByText('Task without execution', {exact: true})
    .first()
    .click();

  await expect(page).toHaveURL(/\/tasks\/task-empty\/execution/);
  await expect(page.getByText('repository-task-b', {exact: true})).toHaveCount(0);
  await expect(page.getByText('repository-task-a', {exact: true})).toHaveCount(0);
});
