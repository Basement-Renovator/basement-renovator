import _ from 'lodash';
import pathlib from 'path';

import { BitfieldNode, EntityNode, FileNode, GfxNode, TabNode, TagNode, VersionNode, Widgets } from "../br-xml-types";
import { EntityType } from '../constants';
import { Door } from '../core';
import { Entities2Root, Entities2XmlNode } from '../entitiesgenerator';
import * as fileutil from "../fileutil";
import * as util from "../util";
import { Choice } from '../util';
import * as XML from "../xml";

const { printf } = util;

class BitfieldElement {
    bitfield: Bitfield;
    name: string;
    unit: string;
    offset: number;
    length: number;
    valueoffset: number;
    minimum: number;
    maximum: number;
    scalarrange?: number;

    widget: Choice<Widgets>;
    tooltip?: string;
    dropdowndata?: Record<string, number>;

    constructor(bitfield: Bitfield, widget: Choice<Widgets>, offset: number, length: number) {
        this.bitfield = bitfield;

        this.widget = widget;
        const node = (widget as any)[Object.keys(widget)[0]] as Widgets[keyof Widgets];

        this.name = node.attrib.Name ?? "";
        this.unit = node.attrib.Unit ?? "";

        this.offset = offset;
        this.length = length;

        this.valueoffset = node.attrib.ValueOffset ?? 0;
        const floatvalueoffset = this.valueoffset % 1; // TODO: fmod?
        this.valueoffset = Math.floor(this.valueoffset - floatvalueoffset);

        this.minimum = node.attrib.Minimum ?? 0;
        this.maximum = node.attrib.Maximum ?? util.bitFill(this.length);

        this.scalarrange = node.attrib.ScalarRange;

        const tooltipNode = node.tooltip;
        this.tooltip = undefined;
        if (tooltipNode) {
            this.tooltip = tooltipNode.innerText;
        }

        this.dropdowndata = undefined;
        if ("dropdown" in this.widget) {
            this.dropdowndata = {};
            for (const [ i, value ] of Object.entries(this.widget.dropdown.choice ?? [])) {
                this.dropdowndata[value.innerText] = value.attrib.Value ?? +i;
            }
        }
    }

    getRawValue(num: number): number {
        return util.bitGet(num, this.offset, this.length);
    }

    setRawValue(num: number, value: number): number {
        return util.bitSet(num, value, this.offset, this.length);
    }

    getRawValueFromWidgetValue(widgetValue: number): number {
        if (this.dropdowndata) {
            return Object.values(this.dropdowndata)[widgetValue];
        }

        if ("dial" in this.widget) {
            return (widgetValue - this.valueoffset) % (this.maximum + 1);
        }
        if ("checkbox" in this.widget) {
            return widgetValue ? 1 : 0;
        }

        return widgetValue - this.valueoffset;
    }

    getWidgetValue(num: number, rawValue?: number): number {
        const value = rawValue ?? this.getRawValue(num);

        if (this.dropdowndata) {
            return Object.values(this.dropdowndata).indexOf(value);
        }

        if ("dial" in this.widget) {
            return (value + this.valueoffset) % (this.maximum + 1);
        }
        if ("checkbox" in this.widget) {
            return value ? 1 : 0;
        }

        return value + this.valueoffset;
    }

    getWidgetRange(): [ number, number ] {
        if ("dropdown" in this.widget) {
            return [ 0, Object.keys(this.dropdowndata ?? {}).length ];
        }
        if ("dial" in this.widget) {
            return [ this.minimum, this.maximum + 1 ];
        }

        return [ this.minimum + this.valueoffset, this.maximum + this.valueoffset ];
    }

    getDisplayValue(num: number, rawValue?: number) {
        const value = this.getWidgetValue(num, rawValue);

        if (this.unit === "Degrees") { // Match Isaac's degrees, where right is 0
            const degrees = value * (360 / (this.maximum + 1));
            return (degrees + 90) % 360;
        }

        if (this.scalarrange) {
            return Math.round(this.scalarrange / value * 1000) / 1000;
        }

        return value;
    }

    clampValue(num: number) {
        const bitValue = this.getRawValue(num);
        if ("dropdown" in this.widget) {
            if (!Object.values(this.dropdowndata ?? {}).includes(bitValue)) {
                return this.setRawValue(num, this.dropdowndata![0]);
            }
        }
        else {
            if (bitValue < this.minimum) {
                return this.setRawValue(num, this.minimum);
            }
            if (bitValue > this.maximum) {
                return this.setRawValue(num, this.maximum);
            }
        }

        return num;
    }
}

export class Bitfield {
    key: string;
    elements: BitfieldElement[];

    constructor(node: BitfieldNode) {
        this.key = node.attrib.Key ?? 'Subtype';
        this.elements = [];

        let offset = 0;
        for (const el of node.bitfield) {
            const elementNode = (el as any)[Object.keys(el)[0]] as Widgets[keyof Widgets];
            elementNode.attrib ??= {} as any;

            const length = elementNode.attrib.Length ?? 1;
            let elementOffset = elementNode.attrib.Offset;
            if (elementOffset === undefined) {
                elementOffset = offset;
                offset += length;
            }
            else {
                elementOffset = elementOffset | 0;
            }

            const element = new BitfieldElement(this, el, elementOffset, length);
            this.elements.push(element);
        }
    }

    isInvalid() {
        const getPrefix = (elem: BitfieldElement) => `${elem.name} (Length: ${elem.length}, Offset: ${elem.offset})`;

        let invalid = false;
        let startsAtZero = false;
        for (const element of this.elements) {
            let hasAdjacent = this.elements.length === 1 && element.offset === 0;
            if (element.offset === 0) {
                startsAtZero = true;
            }

            for (const element2 of this.elements) {
                if (element !== element2) {
                    if (element.offset <= element2.offset && (element.offset + element.length) > element2.offset) {
                        printf(`Element ${getPrefix(element)} conflicts with ${getPrefix(element2)}`);
                        invalid = true;
                    }

                    if ((element.offset  + element.length)  === element2.offset ||
                        (element2.offset + element2.length) === element.offset) {
                        hasAdjacent = true;
                    }
                }
            }

            if (!hasAdjacent) {
                printf(`Element ${element.name} (Length: ${element.length}, Offset: ${element.offset}) is not adjacent to any other elements`);
            }
        }

        if (!startsAtZero) {
            printf("Bitfield does not have an element with an offset of 0.");
        }

        return invalid;
    }

    clampValues(num: number) {
        for (const element of this.elements) {
            num = element.clampValue(num);
        }
        return num;
    }
}

export class Entity {
    mod?: Mod;
    tagConfig?: EntityTag;
    tags: Record<string, TagData> = {};
    name?: string;
    type = -1;
    variant = 0;
    subtype = 0;
    imagePath = "resources/Entities/questionmark.png";
    editorImagePath?: string;
    overlayImagePath?: string;
    baseHP?: number;
    placeVisual?: string;
    disableOffsetIndicator = false;
    renderPit = false;
    renderRock = false;
    invalid = false;
    gfx?: GfxNode;
    mirrorX?: [ number, number?, number? ];
    mirrorY?: [ number, number?, number? ];
    hasBitfields = false;
    invalidBitfield = false;
    bitfields: Bitfield[] = [];
    uniqueid = -1;
    tagsString = "[]";

    constructor(mod?: Mod, tagConfig?: EntityTag) {
        this.mod = mod;
        this.tagConfig = tagConfig;
    }

    getTagConfig(tag: string | TagData): TagData | undefined {
        if (!this.tagConfig) {
            return undefined;
        }

        if (typeof tag === 'string') {
            const name = tag;
            tag = this.tagConfig.getTag({ name })!;
            if (!tag) {
                printf(`Attempted to get undefined tag ${name} for entity ${this.name} from mod ${this.mod?.name}`);
            }
        }

        return tag;
    }

    addTag(tag: string | TagData): void {
        const tagconfig = this.getTagConfig(tag);
        if (tagconfig && !(tagconfig.tag in this.tags)) {
            this.tags[tagconfig.tag] = tagconfig;
            this.tagsString = this.printTags();
        }
    }

    removeTag(tag: string | TagData): void {
        const tagconfig = this.getTagConfig(tag);
        if (tagconfig && tagconfig.tag in this.tags) {
            delete this.tags[tagconfig.tag];
            this.tagsString = this.printTags();
        }
    }

    hasTag(tag: string | TagData): boolean {
        const tagconfig = this.getTagConfig(tag);
        return !!tagconfig && tagconfig.tag in this.tags;
    }

    async validateImagePath(imagePath: string | undefined, resourcePath: string, def?: string): Promise<string | undefined> {
        if (!imagePath) {
            return def;
        }

        imagePath = await fileutil.massageOSPath(pathlib.join(resourcePath, imagePath));

        if (!imagePath || !(await fileutil.stat(imagePath)).isFile()) {
            printf(`Failed loading image for Entity ${this.name} (${this.type}.${this.variant}.${this.subtype}):`, imagePath);
            return def;
        }

        return imagePath;
    }

    static COPYABLE_ATTRIBUTES = new Set<keyof Entity>([
        "type",
        "variant",
        "subtype",
        "imagePath",
        "editorImagePath",
        "overlayImagePath",
        "baseHP",
        "placeVisual",
        "disableOffsetIndicator",
        "renderPit",
        "renderRock",
        "mirrorX",
        "mirrorY",
    ]);

    static DEFAULTS = new Entity();

    fillFromConfig(config: Entity) {
        for (const attribute of Entity.COPYABLE_ATTRIBUTES.keys()) {
            const defaultValue = Entity.DEFAULTS[attribute];
            const selfValue = this[attribute];
            if (selfValue === defaultValue) {
                const configValue = config[attribute];
                (this[attribute] as typeof configValue) = configValue;
            }
        }

        for (const tag of Object.values(config.tags)) {
            this.addTag(tag);
        }

        this.bitfields.push(...config.bitfields);
        this.hasBitfields = this.bitfields.length > 0;
        this.invalidBitfield = this.invalidBitfield || config.invalidBitfield;
    }

    static ENTITY_CLEAN_NAME_REGEX = /[^\w\d]/g;

    getEntities2Node(): {
        entities2Node?: Entities2XmlNode;
        invalid: boolean;
        mismatchedName?: string;
    } {
        if (
            !this.mod ||
            this.matches({
                tags: ["Metadata", "Grid"],
                matchAnyTag: true
            }) ||
            !this.mod.entities2root
        ) {
            return { invalid: false };
        }

        const adjustedId = this.type === EntityType.STB_EFFECT ? EntityType.EFFECT : this.type;
        const query = (ent: Entities2XmlNode) =>
            ent.attrib.id === adjustedId && ent.attrib.variant === this.variant;

        let validMissingSubtype = false;

        let entities2Node = this.mod.entities2root.entities.entity.find(ent =>
            query(ent) && ent.attrib.subtype ===this.subtype
        );
        if (!entities2Node) {
            entities2Node = this.mod.entities2root.entities.entity.find(query);
            validMissingSubtype = entities2Node !== undefined;
        }

        if (!entities2Node) {
            return { invalid: true };
        }

        let mismatchedName: string | undefined;
        const foundName = entities2Node.attrib.name;
        const givenName = this.name ?? '';
        const [ foundNameClean, givenNameClean ] = [ foundName, givenName ].map(s =>
            s.replace(Entity.ENTITY_CLEAN_NAME_REGEX, "").toLowerCase()
        );
        if (!(foundNameClean === givenNameClean || (
            validMissingSubtype && (
                givenNameClean.includes(foundNameClean) ||
                foundNameClean.includes(givenNameClean)
            )
        ))) {
            mismatchedName = foundName;
        }

        return { entities2Node, invalid: false, mismatchedName };
    }

    async fillFromNode(node: EntityNode): Promise<string> {
        let warnings = "";
        node.attrib ??= {} as EntityNode["attrib"];

        if (node.attrib.Name)
            this.name = node.attrib.Name;

        if (node.attrib.ID)
            this.type = node.attrib.ID;

        if (node.attrib.Variant)
            this.variant = node.attrib.Variant;

        if (node.attrib.Subtype)
            this.subtype = node.attrib.Subtype;

        if (node.attrib.Image) {
            this.imagePath = await this.validateImagePath(
                node.attrib.Image,
                this.mod?.resourcePath ?? '',
                "resources/Entities/questionmark.png",
            ) ?? '';
        }

        if (node.attrib.EditorImage) {
            this.editorImagePath = await this.validateImagePath(
                node.attrib.EditorImage, this.mod?.resourcePath ?? ''
            );
        }

        if (node.attrib.OverlayImage) {
            this.overlayImagePath = await this.validateImagePath(
                node.attrib.OverlayImage, this.mod?.resourcePath ?? ''
            ) ?? '';
        }

        // Tags="" attribute allows overriding default tags with nothing / different tags
        const tagsString = node.attrib.Tags;
        if (tagsString) {
            this.tags = {};
            if (tagsString !== "") {
                for (const tag of tagsString.split(",")) {
                    this.addTag(tag.trim());
                }
            }
        }

        const tags = node.entity?.filter((elem): elem is TagNode => 'tag' in elem);
        for (const tag of tags ?? []) {
            this.addTag(tag.tag[0].innerText);
        }

        for (const tag of Object.values(this.tagConfig?.tags ?? {})) {
            if (tag.attribute) {
                const attribute = node.attrib[tag.attribute];
                if (attribute === 1) {
                    this.addTag(tag);
                }
                else if (attribute === 0) {
                    this.removeTag(tag);
                }
            }
        }

        if (node.attrib.DisableOffsetIndicator)
            this.disableOffsetIndicator = !!node.attrib.DisableOffsetIndicator;

        if (node.attrib.UsePitTiling)
            this.renderPit = !!node.attrib.UsePitTiling;

        if (node.attrib.UseRockTiling)
            this.renderRock = !!node.attrib.UseRockTiling;

        const { entities2Node, invalid, mismatchedName } = this.getEntities2Node();
        if (invalid) {
            warnings += "\nHas no entry in entities2.xml!";
            this.invalid = true;
        }

        if (mismatchedName)
            warnings += `\nFound name mismatch! In entities2: ${mismatchedName}; In BR: ${this.name}`;

        if (node.attrib.BaseHP) {
            this.baseHP = node.attrib.BaseHP;
        }
        else if (this.baseHP === undefined && entities2Node) {
            this.baseHP = entities2Node.attrib.baseHP;
        }

        if (!!node.attrib.Boss || !!entities2Node?.attrib.boss)
            this.addTag("Boss");

        if (!!node.attrib.Champion || !!entities2Node?.attrib.champion)
            this.addTag("Champion");

        if (node.attrib.PlaceVisual)
            this.placeVisual = node.attrib.PlaceVisual;

        if (node.attrib.Invalid)
            this.invalid = true;

        const gfx = node.entity?.filter((elem): elem is GfxNode => 'gfx' in elem);
        if (gfx && gfx.length > 0) {
            this.gfx = gfx?.[0];
            const bgPrefix = this.gfx?.attrib?.BGPrefix;
            if (bgPrefix && this.gfx.attrib) {
                this.gfx.attrib.BGPrefix = await fileutil.massageOSPath(
                    pathlib.join(this.mod?.resourcePath ?? '', bgPrefix)
                );
            }
        }

        function getMirrorEntity(s: string): [ number, number?, number? ] {
            return s.split(".").map(i => +i) as [ number, number?, number? ];
        }

        const mirrorX = node.attrib.MirrorX, mirrorY = node.attrib.MirrorY;
        if (mirrorX) {
            this.mirrorX = getMirrorEntity(mirrorX);
        }
        if (mirrorY) {
            this.mirrorY = getMirrorEntity(mirrorY);
        }

        const bitfields = node.entity?.filter((elem): elem is BitfieldNode => 'bitfield' in elem);
        if (bitfields && bitfields.length > 0) {
            this.hasBitfields = true;
            for (const bitfieldNode of bitfields) {
                const bitfield = new Bitfield(bitfieldNode);
                if (bitfield.isInvalid()) {
                    this.invalidBitfield = true;
                    warnings += "\nHas invalid bitfield elements and cannot be configured";
                    break;
                }
                else {
                    this.bitfields.push(bitfield);
                }
            }
        }

        const rangeWarnings = this.getOutOfRangeWarnings();
        if (rangeWarnings) {
            warnings += "\nOut of range:" + rangeWarnings;
        }

        if (warnings) {
            warnings = `\nWarning for Entity ${this.name} (${this.type}.${this.variant}.${this.subtype}) from ${this.mod?.name}:`
                        + warnings;
        }

        return warnings;
    }

    hasBitfieldKey(key: string): boolean {
        return this.bitfields.some(bitfield => bitfield.key === key);
    }

    getBitfieldElements(): BitfieldElement[] {
        return _.flatten(this.bitfields.map(b => b.elements));
    }

    getOutOfRangeWarnings(): string {
        let warnings = "";
        if ((this.type >= 1000 || this.type < 0) && !this.hasTag("Grid")) {
            warnings += `\nType ${this.type} is outside the valid range of 0 - 999! This will not load properly in-game!`;
        }
        if ((this.variant >= 4096 || this.variant < 0) && !this.hasBitfieldKey("Variant")) {
            warnings += `\nVariant ${this.variant} is outside the valid range of 0 - 4095!`;
        }
        if ((this.subtype >= 4096 || this.subtype < 0) && this.type !== EntityType.PICKUP && !this.hasBitfieldKey("Subtype")) {
            warnings += `\nSubtype ${this.subtype} is outside the valid range of 0 - 4095!`;
        }

        return warnings;
    }

    isOutOfRange(): boolean {
        return this.getOutOfRangeWarnings() !== "";
    }

    getEditorWarnings(): string {
        let warnings = this.getOutOfRangeWarnings();
        if (this.invalid) {
            warnings += "\nMissing entities2.xml entry! Trying to spawn this WILL CRASH THE GAME!!";
        }
        if (this.invalidBitfield) {
            warnings += "\nHas incorrectly defined bitfield properties, cannot be configured";
        }
        else if (this.hasBitfields) {
            warnings += "\nMiddle-click to configure entity properties";
        }

        return warnings;
    }

    printTags(): string {
        if (!this.tagConfig) {
            return "undefined";
        }

        return `[${
            Object.values(this.tagConfig.tags).filter(tag => this.hasTag(tag) && tag.label)
            .map(t => t.label).join(", ")
        }]`;
    }

    matches({
        entitytype,
        variant,
        subtype,
        name,
        tags,
        matchAnyTag=false,
    }: Partial<{
        entitytype: number;
        variant: number;
        subtype: number;
        name: string;
        tags: string[];
        matchAnyTag: boolean;
    }>) {
        if (name && this.name !== name) {
            return false;
        }
        if (entitytype !== undefined && this.type !== entitytype) {
            return false;
        }
        if (variant !== undefined && (this.variant !== variant && !this.hasBitfieldKey("Variant"))) {
            return false;
        }
        if (subtype !== undefined && (this.subtype !== subtype && !this.hasBitfieldKey("Subtype"))) {
            return false;
        }
        if (tags !== undefined) {
            let matchedAny = false;
            for (const tag of tags) {
                if (this.hasTag(tag)) {
                    matchedAny = true;
                }
                else if (!matchAnyTag) {
                    return false;
                }
            }

            if (!matchedAny) {
                return false;
            }
        }

        return true;
    }
}

export class EntityGroup {
    name: string;
    label?: string;
    parent?: EntityGroup;

    entityDefaults?: Entity;
    entries: Array<Entity | EntityGroup> = [];
    groupentries: EntityGroup[] = [];

    constructor(node?: {
        attrib: { Name: string; Label?: string; };
    }, name?: string, label?: string, parentGroup?: EntityGroup) {
        if (node) {
            this.label = node.attrib.Label;
            this.name = node.attrib.Name ?? this.label;
        }
        else {
            this.name = name as string;
            this.label = label;
        }

        this.parent = parentGroup;

        this.entityDefaults = undefined;
        if (this.parent?.entityDefaults) {
            this.entityDefaults = new Entity(
                this.parent.entityDefaults.mod, this.parent.entityDefaults.tagConfig
            );
            this.entityDefaults.fillFromConfig(this.parent.entityDefaults);
        }
    }

    addEntry(entry: EntityGroup | Entity) {
        this.entries.push(entry);
        if (entry instanceof EntityGroup) {
            this.groupentries.push(entry);
        }
    }
}

export class EntityTab extends EntityGroup {
    iconSize?: { width: number; height: number; };

    constructor(node?: TabNode, name?: string) {
        super(node, name);

        if (node) {
            const iconSize = node.attrib.IconSize;
            if (iconSize) {
                const parts = iconSize.split(",").map(x => x.trim());
                if (parts.length === 2 && util.checkInt(parts[0]) && util.checkInt(parts[1])) {
                    this.iconSize = { width: +parts[0], height: +parts[1] };
                }
                else {
                    printf("Group", node, "has invalid IconSize, must be 2 integer values");
                }
            }
        }
    }
}

type TagData = {
    tag: string;
    label: string;
    filterable: boolean;
    statisticsgroup: boolean;
    attribute: keyof EntityNode["attrib"];
};

export class EntityTag {
    tags: Record<string, TagData> = {};

    getTag({ node, name }: Partial<{
        node: TagNode;
        name: string;
    }>): TagData | undefined {
        if (!name) {
            name = node?.tag[0]?.innerText;
            if (!name) {
                printf("Attempted to get tag with no text:", node);
                return undefined;
            }
        }

        if (!(name in this.tags)) {
            if (!node) {
                printf(`Attempted to get undefined tag ${name}`);
                return undefined;
            }

            const tag = node.tag[0].innerText;
            this.tags[tag] = {
                tag,
                label: node.attrib.Label,
                filterable: !!node.attrib.Filterable,
                statisticsgroup: !!node.attrib.StatisticsGroup,
                attribute: node.attrib.Attribute as keyof EntityNode["attrib"],
            };
        }

        return this.tags[name];
    }
}

type DataFile = {
    path: string;
    filetype: string;
    name: string;
};

export class Version {
    invalid: boolean;
    name: string;
    toload: Array<DataFile | Version> = [];

    constructor(node: VersionNode, versions: Record<string, Version>) {
        this.invalid = false;
        this.name = node.attrib.Name;
        if (!this.name) {
            printf('Version', node, 'does not have a Name');
        }

        const addFile = (filetype: string, node: FileNode) => {
            this.toload.push({
                filetype,
                path: node.attrib.File,
                name: node.attrib.Name,
            });
        };

        for (const dataNode of node.version) {
            if ("version" in dataNode) {
                const name = dataNode.attrib.Name;
                if (!name) {
                    printf("Cannot load version from node", node, "without Name");
                    this.invalid = true;
                }
                else if (!(name in versions)) {
                    printf('Cannot load version from node', node, 'because it is not defined');
                    this.invalid = true;
                }
                else {
                    this.toload.push(versions[name]);
                }
            }
            else if ("entities" in dataNode) {
                addFile("entities", dataNode);
            }
            else if ("stages" in dataNode) {
                addFile("stages", dataNode);
            }
            else if ("roomtypes" in dataNode) {
                addFile("roomtypes", dataNode);
            }
            else if ("roomshapes" in dataNode) {
                addFile("roomshapes", dataNode);
            }
            else if ("formats" in dataNode) {
                addFile("formats", dataNode);
            }
            else {
                printf(`Cannot load unknown file type ${Object.keys(dataNode)[0]} from node ${node.attrib}`);
                this.invalid = true;
            }
        }
    }

    allFiles(versions: Record<string, true> = {}): DataFile[] {
        const files: DataFile[] = [];
        const namedFiles: Record<string, number> = {};

        versions[this.name] = true;
        for (const entry of this.toload) {
            let addFiles: DataFile[];
            if (entry instanceof Version) {
                addFiles = entry.allFiles(versions);
            }
            else {
                addFiles = [entry];
            }

            for (const file of addFiles) {
                if (file.name) {
                    if (!(file.name in namedFiles)) {
                        namedFiles[file.name] = files.length;
                        files.push(file);
                    }
                    else {
                        files[namedFiles[file.name]] = file;
                    }
                }
                else {
                    files.push(file);
                }
            }
        }

        return files;
    }
}

export class Mod {
    name: string;
    resourcePath: string;
    modPath?: string;
    autogenerateContent: boolean;
    entities2root?: Entities2Root;

    constructor(
        modName="Basement Renovator",
        resourcePath="resources/",
        autogenerateContent=false,
    ) {
        this.name = modName;
        this.resourcePath = resourcePath;
        this.autogenerateContent = autogenerateContent;
    }

    async setModPath(path: string): Promise<void> {
        this.modPath = path;

        const entities2Path = pathlib.join(this.modPath, "content/entities2.xml");
        if ((await fileutil.stat(entities2Path)).isFile()) {
            try {
                const contents = await fileutil.read(entities2Path);
                const parser = new XML.Parser<Entities2Root>([]);
                this.entities2root = parser.decode(contents);
            }
            catch (e) {
                printf(`ERROR parsing entities2 xml for mod "${this.name}": ${e}`);
            }
        }
    }
}

export type Wall = {
    points: Array<util.Point>;
    normal: util.Point;
    doors: Array<Door>;
};

export type RoomShape = {
    id: number;
    name: string;
    dims: util.Size;
    baseShape?: string;
    topLeft?: util.Point;
    mirrorX?: string;
    mirrorY?: string;
    walls: Wall[];
};