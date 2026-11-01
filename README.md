# Olymp Trade CLI Trading Bot

This repository contains the CLI trading bot and its associated tools, as well as the Olymp Trade WebSocket API Python library.

## Project Structure

- `src/` - Source code for the TypeScript CLI Bot:
  - `src/cli.ts` - The main CLI bot script.
  - `src/login.ts` - Headless Chromium login script to retrieve API tokens.
  - `src/indicators.ts` - Technical analysis indicators (ZLEMA, momentum, etc.).
  - `src/types.ts` - TypeScript type definitions.
- `OlympTradeAPI/` - Python client library for Olymp Trade API.
- `debug/` - Automated Puppeteer DOM/GPU inspection scripts.

## Installation

1. Install the required Node.js dependencies:
   ```bash
   npm install
   ```

## Usage

### 1. Headless Authentication
To login to Olymp Trade and save the access credentials/token:
```bash
npm run login
```
This script runs a headless browser to perform anti-detection authentication, saving the authentication token to `access_token.txt`.

### 2. Run the CLI Bot
To run the CLI bot in real-time execution mode:
```bash
npm run cli
```

### 3. Check / Typecheck Code
To run TypeScript compiler checks:
```bash
npm run lint
```

