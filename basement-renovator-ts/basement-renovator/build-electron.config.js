module.exports = {
    mainEntry: 'src-main/index.ts',
    preloadEntry: 'src-preload/index.ts',
    outDir: 'public',
    mainTarget: 'electron18.0-main',
    preloadTarget: 'electron18.0-preload',
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
        },
    },
};