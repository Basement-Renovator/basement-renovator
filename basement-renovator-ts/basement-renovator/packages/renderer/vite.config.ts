import pathlib from 'path';
import { builtinModules } from 'module';
import * as vite from 'vite';
import react from '@vitejs/plugin-react';
import optimizer from 'vite-plugin-optimizer';
import resolve from 'vite-plugin-resolve';
import pkg from '../../package.json';
import fs from 'fs';

const moduleSrc = (f: string) => (() => fs.promises.readFile(pathlib.join(__dirname, `modules/${f}`), 'utf-8'));

/**
 * @see https://vitejs.dev/config/
 */
export default vite.defineConfig({
    mode: process.env.NODE_ENV,
    root: __dirname,
    publicDir: '../..',
    plugins: [
        react(),
        electron(),
        resolve({
            /**
             * Here you resolve some CommonJs module.
             * Or some Node.js native modules they may not be built correctly by vite.
             * At the same time, these modules should be put in `dependencies`,
             * because they will not be built by vite, but will be packaged into `app.asar` by electron-builder
             */
            // ESM format code snippets
            'electron-store': moduleSrc('electron-store.js'),
            // Node.js native module
            serialport: moduleSrc('serialport.js'),
            sharp: moduleSrc('sharp.js'),
        }),
    ],
    base: './',
    build: {
        outDir: '../../dist/renderer',
        emptyOutDir: true,
        sourcemap: true,
    },
    resolve: {
        alias: {
            '@': pathlib.join(__dirname, 'src'),
        },
    },
    server: {
        host: pkg.env.VITE_DEV_SERVER_HOST,
        port: pkg.env.VITE_DEV_SERVER_PORT,
    },
})

/**
 * For usage of Electron and NodeJS APIs in the Renderer process
 * @see https://github.com/caoxiemeihao/electron-vue-vite/issues/52
 */
export function electron(
    entries: Parameters<typeof optimizer>[0] = {}
): vite.Plugin {
    const builtins = builtinModules.filter((t) => !t.startsWith('_'));

    /**
     * @see https://github.com/caoxiemeihao/vite-plugins/tree/main/packages/resolve#readme
     */
    return optimizer({
        electron: moduleSrc('electron.js'),
        ...builtinModulesExport(builtins),
        ...entries,
    });

    function builtinModulesExport(modules: string[]) {
        return modules
            .map((moduleId) => {
                const nodeModule = require(moduleId);

                const nodeModuleCode = `
const M = require("${moduleId}");

export default M;

${Object.keys(nodeModule)
    .map((attr) => `export const ${attr} = M.${attr};`)
    .join('\n')}
`;

                return { [moduleId]: nodeModuleCode };
            })
            .reduce((memo, item) => Object.assign(memo, item), {});
    }
}
