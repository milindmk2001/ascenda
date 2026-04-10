import { test, expect } from '@playwright/test';

test('Ascenda Physics POC - Chrome/Edge Test', async ({ page }) => {
  // 1. Go to your local dev site (or your Vercel URL)
  await page.goto('http://localhost:5173'); 

  // 2. Verify the Brand Name exists
  await expect(page.locator('h1')).toContainText('Ascenda');

  // 3. Find and click the Start Lesson button
  const startBtn = page.getByRole('button', { name: /Start Coulomb's Law/i });
  await expect(startBtn).toBeVisible();
  await startBtn.click();

  // 4. Verify that the loading state appears
  await expect(page.getByText(/Consulting/i)).toBeVisible();

  // 5. Verify that the AI response eventually arrives
  // We give it 15 seconds because AI generation can be slow
  await expect(page.locator('article')).toBeVisible({ timeout: 15000 });
});