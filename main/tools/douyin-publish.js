// Douyin Mini-Game Publishing Automation - Phase 4
// Fill game creation form

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SCREENSHOT_DIR = 'D:\\loopcli\\main\\tools\\screenshots';
const CDP_PORT = 9333;

if (!fs.existsSync(SCREENSHOT_DIR)) fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

async function screenshot(page, name) {
  const file = path.join(SCREENSHOT_DIR, `${name}.png`);
  await page.screenshot({ path: file, fullPage: false });
  console.log(`[Screenshot] ${file}`);
}

async function main() {
  console.log('[1] Connecting to Edge CDP...');
  const browser = await chromium.connectOverCDP(`http://localhost:${CDP_PORT}`);
  const context = browser.contexts()[0];
  const page = context.pages().find(p => p.url().includes('/console/apply/game'));
  await page.bringToFront();
  await new Promise(r => setTimeout(r, 2000));

  // First, check if there's a dropdown for engine and see its options
  console.log('[2] Looking for engine selector...');
  const selects = await page.locator('select, [class*="select"], [class*="dropdown"]').all();
  for (let i = 0; i < selects.length; i++) {
    const visible = await selects[i].isVisible().catch(() => false);
    if (visible) {
      const tag = await selects[i].evaluate(e => e.tagName).catch(() => '');
      const text = await selects[i].textContent().catch(() => '');
      console.log(`  Select[${i}]: <${tag}> text="${text.trim().substring(0, 100)}"`);
    }
  }

  // Click the engine dropdown area (it says "请选择")
  console.log('[3] Clicking engine selector...');
  const engineTrigger = page.locator('text=请选择').first();
  if (await engineTrigger.isVisible().catch(() => false)) {
    await engineTrigger.click();
    await new Promise(r => setTimeout(r, 2000));
    await screenshot(page, '40-engine-options');

    // Get dropdown options
    const options = await page.locator('[class*="option"], [class*="item"], [role="option"], [class*="selection"]').allTextContents();
    const visibleOptions = options.filter(o => o.trim()).map(o => o.trim());
    console.log('Engine options:', visibleOptions.join(' | '));

    // Look for "无引擎" or "JavaScript" or "原生" options
    const engineChoice = page.locator('text=无引擎').first();
    if (await engineChoice.isVisible({ timeout: 3000 }).catch(() => false)) {
      console.log('Selecting "无引擎"...');
      await engineChoice.click();
    } else {
      // Try other common options
      for (const opt of ['JavaScript', '原生', '其他', 'Cocos', 'Laya']) {
        const el = page.locator(`text=${opt}`).first();
        if (await el.isVisible({ timeout: 2000 }).catch(() => false)) {
          console.log(`Selecting "${opt}"...`);
          await el.click();
          break;
        }
      }
    }
  }

  await new Promise(r => setTimeout(r, 1000));
  await screenshot(page, '41-engine-selected');

  // Now fill the form fields
  console.log('\n[4] Filling form...');

  // Get all visible text inputs
  const inputs = await page.locator('input[type="text"], input:not([type])').all();
  const visibleInputs = [];
  for (const input of inputs) {
    if (await input.isVisible().catch(() => false)) {
      visibleInputs.push(input);
    }
  }
  console.log(`Found ${visibleInputs.length} visible text inputs`);

  // Based on form order: name, contact name, phone, email
  // Input 0 = game name
  // Input 1 = contact name
  // Input 2 = contact phone
  // Input 3 = contact email

  // Fill game name (first input)
  if (visibleInputs[0]) {
    console.log('Filling game name: 消消消大作战');
    await visibleInputs[0].fill('消消消大作战');
    await new Promise(r => setTimeout(r, 500));
  }

  // Fill contact name
  if (visibleInputs[1]) {
    console.log('Filling contact name: 周鼎诺');
    await visibleInputs[1].fill('周鼎诺');
    await new Promise(r => setTimeout(r, 500));
  }

  // For phone and email, check if they're required
  // Leave them empty for now and check form state
  if (visibleInputs[2]) {
    console.log('Phone input found - NEED USER INPUT');
  }
  if (visibleInputs[3]) {
    console.log('Email input found - NEED USER INPUT');
  }

  // Check the agreement checkbox
  console.log('\n[5] Checking agreement...');
  const checkbox = page.locator('input[type="checkbox"]').first();
  const isChecked = await checkbox.isChecked().catch(() => false);
  if (!isChecked) {
    // Click the label/area near the checkbox
    const agreeArea = page.locator('text=我已阅读并同意').first();
    await agreeArea.click();
    console.log('Checked agreement');
  }

  await new Promise(r => setTimeout(r, 1000));
  await screenshot(page, '42-form-filled');

  // Check form validation state
  const finalText = await page.locator('body').innerText().catch(() => '');
  console.log('\n--- Current form state ---');
  // Show just the form section
  const formSection = finalText.substring(
    finalText.indexOf('小游戏名称'),
    finalText.indexOf('更多说明') > -1 ? finalText.indexOf('更多说明') : finalText.length
  );
  console.log(formSection);

  // Check for any error messages
  const errors = await page.locator('[class*="error"], [class*="warn"], [class*="invalid"]').allTextContents();
  const visibleErrors = errors.filter(e => e.trim()).map(e => e.trim());
  if (visibleErrors.length > 0) {
    console.log('\nValidation errors:', visibleErrors.join(' | '));
  }

  await screenshot(page, '43-final-state');
  console.log('\nPhase 4 complete. Need user phone and email to proceed.');
  browser.close();
}

main().catch(e => {
  console.error('Error:', e.message);
  process.exit(1);
});
