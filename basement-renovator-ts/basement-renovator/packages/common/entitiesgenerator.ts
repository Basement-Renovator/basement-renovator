import { XMLBuilder } from 'fast-xml-parser';
import { promises as fs } from 'fs';
import pathlib from 'path';

import Anm2 from './anm2';
import { EntityNode } from './br-xml-types';
import { EntityType, PickupVariant } from './constants';
import * as fileutil from './fileutil';
import { printf } from './util';

export type Entities2XmlNode = {
    attrib: {
        id: number;
        variant: number;
        subtype?: number;
        name: string;
        baseHP: number;
        boss: unknown;
        champion: unknown;
        anm2path: string;
    };
};

export type Entities2Root = {
    entities: {
        attrib: {
            anm2root: string;
        };
        entity: Entities2XmlNode[];
    };
}

export async function generateXMLFromEntities2(
    modPath: string,
    modName: string,
    entities2Root: Entities2Root,
    resourcePath: string
): Promise<{ data: EntityNode[]; } | undefined> {
    const cleanUp = /[^\w\d]/g;
    const outputDir = `resources/Entities/ModTemp/${modName.replace(cleanUp, '')}`;
    if (!(await fileutil.stat(outputDir)).isDir()) {
        await fs.mkdir(outputDir, { recursive: true });
    }

    const anm2root = entities2Root.entities.attrib.anm2root;

    // Iterate through all the entities
    const enList = entities2Root.entities.entity;

    // Skip if the mod is empty
    if (enList.length === 0) {
        return undefined;
    }

    printf(`-----------------------\nLoading entities from "${modName}"`);

    async function mapEn(en: Entities2XmlNode): Promise<EntityNode | undefined> {
        // Fix some shit
        let i = en.attrib.id;
        const isEffect = i === EntityType.EFFECT;
        if (isEffect) {
            i = EntityType.STB_EFFECT;
        }
        const v = en.attrib.variant ?? 0;
        const s = en.attrib.subtype ?? 0;

        if (i > EntityType.STB_EFFECT || [
            EntityType.DECORATION,
            EntityType.PLAYER,
            EntityType.FAMILIAR,
            EntityType.LASER,
            EntityType.KNIFE,
            EntityType.PROJECTILE,
        ].includes(i)) {
            printf(`Skipping: Invalid entity type ${i}: ${en.attrib.name}`);
            return undefined;
        }

        // Grab the anm location
        let anmPath = await fileutil.massageOSPath(
            pathlib.join(modPath, "resources", anm2root, en.attrib.anm2path)
        ) ?? "";
        printf("LOADING:", anmPath);
        if (!(await fileutil.stat(anmPath)).isFile()) {
            anmPath = await fileutil.massageOSPath(
                pathlib.join(resourcePath, anm2root, en.attrib.anm2path)
            ) ?? "";

            printf("REDIRECT LOADING:", anmPath)
            if (!(await fileutil.stat(anmPath)).isFile()) {
                printf("Skipping: Invalid anm2!");
                return undefined;
            }
        }

        const anim = new Anm2(anmPath, resourcePath);
        anim.setAnimation();
        anim.anim.frame = anim.anim.len - 1;

        const img = await anim.render();

        let filename = "resources/Entities/questionmark.png"
        if (img) {
            // Save it to a Temp file - better than keeping it in memory for user retrieval purposes?
            const resDir = pathlib.join(outputDir, "icons");
            fileutil.ensureDir(resDir);

            const filename = pathlib.join(resDir, `${en.attrib.id}.${v}.${s} - ${en.attrib.name}.png`);
            await img.toFile(filename);
        }
        else {
            printf(`Could not render icon for entity ${i}.${v}.${s}, anm2 path:`, anmPath);
        }

        // Write the modded entity to the entityXML temporarily for runtime
        const entityTemp: EntityNode = {
            attrib: {
                Name: en.attrib.name,
                ID: i,
                Variant: v,
                Subtype: s,
                Image: filename,
                BaseHP: en.attrib.baseHP,
                Boss: en.attrib.boss,
                Champion: en.attrib.champion,
                Group: `(Mod) ${modName}`,
                Kind: "Mods",
            }
        };

        if (i === EntityType.PICKUP) {
            if (v === PickupVariant.COLLECTIBLE) {
                return undefined;
            }
            entityTemp.attrib.Kind = "Pickups";
        }
        else if ([
            EntityType.TEAR,
            EntityType.LIVEBOMB,
            EntityType.MACHINE
        ].includes(i)) {
            entityTemp.attrib.Kind = "Stage";
        }
        else if (en.attrib.boss) {
            entityTemp.attrib.Kind = "Bosses";
        }
        else if (isEffect) {
            entityTemp.attrib.Kind = "Effects";
        }
        else {
            entityTemp.attrib.Kind = "Enemies";
        }

        return entityTemp;
    }

    const result = (await Promise.all(enList.map(mapEn)))
        .filter((x): x is Exclude<typeof x, undefined> => x !== undefined);

    const outputRoot = { data: result };

    const builder = new XMLBuilder({
        attributesGroupName: 'attrib',
        format: true,
        indentBy: '    ',
    });

    const xml = builder.build(outputRoot);

    const contents = xml
        .replace(outputDir + pathlib.sep, "")
        .replace(pathlib.sep, "/");

    await fileutil.write(pathlib.join(outputDir, "EntitiesMod.xml"), contents, {
        truncate: true,
    });

    return outputRoot;
}
