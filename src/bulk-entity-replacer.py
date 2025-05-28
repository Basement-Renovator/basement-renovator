"""
Bulk replaces entities across room files
"""

import json
from pathlib import Path
from PyQt5.QtCore import QCommandLineOption, QCommandLineParser
from PyQt5.QtWidgets import QApplication

import roomconvert as cvt
from util import printf


def replaceEntities(rooms, replaced, replacement):
    numEnts = 0
    numRooms = 0

    def checkEq(ent, b):
        return (
            ent.Type == b[0]
            and (b[1] < 0 or ent.Variant == b[1])
            and (b[2] < 0 or ent.Subtype == b[2])
        )

    def fixEnt(ent, b):
        ent.Type = b[0]
        if b[1] >= 0:
            ent.Variant = b[1]
        if b[2] >= 0:
            ent.Subtype = b[2]

    for currRoom in rooms:
        n = 0
        for stack, x, y in currRoom.spawns():
            for ent in stack:
                if checkEq(ent, replaced):
                    fixEnt(ent, replacement)
                    n += 1

        if n > 0:
            numRooms += 1
            numEnts += n

    printf(
        f"{replaced} -> {replacement}: "
        + (
            numEnts > 0
            and f"Replaced {numEnts} entities in {numRooms} rooms"
            or "No entities to replace!"
        )
    )

    return numEnts


def recurseGetFiles(path: Path):
    filesList = []
    if path.is_dir():
        for path2 in path.iterdir():
            filesList.extend(recurseGetFiles(path2))
    elif path.suffix == ".xml":
        filesList.append(path)

    return filesList


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    cmdParser = QCommandLineParser()
    cmdParser.setApplicationDescription(
        "Bulk entity replacement utility script for Basement Renovator. Takes a json file path"
    )
    cmdParser.addHelpOption()

    cmdParser.addPositionalArgument(
        "configFile",
        """json config file to grab configuration from. Format:
    {
        stb: optional, true to save an stb version of files,
        files: [ path to file/folder to replace, ... ],
        entities: [
            {
                from: [ type, variant, subtype (can be -1 for wild card) ],
                to: [ type, variant, subtype (can be -1 for wild card) ],
            },
            ...
        ]
    }
    """,
    )

    stbOpt = QCommandLineOption(
        "stb", "whether to save an stb version of the file next to it"
    )
    cmdParser.addOption(stbOpt)

    cmdParser.process(app)

    args = cmdParser.positionalArguments()
    configArg = args[0]
    configPath = Path(configArg).absolute().resolve()
    if not (configArg and configPath.is_file()):
        print("Invalid config path!")
        sys.exit()

    workingDirectory = configPath.parent

    stbArg = cmdParser.isSet(stbOpt)

    with open(configPath) as configFile:
        config = json.load(configFile)

        if "stb" in config and config["stb"]:
            stbArg = True

        totalRooms = 0
        printf("Replacing entities:", config["entities"])

        files = []
        for file in config["files"]:
            basePath = workingDirectory / Path(file)
            if basePath.is_dir() or basePath.suffix == ".xml":
                files.extend(recurseGetFiles(basePath))
            else:
                printf(f"{basePath} is not an XML file or directory, skipping!")

        for path in files:
            printf("Replacing Entities in File: ", path)

            roomFile = cvt.xmlToCommon(path)
            rooms = roomFile.rooms

            printf("Room Count:", len(rooms))
            totalRooms += len(rooms)

            numEnts = 0
            for entPair in config["entities"]:
                numEnts += replaceEntities(rooms, entPair["from"], entPair["to"])

            if numEnts > 0:
                cvt.commonToXML(path, rooms, file=roomFile)
                if stbArg:
                    cvt.commonToSTBAB(path.with_suffix(".stb"), rooms)

    printf("Success!", totalRooms, "affected")
