import fs from 'fs'
import { contextBridge, ipcRenderer } from 'electron'
import { domReady } from './utils'
import { Loading } from './loading'
import React from "react";
import { createRoot } from 'react-dom/client';
import _ from 'lodash';

// `exposeInMainWorld` doesn't detect attributes and methods of a prototype
function withPrototype(obj: Record<string, any>) {
    return _.assignIn(obj, obj);

    //const proto = Object.getPrototypeOf(obj);

    //const protoOnly = _.omitBy(proto, (v, key) => Object.hasOwn(obj, key));

    //for (const [key, value] of Object.entries(protoOnly)) {
    //    if (typeof value === 'function') {
    //        // Some native APIs, like `NodeJS.EventEmitter['on']`, don't work in the Renderer process. Wrapping them into a function.
    //        obj[key] = (...args: any) => value.call(obj, ...args);
    //    }
    //    else {
    //        obj[key] = value;
    //    }
    //}

    //return obj;
}

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

(async () => {
    await domReady();

    console.log('PRELOAD');

    loadingRoot = createRoot(document.getElementById('root')!);
    loadingRoot.render(<Loading />);

    await (await import('./load-state')).default;
})();