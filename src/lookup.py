import xml.etree.cElementTree as ET
from xml.dom import minidom
import os, abc, re

from itertools import zip_longest
from PyQt5.QtGui import QImage

import src.anm2 as anm2
from src.constants import *

def printf(*args):
    print(*args, flush=True)

def bitGet(bits, bitStart, bitCount):
    value = 0
    for i in range(bitCount):
        bit = 1 << (bitStart + i)
        if bits & bit:
            value |= (1 << i)

    return value

def bitSet(bits, value, bitStart, bitCount):
    for i in range(bitCount):
        bit = 1 << i
        if value & bit:
            bits |= (1 << (bitStart + i))
        else:
            bits &= ~(1 << (bitStart + i))

    return bits

def linuxPathSensitivityTraining(path):

    path = path.replace("\\", "/")

    directory, file = os.path.split(os.path.normpath(path))

    if not os.path.isdir(directory):
        return None

    contents = os.listdir(directory)

    for item in contents:
        if item.lower() == file.lower():
            return os.path.normpath(os.path.join(directory, item))

    return os.path.normpath(path)


def sanitizePath(node, key, path):
    prefix = node.get(key)
    if prefix is not None:
        prefixPath = linuxPathSensitivityTraining(os.path.join(path, prefix))
        node.set(key, prefixPath)


def parseCriteria(txt):
    if not txt:
        return None

    tokens = list(filter(bool, re.split(r"[\[\(\)\],]", txt)))

    if txt[0] in ["[", "("]:
        start, end = txt[0], txt[-1]
        mini, maxi = tokens[0], tokens[1]

        if mini == "infinity":
            mini = lambda v: True
        else:
            miniv = int(mini)
            if start == "[":
                mini = lambda v: v >= miniv
            elif start == "(":
                mini = lambda v: v > miniv
            else:
                raise ValueError(f"Invalid range in text: {txt}")

        if maxi == "infinity":
            maxi = lambda v: True
        else:
            maxiv = int(maxi)
            if end == "]":
                maxi = lambda v: v <= maxiv
            elif end == ")":
                maxi = lambda v: v < maxiv
            else:
                raise ValueError(f"Invalid range in text: {txt}")

        return lambda v: mini(v) and maxi(v)

    tokens = list(map(int, tokens))
    return lambda v: v in tokens


def applyGfxReplacement(replacement, gfxchildren):
    for origgfx, newgfx in zip_longest(replacement.findall("Gfx"), gfxchildren):
        if newgfx is None:
            continue
        elif origgfx is None:
            replacement.append(newgfx)
            continue

        for key, val in newgfx.attrib.items():
            origgfx.set(key, val)

        for ent in newgfx.findall("Entity"):
            origent = None
            for orig in origgfx.findall(f'Entity[@ID="{ent.get("ID")}"]'):
                if orig.get("Variant", "0") == ent.get("Variant", "0") and orig.get(
                    "SubType", "0"
                ) == ent.get("SubType", "0"):
                    origent = orig
                    break
            if origent is not None:
                for key, val in ent.attrib.items():
                    origent.set(key, val)
            else:
                origgfx.append(ent)


class Lookup(metaclass=abc.ABCMeta):
    def __init__(self, prefix, version, subVer):
        version = version.replace("+", "Plus")
        self.setup(prefix, version, subVer)

    def setup(self, prefix, version, subVer):
        file = f"resources/{prefix}{version}.xml"
        if subVer is not None:
            fileN = f"resources/{prefix}{subVer}.xml"
            if os.path.exists(fileN):
                file = fileN

        tree = ET.parse(file)
        root = tree.getroot()

        self.xml = root

    @abc.abstractmethod
    def lookup(self):
        pass


class StageLookup(Lookup):
    def __init__(self, version, subVer, parent):
        super().__init__("Stages", version, subVer)
        self.parent = parent

    def loadFromMod(self, modPath, brPath, name):
        stageFile = os.path.join(brPath, "StagesMod.xml")
        if not os.path.isfile(stageFile):
            return

        print(f'-----------------------\nLoading stages from "{name}"')

        root = None
        try:
            tree = ET.parse(stageFile)
            root = tree.getroot()
        except Exception as e:
            print("Error loading BR xml:", e)
            return

        stageList = root.findall("stage")
        if not stageList:
            return

        def mapStage(stage):
            name = stage.get("Name")
            if name is None:
                print("Tried to load stage, but had missing name!", str(stage.attrib))
                return None

            print("Loading stage:", str(stage.attrib))

            replacement = self.xml.find(f'stage[@Name="{name}"]')

            if replacement is None and (
                stage.get("Stage") is None or stage.get("StageType") is None
            ):
                print(
                    "Stage has missing stage/stage type; this may not load properly in testing"
                )

            sanitizePath(stage, "BGPrefix", brPath)

            children = stage.findall("Gfx")
            for gfx in children:
                sanitizePath(gfx, "BGPrefix", brPath)

                for ent in gfx.findall("Entity"):
                    sanitizePath(ent, "Image", brPath)

            if replacement is not None:
                applyGfxReplacement(replacement, children)
                return None

            return stage

        stages = list(filter(lambda x: x is not None, map(mapStage, stageList)))
        if stages:
            self.xml.extend(stages)

    def lookup(
        self, path=None, name=None, stage=None, stageType=None, baseGamePath=None
    ):
        stages = list(self.xml.findall("stage"))

        if stage:
            st = str(stage)
            stages = list(filter(lambda s: s.get("Stage") == st, stages))

        if stageType:
            st = str(stageType)
            stages = list(filter(lambda s: s.get("StageType") == st, stages))

        if path is not None:
            stages = list(filter(lambda s: s.get("Pattern") in path, stages))

        if name:
            stages = list(filter(lambda s: s.get("Name") == name, stages))

        if baseGamePath:
            hasBasePath = None
            if isinstance(baseGamePath, bool):
                hasBasePath = lambda s: s.get("BaseGamePath") is not None
            else:
                hasBasePath = lambda s: s.get("BaseGamePath") == baseGamePath
            stages = list(filter(hasBasePath, stages))

        return stages

    def getGfx(self, node):
        gfx = node.find("Gfx")
        return node if gfx is None else gfx


class RoomTypeLookup(Lookup):
    def __init__(self, version, subVer, parent):
        super().__init__("RoomTypes", version, subVer)
        self.parent = parent

    def loadFromMod(self, modPath, brPath, name):
        roomTypeFile = os.path.join(brPath, "RoomTypesMod.xml")
        if not os.path.isfile(roomTypeFile):
            return

        print(f'-----------------------\nLoading room types from "{name}"')

        root = None
        try:
            tree = ET.parse(roomTypeFile)
            root = tree.getroot()
        except Exception as e:
            print("Error loading BR xml:", e)
            return

        roomTypeList = root.findall("room")
        if not roomTypeList:
            return

        def mapRoomType(roomType):
            name = roomType.get("Name")
            if name is None:
                print(
                    "Tried to load room type, but had missing name!",
                    str(roomType.attrib),
                )
                return None

            print("Loading room type:", str(roomType.attrib))

            replacement = self.xml.find(f'room[@Name="{name}"]')

            sanitizePath(roomType, "Icon", brPath)

            children = roomType.findall("Gfx")
            for gfx in children:
                sanitizePath(gfx, "BGPrefix", brPath)

                for ent in gfx.findall("Entity"):
                    sanitizePath(ent, "Image", brPath)

            if replacement is not None:
                applyGfxReplacement(replacement, children)
                return None

            return roomType

        roomTypes = list(
            filter(lambda x: x is not None, map(mapRoomType, roomTypeList))
        )
        if roomTypes:
            self.xml.extend(roomTypes)

    def filterRoom(self, node, room, path=None):
        typeF = node.get("Type")
        if typeF and typeF != str(room.info.type):
            return False

        nameRegex = node.get("NameRegex")
        if nameRegex and not re.match(nameRegex, room.name):
            return False

        stage = node.get("StageName")
        # TODO replace with check against room file stage
        if (
            stage
            and path
            and not next(
                (
                    st
                    for st in self.parent.stages.lookup(path=path)
                    if st.get("Name") == stage
                ),
                [],
            )
        ):
            return False

        idCriteria = parseCriteria(node.get("ID"))
        if idCriteria and not idCriteria(room.info.variant):
            return False

        return True

    def lookup(self, room=None, name=None, roomfile=None, path=None, showInMenu=None):
        rooms = list(self.xml.findall("room"))

        if name:
            rooms = list(filter(lambda r: r.get("Name") == name, rooms))

        if showInMenu is not None:
            rooms = list(
                filter(
                    lambda node: (node.get("ShowInMenu") == "1") == showInMenu, rooms
                )
            )

        if room:
            rooms = list(
                filter(lambda node: self.filterRoom(node, room, path=path), rooms)
            )

        return rooms

    def getMainType(self, room=None, roomfile=None, path=None):
        candidates = self.lookup(room=room, path=path)
        if not candidates:
            return None

        getCritWeight = lambda r, k, w: w if r.get(k) is not None else 0

        candidates = sorted(
            candidates,
            key=lambda r: -(
                getCritWeight(r, "Type", 1)
                + getCritWeight(r, "NameRegex", 10)
                + getCritWeight(r, "StageName", 10)
                + getCritWeight(r, "ID", 10)
            ),
        )

        return candidates[0]

    def getGfx(self, node, room=None, roomfile=None, path=None):
        possibleGfx = node.findall("Gfx")
        possibleGfx = sorted(possibleGfx, key=lambda g: -len(g.attrib))

        if room is None:
            return possibleGfx[0]

        for gfx in possibleGfx:
            if self.filterRoom(gfx, room, path=path):
                return gfx

        return None

class EntityLookup(Lookup):
    PICKUPS_WITH_SPECIAL_SUBTYPES = (
        PickupVariant["COLLECTIBLE"],
        PickupVariant["TRINKET"],
        PickupVariant["PILL"]
    )

    class EntityConfig():
        class Parameter():
            def __init__(self, node):
                self.prefix = node.get("Prefix") or ""
                self.suffix = node.get("Suffix") or ""
                self.bitoffset = int(node.get("BitOffset") or 0)
                self.bits = int(node.get("BitCount") or 12)

                self.bitmask = ((1 << self.bits) - 1)

                self.basevalue = int(node.get("BaseValue") or 0)

                self.minimum = int(node.get("Minimum") or 0) or 0
                self.maximum = int(node.get("Maximum") or self.bitmask)

                self.secondrange = node.get("SecondRange")
                if self.secondrange:
                    self.secondrange = float(self.secondrange) * 30
                    self.secondrange = int(self.secondrange)

                self.display = node.get("Display") or "Spinner"
                self.tooltip = node.get("Tooltip")

                self.dropdownkeys = None
                self.dropdownvalues = None
                if self.display == "Dropdown":
                    self.dropdownkeys = []
                    self.dropdownvalues = []
                    values = node.findall("value")
                    i = 0
                    for value in values:
                        self.dropdownkeys.append(value.get("Name") or str(i))
                        self.dropdownvalues.append(int(value.get("Value") or i))
                        i = i + 1

            def getBitValue(self, subtype):
                subtype = bitGet(subtype, self.bitoffset, self.bits)

                return subtype

            def setBitValue(self, subtype, value):
                subtype = bitSet(subtype, value, self.bitoffset, self.bits)

                return subtype

            def getValueFromIndex(self, index):
                if self.dropdownvalues:
                    return self.dropdownvalues[index]

                if self.display == "Dial":
                    return (index - self.basevalue) % (self.maximum + 1)

                return index

            def getIndexedValue(self, subtype):
                value = self.getBitValue(subtype)

                if self.dropdownvalues:
                    return self.dropdownvalues.index(value)

                if self.display == "Dial":
                    return (value + self.basevalue) % (self.maximum + 1)

                return value

            def getDisplayValue(self, subtype):
                bitValue = self.getBitValue(subtype)
                if self.basevalue != 0 and self.display != "Dial":
                    bitValue += self.basevalue

                if self.secondrange:
                    bitValue = round(self.secondrange / bitValue / 30, 3)

                return bitValue

        def __init__(self, entity=None, resourcePath=None, modName=None, entities2Node=None):
            self.name = None
            self.mod = None
            self.type = None
            self.variant = None
            self.subtype = None
            self.imagePath = None
            self.editorImagePath = None
            self.overlayImagePath = None
            self.isGridEnt = None
            self.baseHP = None
            self.boss = None
            self.champion = None
            self.placeVisual = None
            self.disableOffsetIndicator = None
            self.blocksDoor = None
            self.renderPit = None
            self.renderRock = None
            self.invalid = None
            self.gfx = None
            self.mirrorX = None
            self.mirrorY = None
            self.kinds = None
            self.hasParameters = None
            self.inEmptyRooms = None

            if entity is not None:
                self.fillFromXML(entity, resourcePath, modName, entities2Node)

        def fillFromXML(self, entity, resourcePath, modName, entities2Node = None):
            imgPath = entity.get("Image") and linuxPathSensitivityTraining(
                os.path.join(resourcePath, entity.get("Image"))
            )
            editorImgPath = entity.get("EditorImage") and linuxPathSensitivityTraining(
                os.path.join(resourcePath, entity.get("EditorImage"))
            )
            overlayImgPath = entity.get("OverlayImage") and linuxPathSensitivityTraining(
                os.path.join(resourcePath, entity.get("OverlayImage"))
            )

            self.name = entity.get("Name")
            self.mod = modName
            self.type = int(entity.get("ID", "-1"))
            self.variant = int(entity.get("Variant", "0"))
            self.subtype = int(entity.get("Subtype", "0"))
            self.imagePath = imgPath
            self.editorImagePath = editorImgPath
            self.overlayImagePath = overlayImgPath
            self.isGridEnt = entity.get("IsGrid") == "1"
            self.baseHP = entities2Node.get("baseHP") if entities2Node else entity.get("BaseHP")
            self.boss = entities2Node.get("boss") if entities2Node else entity.get("Boss")
            self.champion = entities2Node.get("champion") if entities2Node else entity.get("Champion")
            self.placeVisual = entity.get("PlaceVisual")
            self.disableOffsetIndicator = entity.get("DisableOffsetIndicator") == "1"
            self.blocksDoor = entity.get("NoBlockDoors") != "1"
            self.renderPit = entity.get("UsePitTiling") == "1"
            self.renderRock = entity.get("UseRockTiling") == "1"
            self.inEmptyRooms = entity.get("InEmptyRooms") == "1"
            self.invalid = entity.get("Invalid")
            self.gfx = entity.find("Gfx")

            if self.gfx is not None:
                bgPrefix = self.gfx.get("BGPrefix")
                if bgPrefix:
                    self.gfx.set(
                        "BGPrefix",
                        linuxPathSensitivityTraining(os.path.join(resourcePath, bgPrefix)),
                    )

            def getMirrorEntity(s):
                return list(map(int, s.split(".")))

            mirrorX, mirrorY = entity.get("MirrorX"), entity.get("MirrorY")
            if mirrorX:
                self.mirrorX = getMirrorEntity(mirrorX)
            if mirrorY:
                self.mirrorY = getMirrorEntity(mirrorY)

            self.kinds = {}
            entitygroups = entity.findall("group")
            for entitygroup in entitygroups:
                entitykind = entitygroup.get("Kind") or entity.get("Kind")
                entitygroupname = entitygroup.get("Name") or entity.get("Group")
                if not entitykind in self.kinds:
                    self.kinds[entitykind] = []

                if not entitygroupname in self.kinds[entitykind]:
                    self.kinds[entitykind].append(entitygroupname)

            entitykind = entity.get("Kind")
            if entitykind is not None:
                if not entitykind in  self.kinds:
                    self.kinds[entitykind] = []

                entitygroupname = entity.get("Group")
                if (
                    entitygroupname is not None
                    and not entitygroupname in self.kinds[entitykind]
                ):
                    self.kinds[entitykind].append(entitygroupname)

            params = entity.findall("param")
            self.hasParameters = len(params) != 0
            self.parameters = []
            for param in params:
                self.parameters.append(EntityLookup.EntityConfig.Parameter(param))

    def __init__(self, version, subVer, parent):
        super().__init__("Entities", version, subVer)
        self.parent = parent

    def setup(self, prefix, version, subVer):
        file = f"resources/{prefix}{version}.xml"
        if subVer is not None:
            fileN = f"resources/{prefix}{subVer}.xml"
            if os.path.exists(fileN):
                file = fileN

        self.entityList = []
        self.loadXML(self.loadXMLFile(file))

    def loadXMLFile(self, path):
        root = None
        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except Exception as e:
            print("Error loading BR xml:", e)
            return

        return root

    def generateXMLFromEntities2(self, modPath, modName, entities2Root, resourcePath):
        cleanUp = re.compile(r"[^\w\d]")
        outputDir = f"resources/Entities/ModTemp/{cleanUp.sub('', modName)}"
        if not os.path.isdir(outputDir):
            os.mkdir(outputDir)

        anm2root = entities2Root.get("anm2root")

        # Iterate through all the entities
        enList = entities2Root.findall("entity")

        # Skip if the mod is empty
        if len(enList) == 0:
            return

        printf(f'-----------------------\nLoading entities from "{modName}"')

        def mapEn(en):
            # Fix some shit
            i = int(en.get("id"))
            isEffect = i == 1000
            if isEffect:
                i = 999
            v = en.get("variant") or "0"
            s = en.get("subtype") or "0"

            if i >= 1000 or i in (0, 1, 3, 7, 8, 9):
                printf("Skipping: Invalid entity type %d: %s" % (i, en.get("name")))
                return None

            # Grab the anm location
            anmPath = (
                linuxPathSensitivityTraining(
                    os.path.join(modPath, "resources", anm2root, en.get("anm2path"))
                )
                or ""
            )
            printf("LOADING:", anmPath)
            if not os.path.isfile(anmPath):
                anmPath = (
                    linuxPathSensitivityTraining(
                        os.path.join(resourcePath, anm2root, en.get("anm2path"))
                    )
                    or ""
                )

                printf("REDIRECT LOADING:", anmPath)
                if not os.path.isfile(anmPath):
                    printf("Skipping: Invalid anm2!")
                    return None

            anim = anm2.Config(anmPath, resourcePath)
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
                printf(f"Could not render icon for entity {i}.{v}.{s}, anm2 path:", anmPath)

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
            entityTemp.set("Group", "(Mod) %s" % modName)
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

    def loadXML(self, root, resourcePath="", modName="Base", entities2Root = None, fixIconFormat=False):
        entities = root.findall("entity")
        if not entities:
            return

        cleanUp = re.compile(r"[^\w\d]")

        def mapEntity(entity):
            entityType = int(entity.get("ID", "-1"))
            variant = int(entity.get("Variant", "0"))
            subtype = int(entity.get("Subtype", "0"))
            name = entity.get("Name")

            if (entityType >= 1000 or entityType < 0) and entity.get("IsGrid") != "1":
                printf(
                    f'Entity "{name}" from "{modName}" has a type outside the 0 - 999 range! ({entityType}) It will not load properly from rooms!'
                )

            if variant >= 4096 or variant < 0:
                printf(
                    f'Entity "{name}" from "{modName}" has a variant outside the 0 - 4095 range! ({variant})'
                )

            if (subtype >= 256 or subtype < 0) and (entityType != EntityType["PICKUP"] or variant not in EntityLookup.PICKUPS_WITH_SPECIAL_SUBTYPES):
                printf(
                    f'Entity "{name}" from "{modName}" has a subtype outside the 0 - 255 range! ({subtype})'
                )

            entityXML = None

            if entity.get("Metadata") != "1" and entity.get("IsGrid") != "1":
                adjustedId = "1000" if entityType == "999" else entityType
                query = f"entity[@id='{adjustedId}'][@variant='{variant}']"

                validMissingSubtype = False

                if entities2Root:
                    entityXML = entities2Root.find(query + f"[@subtype='{subtype}']")

                    if entityXML is None:
                        entityXML = entities2Root.find(query)
                        validMissingSubtype = entityXML is not None

                    if entityXML is None:
                        printf(
                            "Loading invalid entity (no entry in entities2 xml): "
                            + str(entity.attrib)
                        )
                        entity.set("Invalid", "1")
                    else:
                        foundName = entityXML.get("name")
                        givenName = entity.get("Name")
                        foundNameClean, givenNameClean = list(
                            map(lambda s: cleanUp.sub("", s).lower(), (foundName, givenName))
                        )
                        if not (
                            foundNameClean == givenNameClean
                            or (
                                validMissingSubtype
                                and (
                                    foundNameClean in givenNameClean
                                    or givenNameClean in foundNameClean
                                )
                            )
                        ):
                            printf(
                                "Loading entity, found name mismatch! In entities2: ",
                                foundName,
                                "; In BR: ",
                                givenName,
                            )

            entityConfig = self.lookupOne(entityType, variant, subtype)
            if entityConfig:
                printf(
                    f'Entity "{name}" from "{modName}" ({entityType}.{variant}.{subtype}) is overriding "{entityConfig.name}" from "{entityConfig.mod}"!'
                )
                entityConfig.fillFromXML(entity, resourcePath, modName, entityXML)
            else:
                entityConfig = self.EntityConfig(entity, resourcePath, modName, entityXML)

            if fixIconFormat:
                formatFix = QImage(entityConfig.imagePath)
                formatFix.save(entityConfig.imagePath)
                if entityConfig.editorImagePath:
                    formatFix = QImage(entityConfig.editorImagePath)
                    formatFix.save(entityConfig.editorImagePath)

            return entityConfig

        self.entityList.extend(list(map(mapEntity, entities)))

    def loadFromMod(self, modPath, brPath, name, autoGenerateModContent, fixIconFormat):
        entityFile = os.path.join(brPath, "EntitiesMod.xml")
        if not os.path.isfile(entityFile):
            return

        print(f'-----------------------\nLoading entities from "{name}"')

        # Grab mod Entities2.xml
        entities2Path = os.path.join(modPath, "content/entities2.xml")
        if os.path.exists(entities2Path):
            entities2Root = None
            try:
                entities2Root = ET.parse(entities2Path).getroot()
            except ET.ParseError as e:
                printf(f'ERROR parsing entities2 xml for mod "{name}": {e}')
                return

            if autoGenerateModContent:
                self.loadXML(self.generateXMLFromEntities2(modPath, name, entities2Root, brPath), brPath, name, entities2Root, fixIconFormat)

            self.loadXML(self.loadXMLFile(entityFile), brPath, name, entities2Root, fixIconFormat)

    def lookup(self, entitytype=None, variant=None, subtype=None, kind=None, group=None, inEmptyRooms=None):
        entities = self.entityList

        if entitytype:
            entities = list(filter(lambda entity: entity.type == entitytype, entities))

        if variant:
            entities = list(filter(lambda entity: entity.variant == variant, entities))

        if subtype:
            entities = list(filter(lambda entity: entity.subtype == subtype or entity.hasParameters, entities))

        if kind:
            if group:
                entities = list(filter(lambda entity: kind in entity.kinds and group in entity.kinds[kind], entities))
            else:
                entities = list(filter(lambda entity: kind in entity.kinds, entities))

        if inEmptyRooms:
            entities = list(filter(lambda entity: entity.inEmptyRooms == inEmptyRooms, entities))

        return entities

    def lookupOne(self, entitytype=None, variant=None, subtype=None, kind=None, group=None, inEmptyRooms=None):
        entities = self.lookup(entitytype, variant, subtype, kind, group, inEmptyRooms)

        return entities[0] if len(entities) > 0 else None


class MainLookup:
    def __init__(self, version, subVer):
        self.stages = StageLookup(version, subVer, self)
        self.roomTypes = RoomTypeLookup(version, subVer, self)
        self.entities = EntityLookup(version, subVer, self)

    def loadFromMod(self, modPath, brPath, name, autoGenerateModContent, fixIconFormat):
        self.stages.loadFromMod(modPath, brPath, name)
        self.roomTypes.loadFromMod(modPath, brPath, name)
        self.entities.loadFromMod(modPath, brPath, name, autoGenerateModContent, fixIconFormat)

    def getRoomGfx(self, room=None, roomfile=None, path=None):
        node = self.roomTypes.getMainType(room=room, roomfile=roomfile, path=path)
        if node is not None:
            ret = self.roomTypes.getGfx(node, room=room, roomfile=roomfile, path=path)
            if ret is not None:
                return ret

        node = self.stages.lookup(path=path)
        if not node:
            node = self.stages.lookup(name="Basement")

        return self.stages.getGfx(node[-1])

    def getGfxData(self, node=None):
        if node is None:
            return self.getGfxData(
                self.stages.getGfx(self.stages.lookup(name="Basement")[0])
            )

        baseGfx = None

        stage = node.get("StageGfx")
        if stage:
            stage = self.stages.lookup(name=stage)
            if stage:
                baseGfx = self.getGfxData(self.stages.getGfx(stage[0]))

        roomType = node.get("RoomGfx")
        if roomType:
            roomType = self.roomTypes.lookup(name=roomType)
            if roomType:
                baseGfx = self.getGfxData(self.roomTypes.getGfx(roomType[0]))

        prefix = node.get("BGPrefix")

        paths = None
        entities = {}

        if baseGfx:
            paths = baseGfx["Paths"]
            entities = baseGfx["Entities"]

        if prefix:
            paths = {
                "OuterBG": prefix + ".png",
                "BigOuterBG": prefix + "_big.png"
                if node.get("HasBigBG") == "1"
                else "",
                "InnerBG": prefix + "Inner.png",
                "NFloor": prefix + "_nfloor.png",
                "LFloor": prefix + "_lfloor.png",
            }

        if paths is None:
            raise ValueError("Invalid gfx node!", node.tag, node.attrib)

        for ent in node.findall("Entity"):
            entid = (
                f"{ent.get('ID')}.{ent.get('Variant', '0')}.{ent.get('SubType', '0')}"
            )
            entities[entid] = ent

        ret = {"Paths": paths, "Entities": entities}

        for key, val in ret["Paths"].items():
            if not os.path.isfile(val):
                ret["Paths"][key] = ""

        return ret
