import xml.etree.cElementTree as ET
import os, abc, re

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
    if not txt: return None

    tokens = list(filter(bool, re.split(r'[\[\(\)\],]', txt)))

    if txt[0] in [ '[', '(' ]:
        start, end = txt[0], txt[-1]
        mini, maxi = tokens[0], tokens[1]

        if mini == 'infinity':
            mini = lambda v: True
        else:
            miniv = int(mini)
            if start == '[':
                mini = lambda v: v >= miniv
            elif start == '(':
                mini = lambda v: v > miniv
            else: raise ValueError(f'Invalid range in text: {txt}')

        if maxi == 'infinity':
            maxi = lambda v: True
        else:
            maxiv = int(maxi)
            if end == ']':
                maxi = lambda v: v <= maxiv
            elif end == ')':
                maxi = lambda v: v < maxiv
            else: raise ValueError(f'Invalid range in text: {txt}')

        return lambda v: mini(v) and maxi(v)

    tokens = list(map(int, tokens))
    return lambda v: v in tokens

class Lookup(metaclass=abc.ABCMeta):
    def __init__(self, prefix, mode):
        self.setup(prefix, mode)

    def setup(self, prefix, mode):
        file = f'resources/{prefix}AfterbirthPlus.xml'
        if mode == 'Antibirth':
            fileN = f'resources/{prefix}Antibirth.xml'
            if os.path.exists(fileN):
                file = fileN

        tree = ET.parse(file)
        root = tree.getroot()

        self.xml = root

    @abc.abstractmethod
    def lookup(self): pass

class StageLookup(Lookup):
    def __init__(self, mode, parent):
        super().__init__('Stages', mode)
        self.parent = parent

    def loadFromMod(self, modPath, brPath, name):
        stageFile = os.path.join(brPath, 'StagesMod.xml')
        if not os.path.isfile(stageFile):
            return

        print(f'-----------------------\nLoading stages from "{name}"')

        root = None
        try:
            tree = ET.parse(stageFile)
            root = tree.getroot()
        except Exception as e:
            print('Error loading BR xml:', e)
            return

        stageList = root.findall('stage')
        if not stageList: return

        def mapStage(stage):
            if stage.get('Stage') is None or stage.get('StageType') is None or stage.get('Name') is None:
                print('Tried to load stage, but had missing stage, stage type, or name!', str(stage.attrib))
                return None

            print('Loading stage:', str(stage.attrib))

            sanitizePath(stage, 'BGPrefix', brPath)

            for gfx in stage.findall('Gfx'):
                sanitizePath(gfx, 'BGPrefix', brPath)

                for ent in gfx.findall('Entity'):
                    sanitizePath(ent, 'Image', brPath)

            return stage

        stages = list(filter(lambda x: x is not None, map(mapStage, stageList)))
        if stages:
            self.xml.extend(stages)

    def lookup(self, path=None, name=None, stage=None, stageType=None, baseGamePath=None):
        stages = self.xml.findall('stage')

        doList = False

        if stage:
            doList = True
            st = str(stage)
            stages = filter(lambda s: s.get('Stage') == st)

        if stageType:
            doList = True
            st = str(stageType)
            stages = filter(lambda s: s.get('StageType') == st)

        if path:
            doList = True
            stages = filter(lambda s: s.get('Pattern') in path, stages)

        if name:
            doList = True
            stages = filter(lambda s: s.get('Name') == name, stages)

        if baseGamePath:
            doList = True
            hasBasePath = None
            if isinstance(baseGamePath, bool):
                hasBasePath = lambda s: s.get('BaseGamePath') is not None
            else:
                hasBasePath = lambda s: s.get('BaseGamePath') == baseGamePath
            stages = filter(hasBasePath, stages)

        if doList: stages = list(stages)

        return stages

    def getGfx(self, node):
        gfx = node.find('Gfx')

        if gfx is None: return node
        return gfx


class RoomTypeLookup(Lookup):
    def __init__(self, mode, parent):
        super().__init__('RoomTypes', mode)
        self.parent = parent

    def loadFromMod(self, modPath, brPath, name):
        roomTypeFile = os.path.join(brPath, 'RoomTypesMod.xml')
        if not os.path.isfile(roomTypeFile):
            return

        print(f'-----------------------\nLoading room types from "{name}"')

        root = None
        try:
            tree = ET.parse(roomTypeFile)
            root = tree.getroot()
        except Exception as e:
            print('Error loading BR xml:', e)
            return

        roomTypeList = root.findall('room')
        if not roomTypeList: return

        def mapRoomType(roomType):
            if roomType.get('Name') is None:
                print('Tried to load room type, but had missing name!', str(roomType.attrib))
                return None

            print('Loading room type:', str(roomType.attrib))

            sanitizePath(roomType, 'Icon', brPath)

            for gfx in roomType.findall('Gfx'):
                sanitizePath(gfx, 'BGPrefix', brPath)

                for ent in gfx.findall('Entity'):
                    sanitizePath(ent, 'Image', brPath)

            return roomType

        roomTypes = list(filter(lambda x: x is not None, map(mapRoomType, roomTypeList)))
        if roomTypes:
            self.xml.extend(roomTypes)

    def filterRoom(self, node, room, path=None):
        typeF = node.get('Type')
        if typeF and typeF != str(room.info.type):
            return False

        nameRegex = node.get('NameRegex')
        if nameRegex and not re.match(nameRegex, room.name):
            return False

        stage = node.get('StageName')
        # TODO replace with check against room file stage
        if stage and path \
        and not next((st for st in self.parent.stages.lookup(path=path) if st.get('Name') == stage), []):
            return False

        idCriteria = parseCriteria(node.get('ID'))
        if idCriteria and not idCriteria(room.info.variant):
            return False

        return True

    def lookup(self, room=None, name=None, roomfile=None, path=None, showInMenu=None):
        rooms = self.xml.findall('room')

        doList = False

        if name:
            doList = True
            rooms = filter(lambda r: r.get('Name') == name, rooms)

        if showInMenu is not None:
            doList = True
            rooms = filter(lambda node: (node.get('ShowInMenu') == '1') == showInMenu, rooms)

        if room:
            doList = True
            rooms = filter(lambda node: self.filterRoom(node, room, path=path), rooms)

        if doList: rooms = list(rooms)
        return rooms

    def getMainType(self, room=None, roomfile=None, path=None):
        candidates = self.lookup(room=room, path=path)
        if not candidates: return None

        getCritWeight = lambda r, k, w: w if r.get(k) is not None else 0

        candidates = sorted(candidates, key=lambda r: -(getCritWeight(r, 'Type', 1) + \
                                                       getCritWeight(r, 'NameRegex', 10) + \
                                                       getCritWeight(r, 'StageName', 10) + \
                                                       getCritWeight(r, 'ID', 10)))

        return candidates[0]

    def getGfx(self, node, room=None, roomfile=None, path=None):
        possibleGfx = node.findall('Gfx')
        possibleGfx = sorted(possibleGfx, key=lambda g: -len(g.attrib))

        if room is None: return possibleGfx[0]

        for gfx in possibleGfx:
            if self.filterRoom(gfx, room, path=path):
                return gfx

        return None


class MainLookup:
    def __init__(self, mode):
        self.stages = StageLookup(mode, self)
        self.roomTypes = RoomTypeLookup(mode, self)

    def loadFromMod(self, modPath, brPath, name):
        self.stages.loadFromMod(modPath, brPath, name)
        self.roomTypes.loadFromMod(modPath, brPath, name)

    def getRoomGfx(self, room=None, roomfile=None, path=None):
        node = self.roomTypes.getMainType(room=room, roomfile=roomfile, path=path)
        if node is not None:
            ret = self.roomTypes.getGfx(node, room=room, roomfile=roomfile, path=path)
            if ret is not None: return ret

        node = self.stages.lookup(path=path)
        if not node:
            node = self.stages.lookup(name='Basement')

        return self.stages.getGfx(node[-1])

    def getGfxData(self, node=None):
        if node is None: return self.getGfxData(self.stages.getGfx(self.stages.lookup(name='Basement')[0]))

        baseGfx = None

        stage = node.get('StageGfx')
        if stage:
            stage = self.stages.lookup(name=stage)
            if stage:
                baseGfx = self.getGfxData(self.stages.getGfx(stage[0]))

        roomType = node.get('RoomGfx')
        if roomType:
            roomType = self.roomTypes.lookup(name=roomType)
            if roomType:
                baseGfx = self.getGfxData(self.roomTypes.getGfx(roomType[0]))

        prefix = node.get('BGPrefix')

        paths = None
        entities = []

        if baseGfx:
            paths = baseGfx['Paths']
            entities = baseGfx['Entities']

        if prefix:
            paths = {
                'OuterBG':    prefix + '.png',
                'BigOuterBG': prefix + '_big.png' if node.get('HasBigBG') == '1' else '',
                'InnerBG':    prefix + 'Inner.png',
                'NFloor':     prefix + '_nfloor.png',
                'LFloor':     prefix + '_lfloor.png',
            }

        if paths is None:
            raise ValueError('Invalid gfx node!', node.tag, node.attrib)

        entities.extend(node.findall('Entity'))
        ret = {
            'Paths': paths,
            'Entities': entities
        }

        for key, val in ret['Paths'].items():
            if not os.path.isfile(val):
                ret['Paths'][key] = ''

        return ret
