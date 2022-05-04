import assert from 'assert';
import { printf } from './util';

export type FormatNode = {
    attrib: {
        type: string;
        len?: number | string;
        encoding?: BufferEncoding;
    };
    innerText?: string;
} & {
    [name: string]: Array<FormatNode>;
};

export type FormatXml = {
    format: FormatNode[];
};

type DecodeType = (buff: Buffer, offset: number, len: number, encoding?: BufferEncoding) => unknown;

export type FormatEntry = {
    type: string;
    len: (buff: Buffer) => number;
    value: DecodeType;
    offset: number;
    encoding?: BufferEncoding;
};

function tagInnerTextParser(text: string | undefined): string | number | undefined {
    if (text === undefined) {
        return undefined;
    }

    const num = text.includes('.') ? parseFloat(text) : parseInt(text);
    if (Number.isNaN(num)) {
        return text;
    }
    return num;
}

function toInt(buffer: Buffer, signed: boolean): number {
    let bytes = buffer.toString('binary');

    // if signed, parse out sign byte first
    let sign = 1;
    if (signed) {
        sign = bytes[0] === '1' ? -1 : 1;
        bytes = bytes.slice(1);
    }

    return parseInt(bytes, 2) * sign;
}

const PresetTypes: Record<string, DecodeType> = {
    signed:   (buff, offset, len) => toInt(buff.subarray(offset, offset + len), true),
    unsigned: (buff, offset, len) => toInt(buff.subarray(offset, offset + len), false),
    floating: (buff, offset, len) => {
        assert(len === 4 || len === 8);
        if (len === 4) {
            return buff.readFloatLE(offset);
        }
        return buff.readDoubleLE(offset);
    },
    boolean: (buff, offset, len) => toInt(buff.subarray(offset, offset + len), false) !== 0,
    character: (buff, offset, len, encoding) => buff.toString(encoding ?? 'utf8', offset, offset + len)
};

function xmlToFormat({
    node,
    parsedFormat = {},
}: {
    node: FormatNode;
    parsedFormat: Record<string, FormatEntry>;
}): FormatEntry {
    const tag = Object.keys(node)[0];
    const { type, len = 1, encoding } = node.attrib;

    const result = {
        type: tag,
        offset: 0,
        encoding,
    } as FormatEntry;

    if (typeof len === 'string') {
        result.len = (buff) => {
            const fmt = parsedFormat[len];
            const val = fmt.value(buff, fmt.offset, fmt.len(buff));
            assert(typeof val === 'number');
            return val;
        };
    }
    else {
        result.len = () => len;
    }

    const constant = tagInnerTextParser(node.innerText);
    if (constant !== undefined) {
        result.value = (buff, offset, len) => {
            const fmt = parsedFormat[type];
            const val = fmt.value(buff, offset, len);
            if (len > 0) { // for constants configured in xml with no concrete equivalent
                assert(constant === val);
            }
            return constant;
        };
    }
    else if (type in PresetTypes) {
        result.value = PresetTypes[type];
    }
    else {
        result.value = (buffer, offset, len) => {
            const obj: Record<string, unknown> = {};
            const parsed = Object.assign({}, parsedFormat);
            for (let i = 0; i < len; ++i) {
                for (const subTag of node[tag]) {
                    const format = xmlToFormat({
                        node: subTag,
                        parsedFormat: parsed
                    });
                    format.offset = offset;
                    parsed[format.type] = format;

                    const fmtlen = format.len(buffer);
                    obj[format.type] = format.value(buffer, offset, fmtlen, format.encoding);
                    offset += fmtlen;
                }
            }
            return obj;
        };
    }

    return result;
}

export function parseFormatXml(root: FormatXml): Record<string, FormatEntry> {
    const parsedFormat: Record<string, FormatEntry> = {};
    for (const node of Object.values(root)[0]) {
        const format = xmlToFormat({ node, parsedFormat });
        parsedFormat[format.type] = format;
    }
    return parsedFormat;
}

export function tryParseBuffer<T>(format: FormatEntry, buffer: Buffer): T | undefined {
    try {
        return format.value(buffer, 0, format.len(buffer), format.encoding) as T;
    }
    catch (e) {
        printf('Failed to parse format', format.type, e);
        return undefined;
    }
}