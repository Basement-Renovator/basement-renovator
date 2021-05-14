import xml.etree.cElementTree as ET
import os, abc, re

from itertools import zip_longest


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


class MainLookup:
    def __init__(self, version, subVer):
        self.stages = StageLookup(version, subVer, self)
        self.roomTypes = RoomTypeLookup(version, subVer, self)

    def loadFromMod(self, modPath, brPath, name):
        self.stages.loadFromMod(modPath, brPath, name)
        self.roomTypes.loadFromMod(modPath, brPath, name)

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
