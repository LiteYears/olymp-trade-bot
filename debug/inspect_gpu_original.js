import puppeteer from 'puppeteer-core';

async function main() {
  console.log('Launching browser with original flags...');
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
        '--enable-webgl2'
      ]
    });

    const page = await browser.newPage();
    console.log('Navigating to chrome://gpu...');
    await page.goto('chrome://gpu', { waitUntil: 'networkidle2' });

    // Wait a bit for status to populate
    await new Promise(r => setTimeout(r, 3000));

    // Extract GPU features status
    const gpuInfo = await page.evaluate(() => {
      const featureList = document.querySelector('.feature-status-list');
      return featureList ? featureList.textContent : 'Feature list not found';
    });

    console.log('--- GPU FEATURE STATUS (ORIGINAL) ---');
    console.log(gpuInfo.trim());
    console.log('--------------------------');

    // Take screenshot of chrome://gpu
    const screenshotPath = '/root/.gemini/antigravity-cli/brain/a1ee9d83-4184-4b53-b31b-6c67b86d4a04/gpu_status_original.png';
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log('GPU status screenshot saved to:', screenshotPath);

    await browser.close();
  } catch (err) {
    console.error('Error:', err);
  }
}

main();
