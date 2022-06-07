import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './samples/electron-store';
import './samples/preload-module';
import './styles/index.css';

import type { RoomFile } from 'packages/common/core';

console.log('RENDERER');

(async () => {
    await window.resourceLoadP();

    const root = createRoot(document.getElementById('root')!);

    function render(rooms?: RoomFile) {
        root.render(<StrictMode>
            <App rooms={rooms} />
        </StrictMode>);
    };
    render();

    window.ipcRenderer.on('file-open', (_event, { path, rooms }: {
        path: string;
        rooms: RoomFile;
    }) => {
        console.log('Opening:', path);
        // TODO: replace with a more targeted re-render/config update so the whole palette doesn't refresh
        render(rooms);
    });

    window.removeLoading();
})();
