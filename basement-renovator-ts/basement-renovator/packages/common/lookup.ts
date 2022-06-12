import assert from 'assert';
import pathlib from 'path';

import * as fileutil from './fileutil';
import * as XML from './xml';
import _ from 'lodash';
import { Room } from './core';
import { generateXMLFromEntities2 } from './entitiesgenerator';
import { printf, printSectionBreak, withPrototype } from './util';
import { BaseShapeNode, EntityNode, EntityXml, GfxNode, GroupNode, MirrorShapeNode, PositionNode, RoomShapeNode, RoomShapeXml, RoomTypeNode, RoomTypeXml, StageNode, StageXml, TabNode, TagNode, VersionXML, WallShapeNode } from './br-xml-types';
import { Entity, EntityGroup, Mod, EntityTab, EntityTag, Version, RoomShape } from './config/br-config';
import { FormatEntry, FormatNode, FormatXml, parseFormatXml, tryParseBuffer } from './format';
import { ImageManager } from './resourcemanager';

type File = {
    path: string;
    contents: string;
};

async function sanitizePath<T extends { attrib?: A; }, A extends Record<string, unknown>>(
    node: T, key: keyof A, imageManager: ImageManager, checkFile = true
): Promise<void> {
    if (!node.attrib) {
        return;
    }

    const prefix = node.attrib[key];
    if (typeof prefix === "string") {
        const prefixPath = await imageManager.register(prefix, checkFile);
        (node.attrib[key] as string) = prefixPath ?? '';
    }
}

async function parseXMLFile<T extends XML.XmlParsed>(file: File, ...args: [a:string[]]): Promise<T | undefined> {
    if (!file.contents) return undefined;

    try {
        const parser = new XML.Parser<T[]>(...args, true);

        const p = parser.decode(file.contents)?.[0];
        //printf(file.path, p);
        return p;
    }
    catch (e) {
        printf("Error loading xml", file.path, ":", e);
        return undefined;
    }
}


function parseCriteria(txt?: string | number): undefined | ((v: number) => boolean) {
    if (!txt) {
        return undefined;
    }
    if (typeof txt === 'number') {
        return v => v === txt;
    }

    const tokens = txt.split(/[[()\],]/g).filter(t => t);

    if (!txt.match(/^[[(]/)) {
        const vals = new Set(tokens.map(t => +t));
        return v => vals.has(v);
    }

    const start = txt.at(0), end = txt.at(-1);

    const [ mini, maxi ] = tokens;
    let minf: (v: number) => boolean;
    let maxf: typeof minf;
    if (mini === "infinity") {
        minf = v => true;
    }
    else {
        const miniv = +mini;
        if (start === "[") {
            minf = v => v >= miniv;
        }
        else if (start === "(") {
            minf = v => v > miniv;
        }
        else {
            throw RangeError(`Invalid range in text: ${txt}`);
        }
    }

    if (maxi === "infinity") {
        maxf = v => true;
    }
    else {
        const maxiv = +maxi;
        if (end === "]") {
            maxf = v => v <= maxiv;
        }
        else if (end === ")") {
            maxf = v => v < maxiv;
        }
        else {
            throw new RangeError(`Invalid range in text: ${txt}`);
        }
    }

    return v => minf(v) && maxf(v);
}


function applyGfxReplacement(replacement: GfxNode[] | undefined, gfxchildren: GfxNode[]): void {
    for (const [ origgfx, newgfx ] of _.zip(replacement ?? [], gfxchildren)) {
        if (newgfx === undefined) {
            continue;
        }
        else if (origgfx === undefined) {
            replacement?.push(newgfx);
            continue;
        }

        Object.assign(origgfx.attrib ?? {}, newgfx.attrib);

        for (const ent of newgfx.gfx ?? []) {
            const origent = origgfx?.gfx?.find(e =>
                e.attrib?.ID === ent.attrib?.ID &&
                (e.attrib?.Variant ?? 0) === (ent.attrib?.Variant ?? 0) &&
                (e.attrib?.Subtype ?? 0) === (ent.attrib?.Subtype ?? 0)
            );
            if (origent !== undefined) {
                Object.assign(origent.attrib ?? {}, ent.attrib);
            }
            else {
                origgfx.gfx?.push(ent);
            }
        }
    }
}


abstract class Lookup {
    prefix: string;
    version: string;

    constructor(prefix: string, version: string) {
        this.prefix = prefix;
        this.version = version;
    }

    async loadFile<T extends XML.XmlParsed>(file: File, mod: Mod, ...args: [a:string[]]) {
        printSectionBreak();
        printf(`Loading ${this.prefix} from "${mod.name}" at ${file.path}`);
        const previous = this.count();
        await this.loadXML(await parseXMLFile<T>(file, ...args), mod);
        printf(`Successfully loaded ${this.count() - previous} new ${this.prefix} from "${mod.name}"`);
    }

    async loadFromMod(mod: Mod, ...args: [a: string[]]) {
        const file = pathlib.join(mod.resourcePath, this.prefix + "Mod.xml");
        if (!(await fileutil.stat(file)).isFile()) {
            return;
        }

        this.loadFile({
            path: file,
            contents: await fileutil.read(file, "utf-8")
        }, mod, ...args);
    }

    abstract count(): number;
    abstract loadXML(...args: any[]): void;
    abstract lookup(): void;
}

class StageLookup extends Lookup {
    xml?: StageXml["data"];
    parent: MainLookup;

    constructor(version: string, parent: MainLookup) {
        super("Stages", version);
        this.parent = parent;
        withPrototype(this);
    }

    count() {
        return this.xml?.length ?? 0;
    }

    loadXML(root: StageXml, mod: Mod) {
        const stageList = root.data;
        if (!stageList || stageList.length === 0) return;

        let initialLoad = false;
        if (this.xml === undefined) {
            this.xml = root.data;
            initialLoad = true;
        }

        const mapStage = (stage: StageNode) => {
            const name = stage.attrib.Name;
            if (name === undefined) {
                printf("Tried to load stage, but had missing name!", stage.attrib);
                return undefined;
            }

            if (this.parent.verbose) {
                printf("Loading stage:", stage.attrib);
            }

            const replacement = this.xml?.find(s => s.attrib.Name === name);

            if (!replacement && (stage.attrib.Stage === undefined || stage.attrib.StageType === undefined)) {
                printf(`Stage ${stage.attrib} has missing stage/stage type; this may not load properly in testing`);
            }

            sanitizePath(stage, "BGPrefix", mod.imageManager, false);

            const children = stage.stage ?? [];
            for (const gfx of children) {
                sanitizePath(gfx, "BGPrefix", mod.imageManager, false);

                for (const ent of gfx.gfx ?? []) {
                    sanitizePath(ent, "Image", mod.imageManager);
                }
            }

            if (replacement) {
                for (const key of Object.keys(stage.attrib) as Array<keyof StageNode["attrib"]>) {
                    if (key !== "Name") {
                        (replacement.attrib[key] as string | number | undefined) =
                            stage.attrib[key] ?? replacement.attrib[key];
                    }
                }

                applyGfxReplacement(replacement.stage, children);
                return undefined;
            }

            return stage;
        }

        const stages = stageList.map(mapStage).filter((st): st is StageNode => !!st);
        if (stages.length > 0 && !initialLoad) {
            this.xml ??= [];
            this.xml.push(...stages);
        }
    }

    lookup({ path, name, stage, stageType, baseGamePath }: Partial<{
        path: string;
        name: string;
        stage: number;
        stageType: number;
        baseGamePath: string;
    }> = {}): StageNode[] {
        let stages = this.xml ?? [];

        if (stage !== undefined) {
            stages = stages.filter(s => s.attrib.Stage === stage);
        }

        if (stageType !== undefined) {
            stages = stages.filter(s => s.attrib.StageType === stageType);
        }

        if (path !== undefined) {
            stages = stages.filter(s => path.match(new RegExp(s.attrib.Pattern, 'i')));
        }

        if (name) {
            stages = stages.filter(s => s.attrib.Name === name);
        }

        if (baseGamePath) {
            let hasBasePath: (s: StageNode) => boolean;
            if (typeof baseGamePath === 'boolean') {
                hasBasePath = s => s.attrib.BaseGamePath !== undefined;
            }
            else {
                hasBasePath = s => s.attrib.BaseGamePath === baseGamePath;
            }
            stages = stages.filter(hasBasePath);
        }

        return stages;
    }

    getGfx(node: StageNode | GfxNode): GfxNode {
        return (node as StageNode).stage?.[0] ?? node as GfxNode;
    }
}

export class RoomTypeLookup extends Lookup {
    xml?: RoomTypeXml["data"];
    parent: MainLookup;

    constructor(version: string, parent: MainLookup) {
        super("RoomTypes", version);
        this.parent = parent;
        withPrototype(this);
    }

    count() {
        return this.xml?.length ?? 0;
    }

    loadXML(root: RoomTypeXml, mod: Mod) {
        const roomTypeList = root.data;
        if (!roomTypeList) return;

        let initialLoad = false;
        if (this.xml === undefined) {
            this.xml = root.data;
            initialLoad = true;
        }

        const mapRoomType = (roomType: RoomTypeNode) => {
            const name = roomType.attrib.Name;
            if (name === undefined) {
                printf("Tried to load room type, but had missing name!", roomType.attrib);
                return undefined;
            }

            const replacement = this.xml?.find(r => r.attrib.Name === name);

            sanitizePath(roomType, "Icon", mod.imageManager);

            const children = roomType.room ?? [];
            for (const gfx of children) {
                sanitizePath(gfx, "BGPrefix", mod.imageManager, false);

                for (const ent of gfx.gfx ?? []) {
                    sanitizePath(ent, "Image", mod.imageManager);
                }
            }

            if (replacement) {
                applyGfxReplacement(replacement.room, children);
                return undefined;
            }

            return roomType;
        };

        const roomTypes = roomTypeList.map(mapRoomType).filter((x): x is Exclude<typeof x, undefined> => x !== undefined);
        if (roomTypes.length > 0 && !initialLoad) {
            this.xml ??= [];
            this.xml.push(...roomTypes);
        }
    }

    filterRoom(node: RoomTypeNode, args: { room: Room, path?: string }) {
        const typeF = node.attrib.Type;
        if (typeF !== undefined && typeF !== args.room.info.type) {
            return false;
        }

        const nameRegex = node.attrib.NameRegex;
        if (nameRegex && !args.room.name.match(new RegExp(nameRegex))) {
            return false;
        }

        const stage = node.attrib.StageName;
        // TODO: replace with check against room file stage
        if (stage && args.path && !this.parent.stages.lookup({ path: args.path }).some(st => st.attrib.Name === stage))
            return false;

        const idCriteria = parseCriteria(node.attrib.ID);
        if (idCriteria && !idCriteria(args.room.info.variant)) {
            return false;
        }

        const subtypeCriteria = parseCriteria(node.attrib.Subtype);
        if (subtypeCriteria && !subtypeCriteria(args.room.info.subtype)) {
            return false;
        }

        return true;
    }

    lookup({ room, name, path, showInMenu }: Partial<{
        room: Room;
        name: string;
        path: string;
        showInMenu: boolean;
    }> = {}): RoomTypeNode[] {
        let rooms = this.xml ?? [];

        if (name) {
            rooms = rooms.filter(r => r.attrib.Name === name);
        }

        if (showInMenu !== undefined) {
            rooms = rooms.filter(node => !!node.attrib.ShowInMenu === showInMenu);
        }

        if (room) {
            rooms = rooms.filter(node => this.filterRoom(node, { room, path }));
        }

        return rooms;
    }

    getMainType(args: Partial<{
        room: Room;
        path: string;
    }>) {
        let candidates = this.lookup(args);
        if (candidates.length === 0) {
            return undefined;
        }

        const getCritWeight = (r: RoomTypeNode, k: keyof RoomTypeNode["attrib"], w: number) => r.attrib[k] !== undefined ? w : 0;

        candidates = _.sortBy(candidates, r => -(
                  getCritWeight(r, "Type", 1)
                + getCritWeight(r, "NameRegex", 10)
                + getCritWeight(r, "StageName", 10)
                + getCritWeight(r, "ID", 10)
            )
        );

        return candidates[0];
    }

    getGfx(node: RoomTypeNode, args: { room: Room; path?: string }) {
        let possibleGfx = node.room ?? [];
        possibleGfx = _.sortBy(possibleGfx, g => -Object.keys(g.attrib ?? {}).length);

        if (args.room === undefined) {
            return possibleGfx[0];
        }
        return possibleGfx.find(gfx => this.filterRoom(node, args));
    }
}

export class RoomShapeLookup extends Lookup {
    xml?: RoomShapeXml["data"];
    parent: MainLookup;

    constructor(version: string, parent: MainLookup) {
        super("RoomShapes", version);
        this.parent = parent;
        withPrototype(this);
    }

    count() {
        return this.xml?.length ?? 0;
    }

    loadXML(root: RoomShapeXml) {
        const shapeList = root.data;
        if (!shapeList || shapeList.length === 0) return;

        let initialLoad = false;
        if (this.xml === undefined) {
            this.xml = root.data;
            initialLoad = true;
        }

        const mapShape = (shape: RoomShapeNode) => {
            const name = shape.attrib.Name;
            if (name === undefined) {
                printf("Tried to load room shape, but had missing name!", shape.attrib);
                return undefined;
            }

            if (this.parent.verbose) {
                printf("Loading room shape:", shape.attrib);
            }

            const replacement = this.xml?.find(s => s.attrib.Name === name);

            if (!replacement && (shape.attrib.ID === undefined)) {
                printf(`Shape ${shape.attrib} has missing ID; this will not load properly in game`);
            }

            if (replacement) {
                for (const key of Object.keys(shape.attrib) as Array<keyof RoomShapeNode["attrib"]>) {
                    if (key !== "Name") {
                        (replacement.attrib[key] as string | number) =
                            shape.attrib[key] ?? replacement.attrib[key];
                    }
                }

                return undefined;
            }

            return shape;
        }

        const shapes = shapeList.map(mapShape).filter((st): st is RoomShapeNode => !!st);
        if (shapes.length > 0 && !initialLoad) {
            this.xml ??= [];
            this.xml.push(...shapes);
        }
    }

    lookup({ name, id }: Partial<{
        name: string;
        id: number;
    }> = {}): RoomShapeNode[] {
        let shapes = this.xml ?? [];

        if (name !== undefined) {
            shapes = shapes.filter(s => s.attrib.Name === name);
        }

        if (id !== undefined) {
            shapes = shapes.filter(s => s.attrib.ID === id);
        }

        return shapes;
    }

    static toRoomShape(node: RoomShapeNode): RoomShape {
        const toPoint = (p: {
            attrib: { x?: number, y?: number };
        }) => ({
            x: p.attrib.x as number,
            y: p.attrib.y as number,
        });

        const baseShape = node.shape.find((n): n is BaseShapeNode => "shape" in n);
        const mirror = node.shape.find((n): n is MirrorShapeNode => "mirror" in n);
        const walls = node.shape.filter((n): n is WallShapeNode => "wall" in n);

        return {
            baseShape: baseShape?.attrib.Name,
            dims: {
                width: node.attrib.Width,
                height: node.attrib.Height
            },
            id: node.attrib.ID,
            name: node.attrib.Name,
            topLeft: baseShape?.attrib ? toPoint(baseShape) : undefined,
            mirrorX: mirror?.attrib.x,
            mirrorY: mirror?.attrib.y,
            walls: walls.map(w => {
                const wp = toPoint(w);

                const points = w.wall.filter((n): n is PositionNode & { point: unknown; } => "point" in n);
                const normal = w.wall.find((n): n is PositionNode & { normal: unknown; } => "normal" in n);
                const doors = w.wall.filter((n): n is PositionNode & { door: unknown; } => "door" in n);

                return {
                    points: points.map(p => Object.assign(toPoint(p), wp)),
                    normal: Object.assign({ x: 0, y: 0 }, toPoint(normal!)),
                    doors: doors.map(d => ({ ...Object.assign(toPoint(d), wp), exists: true })),
                };
            }),
        };
    }
}

export class EntityLookup extends Lookup {
    entityList = new EntityGroup();
    entityListByType: Record<string, Entity[]> = {};
    groups: Record<string, EntityGroup> = {};
    tabs: EntityTab[] = [];
    tags = new EntityTag();
    lastuniqueid = 0;

    parent: MainLookup;

    constructor(version: string, parent: MainLookup) {
        super("Entities", version);
        this.parent = parent;
        withPrototype(this);
    }

    count(): number {
        return this.entityList.entries.length;
    }

    addEntity(entity: Entity) {
        ++this.lastuniqueid;
        entity.uniqueid = this.lastuniqueid;
        this.entityList.addEntry(entity);

        if (!(entity.type in this.entityListByType)) {
            this.entityListByType[entity.type] = [];
        }

        this.entityListByType[entity.type].push(entity);
    }

    async loadEntityNode(node: EntityNode, mod: Mod, parentGroup?: EntityGroup): Promise<Entity> {
        let   entitytype = node.attrib.ID;
        let   variant    = node.attrib.Variant;
        let   subtype    = node.attrib.Subtype;
        const name       = node.attrib.Name;

        let entityConfig;
        if (name || entitytype !== undefined) {
            const isRef = Object.keys(node.attrib).every(key =>
                key === 'ID' ||
                key === 'Variant' ||
                key === 'Subtype' ||
                key === 'Name'
            );

            if (isRef) {
                const entityConfig = this.lookupOne({ entitytype, variant, subtype, name });
                if (entityConfig) {
                    // Refs can be used to add tags to entities without overwriting them
                    for (const tag of node.entity?.filter((e): e is TagNode => 'tag' in e) ?? []) {
                        entityConfig.addTag(tag.tag[0].innerText);
                    }

                    return entityConfig;
                }
                else {
                    printf("Entity", node, "looks like a ref, but was not previously defined!");
                }
            }
        }

        entitytype ??= -1;
        variant ??= 0;
        subtype ??= 0;

        let overwrite = !!node.attrib.Overwrite;
        if (overwrite) {
            if (name) {
                entityConfig = this.lookupOne({ name });
            }

            entityConfig ??= this.lookupOne({ entitytype, variant, subtype });

            if (!entityConfig) {
                printf(`Entity "${name}" from ${mod.name} (${entitytype}.${variant}.${subtype}) has the Overwrite attribute, but is not overwriting anything!`);
            }
        }
        else {
            entityConfig = this.lookupOne({ entitytype, variant, subtype });
            if (entityConfig) {
                overwrite = true;
                printf(`Entity "${name}" from "${mod.name}" (${entitytype}.${variant}.${subtype}) is overriding "${entityConfig.name}" from "${entityConfig.mod?.name}"!`);
            }
            else {
                entityConfig = new Entity(mod, this.tags);
            }
        }

        if (entityConfig) {
            entityConfig.mod = mod;
            if (parentGroup?.entityDefaults) {
                entityConfig.fillFromConfig(parentGroup.entityDefaults);
            }

            const warnings = await entityConfig.fillFromNode(node);
            if (warnings !== "") {
                printf(warnings);
            }

            if (!overwrite) {
                this.addEntity(entityConfig);
            }
        }

        const groups: [ kind: string, group: string ][] = [];
        const nodeKind = node.attrib.Kind;
        const nodeGroup = node.attrib.Group;
        if (nodeKind && nodeGroup) {
            groups.push([ nodeKind, nodeGroup ]);
        }

        for (const [ kind, group ] of groups) {
            const groupName = `(${kind}) ${group}`;
            const tab = this.getTab({ name: kind });

            let groupConfig = tab?.entries.find((entry): entry is EntityGroup =>
                entry instanceof EntityGroup && entry.name === groupName
            );
            if (!groupConfig) {
                groupConfig = this.getGroup({ name: groupName, label: group })!;
                tab?.addEntry(groupConfig);
            }

            groupConfig.addEntry(entityConfig);
        }

        return entityConfig;
    }

    getGroup({ node, name, label, parentGroup }: Partial<{
        node: GroupNode;
        name: string;
        label: string;
        parentGroup: EntityGroup;
    }>) {
        if (!name) {
            name = node?.attrib.Name ?? node?.attrib.Label;
            if (!name) {
                printf("Attempted to get group with no Name:", node?.attrib);
                return undefined;
            }
        }

        if (!(name in this.groups)) {
            const group = new EntityGroup(node, name, label, parentGroup);
            this.groups[name] = group;
        }

        return this.groups[name];
    }

    getTab({ node, name }: Partial<{
        node: TabNode;
        name: string;
    }>) {
        if (!name) {
            name = node?.attrib.Name;
            if (!name) {
                printf("Attempted to get tab with no Name:", node?.attrib);
                return undefined;
            }
        }

        if (!(name in this.groups)) {
            const tab = new EntityTab(node, name);
            this.groups[tab.name] = tab;
            this.tabs.push(tab);
        }

        return this.groups[name];
    }

    async loadDefaultsNode(nodes: EntityNode[] = [], mod: Mod, group: EntityGroup): Promise<void> {
        for (const ent of nodes) {
            if (!group.entityDefaults) {
                group.entityDefaults = new Entity(mod, this.tags);
            }
            await group.entityDefaults?.fillFromNode(ent);
        }
    }

    async loadGroupNode(
        node: TabNode | GroupNode,
        mod: Mod,
        parentGroup?: EntityGroup
    ): Promise<EntityGroup | undefined> {
        let groupnode: GroupNode["group"];
        let group: EntityGroup | undefined;
        if ("tab" in node) {
            group = this.getTab({ node });
            groupnode = node.tab;
        }
        else {
            group = this.getGroup({ node, parentGroup });
            groupnode = node.group;
        }

        if (group) {
            for (const subNode of groupnode) {
                let entry;
                if ("group" in subNode) {
                    entry = await this.loadGroupNode(subNode, mod, group);
                }
                else if ("entity" in subNode) {
                    entry = await this.loadEntityNode(subNode, mod, group);
                }
                else if ("defaults" in subNode) {
                    await this.loadDefaultsNode(subNode.defaults, mod, group);
                }

                if (entry) {
                    group.addEntry(entry);
                }
            }
        }

        return group;
    }

    async loadXML(root: EntityXml | undefined, mod: Mod): Promise<void> {
        if (!root) return;

        for (const node of root.data) {
            if ("group" in node || "tab" in node) {
                await this.loadGroupNode(node, mod);
            }
            else if ("entity" in node) {
                await this.loadEntityNode(node, mod);
            }
            else if ("tag" in node) {
                this.tags.getTag({ node });
            }
        }
    }

    async loadFile(file: File, mod: Mod): Promise<void> {
        const root = await parseXMLFile<EntityXml>(file, []);
        if (!root) return;

        printSectionBreak();
        printf(`Loading Entities from "${mod.name}" at ${file.path}`);
        const previous = this.count();

        if (mod.autogenerateContent && mod.entities2root) {
            await this.loadXML(
                await generateXMLFromEntities2(
                    mod.modPath ?? '', mod.name, mod.entities2root, mod.resourcePath
                ),
                mod,
            );
        }

        await this.loadXML(root, mod);

        printf(`Successfully loaded ${this.count() - previous} new Entities from ${mod.name}`);
    }

    lookup({
        entitytype,
        variant,
        subtype,
        name,
        tags,
        matchAnyTag,
        entities,
    }: Partial<{
        entitytype: number;
        variant: number;
        subtype: number;
        name: string;
        tags: string[];
        matchAnyTag: boolean;
        entities: Entity[];
    }> = {}): Entity[] {
        let entList: Array<Entity | EntityGroup>;
        if (entities) {
            entList = entities;
        }
        else {
            if (entitytype !== undefined) {
                if (entitytype in this.entityListByType) {
                    entList = this.entityListByType[entitytype];
                }
                else {
                    return [];
                }
            }
            else {
                entList = this.entityList.entries;
            }
        }

        entities = entList.filter((entity): entity is Entity =>
            entity instanceof Entity && entity.matches({
                entitytype, variant, subtype, name, tags, matchAnyTag
            })
        );

        return entities;
    }

    lookupOne(args: Parameters<EntityLookup["lookup"]>[0]) {
        const entities = this.lookup(args);
        return entities[0];
    }
}

export class FormatLookup extends Lookup {
    xml?: FormatXml["format"];
    parent: MainLookup;

    formats: {
        [name: string]: FormatEntry;
    } = {};

    constructor(version: string, parent: MainLookup) {
        super("Formats", version);
        this.parent = parent;
        withPrototype(this);
    }

    count() {
        return Object.keys(this.xml ?? {}).length ?? 0;
    }

    loadXML(root: FormatXml) {
        const formats = Object.values(root)[0];
        if (!formats || formats.length === 0) return;

        const fmts = parseFormatXml(root);

        let initialLoad = false;
        if (this.xml === undefined) {
            this.xml = formats;
            this.formats = fmts;
            initialLoad = true;
        }

        if (formats.length > 0 && !initialLoad) {
            this.xml.push(...formats);
            Object.assign(this.formats, fmts);
        }
    }

    lookup({ name }: Partial<{
        name: string;
    }> = {}): FormatNode[] {
        let formats = this.xml ?? [];

        if (name !== undefined) {
            formats = formats.filter(s => s.attrib.type === name);
        }

        return formats;
    }

    tryParse<T>(name: string, buffer: Buffer): T | undefined {
        return tryParseBuffer<T>(this.formats[name], buffer);
    }
}

type GfxData = {
    paths: {
        OuterBG: string;
        BigOuterBG: string;
        InnerBG: string;
        NFloor: string;
        LFloor: string;
    };
    entities: Record<string, Partial<EntityNode>>;
};

export class MainLookup {
    basemod = new Mod();
    mods: Mod[] = [];
    stages: StageLookup;
    roomTypes: RoomTypeLookup;
    roomShapes: RoomShapeLookup;
    entities: EntityLookup;
    formats: FormatLookup;
    version: string;
    verbose?: boolean;

    constructor(version: string, verbose?: boolean) {
        this.stages    = new StageLookup(version, this);
        this.roomTypes = new RoomTypeLookup(version, this);
        this.roomShapes = new RoomShapeLookup(version, this);
        this.entities  = new EntityLookup(version, this);
        this.formats = new FormatLookup(version, this);
        this.version = version;
        this.verbose = verbose;
        this.mods.push(this.basemod);
        withPrototype(this);
    }

    async load(path = "resources/Versions.xml", mod = this.basemod): Promise<boolean> {
        if (!(await fileutil.stat(path)).isFile()) {
            return false;
        }

        const contents = await fileutil.read(path, "utf-8");
        await this.loadXML(await parseXMLFile<VersionXML>({ path, contents }, [
            "version",
            "entities",
            "stages",
            "roomtypes",
            "roomshapes",
            "formats",
        ]), mod);
        return true;
    }

    async loadFromMod(modPath: string, brPath: string, name: string, autogenerateContent?: boolean) {
        const modConfig = new Mod(name, brPath, autogenerateContent);
        await modConfig.setModPath(modPath);
        this.mods.push(modConfig);

        // try to load based off VersionsMod, else use fixed set of files
        const versionsPath = pathlib.join(brPath, "VersionsMod.xml");
        if (!this.load(versionsPath, modConfig)) {
            this.stages.loadFromMod(modConfig, []);
            this.roomTypes.loadFromMod(modConfig, []);
            this.entities.loadFromMod(modConfig, []);
        }
    }

    async loadXML(root: VersionXML | undefined, mod: Mod): Promise<void> {
        if (!root) return;

        const versions: Record<string, Version> = {};
        for (const versionNode of root.data ?? []) {
            const version = new Version(versionNode, versions);
            if (!version.invalid) {
                versions[version.name] = version;
            }
        }

        const loadVersion = versions[this.version];
        if (loadVersion) {
            const fileEntries = loadVersion.allFiles().filter(file => file.path);

            const files = await Promise.all(
                fileEntries
                .map(file => pathlib.join(mod.resourcePath, file.path))
                .map(async path => ({
                    path,
                    contents: await fileutil.read(path, 'utf-8')
                }))
            );
            for (const [ fileEntry, file ] of _.zip(fileEntries, files)) {
                const { filetype } = fileEntry!;
                if (filetype === "entities") {
                    await this.entities.loadFile(file!, mod);
                }
                else if (filetype === "stages") {
                    await this.stages.loadFile(file!, mod, []);
                }
                else if (filetype === "roomtypes") {
                    await this.roomTypes.loadFile(file!, mod, []);
                }
                else if (filetype === "roomshapes") {
                    await this.roomShapes.loadFile(file!, mod, []);
                }
                else if (filetype === "formats") {
                    await this.formats.loadFile(file!, mod, []);
                }
            }
        }
        else {
            printf("Could not find valid version to load");
        }
    }

    getRoomGfx({ room, path }: {
        room: Room;
        path?: string;
    }): GfxNode {
        const roomNode = this.roomTypes.getMainType({ room, path });
        if (roomNode) {
            const ret = this.roomTypes.getGfx(roomNode, { room, path });
            if (ret) return ret;
        }

        let node = this.stages.lookup({ path });
        if (node.length === 0) {
            node = this.stages.lookup({ name: "Basement" });
            assert(node.length > 0);
        }

        return this.stages.getGfx(node.at(-1) as StageNode);
    }

    async getGfxData(node?: GfxNode): Promise<GfxData> {
        if (!node) {
            node = this.stages.getGfx(this.stages.lookup({ name: "Basement" })[0]);
        }

        let baseGfx: GfxData | undefined;

        if (node.attrib?.StageGfx) {
            const stage = this.stages.lookup({ name: node.attrib.StageGfx });
            if (stage.length > 0) {
                baseGfx = await this.getGfxData(this.stages.getGfx(stage[0]));
            }
        }

        if (node.attrib?.RoomGfx) {
            const roomType = this.roomTypes.lookup({ name: node.attrib?.RoomGfx });
            if (roomType.length > 0) {
                baseGfx = await this.getGfxData(this.roomTypes.getGfx(roomType[0], { room: new Room({}) })); // TODO:
            }
        }

        const prefix = node.attrib?.BGPrefix;

        let paths: GfxData["paths"] | undefined;
        let entities: GfxData["entities"] = {};

        if (baseGfx) {
            paths = baseGfx.paths;
            entities = baseGfx.entities;
        }
        if (prefix) {
            paths = {
                OuterBG: prefix + ".png",
                BigOuterBG: node.attrib?.HasBigBG ? prefix + "_big.png" : '',
                InnerBG: prefix + "Inner.png",
                NFloor: prefix + "_nfloor.png",
                LFloor: prefix + "_lfloor.png",
            }
        }

        if (!paths) {
            throw new Error("Invalid gfx node!" + JSON.stringify(node));
        }

        for (const ent of node.gfx ?? []) {
            const entid = `${ent.attrib?.ID}.${ent.attrib?.Variant ?? 0}.${ent.attrib?.Subtype ?? 0}`;
            entities[entid] = ent;
        }

        const ret = { paths, entities };
        for await (const [ key, val ] of Object.entries(ret.paths)) {
            if (!(await fileutil.stat(val)).isFile()) {
                ret.paths[key as keyof typeof paths] = "";
            }
        }

        return ret;
    }
}

export class LookupProvider {
    static Main: MainLookup;

    static async init(version: string) {
        // TODO: add verbose setting
        LookupProvider.Main = new MainLookup(version);
        await LookupProvider.Main.load();
    }
}