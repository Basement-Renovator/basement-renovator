import * as vite from 'vite';

await vite.build({ configFile: 'packages/main/vite.config.ts' });
await vite.build({ configFile: 'packages/preload/vite.config.ts' });
await vite.build({ configFile: 'packages/renderer/vite.config.ts' });
