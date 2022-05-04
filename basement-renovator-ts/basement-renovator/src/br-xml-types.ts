import { Choice } from "./util";

export type BitfieldWidgetNode = {
    attrib: {
        Length: number;
        Offset: number;
        Name: string;
        Unit?: string;
        ValueOffset?: number;
        Minimum?: number;
        Maximum?: number;
        ScalarRange?: number;
    }
    tooltip?: { innerText: string; };
};

type DropdownNode = BitfieldWidgetNode & {
    choice: {
        attrib: {
            Value?: number;
        };
        innerText: string;
    }[];
};

export type Widgets = {
    spinner:  BitfieldWidgetNode;
    dropdown: DropdownNode;
    slider:   BitfieldWidgetNode;
    dial:     BitfieldWidgetNode;
    checkbox: BitfieldWidgetNode;
    bitmap:   BitfieldWidgetNode;
};

export type BitfieldNode = {
    attrib: {
        Key: string;
    };
    bitfield: Choice<Widgets>[];
}

export type TagNode = {
    attrib: {
        Label: string;
        Attribute: string;
        Filterable?: unknown;
        StatisticsGroup?: unknown;
    };
    innerText: string;
};

export type TabNode = {
    attrib: {
        Name: string;
        IconSize?: string;
    };
    tab: Choice<{
        group: GroupNode;
        entity: EntityNode;
    }>[];
};

export type EntityNode = {
    attrib: {
        ID: number;
        Variant?: number;
        Subtype?: number;
        Name: string;
        Image: string;
        EditorImage?: string;
        OverlayImage?: string;
        Tags?: string;
        PlaceVisual?: string;
        DisableOffsetIndicator?: unknown;
        UsePitTiling?: unknown;
        UseRockTiling?: unknown;
        InvertDepth?: unknown;
        MirrorX?: string;
        MirrorY?: string;
        BaseHP?: number;

        Overwrite?: unknown;
        Invalid?: unknown;
        Kind?: string;
        Group?: string;
        Boss?: unknown;
        Champion?: unknown;
    };
    tag?: Array<TagNode & {
        attrib: Partial<TagNode["attrib"]>;
    }>;
    gfx?: GfxNode[];
    bitfield?: BitfieldNode[];
};

export type EntityXml = {
    data: Choice<{
        tab: TabNode;
        group: GroupNode;
        entity: EntityNode;
        tag: TagNode
    }>[];
};

export type GroupNode = {
    attrib: {
        Name: string;
        Label?: string;
    };
    group: Choice<{
        defaults: {
            entity?: EntityNode[];
        };
        group: GroupNode;
        entity: EntityNode;
    }>[];
}

export type GfxNode = {
    attrib?: Partial<{
        BGPrefix: string;
        StageGfx: string;
        RoomGfx: string;
        HasBigBG: unknown;
        Subtype: number;
    }>;
    entity?: Partial<EntityNode>[];
};

export type StageNode = {
    attrib: {
        Name: string;
        BaseGamePath?: string;
        Stage: number;
        StageType: number;
        Pattern: string;
    };
    gfx?: GfxNode[];
};

export type StageXml = {
    data: { stage: StageNode[]; };
};

export type RoomTypeNode = {
    attrib: {
        Name: string;
        StageName: string;
        Icon?: string;
        ShowInMenu?: unknown;
        Type?: number;
        ID?: string | number;
        Subtype?: string | number;
        NameRegex?: string;
    };
    gfx?: GfxNode[];
};

export type RoomTypeXml = {
    data: { room: RoomTypeNode[]; };
};

export type FileNode = {
    attrib: {
        File: string;
        Name: string;
    };
};

export type VersionNode = {
    attrib: {
        Name: string;
    };
    version: Choice<{
        version: VersionNode;
        entities: FileNode;
        stages: FileNode;
        roomtypes: FileNode;
        roomshapes: FileNode;
    }>[];
};

export type VersionXML = {
    data: {
        version: VersionNode[];
    };
};

type PositionNode = {
    attrib: Partial<{
        x: number;
        y: number;
    }>;
};

export type RoomShapeNode = {
    attrib: {
        ID: number;
        Name: string;
        Width: number;
        Height: number;
    };
    shape?: PositionNode & {
        attrib: {
            Name: string;
        };
    };
    mirror?: Partial<{
        // names of mirror shapes
        x: string;
        y: string;
    }>;
    wall: Array<PositionNode & {
        point: PositionNode[];
        normal: PositionNode[];
        door: PositionNode[];
    }>;
};

export type RoomShapeXml = {
    data: { shape: RoomShapeNode[]; };
};