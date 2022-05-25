import pathlib from 'path';
import { builtinModules } from 'module';
import * as vite from 'vite';
import pkg from '../../package.json';

export default vite.defineConfig({
    root: __dirname,
    build: {
        outDir: '../../dist/preload',
        emptyOutDir: true,
        minify: process.env.NODE_ENV === 'production', // from mode option
        // https://github.com/caoxiemeihao/electron-vue-vite/issues/61
        sourcemap: 'inline',
        rollupOptions: {
            input: {
                // multiple entry
                index: pathlib.join(__dirname, 'index.tsx'),
            },
            output: {
                format: 'cjs',
                entryFileNames: '[name].cjs',
                manualChunks: {},
            },
            external: [
                'electron',
                ...builtinModules,
                ...Object.keys(pkg.dependencies ?? {}),
            ],
        },
    },
})
