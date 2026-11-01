import puppeteer from 'puppeteer-core';

async function main() {
  console.log('Launching browser to inspect DOM...');
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

    console.log('Waiting 10 seconds...');
    await new Promise(r => setTimeout(r, 10000));

    const domInfo = await page.evaluate(() => {
      const inputs = Array.from(document.querySelectorAll('input')).map(i => ({
        tag: 'INPUT',
        type: i.type,
        value: i.value,
        placeholder: i.placeholder,
        className: i.className,
        id: i.id,
        rect: i.getBoundingClientRect().toJSON()
      }));

      const currencyElements = [];
      const all = document.querySelectorAll('*');
      all.forEach(el => {
        // Look for leaf elements containing Đ or currency
        if (el.children.length === 0 && el.textContent) {
          const txt = el.textContent.trim();
          if (txt.includes('Đ') || txt.includes('$') || txt.includes('demo') || txt.includes('Conta')) {
            currencyElements.push({
              tag: el.tagName,
              className: el.className,
              id: el.id,
              text: txt,
              parentTag: el.parentElement?.tagName,
              parentClass: el.parentElement?.className,
              rect: el.getBoundingClientRect().toJSON()
            });
          }
        }
      });

      return { inputs, currencyElements };
    });

    console.log('=== INPUT ELEMENTS ===');
    console.log(JSON.stringify(domInfo.inputs, null, 2));
    console.log('\n=== CURRENCY/DEMO ELEMENTS ===');
    console.log(JSON.stringify(domInfo.currencyElements, null, 2));

    await browser.close();
  } catch (err) {
    console.error('Error:', err);
  }
}

main();
