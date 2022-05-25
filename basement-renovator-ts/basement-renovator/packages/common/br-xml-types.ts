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
    choice?: {
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
    tag: {
        innerText: string;
    }[];
};

export type TabNode = {
    attrib: {
        Name: string;
        IconSize?: string;
    };
    tab: Array<GroupNode | EntityNode>;
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
    entity?: Array<TagNode & {
        attrib: Partial<TagNode["attrib"]>;
    } | GfxNode | BitfieldNode>;
};

export type EntityXml = {
    data: Array<TabNode | GroupNode | EntityNode | TagNode>;
};

export type GroupNode = {
    attrib: {
        Name: string;
        Label?: string;
    };
    group: Array<{ defaults: EntityNode[]; } | GroupNode | EntityNode>;
}

export type GfxNode = {
    attrib?: Partial<{
        BGPrefix: string;
        StageGfx: string;
        RoomGfx: string;
        HasBigBG: unknown;
        Subtype: number;
    }>;
    gfx?: Partial<EntityNode>[];
};

export type StageNode = {
    attrib: {
        Name: string;
        BaseGamePath?: string;
        Stage: number;
        StageType: number;
        Pattern: string;
    };
    stage?: GfxNode[];
};

export type StageXml = {
    data: StageNode[];
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
    room?: GfxNode[];
};

export type RoomTypeXml = {
    data: RoomTypeNode[];
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
    version: Array<VersionNode | FileNode & Choice<{
        entities: unknown;
        stages: unknown;
        roomtypes: unknown;
        roomshapes: unknown;
        formats: unknown;
    }>>;
};

export type VersionXML = {
    data: VersionNode[];
};

export type PositionNode = {
    attrib: Partial<{
        x: number;
        y: number;
    }>;
};

export type BaseShapeNode = PositionNode & {
    attrib: {
        Name: string;
    };
    shape: unknown;
};

export type MirrorShapeNode = {
    attrib: Partial<{
        // names of mirror shapes
        x: string;
        y: string;
    }>;
    mirror: unknown;
};

export type WallShapeNode = PositionNode & {
    wall: Array<PositionNode & Choice<{
        point: unknown;
        normal: unknown;
        door: unknown;
    }>>;
};

export type RoomShapeNode = {
    attrib: {
        ID: number;
        Name: string;
        Width: number;
        Height: number;
    };
    shape: Array<BaseShapeNode | MirrorShapeNode | WallShapeNode>;
};

export type RoomShapeXml = {
    data: RoomShapeNode[];
};