"""Functions for converting to and from the various stb formats"""

import struct
from pathlib import Path
import xml.etree.cElementTree as ET
from xml.dom import minidom
import re

import cProfile

from src.core import Room, Entity

def commonToXMLSlow(destPath, rooms, isPreview = False):
    """Converts the common format to xml nodes"""
    if isPreview and len(rooms) != 1:
        raise ValueError("Previews must be one room!")

    outputRoot = ET.Element('rooms')

    nodes = []
    for room in rooms:
        width, height = room.info.dims
        roomNode = ET.Element('room', {
            "type":       str(room.info.type),
            "variant":    str(room.info.variant),
            "subtype":    str(room.info.subtype),
            "name":       str(room.name),
            "difficulty": str(room.difficulty),
            "weight":     str(room.weight),
            "shape":      str(room.info.shape),
            "width":      str(width - 2),
            "height":     str(height - 2),
        })

        roomNode.extend(map(lambda door: ET.Element('door', {
            'x': str(door[0] - 1),
            'y': str(door[1] - 1),
            'exists': str(door[2])
        }), room.info.doors))

        stackNodes = []
        for stack, x, y in room.spawns():
            stackNode = ET.Element('spawn', {
                'x': str(x - 1),
                'y': str(y - 1)
            })

            stackNode.extend(list(map(lambda ent: ET.Element('entity', {
                "type":       str(ent.Type),
                "variant":    str(ent.Variant),
                "subtype":    str(ent.Subtype),
                "weight":     str(ent.weight),
            }), stack)))

            stackNodes.append(stackNode)

        roomNode.extend(stackNodes)

        nodes.append(roomNode)

    if isPreview:
        outputRoot = nodes[0]
    else:
        outputRoot.extend(nodes)
    with open(destPath, 'w') as out:
        xml = minidom.parseString(ET.tostring(outputRoot)).toprettyxml(indent="    ")
        out.write(xml)

def commonToXML(destPath, rooms, isPreview = False):
    """Converts the common format to xml nodes"""
    if isPreview and len(rooms) != 1:
        raise ValueError("Previews must be one room!")

    output = [ '<?xml version="1.0" ?>\n' ]
    if not isPreview:
        output.append('<rooms>\n')

    for room in rooms:
        width, height = room.info.dims
        output.append(f'\t<room variant="{room.info.variant}" name="{room.name}" type="{room.info.type}" subtype="{room.info.subtype}" shape="{room.info.shape}" width="{width - 2}" height="{height - 2}" difficulty="{room.difficulty}" weight="{room.weight}">\n')

        for door in room.info.doors:
            output.append(f'\t\t<door exists="{door[2]}" x="{door[0] - 1}" y="{door[1] - 1}"/>\n')

        for stack, x, y in room.spawns():
            output.append(f'\t\t<spawn x="{x - 1}" y="{y - 1}">\n')

            for ent in stack:
                output.append(f'\t\t\t<entity type="{ent.Type}" variant="{ent.Variant}" subtype="{ent.Subtype}" weight="{ent.weight}"/>\n')

            output.append('\t\t</spawn>\n')

        output.append('\t</room>\n')

    if not isPreview:
        output.append("</rooms>\n")

    with open(destPath, 'w') as out:
        out.write(''.join(output))

def commonToSTBAB(path, rooms):
    """Converts the common format to Afterbirth stb"""

    headerPacker = struct.Struct('<4sI')
    roomBegPacker = struct.Struct('<IIIBH')
    roomEndPacker = struct.Struct('<fBBB')
    doorHeaderPacker = struct.Struct('<BH')
    doorPacker = struct.Struct('<hh?')
    stackPacker = struct.Struct('<hhB')
    entPacker = struct.Struct('<HHHf')

    totalBytes = headerPacker.size
    totalBytes += len(rooms) * (roomBegPacker.size + roomEndPacker.size)
    for room in rooms:
        totalBytes += len(room.name)
        totalBytes += doorHeaderPacker.size + doorPacker.size * len(room.info.doors)
        totalBytes += room.getSpawnCount() * stackPacker.size
        for stack, x, y in room.spawns():
            totalBytes += len(stack) * entPacker.size

    out = bytearray(totalBytes)
    off = 0
    headerPacker.pack_into(out, off, "STB1".encode(), len(rooms))
    off += headerPacker.size

    for room in rooms:
        width, height = room.info.dims
        nameLen = len(room.name)
        roomBegPacker.pack_into(out, off, room.info.type, room.info.variant, room.info.subtype, room.difficulty, nameLen)
        off += roomBegPacker.size
        struct.pack_into(f'<{nameLen}s', out, off, room.name.encode())
        off += nameLen
        roomEndPacker.pack_into(out, off, room.weight, width - 2, height - 2, room.info.shape)
        off += roomEndPacker.size

        # Doors and Entities
        doorHeaderPacker.pack_into(out, off, len(room.info.doors), room.getSpawnCount())
        off += doorHeaderPacker.size

        for door in room.info.doors:
            doorPacker.pack_into(out, off, door[0] - 1, door[1] - 1, door[2])
            off += doorPacker.size

        for stack, x, y in room.spawns():
            numEnts = len(stack)
            stackPacker.pack_into(out, off, x - 1, y - 1, numEnts)
            off += stackPacker.size

            for entity in stack:
                entPacker.pack_into(out, off, entity.Type, entity.Variant, entity.Subtype, entity.weight)
                off += entPacker.size

    with open(path, 'wb') as stb:
        stb.write(out)

def commonToSTBRB(path, rooms):
    """Converts the common format to Rebirth stb"""

    headerPacker = struct.Struct('<I')
    roomBegPacker = struct.Struct('<IIBH')
    roomEndPacker = struct.Struct('<fBB')
    doorHeaderPacker = struct.Struct('<BH')
    doorPacker = struct.Struct('<hh?')
    stackPacker = struct.Struct('<hhB')
    entPacker = struct.Struct('<HHHf')

    totalBytes = headerPacker.size
    totalBytes += len(rooms) * (roomBegPacker.size + roomEndPacker.size)
    for room in rooms:
        totalBytes += len(room.name)
        totalBytes += doorHeaderPacker.size + doorPacker.size * len(room.info.doors)
        totalBytes += room.getSpawnCount() * stackPacker.size
        for stack, x, y in room.spawns():
            totalBytes += len(stack) * entPacker.size

    out = bytearray(totalBytes)
    off = 0
    headerPacker.pack_into(out, off, len(rooms))
    off += headerPacker.size

    for room in rooms:
        width, height = room.info.dims
        nameLen = len(room.name)
        roomBegPacker.pack_into(out, off, room.info.type, room.info.variant, room.difficulty, nameLen)
        off += roomBegPacker.size
        struct.pack_into(f'<{nameLen}s', out, off, room.name.encode())
        off += nameLen
        roomEndPacker.pack_into(out, off, room.weight, width - 2, height - 2)
        off += roomEndPacker.size

        # Doors and Entities
        doorHeaderPacker.pack_into(out, off, len(room.info.doors), room.getSpawnCount())
        off += doorHeaderPacker.size

        for door in room.info.doors:
            doorPacker.pack_into(out, off, door[0] - 1, door[1] - 1, door[2])
            off += doorPacker.size

        for stack, x, y in room.spawns():
            numEnts = len(stack)
            stackPacker.pack_into(out, off, x - 1, y - 1, numEnts)
            off += stackPacker.size

            for entity in stack:
                entPacker.pack_into(out, off, entity.Type, entity.Variant, entity.Subtype, entity.weight)
                off += entPacker.size

    with open(path, 'wb') as stb:
        stb.write(out)

def stbToCommon(path):
    header = open(path, 'rb').read(4)

    try:
        header = header.decode()
    except UnicodeDecodeError:
        header = 'STB0' # sometimes the header will actually decode successfully, so can't count on this value

    if header == 'STB1':
        return stbABToCommon(path)
    if header == 'STB2':
        return stbAntiToCommon(path)
    else:
        return stbRBToCommon(path)

def stbABToCommon(path):
    """Converts an Afterbirth STB to the common format"""
    stb = open(path, 'rb').read()

    headerPacker = struct.Struct('<4sI')
    roomBegPacker = struct.Struct('<IIIBH')
    roomEndPacker = struct.Struct('<fBBBBH')
    doorPacker = struct.Struct('<hh?')
    stackPacker = struct.Struct('<hhB')
    entPacker = struct.Struct('<HHHf')

    # Header, Room count
    header, rooms = headerPacker.unpack_from(stb, 0)
    off = headerPacker.size
    if header.decode() != "STB1":
        raise ValueError("Afterbirth STBs must have the STB1 header")

    ret = []

    for r in range(rooms):

        # Room Type, Room Variant, Subtype, Difficulty, Length of Room Name String
        roomData = roomBegPacker.unpack_from(stb, off)
        rtype, rvariant, rsubtype, difficulty, nameLen = roomData
        off += roomBegPacker.size
        #print ("Room Data: {roomData}")

        # Room Name
        roomName = struct.unpack_from(f'<{nameLen}s', stb, off)[0].decode()
        off += nameLen
        #print (f"Room Name: {roomName}")

        # Weight, width, height, shape, number of doors, number of entities
        entityTable = roomEndPacker.unpack_from(stb, off)
        rweight, width, height, shape, numDoors, numEnts = entityTable
        off += roomEndPacker.size
        #print (f"Entity Table: {entityTable}")

        width += 2
        height += 2
        if shape == 0:
            print(f'Bad room shape! {rvariant}, {roomName}, {width}, {height}')
            shape = 1

        doors = []
        for d in range(numDoors):
            # X, Y, exists
            doorX, doorY, exists = doorPacker.unpack_from(stb, off)
            off += doorPacker.size

            doors.append([ doorX + 1, doorY + 1, exists ])

        room = Room(roomName, None, difficulty, rweight, rtype, rvariant, rsubtype, shape, doors)
        ret.append(room)

        realWidth = room.info.dims[0]
        gridLen = room.info.gridLen()
        for e in range(numEnts):
            # x, y, number of entities at this position
            ex, ey, stackedEnts = stackPacker.unpack_from(stb, off)
            ex += 1
            ey += 1
            off += stackPacker.size

            grindex = Room.Info.gridIndex(ex, ey, realWidth)
            if grindex >= gridLen:
                print(f'Discarding the current entity stack due to invalid position! {room.getPrefix()}: {ex-1},{ey-1}')
                off += entPacker.size * stackedEnts
                continue

            ents = room.gridSpawns[grindex]

            for s in range(stackedEnts):
                #  type, variant, subtype, weight
                etype, evariant, esubtype, eweight = entPacker.unpack_from(stb, off)
                off += entPacker.size

                ents.append(Entity(ex, ey, etype, evariant, esubtype, eweight))

            #room.gridSpawns = room.gridSpawns # probably unneeded for now

    return ret

def stbAntiToCommon(path):
    """Converts an Antibirth STB to the common format"""
    stb = open(path, 'rb').read()

    headerPacker = struct.Struct('<4sI')
    roomBegPacker = struct.Struct('<IIIBH')
    roomEndPacker = struct.Struct('<fBBBBH9s') # 9 padding bytes for some other room data
    doorPacker = struct.Struct('<hh?')
    stackPacker = struct.Struct('<hhB')
    entPacker = struct.Struct('<HHHf')

    # Header, Room count
    header, rooms = headerPacker.unpack_from(stb, 0)
    off = headerPacker.size
    if header.decode() != "STB2":
        raise ValueError("Antibirth STBs must have the STB2 header")

    ret = []

    for r in range(rooms):

        # Room Type, Room Variant, Subtype, Difficulty, Length of Room Name String
        roomData = roomBegPacker.unpack_from(stb, off)
        rtype, rvariant, rsubtype, difficulty, nameLen = roomData
        off += roomBegPacker.size
        #print ("Room Data: {roomData}")

        # Room Name
        roomName = struct.unpack_from(f'<{nameLen}s', stb, off)[0].decode()
        off += nameLen
        #print (f"Room Name: {roomName}")

        # Weight, width, height, shape, number of doors, number of entities
        entityTable = roomEndPacker.unpack_from(stb, off)
        rweight, width, height, shape, numDoors, numEnts, extraData = entityTable
        off += roomEndPacker.size
        #print (f"Entity Table: {entityTable}")

        width += 2
        height += 2
        if shape == 0:
            print(f'Bad room shape! {rvariant}, {roomName}, {width}, {height}')
            shape = 1

        doors = []
        for d in range(numDoors):
            # X, Y, exists
            doorX, doorY, exists = doorPacker.unpack_from(stb, off)
            off += doorPacker.size

            doors.append([ doorX + 1, doorY + 1, exists ])

        room = Room(roomName, None, difficulty, rweight, rtype, rvariant, rsubtype, shape, doors)
        ret.append(room)

        if extraData != b'\x00\x00\x00\x00\x00\x00\x00\x00\x00':
            print (f'Room {room.getPrefix()} uses the extra bytes:', extraData)

        realWidth = room.info.dims[0]
        gridLen = room.info.gridLen()
        for e in range(numEnts):
            # x, y, number of entities at this position
            ex, ey, stackedEnts = stackPacker.unpack_from(stb, off)
            ex += 1
            ey += 1
            off += stackPacker.size

            grindex = Room.Info.gridIndex(ex, ey, realWidth)
            if grindex >= gridLen:
                print(f'Discarding the current entity stack due to invalid position! {room.getPrefix()}: {ex-1},{ey-1}')
                off += entPacker.size * stackedEnts
                continue

            ents = room.gridSpawns[grindex]

            for s in range(stackedEnts):
                #  type, variant, subtype, weight
                etype, evariant, esubtype, eweight = entPacker.unpack_from(stb, off)
                off += entPacker.size

                ents.append(Entity(ex, ey, etype, evariant, esubtype, eweight))

            #room.gridSpawns = room.gridSpawns # probably unneeded for now

    return ret

def stbRBToCommon(path):
    """Converts an Rebirth STB to the common format"""
    stb = open(path, 'rb').read()

    headerPacker = struct.Struct('<I')
    roomBegPacker = struct.Struct('<IIBH')
    roomEndPacker = struct.Struct('<fBBBH')
    doorPacker = struct.Struct('<hh?')
    stackPacker = struct.Struct('<hhB')
    entPacker = struct.Struct('<HHHf')

    # Room count
    # No header for rebirth
    rooms = headerPacker.unpack_from(stb, 0)[0]
    off = headerPacker.size
    ret = []

    for r in range(rooms):

        # Room Type, Room Variant, Difficulty, Length of Room Name String
        # No subtype for rebirth
        roomData = roomBegPacker.unpack_from(stb, off)
        rtype, rvariant, difficulty, nameLen = roomData
        off += roomBegPacker.size
        #print ("Room Data: {roomData}")

        # Room Name
        roomName = struct.unpack_from(f'<{nameLen}s', stb, off)[0].decode()
        off += nameLen
        #print (f"Room Name: {roomName}")

        # Weight, width, height, number of doors, number of entities
        # No shape for rebirth
        entityTable = roomEndPacker.unpack_from(stb, off)
        rweight, width, height, numDoors, numEnts = entityTable
        off += roomEndPacker.size
        #print (f"Entity Table: {entityTable}")

        # We have to figure out the shape manually for rebirth
        width += 2
        height += 2
        shape = 1
        for s in [ 1, 4, 6, 8 ]: # only valid room shapes as of rebirth, defaults to 1x1
            w, h = Room.Info(shape=s).dims
            if w == width and h == height:
                shape = s
                break

        doors = []
        for d in range(numDoors):
            # X, Y, exists
            doorX, doorY, exists = doorPacker.unpack_from(stb, off)
            off += doorPacker.size

            doors.append([ doorX + 1, doorY + 1, exists ])

        room = Room(roomName, None, difficulty, rweight, rtype, rvariant, 0, shape, doors)
        ret.append(room)

        realWidth = room.info.dims[0]
        gridLen = room.info.gridLen()
        for e in range(numEnts):
            # x, y, number of entities at this position
            ex, ey, stackedEnts = stackPacker.unpack_from(stb, off)
            ex += 1
            ey += 1
            off += stackPacker.size

            grindex = Room.Info.gridIndex(ex, ey, realWidth)
            if grindex >= gridLen:
                print(f'Discarding the current entity stack due to invalid position! {room.getPrefix()}: {ex-1},{ey-1}')
                off += entPacker.size * stackedEnts
                continue

            ents = room.gridSpawns[grindex]

            for s in range(stackedEnts):
                #  type, variant, subtype, weight
                etype, evariant, esubtype, eweight = entPacker.unpack_from(stb, off)
                off += entPacker.size

                ents.append(Entity(ex, ey, etype, evariant, esubtype, eweight))

            #room.gridSpawns = room.gridSpawns # probably unneeded for now

    return ret

def xmlToCommon(path, destPath=None):
    """Converts an Afterbirth xml to the common format"""

    xml = ET.parse(path)

    root = xml.getroot()  # can be stage, rooms, etc

    rooms = root.findall('room')
    ret = []

    for roomNode in rooms:

        rtype      = int(roomNode.get('type') or '1')
        rvariant   = int(roomNode.get('variant') or '0')
        rsubtype   = int(roomNode.get('subtype') or '0')
        difficulty = int(roomNode.get('difficulty') or '0')
        roomName   = roomNode.get('name') or ''
        rweight    = float(roomNode.get('weight') or '1')
        shape      = int(roomNode.get('shape') or '1')

        doors = list(map(lambda door: [ int(door.get('x')) + 1, int(door.get('y')) + 1, door.get('exists', "0")[0] in "1tTyY" ], roomNode.findall('door')))

        room = Room(roomName, None, difficulty, rweight, rtype, rvariant, rsubtype, shape, doors)
        ret.append(room)

        realWidth = room.info.dims[0]
        gridLen = room.info.gridLen()
        for spawn in roomNode.findall('spawn'):
            ex, ey, stackedEnts = int(spawn.get('x')) + 1, int(spawn.get('y')) + 1, spawn.findall('entity')

            grindex = Room.Info.gridIndex(ex, ey, realWidth)
            if grindex >= gridLen:
                print(f'Discarding the current entity stack due to invalid position! {room.getPrefix()}: {ex-1},{ey-1}')
                continue

            ents = room.gridSpawns[grindex]
            for ent in stackedEnts:
                etype, evariant, esubtype, eweight = int(ent.get('type')), int(ent.get('variant')), int(ent.get('subtype')), float(ent.get('weight'))
                ents.append(Entity(ex, ey, etype, evariant, esubtype, eweight))

    return ret

def stbABToXML(path, destPath=None):
    destPath = destPath or Path(path).with_suffix('.xml')
    return commonToXML(destPath, stbABToCommon(path))

def xmlToSTBAB(path, destPath=None):
    destPath = destPath or Path(path).with_suffix('.stb')
    return commonToSTBAB(destPath, xmlToCommon(path))

# HA HA HA FUNNY MODE FUNNY MODE
def txtToCommon(path, entityXML):
    """Convert a txt file to the common format"""
    text = Path(path).read_text('utf-8')

    text = text.splitlines()
    numLines = len(text)

    def skipWS(i):
        for j in range(i, numLines):
            if text[j]: return j
        return numLines

    entMap = {}

    # Initial section: entity definitions
    # [Character]=[type].[variant].[subtype]
    # one per line, continues until it hits a line starting with ---
    roomBegin = 0
    for i in range(numLines):
        line = text[i]
        line = re.sub(r'\s', '', line)
        roomBegin = i

        if not line: continue
        if line.startswith('---'): break

        char, t, v, s = re.findall(r'(.)=(\d+).(\d+).(\d+)', line)[0]

        if char in [ '-', '|' ]:
            print("Can't use - or | for entities!")
            continue

        t = int(t)
        v = int(v)
        s = int(s)

        en = entityXML.find(f"entity[@ID='{t}'][@Subtype='{s}'][@Variant='{v}']")
        if en is None or en.get('Invalid') == '1':
            print(f"Invalid entity for character '{char}': '{en is None and 'UNKNOWN' or en.get('Name')}'! ({t}.{v}.{s})")
            continue

        entMap[char] = (t, v, s)

    shapeNames = {
        '1x1': 1,
        '2x2': 8,
        'closet': 2,
        'vertcloset': 3,
        '1x2': 4,
        'long': 7,
        'longvert': 5,
        '2x1': 6,
        'l': 10,
        'mirrorl': 9,
        'r': 12,
        'mirrorr': 11
    }

    ret = []

    # Main section: room definitions
    # First line: [id]: [name]
    # Second line, in no particular order: [Weight,] [Shape (within tolerance),] [Difficulty,] [Type[=1],] [Subtype[=0],]
    # Next [room height] lines: room layout
    # horizontal walls are indicated with -, vertical with |
    #   there will be no validation for this, but if lines are the wrong length it prints an error message and skips the line
    # coordinates to entities are 1:1, entity ids can be at most 1 char
    # place xs at door positions to turn them off
    roomBegin += 1
    while roomBegin < numLines:
        # 2 lines
        i = skipWS(roomBegin)
        if i == numLines: break

        rvariant, name = text[i].split(':', 1)
        name = name.strip()
        rvariant = int(rvariant)

        infoParts = re.sub(r'\s', '', text[i+1]).lower().split(',')
        shape = 1
        difficulty = 5
        weight = 1
        rtype = 1
        rsubtype = 0
        for part in infoParts:
            prop, val = re.findall(r'(.+)=(.+)', part)[0]
            if prop == 'shape': shape = shapeNames.get(val) or int(val)
            elif prop == 'difficulty': difficulty = shapeNames.get(val) or int(val)
            elif prop == 'weight': weight = float(val)
            elif prop == 'type': rtype = int(val)
            elif prop == 'subtype': rsubtype = int(val)

        r = Room(name, None, difficulty, weight, rtype, rvariant, rsubtype, shape)
        width, height = r.info.dims
        spawns = r.gridSpawns

        i = skipWS(i + 2)
        for j in range(i, i + height):
            if j == numLines:
                print('Could not finish room!')
                break

            y = j - i
            row = text[j]
            for x, char in enumerate(row):
                if char in [ '-', '|', ' ' ]:
                    continue
                if char.lower() == 'x':
                    changed = False
                    for door in r.info.doors:
                        if door[0] == x and door[1] == y:
                            door[2] = False
                            changed = True
                    if changed: continue

                ent = entMap.get(char)
                if ent:
                    spawns[Room.Info.gridIndex(x,y,width)].append(Entity(x, y, ent[0], ent[1], ent[2], 0))
                else:
                    print(f"Unknown entity! '{char}'")

        ret.append(r)

        i = skipWS(i + height)
        if i == numLines: break

        if not text[i].strip().startswith('---'):
            print('Could not find separator after room!')
            break

        roomBegin = i + 1

    return ret
