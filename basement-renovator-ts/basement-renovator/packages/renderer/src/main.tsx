import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './samples/electron-store';
import './samples/preload-module';
import './styles/index.css';

console.log('RENDERER');

(async () => {
    await window.resourceLoadP();

    const root = createRoot(document.getElementById('root')!);
    root.render(<StrictMode>
        <App />
    </StrictMode>);

    window.removeLoading();
})();
