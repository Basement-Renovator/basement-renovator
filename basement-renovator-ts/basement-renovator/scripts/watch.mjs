import { spawn } from 'child_process';
import * as vite from 'vite';
import electron from 'electron';

const query = new URLSearchParams(import.meta.url.split('?')[1]);
const debug = query.has('debug');

/**
 * @type {(server: import('vite').ViteDevServer) => Promise<import('rollup').RollupWatcher>}
 */
function watchMain(server) {
    /**
     * @type {import('child_process').ChildProcessWithoutNullStreams | null}
     */
    let electronProcess = null;
    const { address, port } = server.httpServer.address();
    const env = Object.assign(process.env, {
        VITE_DEV_SERVER_HOST: address,
        VITE_DEV_SERVER_PORT: port,
    });
    /**
     * @type {import('vite').Plugin}
     */
    const startElectron = {
        name: 'electron-main-watcher',
        writeBundle() {
            electronProcess?.removeAllListeners();
            electronProcess?.kill();
            electronProcess = spawn(electron, ['.'], { stdio: 'inherit', env });
            electronProcess?.once('exit', process.exit);
        },
    };

    return vite.build({
        configFile: 'packages/main/vite.config.ts',
        plugins: debug ? [] : [ startElectron ],
        mode: 'development',
        build: { watch: {} },
    });
}

/**
 * @type {(server: import('vite').ViteDevServer) => Promise<import('rollup').RollupWatcher>}
 */
function watchPreload(server) {
    /**
     * @type {import('vite').Plugin}
     */
    const startElectron = {
        name: 'electron-preload-watcher',
        writeBundle() {
            server.ws.send({ type: 'full-reload' });
        },
    };

    return vite.build({
        configFile: 'packages/preload/vite.config.ts',
        plugins: [ startElectron ],
        mode: 'development',
        build: { watch: {} },
    });
}

// bootstrap
const server = await vite.createServer({
    configFile: 'packages/renderer/vite.config.ts'
});

await server.listen();
await watchPreload(server);
await watchMain(server);
