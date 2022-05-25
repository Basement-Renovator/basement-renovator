import { app, BrowserWindow, ipcMain, shell } from 'electron';
import * as os from 'os';
import pathlib from 'path';
import './samples/electron-store';
import './samples/npm-esm-packages';

// Disable GPU Acceleration for Windows 7
if (os.release().startsWith('6.1')) app.disableHardwareAcceleration();

// Set application name for Windows 10+ notifications
if (process.platform === 'win32') app.setAppUserModelId(app.getName());

let win: BrowserWindow | null = null;

async function createWindow() {
    win = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            preload: pathlib.join(__dirname, '../preload/index.cjs')
        },
    });

    console.log('BROWSER');

    function getWin(event: Electron.IpcMainEvent | Electron.IpcMainInvokeEvent) {
        const webContents = event.sender;
        return BrowserWindow.fromWebContents(webContents);
    }

    ipcMain.on('set-title', (event, title) => getWin(event)?.setTitle(title));
    ipcMain.on('close',     (event) => getWin(event)?.close());
    ipcMain.on('minimize',  (event) => getWin(event)?.minimize());
    ipcMain.on('maximize',  (event) => getWin(event)?.maximize());
    ipcMain.on('restore',   (event) => getWin(event)?.restore());
    ipcMain.handle('isMaximized', (event) => getWin(event)?.isMaximized);

    if (app.isPackaged) {
        win.loadFile(pathlib.join(__dirname, '../renderer/index.html'));
    }
    else {
        // 🚧 Use ['ENV_NAME'] avoid vite:define plugin
        const {
            VITE_DEV_SERVER_HOST: host,
            VITE_DEV_SERVER_PORT: port,
        } = process.env;

        const url = `http://${host}:${port}`;
        win.loadURL(url);
        win.webContents.openDevTools();
    }

    // Test active push message to Renderer-process
    win.webContents.on('did-finish-load', () => {
        win?.webContents.send('main-process-message', new Date().toLocaleString());
    });

    // Make all links open with the browser, not with the application
    win.webContents.setWindowOpenHandler(({ url }) => {
        if (url.startsWith('http')) shell.openExternal(url);
        return { action: 'deny' };
    })
}

app.on('window-all-closed', () => {
    win = null;
    if (process.platform !== 'darwin') app.quit();
});

(async () => {
    await app.whenReady();
    createWindow();
})();

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
})