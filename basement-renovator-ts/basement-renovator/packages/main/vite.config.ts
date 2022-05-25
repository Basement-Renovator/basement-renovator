import { builtinModules } from 'module';
import * as vite from 'vite';
import esmodule from 'vite-plugin-esmodule';
import pkg from '../../package.json';

export default vite.defineConfig({
    root: __dirname,
    plugins: [
        esmodule([ 'execa' ]),
    ],
    build: {
        outDir: '../../dist/main',
        emptyOutDir: true,
        minify: process.env.NODE_ENV === 'production', // from mode option
        sourcemap: true,
        lib: {
            entry: 'index.ts',
            formats: ['cjs'],
            fileName: () => '[name].cjs',
        },
        rollupOptions: {
            external: [
                'electron',
                ...builtinModules,
                ...Object.keys(pkg.dependencies ?? {}),
            ],
        },
    },
})
