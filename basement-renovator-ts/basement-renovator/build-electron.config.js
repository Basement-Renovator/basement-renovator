module.exports = {
    mainEntry: 'src-main/index.ts',
    preloadEntry: 'src-preload/index.ts',
    outDir: 'public',
    mainTarget: 'electron16.0-main',
    preloadTarget: 'electron16.0-preload',
    customConfig: {
        experiments: {
            topLevelAwait: true,
        },
        module: {
            rules: [
                {
                    test: /\.tsx?$/,
                    loader: 'ts-loader',
                    options: {},
                },
                {
                    test: /\.node$/,
                    loader: 'node-loader',
                    options: {},
                },
            ],
        },
        resolve: {
            extensions: ['.tsx', '.ts', '.jsx', '.js'],
            fallback: {
                fs: false,
                path: false
            }
        },
    },
};