/**
 * Right Click AI — Electron Main Process
 * 
 * Manages system tray, global hotkeys, window creation,
 * and clipboard reading for the AI assistant.
 */

const {
  app,
  BrowserWindow,
  Tray,
  Menu,
  globalShortcut,
  clipboard,
  nativeImage,
  ipcMain,
  screen,
  shell,
} = require('electron');
const path = require('path');
const { spawn } = require('child_process');

// --- State ---
let tray = null;
let popupWindow = null;
let resultWindow = null;
let settingsWindow = null;
let backendProcess = null;
let isQuitting = false;

const BACKEND_URL = 'http://127.0.0.1:8765';
const DEFAULT_HOTKEY = 'CommandOrControl+Shift+Q';

// --- Single Instance Lock ---
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
}

app.on('second-instance', () => {
  // If user tries to open again, show settings
  createSettingsWindow();
});

// --- App Lifecycle ---
app.whenReady().then(async () => {
  // Start Python backend
  startBackend();

  // Wait for backend to be ready
  await waitForBackend(15000);

  // Create system tray
  createTray();

  // Register global hotkey
  registerHotkey(DEFAULT_HOTKEY);

  // IPC handlers
  setupIPC();
  
  // Show settings on first launch so user can configure API keys
  createSettingsWindow();
});

app.on('will-quit', () => {
  isQuitting = true;
  globalShortcut.unregisterAll();
  stopBackend();
});

app.on('window-all-closed', (e) => {
  // Don't quit when all windows are closed — we live in the tray
  e.preventDefault?.();
});

// --- Backend Management ---
function startBackend() {
  // Check if backend is already running (e.g., started by start.bat)
  const http = require('http');
  const checkReq = http.get(`${BACKEND_URL}/health`, (res) => {
    if (res.statusCode === 200) {
      console.log('[Backend] Already running externally, skipping spawn.');
      return;
    }
  });
  checkReq.on('error', () => {
    // Not running, start it ourselves
    spawnBackend();
  });
  checkReq.setTimeout(1000, () => {
    checkReq.destroy();
    spawnBackend();
  });
}

function spawnBackend() {
  const backendDir = path.join(__dirname, '..', 'backend');
  const pythonExe = process.platform === 'win32' 
    ? path.join(backendDir, 'venv', 'Scripts', 'python.exe')
    : path.join(backendDir, 'venv', 'bin', 'python');

  console.log('[Backend] Starting Python backend...');

  backendProcess = spawn(pythonExe, ['main.py'], {
    cwd: backendDir,
    stdio: ['pipe', 'pipe', 'pipe'],
    env: { ...process.env },
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`[Backend] Process exited with code ${code}`);
    if (!isQuitting && code !== 0) {
      console.log('[Backend] Restarting in 3s...');
      setTimeout(startBackend, 3000);
    }
  });
}

function stopBackend() {
  if (backendProcess) {
    console.log('[Backend] Stopping...');
    backendProcess.kill();
    backendProcess = null;
  }
}

async function waitForBackend(timeoutMs = 15000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const http = require('http');
      await new Promise((resolve, reject) => {
        const req = http.get(`${BACKEND_URL}/health`, (res) => {
          if (res.statusCode === 200) resolve();
          else reject(new Error(`Status: ${res.statusCode}`));
        });
        req.on('error', reject);
        req.setTimeout(1000, () => { req.destroy(); reject(new Error('Timeout')); });
      });
      console.log('[Backend] Ready!');
      return true;
    } catch {
      await new Promise(r => setTimeout(r, 500));
    }
  }
  console.warn('[Backend] Timeout waiting for backend');
  return false;
}

// --- Tray ---
function createTray() {
  // Create a simple tray icon
  const iconPath = path.join(__dirname, 'assets', 'icon.png');
  let trayIcon;

  try {
    trayIcon = nativeImage.createFromPath(iconPath);
    trayIcon = trayIcon.resize({ width: 16, height: 16 });
  } catch {
    // Fallback: create a simple colored icon
    trayIcon = createDefaultIcon();
  }

  tray = new Tray(trayIcon);
  tray.setToolTip('Right Click AI — Ctrl+Shift+Q');

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '🧠 Right Click AI',
      enabled: false,
    },
    { type: 'separator' },
    {
      label: '⚙️ Settings',
      click: () => createSettingsWindow(),
    },
    {
      label: '🔄 Restart Backend',
      click: () => {
        stopBackend();
        startBackend();
      },
    },
    { type: 'separator' },
    {
      label: '❌ Quit',
      click: () => {
        isQuitting = true;
        app.quit();
      },
    },
  ]);

  tray.setContextMenu(contextMenu);

  tray.on('double-click', () => {
    createSettingsWindow();
  });
}

function createDefaultIcon() {
  // Create a 16x16 purple icon as fallback
  const canvas = Buffer.alloc(16 * 16 * 4);
  for (let i = 0; i < 16 * 16; i++) {
    canvas[i * 4] = 139;     // R
    canvas[i * 4 + 1] = 92;  // G
    canvas[i * 4 + 2] = 246; // B
    canvas[i * 4 + 3] = 255; // A
  }
  return nativeImage.createFromBuffer(canvas, { width: 16, height: 16 });
}

// --- Global Hotkey ---
function registerHotkey(hotkey) {
  try {
    globalShortcut.unregisterAll();
    const success = globalShortcut.register(hotkey, () => {
      onHotkeyPressed();
    });
    if (success) {
      console.log(`[Hotkey] Registered: ${hotkey}`);
    } else {
      console.error(`[Hotkey] Failed to register: ${hotkey}`);
    }
  } catch (err) {
    console.error(`[Hotkey] Error: ${err.message}`);
  }
}

// --- Hotkey Action ---
async function onHotkeyPressed() {
  console.log('[Hotkey] Triggered!');

  // Close existing popup if open
  if (popupWindow && !popupWindow.isDestroyed()) {
    popupWindow.close();
    popupWindow = null;
    return; // Toggle behavior
  }

  // Read clipboard
  const text = clipboard.readText() || '';
  const image = clipboard.readImage();
  const hasImage = !image.isEmpty();

  let imageBase64 = null;
  let imageMimeType = null;
  if (hasImage) {
    imageBase64 = image.toPNG().toString('base64');
    imageMimeType = 'image/png';
  }

  if (!text.trim() && !hasImage) {
    console.log('[Hotkey] Clipboard empty, ignoring');
    return;
  }

  // Get cursor position
  const cursorPoint = screen.getCursorScreenPoint();
  const display = screen.getDisplayNearestPoint(cursorPoint);

  // Calculate popup position (near cursor, but within screen bounds)
  const popupWidth = 320;
  const popupHeight = 420;

  let x = cursorPoint.x - 10;
  let y = cursorPoint.y + 10;

  // Keep within screen bounds
  const bounds = display.workArea;
  if (x + popupWidth > bounds.x + bounds.width) {
    x = bounds.x + bounds.width - popupWidth - 10;
  }
  if (y + popupHeight > bounds.y + bounds.height) {
    y = cursorPoint.y - popupHeight - 10;
  }
  if (x < bounds.x) x = bounds.x + 10;
  if (y < bounds.y) y = bounds.y + 10;

  // Create popup window
  popupWindow = new BrowserWindow({
    width: popupWidth,
    height: popupHeight,
    x: Math.round(x),
    y: Math.round(y),
    frame: false,
    transparent: true,
    resizable: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  popupWindow.loadFile(path.join(__dirname, 'src', 'pages', 'popup.html'));

  popupWindow.once('ready-to-show', () => {
    popupWindow.show();
    popupWindow.focus();
    // Send clipboard data to renderer
    popupWindow.webContents.send('clipboard-data', {
      text,
      imageBase64,
      imageMimeType,
      hasImage,
    });
  });

  // Close popup when it loses focus
  popupWindow.on('blur', () => {
    if (popupWindow && !popupWindow.isDestroyed()) {
      // Small delay to allow clicking on result window
      setTimeout(() => {
        if (popupWindow && !popupWindow.isDestroyed() && !popupWindow.isFocused()) {
          popupWindow.close();
        }
      }, 200);
    }
  });

  popupWindow.on('closed', () => {
    popupWindow = null;
  });
}

// --- Result Window ---
function createResultWindow(actionData) {
  // Close existing popup
  if (popupWindow && !popupWindow.isDestroyed()) {
    popupWindow.close();
  }

  const cursorPoint = screen.getCursorScreenPoint();
  const display = screen.getDisplayNearestPoint(cursorPoint);

  const resultWidth = 480;
  const resultHeight = 400;

  let x = cursorPoint.x - resultWidth / 2;
  let y = cursorPoint.y + 20;

  const bounds = display.workArea;
  if (x + resultWidth > bounds.x + bounds.width) x = bounds.x + bounds.width - resultWidth - 10;
  if (y + resultHeight > bounds.y + bounds.height) y = cursorPoint.y - resultHeight - 20;
  if (x < bounds.x) x = bounds.x + 10;
  if (y < bounds.y) y = bounds.y + 10;

  // Close existing result window
  if (resultWindow && !resultWindow.isDestroyed()) {
    resultWindow.close();
  }

  resultWindow = new BrowserWindow({
    width: resultWidth,
    height: resultHeight,
    x: Math.round(x),
    y: Math.round(y),
    frame: false,
    transparent: true,
    resizable: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    minWidth: 300,
    minHeight: 200,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  resultWindow.loadFile(path.join(__dirname, 'src', 'pages', 'result.html'));

  resultWindow.once('ready-to-show', () => {
    resultWindow.show();
    resultWindow.focus();
    resultWindow.webContents.send('action-data', actionData);
  });

  resultWindow.on('closed', () => {
    resultWindow = null;
  });
}

// --- Settings Window ---
function createSettingsWindow() {
  if (settingsWindow && !settingsWindow.isDestroyed()) {
    settingsWindow.focus();
    return;
  }

  settingsWindow = new BrowserWindow({
    width: 900,
    height: 650,
    frame: false,
    transparent: false,
    resizable: true,
    show: false,
    backgroundColor: '#0f0f1a',
    minWidth: 700,
    minHeight: 500,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  settingsWindow.loadFile(path.join(__dirname, 'src', 'pages', 'settings.html'));

  settingsWindow.once('ready-to-show', () => {
    settingsWindow.show();
    settingsWindow.focus();
  });

  settingsWindow.on('closed', () => {
    settingsWindow = null;
  });
}

// --- IPC Handlers ---
function setupIPC() {
  // Execute AI action
  ipcMain.on('execute-action', (event, actionData) => {
    createResultWindow(actionData);
  });

  // Copy to clipboard
  ipcMain.on('copy-to-clipboard', (event, text) => {
    clipboard.writeText(text);
  });

  // Close window
  ipcMain.on('close-window', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) win.close();
  });

  // Minimize window
  ipcMain.on('minimize-window', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) win.minimize();
  });

  // Open settings
  ipcMain.on('open-settings', () => {
    createSettingsWindow();
  });

  // Get backend URL
  ipcMain.handle('get-backend-url', () => {
    return BACKEND_URL;
  });

  // Pin/unpin window
  ipcMain.on('toggle-pin', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win) {
      const isOnTop = win.isAlwaysOnTop();
      win.setAlwaysOnTop(!isOnTop);
      event.reply('pin-state', !isOnTop);
    }
  });

  // Update hotkey
  ipcMain.on('update-hotkey', (event, newHotkey) => {
    registerHotkey(newHotkey);
  });
}
