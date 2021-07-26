import xml.etree.cElementTree as ET
import os
import abc
import re

from itertools import zip_longest

from src.constants import *
from src.util import *
from src.entitiesgenerator import generateXMLFromEntities2


def loadXMLFile(path):
    root = None
    if not os.path.isfile(path):
        return None

    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception as e:
        print("Error loading BR xml:", e)
        return

    return root


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
    def __init__(self, prefix, version):
        version = version.replace("+", "Plus")
        self.prefix = prefix
        self.version = version

    def loadFile(self, file, resourcePath, modName, *args):
        printf(
            f'-----------------------\nLoading {self.prefix} from "{modName}" at {file}'
        )
        previous = self.count()
        self.loadXML(loadXMLFile(file), resourcePath, modName, *args)
        printf(
            f'Successfully loaded {self.count() - previous} new {self.prefix} from "{modName}"'
        )

    def loadFromMod(self, resourcePath, modName, *args):
        file = os.path.join(resourcePath, self.prefix + "Mod.xml")
        if not os.path.isfile(file):
            return

        self.loadFile(file, resourcePath, modName, *args)

    @abc.abstractmethod
    def count(self):
        return 0

    @abc.abstractmethod
    def loadXML(self, *args):
        pass

    @abc.abstractmethod
    def lookup(self):
        pass


class StageLookup(Lookup):
    def __init__(self, version, parent):
        self.xml = None
        super().__init__("Stages", version)
        self.parent = parent

    def count(self):
        if self.xml:
            return len(self.xml)
        else:
            return 0

    def loadXML(self, root, resourcePath="", modName="Basement Renovator"):
        stageList = root.findall("stage")
        if not stageList:
            return

        initialLoad = False
        if self.xml is None:
            self.xml = root
            initialLoad = True

        def mapStage(stage):
            name = stage.get("Name")
            if name is None:
                print("Tried to load stage, but had missing name!", str(stage.attrib))
                return None

            replacement = self.xml.find(f'stage[@Name="{name}"]')

            if replacement is None and (
                stage.get("Stage") is None or stage.get("StageType") is None
            ):
                printf(
                    f"Stage {stage.attrib} has missing stage/stage type; this may not load properly in testing"
                )

            sanitizePath(stage, "BGPrefix", resourcePath)

            children = stage.findall("Gfx")
            for gfx in children:
                sanitizePath(gfx, "BGPrefix", resourcePath)

                for ent in gfx.findall("Entity"):
                    sanitizePath(ent, "Image", resourcePath)

            if replacement is not None:
                for key in stage.attrib.keys():
                    if key != "Name":
                        replacement.set(key, stage.get(key, replacement.get(key)))

                applyGfxReplacement(replacement, children)
                return None

            return stage

        stages = list(filter(lambda x: x is not None, map(mapStage, stageList)))
        if stages and not initialLoad:
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
    def __init__(self, version, parent):
        self.xml = None
        super().__init__("RoomTypes", version)
        self.parent = parent

    def count(self):
        if self.xml:
            return len(self.xml)
        else:
            return 0

    def loadXML(self, root, resourcePath="", modName="Basement Renovator"):
        roomTypeList = root.findall("room")
        if not roomTypeList:
            return

        initialLoad = False
        if self.xml is None:
            self.xml = root
            initialLoad = True

        def mapRoomType(roomType):
            name = roomType.get("Name")
            if name is None:
                print(
                    "Tried to load room type, but had missing name!",
                    str(roomType.attrib),
                )
                return None

            replacement = self.xml.find(f'room[@Name="{name}"]')

            sanitizePath(roomType, "Icon", resourcePath)

            children = roomType.findall("Gfx")
            for gfx in children:
                sanitizePath(gfx, "BGPrefix", resourcePath)

                for ent in gfx.findall("Entity"):
                    sanitizePath(ent, "Image", resourcePath)

            if replacement is not None:
                applyGfxReplacement(replacement, children)
                return None

            return roomType

        roomTypes = list(
            filter(lambda x: x is not None, map(mapRoomType, roomTypeList))
        )
        if roomTypes and not initialLoad:
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

        subtypeCriteria = parseCriteria(node.get("Subtype"))
        if subtypeCriteria and not subtypeCriteria(room.info.subtype):
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
        PickupVariant["PILL"],
    )

    class EntityConfig:
        class BitfieldElement:
            def __init__(self, bitfield, node: ET.Element, offset, length):
                self.bitfield = bitfield

                self.name = node.get("Name", "")
                self.unit = node.get("Unit", "")

                self.offset = offset
                self.length = length

                self.valueoffset = float(node.get("ValueOffset", 0))
                self.floatvalueoffset = self.valueoffset % 1
                self.valueoffset = int(self.valueoffset - self.floatvalueoffset)

                self.minimum = int(node.get("Minimum", 0))
                self.maximum = int(node.get("Maximum", bitFill(self.length)))

                self.scalarrange = node.get("ScalarRange")
                if self.scalarrange:
                    self.scalarrange = float(self.scalarrange)

                self.widget = node.tag

                tooltipNode = node.find("tooltip")
                self.tooltip = None
                if tooltipNode is not None:
                    self.tooltip = tooltipNode.text

                self.dropdownkeys = None
                self.dropdownvalues = None
                if self.widget == "dropdown":
                    self.dropdownkeys = []
                    self.dropdownvalues = []
                    choices = node.findall("choice")
                    for i, value in enumerate(choices):
                        self.dropdownkeys.append(value.text)
                        self.dropdownvalues.append(int(value.get("Value", i)))

            def getRawValue(self, number):
                number = bitGet(number, self.offset, self.length)

                return number

            def setRawValue(self, number, value):
                number = bitSet(number, value, self.offset, self.length)

                return number

            def getRawValueFromWidgetValue(self, widgetValue):
                if self.dropdownvalues:
                    return self.dropdownvalues[widgetValue]

                if self.widget == "dial":
                    return (widgetValue - self.valueoffset) % (self.maximum + 1)

                if self.widget == "checkbox":
                    return 1 if widgetValue else 0

                return widgetValue - self.valueoffset

            def getWidgetValue(self, number, rawValue=None):
                value = rawValue if rawValue is not None else self.getRawValue(number)

                if self.dropdownvalues:
                    return self.dropdownvalues.index(value)

                if self.widget == "dial":
                    return (value + self.valueoffset) % (self.maximum + 1)

                if self.widget == "checkbox":
                    return value == 1

                return value + self.valueoffset

            def getWidgetRange(self):
                if self.widget == "dropdown":
                    return len(self.dropdownvalues)
                if self.widget == "dial":
                    return self.minimum, self.maximum + 1

                return self.minimum + self.valueoffset, self.maximum + self.valueoffset

            def getDisplayValue(self, number, rawValue=None):
                value = self.getWidgetValue(number, rawValue)

                if self.unit == "Degrees":  # Match Isaac's degrees, where right is 0
                    degrees = value * (360 / (self.maximum + 1))
                    return (degrees + 90) % 360

                if self.scalarrange:
                    return round(self.scalarrange / value, 3)

                return value

            def clampValue(self, number):
                bitValue = self.getRawValue(number)
                if self.widget == "dropdown":
                    if bitValue not in self.dropdownvalues:
                        return self.setRawValue(number, self.dropdownvalues[0])
                else:
                    if bitValue < self.minimum:
                        return self.setRawValue(number, self.minimum)

                    if bitValue > self.maximum:
                        return self.setRawValue(number, self.maximum)

                return number

        class Bitfield:
            def __init__(self, node: ET.Element):
                self.key = node.get("Key", "Subtype")
                self.elements = []
                offset = 0
                for elementNode in node:
                    length = int(elementNode.get("Length", 1))
                    elementOffset = elementNode.get("Offset")
                    if elementOffset is None:
                        elementOffset = offset
                        offset = offset + length
                    else:
                        elementOffset = int(elementOffset)

                    element = EntityLookup.EntityConfig.BitfieldElement(
                        self, elementNode, elementOffset, length
                    )

                    self.elements.append(element)

            def isInvalid(self):
                invalid = False
                startsAtZero = False
                for element in self.elements:
                    hasAdjacent = len(self.elements) == 1 and element.offset == 0
                    if element.offset == 0:
                        startsAtZero = True

                    for element2 in self.elements:
                        if element != element2:
                            if (
                                element.offset <= element2.offset
                                and (element.offset + element.length) > element2.offset
                            ):
                                printf(
                                    f"Element {element.name} (Length: {element.length}, Offset: {element.offset}) conflicts with {element2.name} (Length: {element.length}, Offset: {element.offset})"
                                )
                                invalid = True

                            if (element.offset + element.length) == element2.offset or (
                                element2.offset + element2.length
                            ) == element.offset:
                                hasAdjacent = True

                    if not hasAdjacent:
                        printf(
                            f"Element {element.name} (Length: {element.length}, Offset: {element.offset}) is not adjacent to any other elements"
                        )

                if not startsAtZero:
                    printf("Bitfield does not have an element with an offset of 0.")

                return invalid

            def clampValues(self, number):
                for element in self.elements:
                    number = element.clampValue(number)

                return number

        def __init__(
            self, entity=None, resourcePath=None, modName=None, entities2Node=None
        ):
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
            self.hasBitfields = None
            self.invalidBitfield = False
            self.bitfields = []
            self.inEmptyRooms = None
            self.uniqueid = -1

            if entity is not None:
                self.fillFromXML(entity, resourcePath, modName, entities2Node)

        def fillFromXML(
            self, entity: ET.Element, resourcePath, modName, entities2Node=None
        ):
            imgPath = entity.get("Image") and linuxPathSensitivityTraining(
                os.path.join(resourcePath, entity.get("Image"))
            )
            editorImgPath = entity.get("EditorImage") and linuxPathSensitivityTraining(
                os.path.join(resourcePath, entity.get("EditorImage"))
            )
            overlayImgPath = entity.get(
                "OverlayImage"
            ) and linuxPathSensitivityTraining(
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
            self.baseHP = (
                entities2Node.get("baseHP") if entities2Node else entity.get("BaseHP")
            )
            self.boss = (
                entities2Node.get("boss") if entities2Node else entity.get("Boss")
            )
            self.champion = (
                entities2Node.get("champion")
                if entities2Node
                else entity.get("Champion")
            )
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
                        linuxPathSensitivityTraining(
                            os.path.join(resourcePath, bgPrefix)
                        ),
                    )

            def getMirrorEntity(s):
                return list(map(int, s.split(".")))

            mirrorX, mirrorY = entity.get("MirrorX"), entity.get("MirrorY")
            if mirrorX:
                self.mirrorX = getMirrorEntity(mirrorX)
            if mirrorY:
                self.mirrorY = getMirrorEntity(mirrorY)

            bitfields = entity.findall("bitfield")
            self.hasBitfields = len(bitfields) != 0
            self.bitfields = list(map(EntityLookup.EntityConfig.Bitfield, bitfields))
            for bitfield in self.bitfields:
                if bitfield.isInvalid():
                    self.invalidBitfield = True
                    printf(
                        f"Entity {self.name} ({self.type}.{self.variant}.{self.subtype}) has invalid bitfield elements and cannot be configured"
                    )
                    break

        def hasBitfieldKey(self, key):
            for bitfield in self.bitfields:
                if bitfield.key == key:
                    return True

            return False

        def getBitfieldElements(self):
            elements = []
            for bitfield in self.bitfields:
                elements.extend(bitfield.elements)

            return elements

        def getOutOfRangeWarnings(self):
            warnings = ""
            if self.type >= 1000 and not self.isGridEnt:
                warnings += "\nType is outside the valid range of 0 - 999! This will not load properly in-game!"
            if self.variant >= 4096 and not self.hasBitfieldKey("Variant"):
                warnings += "\nVariant is outside the valid range of 0 - 4095!"
            if self.subtype >= 255 and not self.hasBitfieldKey("Subtype"):
                warnings += "\nSubtype is outside the valid range of 0 - 255!"

            return warnings

        def isOutOfRange(self):
            return self.getOutOfRangeWarnings() != ""

        def getEditorWarnings(self):
            warnings = self.getOutOfRangeWarnings()
            if self.invalid:
                warnings += "\nMissing entities2.xml entry! Trying to spawn this WILL CRASH THE GAME!!"

            if self.invalidBitfield:
                warnings += "\nHas incorrectly defined bitfield properties, cannot be configured"
            elif self.hasBitfields:
                warnings += "\nMiddle-click to configure entity properties"

            return warnings

        def matches(self, entitytype=None, variant=None, subtype=None, name=None):
            if name is not None and self.name != name:
                return False
            if entitytype is not None and self.type != entitytype:
                return False
            if variant is not None and (
                self.variant != variant and not self.hasBitfieldKey("Variant")
            ):
                return False
            if subtype is not None and (
                self.subtype != subtype and not self.hasBitfieldKey("Subtype")
            ):
                return False

            return True

    class GroupConfig:
        def __init__(self, node=None, name=None, label=None, isTab=False):
            self.iconSize = None
            self.hasEntity = False
            if node is not None:
                self.label = node.get("Label")
                self.name = node.get("Name", self.label)
                self.isTab = node.get("IsTab") == "1"

                iconSize = node.get("IconSize")
                if iconSize:
                    parts = list(map(lambda x: x.strip(), iconSize.split(",")))
                    if len(parts) == 2 and checkNum(parts[0]) and checkNum(parts[1]):
                        self.iconSize = (int(parts[0]), int(parts[1]))
                    elif len(parts) == 1 and checkNum(parts[0]):
                        self.iconSize = (int(parts[0]), int(parts[0]))
                    else:
                        printf(
                            f"Group {node.attrib} has invalid IconSize, must be 1 or 2 integer values"
                        )
            else:
                self.name = name
                self.label = label
                self.isTab = isTab

            self.entries = []
            self.groupentries = []

        def addEntry(self, entry):
            self.entries.append(entry)
            if isinstance(entry, EntityLookup.GroupConfig):
                self.groupentries.append(entry)
            elif isinstance(entry, EntityLookup.EntityConfig):
                self.hasEntity = True

        def getAllEntries(self):
            entries = []
            for entry in self.entries:
                entries.append(entry)
                if isinstance(entry, EntityLookup.GroupConfig):
                    entries.extend(entry.getAllEntries())

            return entries

        def containsEntity(self):
            if self.hasEntity:
                return True

            for group in self.groupentries:
                if group.containsEntity():
                    return True

            return False

    def __init__(self, version, parent):
        self.entityList = []
        self.groups = {}
        self.tabGroups = []
        self.lastuniqueid = 0
        super().__init__("Entities", version)
        self.parent = parent

    def count(self):
        return len(self.entityList)

    def addEntity(self, entity: EntityConfig):
        self.lastuniqueid += 1
        entity.uniqueid = self.lastuniqueid
        self.entityList.append(entity)

    ENTITY_CLEANUP_REGEX = re.compile(r"[^\w\d]")

    def loadEntityNode(
        self,
        node: ET.Element,
        resourcePath="",
        modName="Basement Renovator",
        entities2Root=None,
    ):
        entityType = node.get("ID")
        variant = node.get("Variant")
        subtype = node.get("Subtype")
        name = node.get("Name")

        if (name is not None) or (entityType is not None):
            isRef = True
            for key in node.attrib.keys():
                if key not in ("ID", "Variant", "Subtype", "Name"):
                    isRef = False
                    break

            if isRef:
                if entityType:
                    entityType = int(entityType)
                if variant:
                    variant = int(variant)
                if subtype:
                    subtype = int(subtype)

                entityConfig = self.lookupOne(
                    entitytype=entityType, variant=variant, subtype=subtype, name=name
                )
                if entityConfig:
                    return entityConfig
                else:
                    printf(
                        f"Entity {node.attrib} looks like a ref, but was not previously defined!"
                    )

        entityType = int(entityType or -1)
        variant = int(variant or 0)
        subtype = int(subtype or 0)

        if (entityType >= 1000 or entityType < 0) and node.get("IsGrid") != "1":
            printf(
                f'Entity "{name}" from "{modName}" has a type outside the 0 - 999 range! ({entityType}) It will not load properly from rooms!'
            )

        if variant >= 4096 or variant < 0:
            printf(
                f'Entity "{name}" from "{modName}" has a variant outside the 0 - 4095 range! ({variant})'
            )

        if (subtype >= 256 or subtype < 0) and (
            entityType != EntityType["PICKUP"]
            or variant not in self.PICKUPS_WITH_SPECIAL_SUBTYPES
        ):
            printf(
                f'Entity "{name}" from "{modName}" has a subtype outside the 0 - 255 range! ({subtype})'
            )

        entityXML = None

        if node.get("Metadata") != "1" and node.get("IsGrid") != "1":
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
                        + str(node.attrib)
                    )
                    node.set("Invalid", "1")
                else:
                    foundName = entityXML.get("name")
                    givenName = node.get("Name")
                    foundNameClean, givenNameClean = list(
                        map(
                            lambda s: self.ENTITY_CLEANUP_REGEX.sub("", s).lower(),
                            (foundName, givenName),
                        )
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

        overwrite = node.get("Overwrite") == "1"

        entityConfig = self.lookupOne(entityType, variant, subtype)
        if entityConfig:
            if not overwrite:
                printf(
                    f'Entity "{name}" from "{modName}" ({entityType}.{variant}.{subtype}) is overriding "{entityConfig.name}" from "{entityConfig.mod}"!'
                )

            entityConfig.fillFromXML(node, resourcePath, modName, entityXML)
        else:
            if overwrite:
                printf(
                    f'Entity "{name} from {modName} ({entityType}.{variant}.{subtype}) has the Overwrite attribute, but is not overwriting anything!'
                )

            entityConfig = self.EntityConfig(node, resourcePath, modName, entityXML)
            self.addEntity(entityConfig)

        groups = []
        nodeKind = node.get("Kind")
        nodeGroup = node.get("Group")
        if nodeKind is not None and nodeGroup is not None:
            groups.append((nodeKind, nodeGroup))

        for group in node.findall("group"):
            kind = group.get("Kind", nodeKind)
            name = group.get("Name", nodeGroup)
            groups.append((kind, name))

        for kind, group in groups:
            groupName = f"({kind}) {group}"
            tabGroupConfig = None
            for tabGroup in self.tabGroups:
                if tabGroup.isTab and tabGroup.name == kind:
                    tabGroupConfig = tabGroup
                    break

            if tabGroupConfig is None:
                tabGroupConfig = self.getGroup(name=kind, isTab=True)

            groupConfig = None
            for entry in tabGroupConfig.entries:
                if isinstance(entry, self.GroupConfig) and entry.name == groupName:
                    groupConfig = entry
                    break

            if groupConfig is None:
                groupConfig = self.getGroup(name=groupName, label=group)
                tabGroupConfig.addEntry(groupConfig)

            groupConfig.addEntry(entityConfig)

        return entityConfig

    def getGroup(self, node=None, name=None, label=None, isTab=False):
        if name is None:
            name = node.get("Name", node.get("Label"))
            if name is None:
                printf(f"Attempted to get group with no Name {node.attrib}")
                return None

        if name not in self.groups:
            group = self.GroupConfig(node=node, name=name, label=label, isTab=isTab)
            self.groups[name] = group
            if group.isTab:
                self.tabGroups.append(group)

        return self.groups[name]

    def loadGroupNode(
        self,
        node: ET.Element,
        resourcePath="",
        modName="Basement Renovator",
        entities2Root=None,
    ):
        group = self.getGroup(node)
        if group:
            for subNode in node:
                entry = None
                if subNode.tag == "group":
                    entry = self.loadGroupNode(
                        subNode, resourcePath, modName, entities2Root
                    )
                elif subNode.tag == "entity":
                    entry = self.loadEntityNode(
                        subNode, resourcePath, modName, entities2Root
                    )

                if entry:
                    group.addEntry(entry)

            return group

        return None

    def loadXML(
        self,
        root: ET.Element,
        resourcePath="",
        modName="Basement Renovator",
        entities2Root=None,
    ):
        if not root:
            return

        for subNode in root:
            if subNode.tag == "group":
                self.loadGroupNode(subNode, resourcePath, modName, entities2Root)
            elif subNode.tag == "entity":
                self.loadEntityNode(subNode, resourcePath, modName, entities2Root)

    def loadFile(
        self,
        path,
        resourcePath="resources/",
        modName="Basement Renovator",
        modPath=None,
        autogenerateContent=False,
    ):
        root = loadXMLFile(path)
        if root is None:
            return

        printf(f'-----------------------\nLoading Entities from "{modName}" at {path}')
        previous = self.count()

        entities2Root = None
        if modPath:
            entities2Path = os.path.join(modPath, "content/entities2.xml")
            if os.path.exists(entities2Path):
                entities2Root = None
                try:
                    entities2Root = ET.parse(entities2Path).getroot()
                except ET.ParseError as e:
                    printf(f'ERROR parsing entities2 xml for mod "{modName}": {e}')
                    return

                if autogenerateContent:
                    self.loadXML(
                        generateXMLFromEntities2(
                            modPath, modName, entities2Root, resourcePath
                        ),
                        resourcePath,
                        modName,
                        entities2Root,
                    )

        self.loadXML(root, resourcePath, modName, entities2Root)

        printf(
            f"Successfully loaded {self.count() - previous} new Entities from {modName}"
        )

    def lookupGroup(self, name):
        if name in self.groups:
            return self.groups[name].getAllEntries()
        else:
            return []

    def lookup(
        self,
        entitytype=None,
        variant=None,
        subtype=None,
        inEmptyRooms=None,
        name=None,
    ):
        entities = self.entityList

        entities = list(
            filter(
                lambda entity: entity.matches(entitytype, variant, subtype, name),
                entities,
            )
        )

        if inEmptyRooms:
            entities = list(
                filter(lambda entity: entity.inEmptyRooms == inEmptyRooms, entities)
            )

        return entities

    def lookupOne(
        self,
        entitytype=None,
        variant=None,
        subtype=None,
        inEmptyRooms=None,
        name=None,
    ):
        entities = self.lookup(entitytype, variant, subtype, inEmptyRooms, name)

        return next(iter(entities), None)


class MainLookup:
    class Version:
        class DataFile:
            def __init__(self, filetype, path, ignorewith):
                self.path = path
                self.filetype = filetype
                self.ignorewith = ignorewith

        def __init__(self, node, versions):
            self.invalid = False
            self.name = node.get("Name")
            if self.name is None:
                printf(f"Version {node.attrib} does not have a Name")

            self.toload = []

            for dataNode in node:
                if dataNode.tag == "version":
                    name = dataNode.get("Name")
                    if name is None:
                        printf(
                            f"Cannot load version from node {node.attrib} without Name"
                        )
                        self.invalid = True
                    elif name not in versions:
                        printf(
                            f"Cannot load version from node {node.attrib} because it is not defined"
                        )
                        self.invalid = True
                    else:
                        self.toload.append(versions[name])
                elif dataNode.tag in ("entities", "stages", "roomtypes"):
                    path = dataNode.get("File")
                    if path:
                        self.toload.append(
                            self.DataFile(
                                dataNode.tag, path, dataNode.get("IgnoreWith")
                            )
                        )
                    else:
                        printf(
                            f"Cannot load file from node {node.attrib} without File path"
                        )
                        self.invalid = True
                else:
                    printf(
                        f"Cannot load unknown file type {dataNode.tag} from node {node.attrib}"
                    )
                    self.invalid = True

        def allFiles(self, versions=None):
            files = []

            if versions is None:
                versions = {}

            versions[self.name] = True
            for entry in self.toload:
                if isinstance(entry, MainLookup.Version):
                    files.extend(entry.allFiles(versions))
                else:
                    files.append(entry)

            files = list(
                filter(
                    lambda file: file.ignorewith is None
                    or file.ignorewith not in versions,
                    files,
                )
            )

            return files

    def __init__(self, version):
        self.stages = StageLookup(version, self)
        self.roomTypes = RoomTypeLookup(version, self)
        self.entities = EntityLookup(version, self)
        self.version = version

        self.loadXML(loadXMLFile("resources/Versions.xml"))

    def loadFromMod(self, modPath, brPath, name, autogenerateContent):
        versionsPath = os.path.join(brPath, "VersionsMod.xml")
        if os.path.exists(versionsPath):
            self.loadXML(
                loadXMLFile(versionsPath), brPath, modPath, name, autogenerateContent
            )
        else:
            self.stages.loadFromMod(brPath, name)
            self.roomTypes.loadFromMod(brPath, name)
            self.entities.loadFromMod(brPath, name, modPath, autogenerateContent)

    def loadXML(
        self,
        root=None,
        resourcePath="resources/",
        modPath=None,
        modName="Basement Renovator",
        autogenerateContent=False,
    ):
        if root is None:
            return

        loadVersion = None
        versions = {}
        for versionNode in root:
            version = self.Version(versionNode, versions)
            if version.invalid is False:
                versions[version.name] = version
                if version.name == self.version:
                    loadVersion = version

        if loadVersion:
            files = loadVersion.allFiles()
            for file in files:
                path = os.path.join(resourcePath, file.path)
                if file.filetype == "entities":
                    self.entities.loadFile(
                        path, resourcePath, modName, modPath, autogenerateContent
                    )
                elif file.filetype == "stages":
                    self.stages.loadFile(path, resourcePath, modName)
                elif file.filetype == "roomtypes":
                    self.roomTypes.loadFile(path, resourcePath, modName)
        else:
            printf("Could not find valid version to load")

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
