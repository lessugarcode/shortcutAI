/**
 * shortcutAI — Preload Script
 * Exposes safe IPC bridge to renderer processes.
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('rightClickAI', {
  // Backend communication
  getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),
  getAuthToken: () => ipcRenderer.invoke('get-auth-token'),

  // Window actions
  closeWindow: () => ipcRenderer.send('close-window'),
  minimizeWindow: () => ipcRenderer.send('minimize-window'),
  togglePin: () => ipcRenderer.send('toggle-pin'),
  openSettings: () => ipcRenderer.send('open-settings'),

  // Clipboard
  copyToClipboard: (text) => ipcRenderer.send('copy-to-clipboard', text),
  pasteToActiveWindow: () => ipcRenderer.send('paste-to-active-window'),

  // AI actions
  executeAction: (actionData) => ipcRenderer.send('execute-action', actionData),

  // Settings
  updateHotkey: (hotkey) => ipcRenderer.send('update-hotkey', hotkey),
  getAutoPaste: () => ipcRenderer.invoke('get-auto-paste'),

  // File dialog
  saveFileDialog: (opts) => ipcRenderer.invoke('save-file-dialog', opts),

  // Event listeners
  onClipboardData: (callback) => {
    ipcRenderer.on('clipboard-data', (event, data) => callback(data));
  },
  onActionData: (callback) => {
    ipcRenderer.on('action-data', (event, data) => callback(data));
  },
  onPinState: (callback) => {
    ipcRenderer.on('pin-state', (event, isPinned) => callback(isPinned));
  },
});
