import puppeteer from 'puppeteer-core';

async function main() {
  console.log('Launching browser with session...');
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

    // Capture all console messages
    page.on('console', msg => {
      console.log(`[PAGE CONSOLE] [${msg.type()}] ${msg.text()}`);
    });

    // Capture failed requests
    page.on('requestfailed', request => {
      console.log(`[REQUEST FAILED] ${request.url()} - ${request.failure()?.errorText}`);
    });

    console.log('Navigating to platform...');
    await page.goto('https://olymptrade.com/platform', {
      waitUntil: 'networkidle0',
      timeout: 60000
    });

    console.log('Current URL:', page.url());
    console.log('Page Title:', await page.title());

    console.log('Waiting 15 seconds to collect logs...');
    await new Promise(r => setTimeout(r, 15000));

    // Let's see if we have any "Try again" buttons and print their info
    const buttons = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('button')).map(b => ({
        text: b.textContent?.trim(),
        class: b.className,
        visible: b.getBoundingClientRect().width > 0
      }));
    });
    console.log('Buttons on page:', buttons);

    // Save screenshot
    const screenshotPath = '/root/.gemini/antigravity-cli/brain/a1ee9d83-4184-4b53-b31b-6c67b86d4a04/screenshot_details.png';
    await page.screenshot({ path: screenshotPath });
    console.log('Screenshot saved to:', screenshotPath);

    await browser.close();
  } catch (err) {
    console.error('Error:', err);
  }
}

main();
