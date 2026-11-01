import puppeteer from 'puppeteer-core';
import fs from 'fs';

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

    console.log('Navigating to platform...');
    await page.goto('https://olymptrade.com/platform', {
      waitUntil: 'networkidle2',
      timeout: 60000
    });

    console.log('Current URL:', page.url());
    console.log('Page Title:', await page.title());

    // Wait a bit for dynamic content
    console.log('Waiting 10s for page load...');
    await new Promise(r => setTimeout(r, 10000));

    // Save screenshot to the artifact directory so it's accessible
    const screenshotPath = '/root/.gemini/antigravity-cli/brain/a1ee9d83-4184-4b53-b31b-6c67b86d4a04/screenshot.png';
    await page.screenshot({ path: screenshotPath });
    console.log('Screenshot saved to:', screenshotPath);

    // Scan for potential balance elements in the DOM
    const elementsInfo = await page.evaluate(() => {
      const all = document.querySelectorAll('*');
      const results = [];
      all.forEach(el => {
        // Look for any elements with text resembling a number/balance
        if (el.children.length === 0 && el.textContent) {
          const txt = el.textContent.trim();
          if (/\d+/.test(txt) && txt.length < 30) {
            results.push({
              tag: el.tagName,
              className: el.className,
              id: el.id,
              text: txt,
              parentClass: el.parentElement ? el.parentElement.className : ''
            });
          }
        }
      });
      return results;
    });

    console.log('Found elements with numbers (first 50):');
    console.log(JSON.stringify(elementsInfo.slice(0, 50), null, 2));

    await browser.close();
  } catch (err) {
    console.error('Error:', err);
  }
}

main();
