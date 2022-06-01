import pathlib from 'path';
import * as fileutil from './fileutil';
import { printf } from './util';

// each mod has an image manager
export class ImageManager {
    imagePaths: Record<string, Promise<string | undefined>> = {};
    resourcePath: string;

    static DEFAULT_IMAGE = "resources/Entities/questionmark.png";

    constructor(resourcePath: string) {
        this.resourcePath = resourcePath;
    }

    async waitAll(): Promise<void> {
        await Promise.allSettled(Object.values(this.imagePaths));
    }

    register(path: string, checkFile = true): Promise<string | undefined> {
        if (!(path in this.imagePaths)) {
            this.imagePaths[path] = this.#getImagePath(path, checkFile);
        }
        return this.imagePaths[path];
    }

    async #getImagePath(path: string, checkFile: boolean): Promise<string | undefined> {
        if (!path) {
            return undefined;
        }

        const imagePath = await fileutil.massageOSPath(pathlib.join(this.resourcePath, path));

        if (!imagePath || (checkFile && !(await fileutil.stat(imagePath)).isFile())) {
            return undefined;
        }

        return imagePath;
    }
}