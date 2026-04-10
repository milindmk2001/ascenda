import { test, expect } from '@playwright/test';

test('Physics Brain Lesson Generation - Chrome/Edge Baseline', async ({ page }) => {
  await page.goto('https://ascenda-umber.vercel.app');

  // Verify Header
  await expect(page.locator('h1')).toContainText('Ascenda');

  // Click the Button
  const startBtn = page.getByRole('button', { name: /Launch Coulomb's Law/i });
  await startBtn.click();

  // Verify Loading State
  await expect(page.getByText('Synthesizing Physics Concept...')).toBeVisible();

  // Verify Content Arrival (timeout 15s for AI)
  await expect(page.locator('article')).toBeVisible({ timeout: 15000 });
  await expect(page.getByText('Unit 1: Electrostatics')).toBeVisible();
});
