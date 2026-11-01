import WebSocket from 'ws';
import fs from 'fs';

const TOKEN_PATH = '../access_token.txt';
const token = fs.readFileSync(TOKEN_PATH, 'utf-8').trim();

const wsUri = 'wss://ws.olymptrade.com/otp?cid_ver=1&cid_app=web%40OlympTrade%402026.2.1763569%401763569&cid_device=%40%40phone&cid_os=android%4016';
const headers = {
  'Origin': 'https://olymptrade.com',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
  'Cookie': `access_token=${token}`
};

console.log('Connecting to WebSocket...');
const ws = new WebSocket(wsUri, { headers });

function sendWsMessage(eventCode, data, uuid) {
  const payload = [{
    t: 2,
    e: eventCode,
    d: data,
    uuid: uuid || 'cli_' + Math.floor(Math.random() * 100000)
  }];
  ws.send(JSON.stringify(payload));
}

ws.on('open', () => {
  console.log('WS Open. Sending subscriptions and account requests...');
  
  const subs = [
    [220],
    [110, 700, 112, 140, 1038, 1037, 1039, 22, 26, 111],
    [1054, 1076, 1301, 1097],
    [141, 241],
    [230, 231],
    [126]
  ];
  for (const sub of subs) {
    sendWsMessage(98, sub);
  }

  // Request accounts
  sendWsMessage(1068, [{ group: 'demo' }], 'req-demo');
  sendWsMessage(1068, [{ group: 'real' }], 'req-real');
  sendWsMessage(1068, [{ group: 'real_usdt' }], 'req-real-usdt');
});

ws.on('message', (data) => {
  try {
    const parsed = JSON.parse(data.toString());
    for (const msg of parsed) {
      const e = msg.e;
      // Filter out high-volume events
      if (e !== 110 && e !== 283 && e !== 11 && e !== 1) {
        console.log(`[RECV] Event: ${e}, UUID: ${msg.uuid || 'none'}`);
        console.log(JSON.stringify(msg, null, 2));
      }
    }
  } catch (err) {
    console.error('Error parsing:', err);
  }
});

setTimeout(() => {
  console.log('Closing...');
  ws.close();
}, 10000);
