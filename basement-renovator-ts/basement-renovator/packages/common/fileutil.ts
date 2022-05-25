import { promises as fs } from 'fs';
import pathlib from 'path';


/**
 * Performs certain linux-friendly file path transforms:
 * - converts \ to /
 * - validates the parent directory exists and is a directory
 * - do a case insensitive search for the filename in the directory, return if found
 *   - this helps open case-sensitive files on linux
 */
export async function massageOSPath(path: string): Promise<string | undefined> {
    path = path.replace("\\", "/");
    path = pathlib.normalize(path);

    const { dir: directory, base: file } = pathlib.parse(path);

    if (!(await stat(directory)).isDir()) {
        return undefined;
    }

    for await (const item of dirIter(directory)) {
        if (item.name.toLowerCase() === file.toLowerCase()) {
            return pathlib.normalize(pathlib.join(directory, item.name));
        }
    }

    return path;
}

export function with_suffix(path: string, ext: string): string {
    return pathlib.format(
        Object.assign(pathlib.parse(path), { ext })
    );
}

type StatEntry = {
    isFile: () => boolean;
    isDir: () => boolean;
    lastAccessed: Date;
    lastModified: Date;
    created: Date;
};

export async function stat(path: string): Promise<StatEntry> {
    const stat = await fs.stat(path);
    return {
        isFile: () => stat.isFile(),
        isDir: () => stat.isDirectory(),
        get lastAccessed() { return stat.atime; },
        get lastModified() { return stat.mtime; },
        get created() { return stat.birthtime; },
    };
}

type DirEntry = {
    name: string;
    isFile: () => boolean;
    isDir: () => boolean;
};

export async function* dirIter(directory: string): AsyncGenerator<DirEntry, void> {
    const dir = await fs.opendir(directory);
    try {
        for await (const item of dir) {
            yield {
                get name() { return item.name; },
                isFile: () => item.isFile(),
                isDir: () => item.isDirectory(),
            };
        }
    }
    finally {
        // if the dir handle is already closed this throws
        try { await dir.close(); }
        catch {}
    }
}

export async function readBinary(path: string): Promise<Buffer> {
    const res = await fs.readFile(path);
    return res;
}

export async function read(path: string, encoding: BufferEncoding = 'utf8'): Promise<string> {
    const res = await fs.readFile(path, { encoding });
    return res;
}

// creates file if it doesn't exist
export async function write(path: string, data: string | Buffer, options: Partial<{
    encoding: BufferEncoding;
    truncate: boolean;
}> = {}): Promise<void> {
    await fs.writeFile(path, data, {
        encoding: options.encoding,
        flag: options.truncate ? 'w' : 'a'
    });
}

export async function ensureDir(path: string, recursive = true): Promise<void> {
    await fs.mkdir(path, { recursive });
}

export async function copy(src: string, dest: string): Promise<void> {
    await fs.cp(src, dest, {
        recursive: true,
        force: true,
    });
}

export async function remove(path: string): Promise<void> {
    await fs.rm(path, {
        recursive: true,
        force: true,
    });
}