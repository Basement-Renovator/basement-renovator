from __future__ import annotations
from typing import TYPE_CHECKING

import xml.etree.cElementTree as ET
from xml.dom import minidom
import os
import re

if not __package__:
    import anm2 as anm2
    from util import printf
else:
    import src.anm2 as anm2
    from src.util import printf


if TYPE_CHECKING:
    from src.lookup import MainLookup


def generateXMLFromEntities2(
    modConfig: MainLookup.ModConfig, entities2Root: ET.Element
):
    cleanUp = re.compile(r"[^\w\d]")
    outputDir = f"resources/Entities/ModTemp/{cleanUp.sub('', modConfig.name)}"
    if not os.path.isdir(outputDir):
        os.mkdir(outputDir)

    # assume by merit of coming from resources/entities2 that the anm2root is relative to the resources folder
    anm2root = "resources/" + entities2Root.get("anm2root")

    # Iterate through all the entities
    enList = entities2Root.findall("entity")

    # Skip if the mod is empty
    if len(enList) == 0:
        return

    printf(f'-----------------------\nLoading entities from "{modConfig.name}"')

    def mapEn(en):
        # Fix some shit
        i = int(en.get("id"))
        isEffect = i == 1000
        if isEffect:
            i = 999
        v = en.get("variant") or "0"
        s = en.get("subtype") or "0"

        if i >= 1000 or i in (0, 1, 3, 7, 8, 9):
            printf(f"Skipping: Invalid entity type {i}:", en.get("name"))
            return None

        anm2Path = en.get("anm2path")
        if not anm2Path:
            printf("Skipping: No anm2 path for entity", en.get("name"))
            return None

        # Grab the anm location
        anm2Path = os.path.join(anm2root, anm2Path)
        resolvedPath = modConfig.resolveResource(anm2Path)
        printf("LOADING:", resolvedPath)
        if not os.path.isfile(resolvedPath):
            printf("Skipping: Invalid anm2!", anm2Path)
            return None

        anim = anm2.Config(resolvedPath, modConfig)
        anim.setAnimation()
        anim.frame = anim.animLen - 1
        img = anim.render()

        filename = "resources/Entities/questionmark.png"
        if img:
            # Save it to a Temp file - better than keeping it in memory for user retrieval purposes?
            resDir = os.path.join(outputDir, "icons")
            if not os.path.isdir(resDir):
                os.mkdir(resDir)
            filename = os.path.join(
                resDir, f'{en.get("id")}.{v}.{s} - {en.get("name")}.png'
            )
            img.save(filename, "PNG")
        else:
            printf(
                f"Could not render icon for entity {i}.{v}.{s}, anm2 path:",
                resolvedPath,
            )

        # Write the modded entity to the entityXML temporarily for runtime
        entityTemp = ET.Element("entity")
        entityTemp.set("Name", en.get("name"))
        entityTemp.set("ID", str(i))
        entityTemp.set("Variant", v)
        entityTemp.set("Subtype", s)
        entityTemp.set("Image", filename)

        def condSet(setName, name):
            val = en.get(name)
            if val is not None:
                entityTemp.set(setName, val)

        condSet("BaseHP", "baseHP")
        condSet("Boss", "boss")
        condSet("Champion", "champion")

        i = int(i)
        entityTemp.set("Group", f"(Mod) {modConfig.name}")
        entityTemp.set("Kind", "Mods")
        if i == 5:  # pickups
            if v == 100:  # collectible
                return None
            entityTemp.set("Kind", "Pickups")
        elif i in (2, 4, 6):  # tears, live bombs, machines
            entityTemp.set("Kind", "Stage")
        elif en.get("boss") == "1":
            entityTemp.set("Kind", "Bosses")
        elif isEffect:
            entityTemp.set("Kind", "Effects")
        else:
            entityTemp.set("Kind", "Enemies")

        return entityTemp

    result = list(filter(lambda x: x is not None, map(mapEn, enList)))

    outputRoot = ET.Element("data")
    outputRoot.extend(result)
    with open(os.path.join(outputDir, "EntitiesMod.xml"), "w") as out:
        xml = minidom.parseString(ET.tostring(outputRoot)).toprettyxml(indent="    ")
        s = str.replace(xml, outputDir + os.path.sep, "").replace(os.path.sep, "/")
        out.write(s)

    return result
