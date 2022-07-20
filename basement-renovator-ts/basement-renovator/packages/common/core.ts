import _ from "lodash";
import { EntityNode } from "./br-xml-types";
import { RoomShape, Wall } from "./config/br-config";
import { LookupProvider, RoomShapeLookup } from "./lookup";
import { Point, range, Vector } from "./util";

export class Entity {
    x: number;
    y: number;
    weight: number;

    Type?: number;
    Variant?: number;
    Subtype?: number;

    xmlProps?: Record<string, unknown>;

    xml?: EntityNode;

    constructor({ x=0, y=0, type=0, variant=0, subtype=0, weight=0, xmlProps={} }) {
        // Supplied entity info
        this.x = x;
        this.y = y;
        this.weight = weight;
        this.xmlProps = xmlProps;

        this.clearValues()
        this.Type = type;
        this.Variant = variant;
        this.Subtype = subtype;
    }

    clearValues() {
        this.Type = undefined
        this.Variant = undefined
        this.Subtype = undefined

        // Derived Entity Info
        // this.name = undefined
        // this.isGridEnt = false
        // this.baseHP = undefined
        // this.boss = undefined
        // this.champion = undefined

        // this.pixmap = undefined

        // this.known = false
        // this.invalid = false
        // this.placeVisual = undefined
        // this.blocksDoor = true

        // this.mirrorX = undefined
        // this.mirrorY = undefined
    }
}

export type Door = {
    x: number;
    y: number;
    exists: boolean;
};

/**
 * contains concrete room information necessary for examining a room's game qualities
 * such as type, variant, subtype, and shape information
 */
export class Room {
    name: string;
    info: Room.Info;
    difficulty: number;
    weight: number;

    lastTestTime?: Date;
    xmlProps: Record<string, any> = {};

    #spawnCount = 0;
    #gridSpawns!: Entity[][];

    constructor({
        name="New Room",
        spawns,
        difficulty=1,
        weight=1.0,
        type=1,
        variant=0,
        subtype=0,
        shape=1,
        doors=undefined,
    }: Partial<{
        name: string;
        spawns: Entity[][];
        difficulty: number;
        weight: number;
        type: number;
        variant: number;
        subtype: number;
        shape: number;
        doors?: Door[];
    }>) {
        this.name = name;

        this.info = new Room.Info(type, variant, subtype, shape);
        if (doors) {
            if (this.info.doors.length !== doors.length) {
                console.log(`${name} (${variant}): Invalid doors!`, doors);
            }
            this.info.doors = doors;
        }

        spawns ??= Array.from(range(this.info.gridLen())).map(() => []);
        this.gridSpawns = spawns;
        if (this.info.gridLen() !== this.gridSpawns.length) {
            console.log(`${name} (${variant}): Invalid grid spawns!`);
        }

        this.difficulty = difficulty
        this.weight = weight
    }

    get gridSpawns() {
        return this.#gridSpawns;
    }

    set gridSpawns(g) {
        this.#gridSpawns = g;

        this.#spawnCount = 0;
        for (const entStack of this.gridSpawns) {
            if (entStack.length > 0) this.#spawnCount++;
        }
    }

    static DoorSortKey = ['x','y'];

    getSpawnCount() {
        return this.#spawnCount;
    }

    reshape(shape: number, doors=undefined): void {
        this.info.shape = shape;
        if (doors) {
            this.info.doors = doors;
        }

        const realWidth = this.info.dims.width;

        const gridLen = this.info.gridLen();
        const newGridSpawns: Entity[][] = Array.from(range(gridLen)).map(() => []);

        for (const [ stack, x, y ] of this.spawns()) {
            const idx = Room.Info.gridIndex(x, y, realWidth);
            if (idx < gridLen) {
                newGridSpawns[idx] = stack;
            }
        }

        this.gridSpawns = newGridSpawns;
    }

    static getDesc(info: Room.Info, name: string, difficulty: number, weight: number) {
        return `${name} (${info.type}.${info.variant}.${info.subtype}) (${info.width-2}x${info.height-2}) - Difficulty: ${difficulty}, Weight: ${weight}, Shape: ${info.shape}`;
    }

    getPrefix() {
        return Room.getDesc(this.info, this.name, this.difficulty, this.weight);
    }

    *spawns(): IterableIterator<[ Entity[], number, number ]> {
        for (let i = 0;
            i <= this.info.width * this.info.height ||
            i <= this.gridSpawns.length;
        i++) {
            const stack = this.gridSpawns[i];
            if (stack && stack.length > 0) {
                const x = (i % this.info.width) | 0;
                const y = (i / this.info.width) | 0;
                yield [ stack, x, y ];
            }
        }
    }
}

export namespace Room {
    export class Info {
        type: number;
        variant: number;
        subtype: number;
        doors!: Door[];

        #shape!: number;
        shapeData!: RoomShape;
        baseShapeData?: RoomShape;

        constructor(t=0, v=0, s=0, shape=1) {
            this.type = t;
            this.variant = v;
            this.subtype = s;
            this.shape = shape;
        }

        get shape() {
            return this.#shape;
        }

        set shape(val) {
            this.#shape = val;
            this.shapeData = RoomShapeLookup.toRoomShape(
                LookupProvider.Main.roomShapes.lookup({ id: this.shape })[0]
            );
            const bs = this.shapeData.baseShape;
            this.baseShapeData = bs ? RoomShapeLookup.toRoomShape(
                LookupProvider.Main.roomShapes.lookup({ name: bs })[0]
            ) : undefined;
            this.makeNewDoors();
        }

        // represents the actual dimensions of the room, including out of bounds
        get dims() {
            return (this.baseShapeData ?? this.shapeData).dims;
        }

        get width() {
            return this.shapeData.dims.width;
        }

        get height() {
            return this.shapeData.dims.height;
        }

        makeNewDoors() {
            this.doors = _.flatten(this.shapeData.walls.map(w => w.doors.map(d => ({ ...d }))));
        }

        gridLen() {
            return this.dims.width * this.dims.height;
        }

        static gridIndex(x: number, y: number, w: number): number {
            return y * w + x;
        }

        static coords(g: number, w: number): Point {
            return { x: g % w, y: Math.floor(g / w) };
        }

        static isInFrontOfWall(p: Point, w: Wall): boolean {
            return Vector.dot(Vector.sub(p, w.points[0]), w.normal) > 0;
        }

        inFrontOfDoor(x: number, y: number): Door | undefined {
            for (const wall of this.shapeData.walls) {
                for (const door of wall.doors) {
                    if (x - door.x === wall.normal.x && y - door.y === wall.normal.y) {
                        return door;
                    }
                }
            }
            return undefined
        }

        isInBounds(x: number, y: number): boolean {
            const p = { x, y };
            return this.shapeData.walls.every(w => Room.Info.isInFrontOfWall(p, w));
        }

        snapToBounds(x: number, y: number, dist=1) {
            let p = { x, y };
            for (const w of this.shapeData.walls) {
                if (!Room.Info.isInFrontOfWall(p, w)) {
                    const wallToPoint = Vector.sub(p, w.points[0]);
                    const wallLine = Vector.sub(w.points[1], w.points[0]);
                    const toWall = Vector.sub(wallToPoint, Vector.mul(wallLine, Vector.dot(wallToPoint, wallLine)));
                    // adding the normal pushes out of the wall
                    p = Vector.add(Vector.add(p, toWall), w.normal);
                }
            }

            return p;
        }
    }
}


export class RoomFile {
    rooms: Room[];
    xmlProps: Record<string, any>;

    constructor(rooms: Room[], xmlProps={}) {
        this.rooms = rooms;
        this.xmlProps = xmlProps;
    }
}
