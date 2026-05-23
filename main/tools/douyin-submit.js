// Douyin Mini-Game - Fill phone/email and submit
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SCREENSHOT_DIR = 'D:\\loopcli\\main\\tools\\screenshots';
const CDP_PORT = 9333;
const PHONE = '18108431035';
const EMAIL = '1163155015@qq.com';

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

  // Find the page - could be on apply/game or need to navigate
  let page = context.pages().find(p => p.url().includes('/console/apply/game'));
  if (!page) {
    page = context.pages().find(p => p.url().includes('/console'));
    if (page) {
      console.log('[1b] Navigating to game creation page...');
      await page.goto('https://developer.open-douyin.com/console/apply/game');
      await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    }
  }
  if (!page) {
    page = context.pages()[0];
    await page.goto('https://developer.open-douyin.com/console/apply/game');
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  }

  await page.bringToFront();
  await new Promise(r => setTimeout(r, 3000));
  await screenshot(page, '50-page-state');

  // Get current URL
  console.log('Current URL:', page.url());

  // Find all visible text inputs
  console.log('\n[2] Finding form inputs...');
  const inputs = await page.locator('input[type="text"], input:not([type]), input[type="tel"], input[type="email"]').all();
  const visibleInputs = [];
  for (let i = 0; i < inputs.length; i++) {
    if (await inputs[i].isVisible().catch(() => false)) {
      const placeholder = await inputs[i].getAttribute('placeholder').catch(() => '');
      const value = await inputs[i].inputValue().catch(() => '');
      console.log(`  Input[${i}]: placeholder="${placeholder}" value="${value}"`);
      visibleInputs.push({ index: i, locator: inputs[i], placeholder, value });
    }
  }

  // Fill phone and email based on current state
  // First check what's already filled
  for (const inp of visibleInputs) {
    if (inp.value && inp.value.length > 0) {
      console.log(`  Input[${inp.index}] already has value: "${inp.value}"`);
    }
  }

  // Strategy: find inputs by placeholder or by position
  // Common placeholders: 联系人电话, 联系人邮箱, or similar
  let phoneFilled = false;
  let emailFilled = false;

  for (const inp of visibleInputs) {
    const ph = (inp.placeholder || '').toLowerCase();
    const val = inp.value || '';

    if ((ph.includes('电话') || ph.includes('手机') || ph.includes('phone')) && !val) {
      console.log(`Filling phone in input[${inp.index}]: ${PHONE}`);
      await inp.locator.click();
      await inp.locator.fill(PHONE);
      phoneFilled = true;
      await new Promise(r => setTimeout(r, 500));
    }
    if ((ph.includes('邮箱') || ph.includes('email') || ph.includes('mail')) && !val) {
      console.log(`Filling email in input[${inp.index}]: ${EMAIL}`);
      await inp.locator.click();
      await inp.locator.fill(EMAIL);
      emailFilled = true;
      await new Promise(r => setTimeout(r, 500));
    }
  }

  // If placeholders didn't match, try by position (assuming inputs 2 and 3)
  if (!phoneFilled && visibleInputs.length >= 3) {
    const phoneInput = visibleInputs[2];
    if (!phoneInput.value) {
      console.log(`Filling phone by position in input[${phoneInput.index}]: ${PHONE}`);
      await phoneInput.locator.click();
      await phoneInput.locator.fill(PHONE);
      phoneFilled = true;
      await new Promise(r => setTimeout(r, 500));
    }
  }
  if (!emailFilled && visibleInputs.length >= 4) {
    const emailInput = visibleInputs[3];
    if (!emailInput.value) {
      console.log(`Filling email by position in input[${emailInput.index}]: ${EMAIL}`);
      await emailInput.locator.click();
      await emailInput.locator.fill(EMAIL);
      emailFilled = true;
      await new Promise(r => setTimeout(r, 500));
    }
  }

  await screenshot(page, '51-form-filled');

  // Check agreement checkbox
  console.log('\n[3] Checking agreement...');
  try {
    const agreeArea = page.locator('text=我已阅读并同意').first();
    if (await agreeArea.isVisible({ timeout: 3000 }).catch(() => false)) {
      await agreeArea.click();
      console.log('Agreement clicked');
    }
  } catch (e) {
    console.log('Agreement handling:', e.message);
  }

  await new Promise(r => setTimeout(r, 1000));
  await screenshot(page, '52-agreement-checked');

  // Check for validation errors before submitting
  console.log('\n[4] Checking form state...');
  const errors = await page.locator('[class*="error"], [class*="warn"], [class*="invalid"]').allTextContents();
  const visibleErrors = errors.filter(e => e.trim()).map(e => e.trim());
  if (visibleErrors.length > 0) {
    console.log('Validation errors:', visibleErrors.join(' | '));
  } else {
    console.log('No validation errors detected');
  }

  // Find and click submit button
  console.log('\n[5] Looking for submit button...');
  const submitBtn = page.locator('button:has-text("创建"), button:has-text("提交"), button:has-text("确认"), button:has-text("保存")').first();
  if (await submitBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
    console.log('Found submit button, clicking...');
    await submitBtn.click();
    await new Promise(r => setTimeout(r, 5000));
    await screenshot(page, '53-after-submit');

    // Check result
    const currentUrl = page.url();
    console.log('URL after submit:', currentUrl);

    // Check for success or error messages
    const bodyText = await page.locator('body').innerText().catch(() => '');
    if (bodyText.includes('成功') || bodyText.includes('success') || currentUrl !== 'https://developer.open-douyin.com/console/apply/game') {
      console.log('\n=== FORM SUBMISSION SUCCESSFUL ===');
      // Check if we can find AppID
      const appIdMatch = bodyText.match(/tt[a-f0-9]+/i) || bodyText.match(/AppID[:\s]*([a-zA-Z0-9]+)/);
      if (appIdMatch) {
        console.log('Found AppID:', appIdMatch[0]);
      }
    } else if (bodyText.includes('失败') || bodyText.includes('错误') || bodyText.includes('error')) {
      console.log('\n=== FORM SUBMISSION FAILED ===');
      console.log('Page text snippet:', bodyText.substring(0, 500));
    } else {
      console.log('\n=== SUBMIT STATE UNCLEAR ===');
      console.log('Page text snippet:', bodyText.substring(0, 500));
    }
  } else {
    console.log('Submit button not found');
    // Try to find any button
    const buttons = await page.locator('button').all();
    for (let i = 0; i < buttons.length; i++) {
      const visible = await buttons[i].isVisible().catch(() => false);
      if (visible) {
        const text = await buttons[i].textContent().catch(() => '');
        console.log(`  Button[${i}]: "${text.trim()}"`);
      }
    }
  }

  await screenshot(page, '54-final');
  console.log('\nDone.');
  browser.close();
}

main().catch(e => {
  console.error('Error:', e.message);
  process.exit(1);
});
