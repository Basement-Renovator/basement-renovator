"""
Merges room files into one
"""
from pathlib import Path

import subprocess
import roomconvert as cvt

from PyQt5.QtCore import QCommandLineOption, QCommandLineParser, QSettings
from PyQt5.QtWidgets import QApplication


def recomputeRoomIDs(roomList, startingId=None):
    # sort rooms by type
    # special rooms are at the bottom
    # ignore subtype since mineshaft rooms depend on sequential pairs
    roomList.sort(key=lambda r: r.info.type)

    roomsByType = {}

    for room in roomList:
        if room.info.type not in roomsByType:
            roomsByType[room.info.type] = startingId or room.info.variant

        room.info.variant = roomsByType[room.info.type]

        roomsByType[room.info.type] += 1


def runmain():
    import sys

    app = QApplication(sys.argv)

    cmdParser = QCommandLineParser()
    cmdParser.setApplicationDescription(
        "Room file merger utility script for Basement Renovator. Takes a set of file paths"
    )
    cmdParser.addHelpOption()

    cmdParser.addPositionalArgument("file", "xml files to merge")

    outputFileOpt = QCommandLineOption("output", "output filename, must be xml", "file")
    cmdParser.addOption(outputFileOpt)

    stbOpt = QCommandLineOption(
        "stb", "whether to save an stb version of the file next to it"
    )
    cmdParser.addOption(stbOpt)

    noRecompIdsOpt = QCommandLineOption(
        "noRecomputeIds",
        "turn off recomputing room ids; useful for special room merging",
    )
    cmdParser.addOption(noRecompIdsOpt)

    idOpt = QCommandLineOption(
        "startingId", "optional starting id to use when recomputing room ids", "id"
    )
    cmdParser.addOption(idOpt)

    skipOpt = QCommandLineOption(
        "roommerge", "placeholder argument used to prevent recursive execution"
    )
    cmdParser.addOption(skipOpt)

    cmdParser.process(app)

    if cmdParser.isSet(skipOpt):
        print("Recursive execution from save hook, skipping")
        return

    paths = cmdParser.positionalArguments()
    if not paths:
        print("Must specify at least one file to merge!")
        return

    outputFileArg = cmdParser.value(outputFileOpt)
    outputFilePath = Path(outputFileArg).absolute().resolve()
    if not outputFileArg or outputFilePath.suffix != ".xml":
        print("Must specify xml output file!")
        return

    lastModified = None
    if outputFilePath.exists():
        lastModified = outputFilePath.stat().st_mtime

    idArg = cmdParser.value(idOpt)

    noRecompIdsArg = cmdParser.isSet(noRecompIdsOpt)
    stbArg = cmdParser.isSet(stbOpt)

    mergeRoomFile = None
    i = -1
    while (i + 1) < len(paths):
        i += 1

        file = paths[i]

        path = Path(file)
        if path.is_dir():
            files = list(filter(lambda f: f.suffix == ".xml", path.iterdir()))
            print("Adding xml files to queue from: ", path)
            del paths[i]
            i -= 1
            paths.extend(files)

    paths = list(filter(lambda f: Path(f).exists(), paths))

    if lastModified:
        anyModified = (
            next((file for file in paths if file.stat().st_mtime > lastModified), None)
            is not None
        )
        if not anyModified:
            print("----")
            print(
                "Skipping since no xmls in folder have been modified since last update"
            )
            return

    for file in paths:
        print("----")
        print("Path:", file)

        path = Path(file)

        print("Merging file...")
        if path.suffix != ".xml":
            print("Must be xml! Skipping!")
            continue

        roomFile = cvt.xmlToCommon(path)
        if not mergeRoomFile:
            mergeRoomFile = roomFile
        else:
            mergeRoomFile.rooms.extend(roomFile.rooms)

    print("----")

    if not mergeRoomFile:
        print("No rooms files to merge")
        return

    if not noRecompIdsArg:
        recomputeRoomIDs(mergeRoomFile.rooms, idArg and int(idArg))

    cvt.commonToXML(outputFilePath, mergeRoomFile.rooms, file=mergeRoomFile)
    if stbArg:
        cvt.commonToSTBAB(outputFileArg.replace(".xml", ".stb"), mergeRoomFile.rooms)

    settings = QSettings(__file__ + "/../../settings.ini", QSettings.IniFormat)
    saveHooks = settings.value("HooksSave")
    if saveHooks:
        fullPath = str(outputFilePath)
        for hook in saveHooks:
            hook = Path(hook).absolute().resolve()
            try:
                subprocess.run(
                    [str(hook), fullPath, "--save", "--roommerge"],
                    cwd=hook.parent,
                    timeout=60,
                )
            except Exception as e:
                print("Save hook failed! Reason:", e)

    print("Success! Merged to", outputFileArg)


if __name__ == "__main__":
    runmain()
