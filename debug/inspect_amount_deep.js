import puppeteer from 'puppeteer-core';

async function main() {
  console.log('Launching browser to inspect amount elements...');
  try {
    const browser = await puppeteer.launch({
      executablePath: '/bin/chromium',
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--enable-unsafe-swiftshader',
        '--ignore-gpu-blocklist',
        '--enable-webgl',
        '--enable-webgl2',
        '--window-size=412,850',
        '--user-data-dir=/root/olymp-chrome-session'
      ],
      defaultViewport: { 
        width: 412, 
        height: 850,
        isMobile: true,
        hasTouch: true,
        deviceScaleFactor: 2
      }
    });

    const pages = await browser.pages();
    const page = pages[0] || (await browser.newPage());
    
    await page.setUserAgent(
      'Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'
    );

    console.log('Navigating to platform...');
    await page.goto('https://olymptrade.com/platform', {
      waitUntil: 'domcontentloaded',
      timeout: 60000
    });

    console.log('Waiting 15 seconds...');
    await new Promise(r => setTimeout(r, 15000));

    const url = page.url();
    const title = await page.title();
    console.log('Final URL:', url);
    console.log('Final Page Title:', title);

    // Save screenshot
    const screenshotPath = '/root/.gemini/antigravity-cli/brain/a1ee9d83-4184-4b53-b31b-6c67b86d4a04/screenshot_deep_amount.png';
    await page.screenshot({ path: screenshotPath });
    console.log('Screenshot saved to:', screenshotPath);

    // Find all elements containing any digits
    const results = await page.evaluate(() => {
      const matches = [];
      const all = document.querySelectorAll('*');
      all.forEach(el => {
        const text = (el.textContent || '').trim();
        const value = el.value || '';
        // Look for specific target like "40" or "Đ40"
        if ((text.includes('40') || value.includes('40')) && el.children.length <= 3) {
          matches.push({
            tag: el.tagName,
            className: el.className,
            id: el.id,
            text: text,
            value: value,
            parentTag: el.parentElement?.tagName,
            parentClass: el.parentElement?.className
          });
        }
      });
      return matches;
    });

    console.log('=== MATCHING AMOUNT ELEMENTS ===');
    console.log(JSON.stringify(results, null, 2));

    await browser.close();
  } catch (err) {
    console.error('Error:', err);
  }
}

main();
