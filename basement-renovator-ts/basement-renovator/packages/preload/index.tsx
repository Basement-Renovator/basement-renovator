import fs from 'fs'
import { contextBridge, ipcRenderer } from 'electron'
import { domReady } from './utils'
import { Loading } from './loading'
import React from "react";
import { createRoot } from 'react-dom/client';
import _ from 'lodash';
import { LookupProvider } from '../common/lookup';
import LoadP from '../main/load-state';
import { withPrototype } from '../common/util';

// --------- Expose APIs to the Renderer process. ---------
contextBridge.exposeInMainWorld('fs', fs);
contextBridge.exposeInMainWorld('ipcRenderer', withPrototype(ipcRenderer));

contextBridge.exposeInMainWorld("electronAPI", {
    setTitle: (title: string) => ipcRenderer.send('set-title', title),
    //close:    () => ipcRenderer.send('close'),
    //minimize: () => ipcRenderer.send('minimize'),
    //restore:  () => ipcRenderer.send('restore'),
    //maximize: () => ipcRenderer.send('maximize'),
    //isMaximized: (): Promise<boolean> => ipcRenderer.invoke('isMaximimzed'),
});

let loadingRoot: ReturnType<typeof createRoot> | undefined;
contextBridge.exposeInMainWorld('removeLoading', () => loadingRoot?.unmount());

contextBridge.exposeInMainWorld('resourceLoadP', async (): Promise<void> => { await LoadP; });
contextBridge.exposeInMainWorld('resources', () => LookupProvider.Main);

(async () => {
    await domReady();

    console.log('PRELOAD');

    loadingRoot = createRoot(document.getElementById('root')!);
    loadingRoot.render(<Loading />);
})();