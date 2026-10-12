// Browser regression against the real HTML and synthetic HTTP responses only.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require('playwright');

(async () => {
  const html = fs.readFileSync(process.env.UI_HTML_PATH || path.join(__dirname, 'static/index.html'));
  const marker = '<img src=x onerror="window.__injected=true">';
  let queries = 0;
  let pendingResponse;
  let response = { answer: marker, sources: [{ source: marker, chunk_id: marker }],
    latency_ms: 1, cost_usd: 0, grounded: true };
  let status = 200;
  const server = http.createServer((req, res) => {
    if (req.url === '/') {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      return res.end(html);
    }
    if (req.url === '/query') {
      queries++;
      req.resume();
      pendingResponse = () => {
        res.writeHead(status, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(response));
      };
      return;
    }
    if (req.url === '/stats') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ total_documents: 1, total_chunks: 1 }));
    }
    res.writeHead(404);
    res.end();
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    await page.setViewportSize({ width: 390, height: 844 });
    const origin = `http://127.0.0.1:${server.address().port}`;
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/*', route => new URL(route.request().url()).origin === origin
      ? route.continue() : route.abort());
    await page.goto(origin);
    const navigation = await page.evaluate(() => {
      const entry = performance.getEntriesByType('navigation')[0];
      return entry && { domInteractive: entry.domInteractive, domComplete: entry.domComplete };
    });
    assert.ok(navigation && Number.isFinite(navigation.domComplete)
      && navigation.domComplete >= navigation.domInteractive, 'Navigation timing is available');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), true,
      'Mobile layout has no horizontal overflow');
    assert.equal(await page.locator('#chat').getAttribute('role'), 'log');
    assert.equal(await page.locator('#chat').getAttribute('aria-live'), 'polite');
    assert.equal(await page.getByLabel('คำถาม').count(), 1, 'Question input has an accessible label');
    await page.locator('#question').fill(marker);
    await page.locator('#send-btn').click();
    await page.waitForFunction(() => document.querySelector('#send-btn').disabled);
    assert.equal(await page.locator('#chat').getAttribute('aria-busy'), 'true');
    assert.equal(await page.locator('.message.user img').count(), 0, 'User input became HTML');
    assert.equal(await page.locator('.message.user .bubble').textContent(), marker);
    await page.locator('#question').fill('second request while waiting');
    await page.locator('#question').press('Enter');
    await page.waitForFunction(() => document.querySelectorAll('.message.user').length === 1);
    // Explicitly flush the fixture after the browser has received the request.
    for (let i = 0; !pendingResponse && i < 100; i++) await new Promise(r => setTimeout(r, 10));
    assert.ok(pendingResponse, 'Query did not reach HTTP fixture');
    pendingResponse();
    await page.waitForFunction(() => !document.querySelector('#send-btn').disabled);
    assert.equal(await page.locator('#chat').getAttribute('aria-busy'), 'false');
    assert.equal(await page.locator('#question').evaluate(node => document.activeElement === node), true,
      'Focus returns to the question field after a response');
    assert.equal(queries, 1, 'Enter bypassed the pending-request guard');
    assert.equal(await page.locator('.message img').count(), 0, 'Answer or source became HTML');
    assert.equal(await page.evaluate(() => window.__injected === true), false);
    assert.ok((await page.locator('.source-item').textContent()).includes(marker));
    await page.locator('details.sources summary').click();
    assert.equal(await page.locator('details.sources').getAttribute('open'), '');

    async function submit(nextResponse, nextStatus = 200) {
      response = nextResponse;
      status = nextStatus;
      pendingResponse = null;
      await page.locator('#question').fill('synthetic question');
      await page.locator('#send-btn').click();
      for (let i = 0; !pendingResponse && i < 100; i++) await new Promise(r => setTimeout(r, 10));
      assert.ok(pendingResponse);
      pendingResponse();
      await page.waitForFunction(() => !document.querySelector('#send-btn').disabled);
      assert.equal(await page.locator('#chat').getAttribute('aria-busy'), 'false');
    }
    await submit({ answer: 'ไม่พบข้อมูลในเอกสาร', sources: [], grounded: false,
                   latency_ms: 1, cost_usd: 0 });
    assert.equal(await page.locator('.message.not-found').count(), 1);
    await submit({ answer: 'Missing optional metrics', sources: null, grounded: true });
    assert.ok((await page.locator('.message.bot').last().textContent()).includes('unavailable'));
    await submit({ detail: marker }, 503);
    assert.ok((await page.locator('.message.bot').last().textContent()).includes(marker));
    assert.equal(await page.locator('.message img').count(), 0);
    assert.equal(await page.locator('#typing-indicator').count(), 0);
    assert.deepEqual(errors, []);
    await page.screenshot({ path: '/tmp/solo-ai-prototype-ui.png', fullPage: true });
    console.log('PASS: user/answer/source/error text safety, pending request guard, citations, no-evidence state, missing metrics, recovery');
  } finally {
    if (browser) await browser.close();
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
