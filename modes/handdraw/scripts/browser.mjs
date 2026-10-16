import {existsSync} from 'node:fs';
import path from 'node:path';

export function browserExecutable() {
  if (process.env.REMOTION_BROWSER_EXECUTABLE) return process.env.REMOTION_BROWSER_EXECUTABLE;
  const candidates = process.platform === 'win32'
    ? [process.env.PROGRAMFILES, process.env['PROGRAMFILES(X86)'], process.env.LOCALAPPDATA].filter(Boolean)
      .flatMap(base => ['BraveSoftware/Brave-Browser/Application/brave.exe', 'Google/Chrome/Application/chrome.exe', 'Microsoft/Edge/Application/msedge.exe'].map(file => path.join(base, file)))
    : ['/Applications/Brave Browser.app/Contents/MacOS/Brave Browser', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/google-chrome', '/usr/bin/chromium'];
  const executable = candidates.find(existsSync);
  if (!executable) throw new Error('请安装 Chrome / Brave，或设置 REMOTION_BROWSER_EXECUTABLE。');
  return executable;
}
