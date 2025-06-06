"""
Converts an xml file to an stb file
"""

from pathlib import Path

import roomconvert as cvt

from PyQt5.QtCore import QCommandLineOption, QCommandLineParser, QSettings
from PyQt5.QtWidgets import QApplication


def main():
    import sys

    app = QApplication(sys.argv)

    cmdParser = QCommandLineParser()
    cmdParser.setApplicationDescription(
        "Room file converter utility script for Basement Renovator. Takes a set of file paths"
    )
    cmdParser.addHelpOption()

    cmdParser.addPositionalArgument("file", "xml files to convert")

    sortEntsOpt = QCommandLineOption(
        "sortEntities",
        "if specified, sorts entity stacks by type, variant, subtype",
    )
    cmdParser.addOption(sortEntsOpt)

    skipOpt = QCommandLineOption(
        "roomconvert", "placeholder argument used to prevent recursive execution"
    )
    cmdParser.addOption(skipOpt)

    cmdParser.process(app)

    if cmdParser.isSet(skipOpt):
        print("Recursive execution from save hook, skipping")
        return

    paths = cmdParser.positionalArguments()
    if not paths:
        print("Must specify at least one file to convert!")
        return

    doSortEnts = cmdParser.isSet(sortEntsOpt)

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

    for file in paths:
        print("----")
        print("Converting path:", file)

        path = Path(file)

        if path.suffix != ".xml":
            print("Must be xml! Skipping!")
            continue

        outputFilePath = path.with_suffix(".stb")
        roomFile = cvt.xmlToCommon(path)

        if doSortEnts:
            for room in roomFile.rooms:
                for stack, x, y in room.spawns():
                    stack.sort(key=lambda ent: (ent.Type, ent.Variant, ent.Subtype))

        cvt.commonToSTBAB(outputFilePath, roomFile.rooms)

    print("----")
    print("Done!")


if __name__ == "__main__":
    main()
