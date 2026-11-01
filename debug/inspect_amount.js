import puppeteer from 'puppeteer-core';

async function main() {
  console.log('Launching browser to inspect amount field...');
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

    console.log('Waiting 8 seconds for page content...');
    await new Promise(r => setTimeout(r, 8000));

    // Inspect elements with '40' or classes related to amount/deal
    const amountElements = await page.evaluate(() => {
      const results = [];
      const all = document.querySelectorAll('*');
      all.forEach(el => {
        const text = el.textContent || '';
        const isTarget = text.includes('40') || el.className?.includes('amount') || el.id?.includes('amount');
        if (isTarget && el.children.length <= 3) {
          results.push({
            tag: el.tagName,
            className: el.className,
            id: el.id,
            text: text.trim(),
            html: el.outerHTML.substring(0, 300),
            attributes: Array.from(el.attributes).map(a => `${a.name}="${a.value}"`)
          });
        }
      });
      return results;
    });

    console.log('--- AMOUNT RELATED ELEMENTS ---');
    console.log(JSON.stringify(amountElements, null, 2));
    console.log('-------------------------------');

    await browser.close();
  } catch (err) {
    console.error('Error:', err);
  }
}

main();
