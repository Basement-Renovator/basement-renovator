import 'source-map-support/register';

import path from 'path';

import { app, BrowserWindow, ipcMain } from 'electron';
import isDev from 'electron-is-dev';

async function createWindow() {
    const win = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
        },
    });

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

    console.log('BROWSER');

    win.loadURL(isDev ? 'http://localhost:3000' : `file://${path.join(__dirname, '../build/index.html')}`);
}

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});

await app.whenReady();

createWindow();

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
})