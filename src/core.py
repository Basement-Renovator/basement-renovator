class Entity:
    def __init__(self, x=0, y=0, t=0, v=0, s=0, weight=0, xmlProps=None):
        # Supplied entity info
        self.x = x
        self.y = y
        self.weight = weight

        self.xmlProps = xmlProps or {}

        self.clearValues()
        self.Type = t
        self.Variant = v
        self.Subtype = s

    def clearValues(self):
        self.Type = None
        self.Variant = None
        self.Subtype = None

        # Derived Entity Info
        self.name = None
        self.isGridEnt = False
        self.baseHP = None
        self.stageHP = None
        self.armor = None
        self.boss = None
        self.champion = None
        self.pixmap = None
        self.known = False
        self.invalid = False
        self.placeVisual = None
        self.blocksDoor = True

        self.mirrorX = None
        self.mirrorY = None


class Room:
    """
    contains concrete room information necessary for examining a room's game qualities
    such as type, variant, subtype, and shape information
    """

    ########## SHAPE DEFINITIONS
    # w x h
    # 1 = 1x1, 2 = 1x0.5, 3 = 0.5x1, 4 = 1x2, 5 = 0.5x2, 6 = 2x1, 7 = 2x0.5, 8 = 2x2
    # 9 = DR corner, 10 = DL corner, 11 = UR corner, 12 = UL corner
    # all coords must be offset -1, -1 when saving
    Shapes = {
        1: {  # 1x1
            "Doors": [[7, 0], [0, 4], [14, 4], [7, 8]],
            # format: min, max on axis, cross axis coord, normal direction along cross axis
            "Walls": {
                "X": [(0, 14, 0, 1), (0, 14, 8, -1)],
                "Y": [(0, 8, 0, 1), (0, 8, 14, -1)],
            },
            "Dims": (15, 9),
        },
        2: {  # horizontal closet (1x0.5)
            "Doors": [[0, 4], [14, 4]],
            "Walls": {
                "X": [(0, 14, 2, 1), (0, 14, 6, -1)],
                "Y": [(2, 6, 0, 1), (2, 6, 14, -1)],
            },
            "TopLeft": 30,  # Grid coord
            "BaseShape": 1,  # Base Room shape this is rendered over
            "Dims": (15, 5),
        },
        3: {  # vertical closet (0.5x1)
            "Doors": [[7, 0], [7, 8]],
            "Walls": {
                "X": [(4, 10, 0, 1), (4, 10, 8, -1)],
                "Y": [(0, 8, 4, 1), (0, 8, 10, -1)],
            },
            "TopLeft": 4,
            "BaseShape": 1,
            "Dims": (7, 9),
        },
        4: {  # 1x2 room
            "Doors": [[7, 0], [14, 4], [0, 4], [14, 11], [0, 11], [7, 15]],
            "Walls": {
                "X": [(0, 14, 0, 1), (0, 14, 15, -1)],
                "Y": [(0, 15, 0, 1), (0, 15, 14, -1)],
            },
            "Dims": (15, 16),
        },
        5: {  # tall closet (0.5x2)
            "Doors": [[7, 0], [7, 15]],
            "Walls": {
                "X": [(4, 10, 0, 1), (4, 10, 15, -1)],
                "Y": [(0, 15, 4, 1), (0, 15, 10, -1)],
            },
            "TopLeft": 4,
            "BaseShape": 4,
            "Dims": (7, 16),
        },
        6: {  # 2x1 room
            "Doors": [[7, 0], [0, 4], [7, 8], [20, 8], [27, 4], [20, 0]],
            "Walls": {
                "X": [(0, 27, 0, 1), (0, 27, 8, -1)],
                "Y": [(0, 8, 0, 1), (0, 8, 27, -1)],
            },
            "Dims": (28, 9),
        },
        7: {  # wide closet (2x0.5)
            "Doors": [[0, 4], [27, 4]],
            "Walls": {
                "X": [(0, 27, 2, 1), (0, 27, 6, -1)],
                "Y": [(2, 6, 0, 1), (2, 6, 27, -1)],
            },
            "TopLeft": 56,
            "BaseShape": 6,
            "Dims": (28, 5),
        },
        8: {  # 2x2 room
            "Doors": [
                [7, 0],
                [0, 4],
                [0, 11],
                [20, 0],
                [7, 15],
                [20, 15],
                [27, 4],
                [27, 11],
            ],
            "Walls": {
                "X": [(0, 27, 0, 1), (0, 27, 15, -1)],
                "Y": [(0, 15, 0, 1), (0, 15, 27, -1)],
            },
            "Dims": (28, 16),
        },
        9: {  # mirrored L room
            "Doors": [
                [20, 0],
                [27, 4],
                [7, 15],
                [20, 15],
                [13, 4],
                [0, 11],
                [27, 11],
                [7, 7],
            ],
            "Walls": {
                "X": [(0, 13, 7, 1), (13, 27, 0, 1), (0, 27, 15, -1)],
                "Y": [(7, 15, 0, 1), (0, 7, 13, 1), (0, 15, 27, -1)],
            },
            "BaseShape": 8,
            "MirrorX": 10,
            "MirrorY": 11,
            "Dims": (28, 16),
        },
        10: {  # L room
            "Doors": [
                [0, 4],
                [14, 4],
                [7, 0],
                [20, 7],
                [7, 15],
                [20, 15],
                [0, 11],
                [27, 11],
            ],
            "Walls": {
                "X": [(0, 14, 0, 1), (14, 27, 7, 1), (0, 27, 15, -1)],
                "Y": [(0, 15, 0, 1), (0, 7, 14, -1), (7, 15, 27, -1)],
            },
            "BaseShape": 8,
            "MirrorX": 9,
            "MirrorY": 12,
            "Dims": (28, 16),
        },
        11: {  # mirrored r room
            "Doors": [
                [0, 4],
                [7, 8],
                [7, 0],
                [13, 11],
                [20, 0],
                [27, 4],
                [20, 15],
                [27, 11],
            ],
            "Walls": {
                "X": [(0, 27, 0, 1), (0, 13, 8, -1), (13, 27, 15, -1)],
                "Y": [(0, 8, 0, 1), (8, 15, 13, 1), (0, 15, 27, -1)],
            },
            "BaseShape": 8,
            "MirrorX": 12,
            "MirrorY": 9,
            "Dims": (28, 16),
        },
        12: {  # r room
            "Doors": [
                [0, 4],
                [7, 0],
                [20, 0],
                [14, 11],
                [27, 4],
                [7, 15],
                [0, 11],
                [20, 8],
            ],
            "Walls": {
                "X": [(0, 27, 0, 1), (14, 27, 8, -1), (0, 14, 15, -1)],
                "Y": [(0, 15, 0, 1), (8, 15, 14, -1), (0, 8, 27, -1)],
            },
            "BaseShape": 8,
            "MirrorX": 11,
            "MirrorY": 10,
            "Dims": (28, 16),
        },
    }

    for shape in Shapes.values():
        doorWalls = shape["DoorWalls"] = []
        for door in shape["Doors"]:
            door.append(True)
            for wall in shape["Walls"]["X"]:
                if door[0] >= wall[0] and door[0] <= wall[1] and door[1] == wall[2]:
                    doorWalls.append((door, wall, "X"))
                    break
            for wall in shape["Walls"]["Y"]:
                if door[1] >= wall[0] and door[1] <= wall[1] and door[0] == wall[2]:
                    doorWalls.append((door, wall, "Y"))

    class Info:
        def __init__(self, t=0, v=0, s=0, shape=1):
            self.type = t
            self.variant = v
            self.subtype = s
            self.shape = shape

        @property
        def shape(self):
            return self._shape

        @shape.setter
        def shape(self, val):
            self._shape = val
            self.shapeData = Room.Shapes[self.shape]
            bs = self.shapeData.get("BaseShape")
            self.baseShapeData = bs and Room.Shapes[bs]
            self.makeNewDoors()

        # represents the actual dimensions of the room, including out of bounds
        @property
        def dims(self):
            return (self.baseShapeData or self.shapeData)["Dims"]

        @property
        def width(self):
            return self.shapeData["Dims"][0]

        @property
        def height(self):
            return self.shapeData["Dims"][1]

        def makeNewDoors(self):
            self.doors = [door[:] for door in self.shapeData["Doors"]]

        def gridLen(self):
            dims = self.dims
            return dims[0] * dims[1]

        @staticmethod
        def gridIndex(x, y, w):
            return y * w + x

        @staticmethod
        def coords(g, w):
            return g % w, int(g / w)

        @staticmethod
        def _axisBounds(a, c, w):
            wmin, wmax, wlvl, wdir = w
            return a < wmin or a > wmax or ((c > wlvl) - (c < wlvl)) == wdir

        def inFrontOfDoor(self, x, y):
            for door, wall, axis in self.shapeData["DoorWalls"]:
                if axis == "X" and door[0] == x and y - door[1] == wall[3]:
                    return door
                if axis == "Y" and door[1] == y and x - door[0] == wall[3]:
                    return door
            return None

        def isInBounds(self, x, y):
            return all(
                Room.Info._axisBounds(x, y, w) for w in self.shapeData["Walls"]["X"]
            ) and all(
                Room.Info._axisBounds(y, x, w) for w in self.shapeData["Walls"]["Y"]
            )

        def snapToBounds(self, x, y, dist=1):
            for w in self.shapeData["Walls"]["X"]:
                if not Room.Info._axisBounds(x, y, w):
                    y = w[2] + w[3] * dist

            for w in self.shapeData["Walls"]["Y"]:
                if not Room.Info._axisBounds(y, x, w):
                    x = w[2] + w[3] * dist

            return (x, y)

    def __init__(
        self,
        name="New Room",
        spawns=None,
        difficulty=1,
        weight=1.0,
        mytype=1,
        variant=0,
        subtype=0,
        shape=1,
        doors=None,
    ):
        """Initializes the room item."""
        self.name = name

        self.info = Room.Info(mytype, variant, subtype, shape)
        if doors:
            if len(self.info.doors) != len(doors):
                print(f"{name} ({variant}): Invalid doors!", doors)
            self.info.doors = doors

        self.gridSpawns = spawns or [[] for x in range(self.info.gridLen())]
        if self.info.gridLen() != len(self.gridSpawns):
            print(f"{name} ({variant}): Invalid grid spawns!")

        self.difficulty = difficulty
        self.weight = weight

        self.lastTestTime = None
        self.xmlProps = {}

    @property
    def gridSpawns(self):
        return self._gridSpawns

    @gridSpawns.setter
    def gridSpawns(self, g):
        self._gridSpawns = g

        self._spawnCount = 0
        for entStack in self.gridSpawns:
            if entStack:
                self._spawnCount += 1

    DoorSortKey = lambda door: (door[0], door[1])

    def getSpawnCount(self):
        return self._spawnCount

    def reshape(self, shape, doors=None):
        spawnIter = self.spawns()

        self.info.shape = shape
        if doors:
            self.info.doors = doors
        realWidth = self.info.dims[0]

        gridLen = self.info.gridLen()
        newGridSpawns = [[] for x in range(gridLen)]

        for stack, x, y in spawnIter:
            idx = Room.Info.gridIndex(x, y, realWidth)
            if idx < gridLen:
                newGridSpawns[idx] = stack

        self.gridSpawns = newGridSpawns

    @staticmethod
    def getDesc(info, name, difficulty, weight):
        return f"{name} ({info.type}.{info.variant}.{info.subtype}) ({info.width-2}x{info.height-2}) - Difficulty: {difficulty}, Weight: {weight}, Shape: {info.shape}"

    def getPrefix(self):
        return Room.getDesc(self.info, self.name, self.difficulty, self.weight)

    class _SpawnIter:
        def __init__(self, gridSpawns, dims):
            self.idx = -1
            self.spawns = gridSpawns
            self.width, self.height = dims

        def __iter__(self):
            return self

        def __next__(self):
            stack = None
            while True:
                self.idx += 1
                if self.idx >= self.width * self.height or self.idx >= len(self.spawns):
                    raise StopIteration

                stack = self.spawns[self.idx]
                if stack:
                    break
            x = int(self.idx % self.width)
            y = int(self.idx / self.width)
            return (stack, x, y)

    def spawns(self):
        return Room._SpawnIter(self.gridSpawns, self.info.dims)


class File:
    def __init__(self, rooms, xmlProps=None):
        self.rooms = rooms
        self.xmlProps = xmlProps or {}
