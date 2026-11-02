const {defineConfig}=require('@playwright/test');
module.exports=defineConfig({
  testDir:'.',
  testMatch:['browser-smoke.spec.cjs','pwa.spec.cjs'],
  timeout:30000,
  retries:1,
  workers:1,
  reporter:'list',
  use:{
    baseURL:'http://127.0.0.1:8765',
    browserName:process.env.BROWSER_NAME||'chromium',
    screenshot:'only-on-failure',
    trace:'retain-on-failure'
  },
  webServer:{
    command:'python3 -m http.server 8765 --bind 127.0.0.1',
    cwd:require('node:path').resolve(__dirname,'..'),
    url:'http://127.0.0.1:8765',
    reuseExistingServer:!process.env.CI,
    timeout:30000
  }
});
