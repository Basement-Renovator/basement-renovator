// Functions for converting to and from the various stb formats

import assert from 'assert';
import _ from 'lodash';
import xmlescape from 'xml-escape';
import { Entity, Room, RoomFile } from "./core";
import * as fileutil from './fileutil';
import { LookupProvider, EntityLookup } from './lookup';
import { printf } from './util';
import * as XML from './xml';

type StbEntity = {
    attrib: {
        type: number;
        variant: number;
        subtype: number;
        weight?: number;
    };
};

type StbSpawn = {
    attrib: {
        x: number;
        y: number;
    };
    entity: StbEntity[];
};

type StbDoor = {
    attrib: {
        x: number;
        y: number;
        exists: boolean;
    };
};

type StbRoom = {
    attrib: {
        type: number;
        variant: number;
        subtype: number;
        name: string;
        shape?: number;
        width: number;
        height: number;
        difficulty: number;
        weight: number;
    };
    door: StbDoor[];
    spawn: StbSpawn[];
};

type StbXml = {
    rooms: {
        attrib: Record<string, unknown>;
        room: StbRoom[];
    };
};

type SimpleRooms = {
    room: Array<StbRoom["attrib"] & {
        door: StbDoor["attrib"][];
        spawn: Array<StbSpawn["attrib"] & {
            entity: Array<StbEntity["attrib"] & {
                xmlProps: Record<string, unknown>;
            }>;
        }>;
        xmlProps: Record<string, unknown>;
    }>;
    xmlProps: Record<string, unknown>;
};

function _xmlStrFix(x: string): string {
    return xmlescape(x);
}

/**
 * Converts the common format to xml nodes
 */
export async function commonToXML(destPath: string, rooms: Room[], file?: RoomFile, isPreview=false) {
    if (isPreview) {
        assert.equal(rooms.length, 1, "Previews must be one room!");
    }

    function flattenDictList(l: Array<[string, unknown]>) {
        return l.map(p => `${p[0]}="${p[1]}"`).join(' ');
    }

    // if BR version is out of sync, xml acts as a failsafe to ensure
    // any extra props are written properly
    function flattenXml(d: Record<string, unknown>) {
        return Object.entries(d).map(item => ` ${item[0]}="${_xmlStrFix(item[1] + '')}"`).join("");
    }

    const output = ['<?xml version="1.0" ?>']
    if (!isPreview) {
        output.push(`<rooms${file ? flattenXml(file.xmlProps) : ""}>`);
    }

    for (const room of rooms) {
        const { width, height } = room.info.dims;

        const attrs: Array<[string, unknown]> = [
            [ "variant", room.info.variant ],
            [ "name", _xmlStrFix(room.name) ],
            [ "type", room.info.type ],
            [ "subtype", room.info.subtype ],
            [ "shape", room.info.shape ],
            [ "width", width - 2 ],
            [ "height", height - 2 ],
            [ "difficulty", room.difficulty ],
            [ "weight", room.weight ],
        ];

        // extra props here
        if (room.lastTestTime) {
            // TODO: remove sub-minute time values
            attrs.push([ "lastTestTime", room.lastTestTime.toISOString() ]); // converts to UTC
        }

        output.push(`\t<room ${flattenDictList(attrs)}${flattenXml(room.xmlProps)}>`)

        for (const door of _.sortBy(room.info.doors, Room.DoorSortKey)) {
            let { x, y, exists } = door;

            // FIXME: there's a vanilla bug with xml reading that messes up L rooms
            // remove this when rep is out or only apply it for ab+
            if (isPreview) {
                if (room.info.shape === 9) {
                    if (x === 7 && y === 7) {
                        y = 0;
                    }
                    else if (x === 13 && y === 4) {
                        x = 0;
                    }
                }
                else if (room.info.shape === 10) {
                    if (x === 20 && y === 7) {
                        y = 0;
                    }
                }
                else if (room.info.shape === 11) {
                    if (x === 13 && y === 11) {
                        x = 0;
                    }
                }
            }

            output.push(`\t\t<door exists="${exists}" x="${x - 1}" y="${y - 1}"/>`);
        }

        for (const [ stack, x, y ] of room.spawns()) {
            output.push(`\t\t<spawn x="${x - 1}" y="${y - 1}">`);

            for (const ent of stack) {
                output.push(
                    `\t\t\t<entity type="${ent.Type}" variant="${ent.Variant}" subtype="${ent.Subtype}" weight="${ent.weight}"${flattenXml(ent.xmlProps ?? {})}/>`
                );
            }

            output.push("\t\t</spawn>");
        }

        output.push("\t</room>");
    }

    if (!isPreview) {
        output.push("</rooms>");
    }

    output.push("");

    await fileutil.write(destPath, output.join("\n"), {
        encoding: 'ascii',
        truncate: true,
    });
}

function simpleToCommon(rooms: SimpleRooms): RoomFile {
    const ret: Room[] = [];

    for (const roomEnt of rooms.room) {
        let {
            type = 1,
            variant = 0,
            subtype = 0,
            difficulty = 0,
            name = '',
            weight = 1,
            shape = -1 as number | undefined,
            width = 13,
            height = 7,
            xmlProps = {},
        } = roomEnt;

        if (shape === -1) {
            shape = undefined;
            width += 2;
            height += 2;
            shape = LookupProvider.Main.roomShapes.lookup().find(s =>
                s.attrib.Width === width && s.attrib.Height === height
            )?.attrib.ID;
        }

        shape ??= 1;

        let lastTestTime = xmlProps.lastTestTime as Date | undefined;
        if (lastTestTime) {
            try {
                lastTestTime = new Date(lastTestTime as unknown as string);
                delete xmlProps.lastTestTime;
            }
            catch (e) {
                printf("Invalid test time string found", lastTestTime, e);
                lastTestTime = undefined;
            }
        }

        const doors = roomEnt.door.map(door => ({
            x: door.x + 1,
            y: door.y + 1,
            exists: door.exists,
        }));

        const room = new Room({
            name,
            difficulty,
            weight,
            type,
            variant,
            subtype,
            shape,
            doors
        })
        room.xmlProps = xmlProps;
        room.lastTestTime = lastTestTime;
        ret.push(room);

        const realWidth = room.info.dims.width;
        const gridLen = room.info.gridLen();
        for (const spawn of roomEnt.spawn) {
            let { x, y, entity: stackedEnts } = spawn;
            x++;
            y++;

            const grindex = Room.Info.gridIndex(x, y, realWidth);
            if (grindex >= gridLen) {
                printf(`Discarding the current entity stack due to invalid position! ${room.getPrefix()}: ${x-1},${y-1}`);
                continue;
            }

            const ents = room.gridSpawns[grindex];
            for (const ent of stackedEnts) {
                const { type, variant, subtype, weight, xmlProps = {} } = ent;

                ents.push(new Entity({
                    x, y, type, variant, subtype, weight, xmlProps
                }));
            }

            room.gridSpawns = room.gridSpawns; // eslint-disable-line no-self-assign
        }
    }

    return new RoomFile(ret, rooms.xmlProps);
}

async function stbToCommon(path: string): Promise<RoomFile> {
    const buffer = await fileutil.readBinary(path);
    const contents = buffer.toString();

    const header = contents.slice(0, 4);

    let format: string;
    if (header === "STB1") {
        format = 'stb1';
    }
    if (header === "STB2") {
        format = 'stb2';
    }
    else {
        format = 'stb0';
    }

    const result = LookupProvider.Main.formats.tryParse<SimpleRooms>(format, buffer);
    if (!result) {
        throw new Error(`Failed to parse ${path} with format ${format}`);
    }

    return simpleToCommon(result);
}

/**
 * Converts an Afterbirth xml to the common format
 */
export async function xmlToCommon(path: string, destPath?: string): Promise<RoomFile> {

    const contents = await fileutil.read(path, 'ascii');

    const parser = new XML.Parser<StbXml>([
        'room',
        'door',
        'spawn',
        'entity'
    ]);

    const root = parser.decode(contents);

    const rooms = root[Object.keys(root)[0] as keyof StbXml]; // can be stage, rooms, etc

    return simpleToCommon({
        room: rooms.room.map(roomNode => {
            const roomXmlProps: Record<string, unknown> = Object.assign({}, roomNode.attrib);
            delete roomXmlProps.type;
            delete roomXmlProps.variant;
            delete roomXmlProps.subtype;
            delete roomXmlProps.difficulty;
            delete roomXmlProps.name;
            delete roomXmlProps.weight;
            delete roomXmlProps.shape;
            delete roomXmlProps.width;
            delete roomXmlProps.height;

            return Object.assign({
                door: roomNode.door.map(d => Object.assign({}, d.attrib)),
                spawn: roomNode.spawn.map(s => Object.assign({
                    entity: s.entity.map(ent => {
                        const xmlProps: Record<string, unknown> = Object.assign({}, ent.attrib);
                        delete xmlProps.type;
                        delete xmlProps.variant;
                        delete xmlProps.subtype;
                        delete xmlProps.weight;

                        return Object.assign({ xmlProps }, ent.attrib);
                    })
                }, s.attrib)),
                xmlProps: roomXmlProps,
            }, roomNode.attrib);
        }),
        xmlProps: Object.assign({}, rooms.attrib ?? {}),
    });
}


export async function stbToXML(path: string, destPath?: string): Promise<void> {
    destPath ??= fileutil.with_suffix(path, '.xml');
    const roomfile = await stbToCommon(path);
    await commonToXML(destPath, roomfile.rooms, roomfile);
}

//function xmlToSTBAB(path: string, destPath?: string) {
//    destPath ??= fileutil.with_suffix(path, '.stb');
//    return commonToSTBAB(destPath, xmlToCommon(path))
//}

/**
 * Convert a txt file to the common format
 *
 * HA HA HA FUNNY MODE FUNNY MODE
 */
async function txtToCommon(path: string, entityLookup: EntityLookup): Promise<RoomFile> {
    const content = await fileutil.read(path);

    const text = content.split('\n');
    const numLines = text.length;

    function skipWS(i: number) {
        for (let j = i; j < numLines; ++j) {
            if (text[j]) return j;
        }
        return numLines;
    }

    const entMap: Record<string, [ type: number, variant: number, subtype: number ]> = {};

    // Initial section: entity definitions
    // [Character]=[type].[variant].[subtype]
    // one per line, continues until it hits a line starting with ---
    let roomBegin = 0
    for (let i = 0; i < numLines; ++i) {
        const line = text[i].replace(/\s/g, '');
        roomBegin = i;

        if (!line) continue;
        if (line.startsWith("---")) break;

        const [ char, type, variant, subtype ] = line.match(/(.)=(\d+).(\d+).(\d+)/) ?? [];

        if (["-", "|"].includes(char)) {
            printf("Can't use - or | for entities!");
            continue;
        }

        const [ t, v, s ] = [ +type, +variant, +subtype ];

        const en = entityLookup.lookupOne({ entitytype: t, variant: v, subtype: s });
        if (!en || en.invalid) {
            printf(`Invalid entity for character '${char}': '${en?.name ?? 'UNKNOWN'}'! (${t}.${v}.${s})`);
            continue;
        }

        entMap[char] = [ t, v, s ];
    }

    // TODO: somehow read these from xml
    const shapeNames: Record<string, number> = {
        "1x1": 1,
        "2x2": 8,
        "closet": 2,
        "vertcloset": 3,
        "1x2": 4,
        "long": 7,
        "longvert": 5,
        "2x1": 6,
        "l": 10,
        "mirrorl": 9,
        "r": 12,
        "mirrorr": 11,
    };

    const ret: Room[] = [];

    // Main section: room definitions
    // First line: [id]: [name]
    // Second line, in no particular order: [Weight,] [Shape (within tolerance),] [Difficulty,] [Type[=1],] [Subtype[=0],]
    // Next [room height] lines: room layout
    // horizontal walls are indicated with -, vertical with |
    //   there will be no validation for this, but if lines are the wrong length it prints an error message and skips the line
    // coordinates to entities are 1:1, entity ids can be at most 1 char
    // place xs at door positions to turn them off
    ++roomBegin;
    while (roomBegin < numLines) {
        // 2 lines
        let i = skipWS(roomBegin);
        if (i === numLines) break;

        const [ rvariant, rname ] = text[i].split(":", 1);
        const name = rname.trim();
        const roomVariant = +rvariant;

        const infoParts = text[i + 1].replace(/\s/g, "").toLowerCase().split(",");
        let shape = 1;
        let difficulty = 5;
        let weight = 1;
        let rtype = 1;
        let rsubtype = 0;
        for (const part of infoParts) {
            const [ prop, val ] = part.match(/(.+)=(.+)/) ?? [];
            switch (prop) {
            case "shape": {
                shape = shapeNames[val] ?? +val;
            } break;
            case "difficulty": {
                difficulty = shapeNames[val] ?? +val;
            } break;
            case "weight": {
                weight = parseFloat(val);
            } break;
            case "type": {
                rtype = +val;
            } break;
            case "subtype": {
                rsubtype = +val;
            } break;
            }
        }

        const r = new Room({ name, difficulty, weight, type: rtype, variant: roomVariant, subtype: rsubtype, shape });
        const { width, height } = r.info.dims;
        const spawns = r.gridSpawns;

        i = skipWS(i + 2);
        for (let j = i; j < i + height; ++j) {
            if (j === numLines) {
                printf("Could not finish room!");
                break;
            }

            const y = j - i;
            const row = text[j];
            for (const [ xs, char ] of Object.entries(row)) {
                const x = +xs;
                if (["-", "|", " "].includes(char)) continue;
                if (char.toLowerCase() === "x") {
                    const changedDoor = r.info.doors.find(door => door.x === x && door.y === y);
                    if (changedDoor) {
                        changedDoor.exists = false;
                        continue;
                    }
                }

                const ent = entMap[char];
                if (ent) {
                    spawns[Room.Info.gridIndex(x, y, width)].push(new Entity({
                        x, y,
                        type: ent[0], variant: ent[1], subtype: ent[2],
                        weight: 0
                    }));
                }
                else {
                    printf(`Unknown entity! '${char}'`);
                }
            }
        }

        r.gridSpawns = r.gridSpawns;
        ret.push(r);

        i = skipWS(i + height);
        if (i === numLines) break;

        if (!text[i].trim().startsWith("---")) {
            printf("Could not find separator after room!");
            break;
        }

        roomBegin = i + 1;
    }

    return new RoomFile(ret);
}
