import {expect, test} from '@playwright/test';

test('boots the Angular application shell', async ({page}) => {
  const response = await page.goto('/');

  expect(response?.ok()).toBe(true);
  await expect(page).toHaveTitle('stackup');
  await expect(page.locator('sm-root[ng-version]')).toBeAttached();
});
