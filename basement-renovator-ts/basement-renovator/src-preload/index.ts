import { contextBridge, ipcRenderer } from 'electron';

window.addEventListener('DOMContentLoaded', () => {
    console.log('PRELOAD');
});

contextBridge.exposeInMainWorld("electronAPI", {
    setTitle: (title: string) => ipcRenderer.send('set-title', title),
    close:    () => ipcRenderer.send('close'),
    minimize: () => ipcRenderer.send('minimize'),
    restore:  () => ipcRenderer.send('restore'),
    maximize: () => ipcRenderer.send('maximize'),
    isMaximized: (): Promise<boolean> => ipcRenderer.invoke('isMaximimzed'),
});