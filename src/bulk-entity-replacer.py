"""
Bulk replaces entities across room files
"""
import json

import roomconvert as cvt

from PyQt5.QtCore import QCommandLineOption, QCommandLineParser
from PyQt5.QtWidgets import QApplication


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

    print(
        f"{replaced} -> {replacement}: "
        + (
            numEnts > 0
            and f"Replaced {numEnts} entities in {numRooms} rooms"
            or "No entities to replace!"
        )
    )

    return numEnts


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
        files: [ absolute path to file to replace, ... ],
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

    stbArg = cmdParser.isSet(stbOpt)

    with open(configArg) as configFile:
        config = json.load(configFile)

        totalRooms = 0
        print("Replacing entities:", config["entities"])
        for rf in config["files"]:
            print("File: ", rf)
            if ".xml" not in rf:
                print("Must be xml! Skipping!")
                continue

            roomFile = cvt.xmlToCommon(rf)
            rooms = roomFile.rooms

            print("Room Count:", len(rooms))
            totalRooms += len(rooms)

            numEnts = 0
            for entPair in config["entities"]:
                numEnts += replaceEntities(rooms, entPair["from"], entPair["to"])

            if numEnts > 0:
                cvt.commonToXML(rf, rooms, file=roomFile)
                if stbArg:
                    cvt.commonToSTBAB(rf.replace(".xml", ".stb"), rooms)

    print("Success!", totalRooms, "affected")
