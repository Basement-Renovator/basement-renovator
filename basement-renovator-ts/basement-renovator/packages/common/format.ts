import assert from 'assert';
import _ from 'lodash';
import { constrainLiteral, printf } from './util';

export type FormatNode = {
    attrib: {
        type: string;
        len?: number | string;
        encoding?: BufferEncoding;
    };
} & {
    [name: string]: Array<FormatNode> | [{
        innerText: string;
    }];
};

export type FormatXml = {
    format: FormatNode[];
};

type DecodeType<T> = {
    get: (buff: Buffer, offset: number, len: number, encoding?: BufferEncoding) => T;
    set: (buff: Buffer, offset: number, len: number, value: T, encoding?: BufferEncoding) => void;
};

export type FormatEntry = {
    type: string;
    len: (buff: Buffer) => number;
    value: DecodeType<any>;
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

const to2sComp = (val: number, len: number): number => {
    const q = 1 << len - 1;
    return (val + q ^ q);
};

const from2sComp = (val: string): number => {
    const q = 1 << val.length - 1;
    return (+`0b${val}` ^ q) - q;
};

function toInt(buffer: Buffer, signed: boolean): number {
    let bytes = buffer.toString('hex');

    let num = parseInt(bytes, 16);
    if (signed) {
        num = from2sComp(num.toString(2));
    }

    return num;
}

function fromInt(buffer: Buffer, value: number, signed: boolean): string {
    if (signed) {
        value = to2sComp(value, buffer.length);
    }

    return value.toString(2).padStart(buffer.length, '0');
}

const PresetTypes = constrainLiteral<Record<string, DecodeType<any>>>()({
    signed: {
        get: (buff, offset, len) => toInt(buff.subarray(offset, offset + len), true),
        set: (buff, offset, len, value: number) => {
            buff = buff.subarray(offset, offset + len);
            buff.write(fromInt(buff, value, true));
        },
    },
    unsigned: {
        get: (buff, offset, len) => toInt(buff.subarray(offset, offset + len), false),
        set: (buff, offset, len, value: number) => {
            buff = buff.subarray(offset, offset + len);
            buff.write(fromInt(buff, value, true));
        },
    },
    floating: {
        get: (buff, offset, len) => {
            assert(len === 4 || len === 8);
            if (len === 4) {
                return buff.readFloatLE(offset);
            }
            return buff.readDoubleLE(offset);
        },
        set: (buff, offset, len, value: number) => {
            assert(len === 4 || len === 8);
            if (len === 4) {
                buff.writeFloatLE(value, offset);
            }
            else {
                buff.writeDoubleLE(value, offset);
            }
        },
    },
    boolean: {
        get: (buff, offset, len) => toInt(buff.subarray(offset, offset + len), false) !== 0,
        set: (buff, offset, len, value: boolean) => buff.writeInt8(value ? 1 : 0, offset),
    },
    character: {
        get: (buff, offset, len, encoding) => buff.toString(encoding ?? 'utf8', offset, offset + len),
        set: (buff, offset, len, value, encoding) => {
            buff.subarray(offset, len).write(value, encoding);
        }
    },
} as const);

function xmlToFormat({
    node,
    parsedFormat = {},
}: {
    node: FormatNode;
    parsedFormat: Record<string, FormatEntry>;
}): FormatEntry {
    const tag = Object.keys(node)[0];
    const { type, len = 1, encoding } = node.attrib ?? {};

    const result = {
        type: tag,
        offset: 0,
        encoding,
    } as FormatEntry;

    if (typeof len === 'string') {
        result.len = (buff) => {
            const fmt = parsedFormat[len];
            const val = fmt.value.get(buff, fmt.offset, fmt.len(buff), fmt.encoding);
            assert(typeof val === 'number');
            return val;
        };
    }
    else {
        result.len = () => len;
    }

    const content = node[tag];
    if (content.length === 1 && "innerText" in content[0]) {
        const constant = tagInnerTextParser(content[0].innerText as string);
        if (constant !== undefined) {
            result.value = {
                get: (buff, offset, len) => {
                    const fmt = parsedFormat[type];
                    const val = fmt.value.get(buff, offset, len);
                    if (len > 0) { // for constants configured in xml with no concrete equivalent
                        assert.equal(val, constant);
                    }
                    return constant;
                },
                set: (buff, offset, len) => {
                    const fmt = parsedFormat[type];
                    fmt.value.set(buff, offset, len, constant);
                },
            };
        }
    }
    else if (type in PresetTypes) {
        result.value = PresetTypes[type as keyof typeof PresetTypes];
    }
    else {
        const parsed = Object.assign({}, parsedFormat);
        const order = content.map(subTag => xmlToFormat({
            node: subTag as FormatNode,
            parsedFormat: parsed
        }));

        result.value = {
            get: (buffer, offset, len): Record<string, unknown>[] => {
                const res: Record<string, unknown>[] = []
                for (let i = 0; i < len; ++i) {
                    const obj: Record<string, unknown> = {};
                    for (const format of order) {
                        format.offset = offset;
                        parsed[format.type] = format;

                        const fmtlen = format.len(buffer);
                        obj[format.type] = format.value.get(buffer, offset, fmtlen, format.encoding);
                        offset += fmtlen;
                    }
                    res.push(obj);
                }
                return res;
            },
            set: (buffer, offset, len, values: Record<string, unknown>[]) => {
                assert.equal(values.length, len);

                for (const val of values) {
                    for (const format of order) {
                        format.offset = offset;
                        parsed[format.type] = format;

                        const fmtlen = format.len(buffer);
                        format.value.set(buffer, offset, fmtlen, val, format.encoding);
                        offset += fmtlen;
                    }
                }
            }
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
        return format.value.get(buffer, 0, format.len(buffer), format.encoding) as T;
    }
    catch (e) {
        printf('Failed to parse format', format.type, e);
        return undefined;
    }
}

export function trySerializeBuffer<T>(format: FormatEntry, value: T): Buffer | undefined {
    try {
        const len = Array.isArray(value) ? value.length : 1;
        const buffer = Buffer.alloc(len * 100); // TODO: size appropriately
        format.value.set(buffer, 0, len, value, format.encoding);
        return buffer;
    }
    catch (e) {
        printf('Failed to serialize format', format.type, e);
        return undefined;
    }
}