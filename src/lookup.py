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
        self.prefix = prefix
        self.version = version

    def loadFile(self, file, mod, *args):
        printSectionBreak()
        printf(f'Loading {self.prefix} from "{mod.name}" at {file}')
        previous = self.count()
        self.loadXML(loadXMLFile(file), mod, *args)
        printf(
            f'Successfully loaded {self.count() - previous} new {self.prefix} from "{mod.name}"'
        )

    def loadFromMod(self, mod, *args):
        file = os.path.join(mod.resourcePath, self.prefix + "Mod.xml")
        if not os.path.isfile(file):
            return

        self.loadFile(file, mod, *args)

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
        if self.xml is not None:
            return len(self.xml)
        else:
            return 0

    def loadXML(self, root, mod):
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

            if self.parent.verbose:
                print("Loading stage:", str(stage.attrib))

            replacement = self.xml.find(f'stage[@Name="{name}"]')

            if replacement is None and (
                stage.get("Stage") is None or stage.get("StageType") is None
            ):
                printf(
                    f"Stage {stage.attrib} has missing stage/stage type; this may not load properly in testing"
                )

            sanitizePath(stage, "BGPrefix", mod.resourcePath)

            children = stage.findall("Gfx")
            for gfx in children:
                sanitizePath(gfx, "BGPrefix", mod.resourcePath)

                for ent in gfx.findall("Entity"):
                    sanitizePath(ent, "Image", mod.resourcePath)

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
            stages = list(
                filter(lambda s: s.get("Pattern").lower() in path.lower(), stages)
            )

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
        if self.xml is not None:
            return len(self.xml)
        else:
            return 0

    def loadXML(self, root, mod):
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

            sanitizePath(roomType, "Icon", mod.resourcePath)

            children = roomType.findall("Gfx")
            for gfx in children:
                sanitizePath(gfx, "BGPrefix", mod.resourcePath)

                for ent in gfx.findall("Entity"):
                    sanitizePath(ent, "Image", mod.resourcePath)

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

                self.gridwidth = None
                if self.widget == "bitmap":
                    self.gridwidth = int(node.get("Width", self.length))

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

        def __init__(self, mod=None, parent=None):
            self.mod = mod
            self.parent = parent
            self.name = None
            self.type = -1
            self.variant = 0
            self.subtype = 0
            self.imagePath = "resources/Entities/questionmark.png"
            self.editorImagePath = None
            self.overlayImagePath = None
            self.baseHP = None
            self.stageHP = None
            self.armor = None
            self.placeVisual = None
            self.disableOffsetIndicator = False
            self.renderPit = False
            self.renderRock = False
            self.invalid = False
            self.gfx = None
            self.mirrorX = None
            self.mirrorY = None
            self.hasBitfields = False
            self.invalidBitfield = False
            self.bitfields = []
            self.tags = {}
            self.uniqueid = -1
            self.tagsString = "[]"

        def getTagConfig(self, tag):
            if not self.parent:
                return None

            if not isinstance(tag, EntityLookup.TagConfig):
                name = tag
                tag = self.parent.getTag(name=name)
                if tag is None:
                    printf(
                        f"Attempted to get undefined tag {name} for entity {self.name} from mod {self.mod.name}"
                    )

            return tag

        def addTag(self, tag):
            tag = self.getTagConfig(tag)
            if tag and tag.tag not in self.tags:
                self.tags[tag.tag] = tag
                self.tagsString = self.printTags()

        def removeTag(self, tag):
            tag = self.getTagConfig(tag)
            if tag and tag.tag in self.tags:
                self.tags[tag.tag] = None
                self.tagsString = self.printTags()

        def hasTag(self, tag):
            tag = self.getTagConfig(tag)
            return tag and tag.tag in self.tags

        def validateImagePath(self, imagePath, resourcePath, default=None):
            if imagePath is None:
                return default

            imagePath = linuxPathSensitivityTraining(
                os.path.join(resourcePath, imagePath)
            )

            if not os.path.exists(imagePath):
                printf(
                    f"Failed loading image for Entity {self.name} ({self.type}.{self.variant}.{self.subtype}):",
                    imagePath,
                )
                return default

            return imagePath

        COPYABLE_ATTRIBUTES = (
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
        )

        def fillFromConfig(self, config):
            for attribute in EntityLookup.EntityConfig.COPYABLE_ATTRIBUTES:
                defaultValue = getattr(EntityLookup.DEFAULT_ENTITY_CONFIG, attribute)
                selfValue = getattr(self, attribute)
                if selfValue == defaultValue:
                    configValue = getattr(config, attribute)
                    setattr(self, attribute, configValue)

            for tag in config.tags.values():
                self.addTag(tag)

            self.bitfields.extend(config.bitfields)
            self.hasBitfields = len(self.bitfields) != 0
            self.invalidBitfield = self.invalidBitfield or config.invalidBitfield

        ENTITY_CLEAN_NAME_REGEX = re.compile(r"[^\w\d]")

        def getEntities2Node(self):
            if (
                not self.mod
                or self.matches(tags=("Metadata", "Grid"), matchAnyTag=True)
                or self.mod.entities2root is None
            ):
                return None, False, None

            adjustedId = 1000 if self.type == 999 else self.type
            query = f"entity[@id='{adjustedId}'][@variant='{self.variant}']"

            validMissingSubtype = False
            entityXML = self.mod.entities2root.find(
                query + f"[@subtype='{self.subtype}']"
            )

            if entityXML is None:
                entityXML = self.mod.entities2root.find(query)
                validMissingSubtype = entityXML is not None

            if entityXML is None:
                return None, True, None
            else:
                foundName = entityXML.get("name")
                givenName = self.name
                foundNameClean, givenNameClean = list(
                    map(
                        lambda s: self.ENTITY_CLEAN_NAME_REGEX.sub("", s).lower(),
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
                    return entityXML, False, foundName

            return entityXML, False, None

        def fillFromNode(self, node: ET.Element):
            warnings = ""

            if node.get("Name"):
                self.name = node.get("Name")

            if node.get("ID"):
                self.type = int(node.get("ID"))

            if node.get("Variant"):
                self.variant = int(node.get("Variant"))

            if node.get("Subtype"):
                self.subtype = int(node.get("Subtype"))

            if node.get("Image"):
                self.imagePath = self.validateImagePath(
                    node.get("Image"),
                    self.mod.resourcePath,
                    "resources/Entities/questionmark.png",
                )

            if node.get("EditorImage"):
                self.editorImagePath = self.validateImagePath(
                    node.get("EditorImage"), self.mod.resourcePath
                )

            if node.get("OverlayImage"):
                self.overlayImagePath = self.validateImagePath(
                    node.get("OverlayImage"), self.mod.resourcePath
                )

            # Tags="" attribute allows overriding default tags with nothing / different tags
            tagsString = node.get("Tags")
            if tagsString is not None:
                self.tags = {}
                if tagsString != "":
                    for tag in tagsString.split(","):
                        self.addTag(tag.strip())

            tags = node.findall("tag")
            for tag in tags:
                self.addTag(tag.text)

            for tag in self.parent.tags.values():
                if tag.attribute:
                    attribute = node.get(tag.attribute)
                    if attribute == "1":
                        self.addTag(tag)
                    elif attribute == "0":
                        self.removeTag(tag)

            if node.get("DisableOffsetIndicator"):
                self.disableOffsetIndicator = node.get("DisableOffsetIndicator") == "1"

            if node.get("UsePitTiling"):
                self.renderPit = node.get("UsePitTiling") == "1"

            if node.get("UseRockTiling"):
                self.renderRock = node.get("UseRockTiling") == "1"

            entities2Node, invalid, mismatchedName = self.getEntities2Node()
            if invalid:
                warnings += "\nHas no entry in entities2.xml!"
                self.invalid = True

            if mismatchedName:
                warnings += f"\nFound name mismatch! In entities2: {mismatchedName}; In BR: {self.name}"

            if node.get("BaseHP"):
                self.baseHP = node.get("BaseHP")
            elif self.baseHP is None and entities2Node is not None:
                self.baseHP = entities2Node.get("baseHP")

            if node.get("StageHP"):
                self.stageHP = node.get("StageHP")
            elif self.stageHP is None and entities2Node is not None:
                self.stageHP = entities2Node.get("stageHP")

            if node.get("Armor"):
                self.armor = node.get("Armor")
            elif self.armor is None and entities2Node is not None:
                self.armor = entities2Node.get("shieldStrength")

            if node.get("Boss") == "1" or (
                entities2Node is not None and entities2Node.get("boss") == "1"
            ):
                self.addTag("Boss")

            if node.get("Champion") or (
                entities2Node is not None and entities2Node.get("champion") == "1"
            ):
                self.addTag("Champion")

            if node.get("PlaceVisual"):
                self.placeVisual = node.get("PlaceVisual")

            if node.get("Invalid"):
                self.invalid = True

            if node.find("Gfx") is not None:
                self.gfx = node.find("Gfx")
                bgPrefix = self.gfx.get("BGPrefix")
                if bgPrefix:
                    self.gfx.set(
                        "BGPrefix",
                        linuxPathSensitivityTraining(
                            os.path.join(self.mod.resourcePath, bgPrefix)
                        ),
                    )

            def getMirrorEntity(s):
                return list(map(int, s.split(".")))

            mirrorX, mirrorY = node.get("MirrorX"), node.get("MirrorY")
            if mirrorX:
                self.mirrorX = getMirrorEntity(mirrorX)
            if mirrorY:
                self.mirrorY = getMirrorEntity(mirrorY)

            bitfields = node.findall("bitfield")
            if len(bitfields) != 0:
                self.hasBitfields = True
                for bitfieldNode in bitfields:
                    bitfield = self.Bitfield(bitfieldNode)
                    if bitfield.isInvalid():
                        self.invalidBitfield = True
                        warnings += (
                            "\nHas invalid bitfield elements and cannot be configured"
                        )
                        break
                    else:
                        self.bitfields.append(bitfield)

            rangeWarnings = self.getOutOfRangeWarnings()
            if rangeWarnings != "":
                warnings += "\nOut of range:" + rangeWarnings

            if warnings != "":
                warnings = (
                    f"\nWarning for Entity {self.name} ({self.type}.{self.variant}.{self.subtype}) from {self.mod.name}:"
                    + warnings
                )

            return warnings

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
            if (self.type >= 1000 or self.type < 0) and not self.hasTag("Grid"):
                warnings += f"\nType {self.type} is outside the valid range of 0 - 999! This will not load properly in-game!"
            if (self.variant >= 4096 or self.variant < 0) and not self.hasBitfieldKey(
                "Variant"
            ):
                warnings += (
                    f"\nVariant {self.variant} is outside the valid range of 0 - 4095!"
                )
            if (
                (self.subtype >= 4096 or self.subtype < 0)
                and (self.type != EntityType["PICKUP"])
                and not self.hasBitfieldKey("Subtype")
            ):
                warnings += (
                    f"\nSubtype {self.subtype} is outside the valid range of 0 - 4095!"
                )

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

        def printTags(self):
            if not self.parent:
                return "None"

            return f'[{", ".join(map(lambda t: t.label, filter(lambda tag: self.hasTag(tag) and tag.label, self.parent.tags.values())))}]'

        def matches(
            self,
            entitytype=None,
            variant=None,
            subtype=None,
            name=None,
            tags=None,
            matchAnyTag=False,
        ):
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
            if tags is not None:
                matchedAny = False
                for tag in tags:
                    if self.hasTag(tag):
                        matchedAny = True
                    elif not matchAnyTag:
                        return False

                if not matchedAny:
                    return False

            return True

    DEFAULT_ENTITY_CONFIG = EntityConfig()

    class GroupConfig:
        def __init__(self, node=None, name=None, label=None, parentGroup=None):
            if node is not None:
                self.label = node.get("Label")
                self.name = node.get("Name", self.label)
            else:
                self.name = name
                self.label = label

            self.parent = parentGroup

            self.entityDefaults = None
            if self.parent is not None and self.parent.entityDefaults:
                self.entityDefaults = EntityLookup.EntityConfig(
                    self.parent.entityDefaults.mod, self.parent.entityDefaults.parent
                )
                self.entityDefaults.fillFromConfig(self.parent.entityDefaults)

            self.entries = []
            self.groupentries = []

        def addEntry(self, entry):
            self.entries.append(entry)
            if isinstance(entry, EntityLookup.GroupConfig):
                self.groupentries.append(entry)

    class TabConfig(GroupConfig):
        def __init__(self, node=None, name=None):
            super().__init__(node, name)

            self.iconSize = None
            if node is not None:
                iconSize = node.get("IconSize")
                if iconSize:
                    parts = list(map(lambda x: x.strip(), iconSize.split(",")))
                    if len(parts) == 2 and checkInt(parts[0]) and checkInt(parts[1]):
                        self.iconSize = (int(parts[0]), int(parts[1]))
                    else:
                        printf(
                            f"Group {node.attrib} has invalid IconSize, must be 2 integer values"
                        )

    class TagConfig:
        def __init__(self, node: ET.Element):
            self.tag = node.text
            self.label = node.get("Label")
            self.filterable = node.get("Filterable") == "1"
            self.statisticsgroup = node.get("StatisticsGroup") == "1"
            self.attribute = node.get("Attribute")

    def __init__(self, version, parent):
        self.entityList = self.GroupConfig()
        self.entityListByType = {}
        self.groups = {}
        self.tags = {}
        self.tabs = []
        self.lastuniqueid = 0
        super().__init__("Entities", version)
        self.parent = parent

    def count(self):
        return len(self.entityList.entries)

    def addEntity(self, entity: EntityConfig):
        self.lastuniqueid += 1
        entity.uniqueid = self.lastuniqueid
        self.entityList.addEntry(entity)

        if entity.type not in self.entityListByType:
            self.entityListByType[entity.type] = []

        self.entityListByType[entity.type].append(entity)

    def loadEntityNode(self, node: ET.Element, mod, parentGroup=None):
        entityType = node.get("ID")
        variant = node.get("Variant")
        subtype = node.get("Subtype")
        name = node.get("Name")

        entityConfig = None
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
                    # Refs can be used to add tags to entities without overwriting them
                    tags = node.findall("tag")
                    for tag in tags:
                        entityConfig.addTag(tag.text)

                    return entityConfig
                else:
                    printf(
                        f"Entity {node.attrib} looks like a ref, but was not previously defined!"
                    )

        entityType = int(entityType or -1)
        variant = int(variant or 0)
        subtype = int(subtype or 0)

        overwrite = node.get("Overwrite") == "1"

        if overwrite:
            if name:
                entityConfig = self.lookupOne(name=name)

            if entityConfig is None:
                entityConfig = self.lookupOne(entityType, variant, subtype)

            if entityConfig is None:
                printf(
                    f'Entity "{name}" from {mod.name} ({entityType}.{variant}.{subtype}) has the Overwrite attribute, but is not overwriting anything!'
                )
        else:
            entityConfig = self.lookupOne(entityType, variant, subtype)
            if entityConfig:
                overwrite = True
                printf(
                    f'Entity "{name}" from "{mod.name}" ({entityType}.{variant}.{subtype}) is overriding "{entityConfig.name}" from "{entityConfig.mod.name}"!'
                )
            else:
                entityConfig = self.EntityConfig(mod, self)

        if entityConfig:
            entityConfig.mod = mod
            if parentGroup is not None and parentGroup.entityDefaults:
                entityConfig.fillFromConfig(parentGroup.entityDefaults)

            warnings = entityConfig.fillFromNode(node)
            if warnings != "":
                printf(warnings)

            if not overwrite:
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
            tab = self.getTab(name=kind)

            groupConfig = None
            for entry in tab.entries:
                if isinstance(entry, self.GroupConfig) and entry.name == groupName:
                    groupConfig = entry
                    break

            if groupConfig is None:
                groupConfig = self.getGroup(name=groupName, label=group)
                tab.addEntry(groupConfig)

            groupConfig.addEntry(entityConfig)

        return entityConfig

    def getGroup(self, node=None, name=None, label=None, parentGroup=None):
        if name is None:
            name = node.get("Name", node.get("Label"))
            if name is None:
                printf(f"Attempted to get group with no Name {node.attrib}")
                return None

        if name not in self.groups:
            group = self.GroupConfig(
                node=node, name=name, label=label, parentGroup=parentGroup
            )
            self.groups[name] = group

        return self.groups[name]

    def getTab(self, node=None, name=None):
        if name is None:
            name = node.get("Name")
            if name is None:
                printf(f"Attempted to get tab with no Name {node.attrib}")
                return None

        if name not in self.groups:
            tab = self.TabConfig(node, name)
            self.groups[tab.name] = tab
            self.tabs.append(tab)

        return self.groups[name]

    def getTag(self, node=None, name=None):
        if name is None:
            name = node.text
            if name == "":
                printf(f"Attempted to get tag with no text {node.attrib}")
                return None

        if name not in self.tags:
            if node is None:
                printf(f"Attempted to get undefined tag {name}")
                return None

            tag = self.TagConfig(node)
            self.tags[tag.tag] = tag

        return self.tags[name]

    def loadDefaultsNode(self, node: ET.Element, mod, group):
        for subNode in node:
            if subNode.tag == "entity":
                if not group.entityDefaults:
                    group.entityDefaults = self.EntityConfig(mod, self)

                group.entityDefaults.fillFromNode(subNode)

    def loadGroupNode(self, node: ET.Element, mod, parentGroup=None):
        group = None
        if node.tag == "tab":
            group = self.getTab(node)
        else:
            group = self.getGroup(node, parentGroup=parentGroup)

        if group:
            for subNode in node:
                entry = None
                if subNode.tag == "group":
                    entry = self.loadGroupNode(subNode, mod, group)
                elif subNode.tag == "entity":
                    entry = self.loadEntityNode(subNode, mod, group)
                elif subNode.tag == "defaults":
                    self.loadDefaultsNode(subNode, mod, group)

                if entry:
                    group.addEntry(entry)

        return group

    def loadXML(self, root: ET.Element, mod):
        if not root:
            return

        for subNode in root:
            if subNode.tag == "group" or subNode.tag == "tab":
                self.loadGroupNode(subNode, mod)
            elif subNode.tag == "entity":
                self.loadEntityNode(subNode, mod)
            elif subNode.tag == "tag":
                self.getTag(subNode)

    def loadFile(self, path, mod):
        root = loadXMLFile(path)
        if root is None:
            return

        printSectionBreak()
        printf(f'Loading Entities from "{mod.name}" at {path}')
        previous = self.count()

        if mod.autogenerateContent and mod.entities2root is not None:
            self.loadXML(
                generateXMLFromEntities2(
                    mod.modPath, mod.name, mod.entities2root, mod.resourcePath
                ),
                mod,
            )

        self.loadXML(root, mod)

        printf(
            f"Successfully loaded {self.count() - previous} new Entities from {mod.name}"
        )

    def lookup(
        self,
        entitytype=None,
        variant=None,
        subtype=None,
        name=None,
        tags=None,
        matchAnyTag=False,
        entities=None,
    ):
        if entities is None:
            if entitytype is not None:
                if entitytype in self.entityListByType:
                    entities = self.entityListByType[entitytype]
                else:
                    return []
            else:
                entities = self.entityList.entries

        entities = list(
            filter(
                lambda entity: entity.matches(
                    entitytype, variant, subtype, name, tags, matchAnyTag
                ),
                entities,
            )
        )

        return entities

    def lookupOne(
        self,
        entitytype=None,
        variant=None,
        subtype=None,
        name=None,
        tags=None,
        matchAnyTag=False,
        entities=None,
    ):
        entities = self.lookup(
            entitytype, variant, subtype, name, tags, matchAnyTag, entities
        )

        return next(iter(entities), None)


class MainLookup:
    class VersionConfig:
        class DataFile:
            def __init__(self, filetype, path, name):
                self.path = path
                self.filetype = filetype
                self.name = name

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
                    self.toload.append(
                        self.DataFile(
                            dataNode.tag, dataNode.get("File"), dataNode.get("Name")
                        )
                    )
                else:
                    printf(
                        f"Cannot load unknown file type {dataNode.tag} from node {node.attrib}"
                    )
                    self.invalid = True

        def allFiles(self, versions=None):
            files = []
            namedFiles = {}

            if versions is None:
                versions = {}

            versions[self.name] = True
            for entry in self.toload:
                addFiles = None
                if isinstance(entry, MainLookup.VersionConfig):
                    addFiles = entry.allFiles(versions)
                else:
                    addFiles = [entry]

                for file in addFiles:
                    if file.name:
                        if file.name not in namedFiles:
                            namedFiles[file.name] = len(files)
                            files.append(file)
                        else:
                            files[namedFiles[file.name]] = file
                    else:
                        files.append(file)

            return files

    class ModConfig:
        def __init__(
            self,
            modName="Basement Renovator",
            resourcePath="resources/",
            modPath=None,
            autogenerateContent=False,
        ):
            self.name = modName
            self.resourcePath = resourcePath
            self.modPath = modPath
            self.autogenerateContent = autogenerateContent

            self.entities2root = None
            if self.modPath:
                entities2Path = os.path.join(modPath, "content/entities2.xml")
                if os.path.exists(entities2Path):
                    try:
                        self.entities2root = ET.parse(entities2Path).getroot()
                    except ET.ParseError as e:
                        printf(f'ERROR parsing entities2 xml for mod "{modName}": {e}')
                        return

    def __init__(self, version, verbose):
        self.basemod = self.ModConfig()
        self.stages = StageLookup(version, self)
        self.roomTypes = RoomTypeLookup(version, self)
        self.entities = EntityLookup(version, self)
        self.version = version
        self.verbose = verbose

        self.loadXML(loadXMLFile("resources/Versions.xml"), self.basemod)

    def loadFromMod(self, modPath, brPath, name, autogenerateContent):
        modConfig = self.ModConfig(name, brPath, modPath, autogenerateContent)
        versionsPath = os.path.join(brPath, "VersionsMod.xml")
        if os.path.exists(versionsPath):
            self.loadXML(loadXMLFile(versionsPath), modConfig)
        else:
            self.stages.loadFromMod(modConfig)
            self.roomTypes.loadFromMod(modConfig)
            self.entities.loadFromMod(modConfig)

    def loadXML(self, root=None, mod=None):
        if root is None:
            return

        loadVersion = None
        versions = {}
        for versionNode in root:
            version = self.VersionConfig(versionNode, versions)
            if version.invalid is False:
                versions[version.name] = version
                if version.name == self.version:
                    loadVersion = version

        if loadVersion:
            files = loadVersion.allFiles()
            for file in files:
                if file.path:
                    path = os.path.join(mod.resourcePath, file.path)
                    if file.filetype == "entities":
                        self.entities.loadFile(path, mod)
                    elif file.filetype == "stages":
                        self.stages.loadFile(path, mod)
                    elif file.filetype == "roomtypes":
                        self.roomTypes.loadFile(path, mod)
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
