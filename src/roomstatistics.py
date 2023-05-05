"""
Generates a readout of various room file and entity usage statistics
"""

import sys
import roomconvert as cvt

from pathlib import Path
from PyQt5.QtCore import QCommandLineOption, QCommandLineParser
from PyQt5.QtWidgets import QApplication
from lookup import MainLookup, EntityLookup
from settings import *


def addEntityToDat(entityConfigToDat, tracked, groupName, key):
    if key not in entityConfigToDat:
        entityConfigToDat[key] = {
            "totalentities": 0,
            "totalrooms": 0,
            "totalentitiespergroup": {},
            "totalroomspergroup": {},
        }

    if key not in tracked:
        tracked[key] = True
        entityConfigToDat[key]["totalrooms"] += 1

        if groupName in entityConfigToDat[key]["totalroomspergroup"]:
            entityConfigToDat[key]["totalroomspergroup"][groupName] += 1
        else:
            entityConfigToDat[key]["totalroomspergroup"][groupName] = 1

    entityConfigToDat[key]["totalentities"] += 1

    if groupName in entityConfigToDat[key]["totalentitiespergroup"]:
        entityConfigToDat[key]["totalentitiespergroup"][groupName] += 1
    else:
        entityConfigToDat[key]["totalentitiespergroup"][groupName] = 1


def getRoomEntityStats(
    rooms,
    filepath,
    group,
    entityConfigToDat,
    lookup: MainLookup,
    statisticsGroups=False,
    weightThreshold=None,
    difficultyThreshold=None,
):
    totalEntities = 0
    totalRoomsMatched = 0
    errors = ""
    for currRoom in rooms:
        if (weightThreshold is not None and currRoom.weight < weightThreshold) or (
            difficultyThreshold is not None
            and currRoom.difficulty < difficultyThreshold
        ):
            continue

        totalRoomsMatched += 1

        tracked = {}
        markedAsBugged = False
        for stack, x, y in currRoom.spawns():
            for ent in stack:
                entity = lookup.entities.lookupOne(
                    entitytype=ent.Type, variant=ent.Variant, subtype=ent.Subtype
                )
                if entity is None:
                    printf(
                        f"Encountered an unknown entity: {ent.Type}.{ent.Variant}.{ent.Subtype}, skipping!"
                    )
                    if markedAsBugged is False:
                        markedAsBugged = True
                        errors += f'Room {currRoom.name} (variant {currRoom.info.variant}, subtype {currRoom.info.subtype}, room type {currRoom.info.type}) from file "{filepath}" contains an invalid entity!\n'

                    continue

                totalEntities += 1

                inStatsGroup = False
                if statisticsGroups:
                    for tag in entity.tags.values():
                        if tag.statisticsgroup:
                            inStatsGroup = True
                            addEntityToDat(entityConfigToDat, tracked, group, tag)

                if not inStatsGroup:
                    addEntityToDat(entityConfigToDat, tracked, group, entity)

    return entityConfigToDat, totalEntities, errors, totalRoomsMatched


def recurseGetFiles(path, ignoreSTB, ignoreXML):
    filesList = []
    if path.is_dir():
        for path2 in path.iterdir():
            filesList.extend(recurseGetFiles(path2))
    elif (not ignoreXML and path.suffix == ".xml") or (
        not ignoreSTB and path.suffix == ".stb"
    ):
        filesList.append(path)

    return filesList


def runmain():
    app = QApplication(sys.argv)

    cmdParser = QCommandLineParser()
    cmdParser.setApplicationDescription(
        "Room file & entity usage statistics utility script for Basement Renovator. Takes a set of file paths."
    )
    cmdParser.addHelpOption()

    cmdParser.addPositionalArgument("file", "room files to read")

    outputFileOpt = QCommandLineOption(
        "output",
        "output filename; if specified writes to file rather than stdout, must be txt",
        "file",
    )
    cmdParser.addOption(outputFileOpt)

    errorOutputFileOpt = QCommandLineOption(
        "errors",
        "error output filename; if specified writes errors to file, must be txt",
        "file",
    )
    cmdParser.addOption(errorOutputFileOpt)

    roomThresholdOpt = QCommandLineOption(
        "roomThreshold",
        "whether to ignore entities that appear in less than 'threshold' rooms",
        "threshold",
    )
    cmdParser.addOption(roomThresholdOpt)

    weightThresholdOpt = QCommandLineOption(
        "weightThreshold",
        "whether to ignore rooms with a weight less than 'threshold'",
        "threshold",
    )
    cmdParser.addOption(weightThresholdOpt)

    difficultyThresholdOpt = QCommandLineOption(
        "difficultyThreshold",
        "whether to ignore rooms with a difficulty less than 'threshold'",
        "threshold",
    )
    cmdParser.addOption(difficultyThresholdOpt)

    groupRoomThresholdOpt = QCommandLineOption(
        "groupRoomThreshold",
        "how many rooms an entity must appear in within a group to count as being a part of it",
        "threshold",
    )
    cmdParser.addOption(groupRoomThresholdOpt)

    statisticsGroupOpt = QCommandLineOption(
        "statisticsGroups",
        "whether to group entities with a StatisticsGroup tag together",
    )
    cmdParser.addOption(statisticsGroupOpt)

    ignoreSTBOpt = QCommandLineOption(
        "ignoreSTB",
        "whether to ignore stb room files, only loading xml",
    )
    cmdParser.addOption(ignoreSTBOpt)

    ignoreXMLOpt = QCommandLineOption(
        "ignoreXML",
        "whether to ignore xml room files, only loading stb",
    )
    cmdParser.addOption(ignoreXMLOpt)

    disableModsOpt = QCommandLineOption(
        "disableMods",
        "whether to disable modded entities",
    )
    cmdParser.addOption(disableModsOpt)

    printGroupEntitiesOpt = QCommandLineOption(
        "printGroupEntities",
        "whether to print a list of all entities and their appear count for each group",
    )
    cmdParser.addOption(printGroupEntitiesOpt)

    groupFilesOpt = QCommandLineOption(
        "groupFiles",
        "whether to group files together, using every other file as the group name for the previous",
    )
    cmdParser.addOption(groupFilesOpt)

    cmdParser.process(app)

    positionals = cmdParser.positionalArguments()
    if not positionals:
        print("Must specify at least one room file to read!")
        return

    outputFileArg = cmdParser.value(outputFileOpt)
    outputFilePath = Path(outputFileArg).absolute().resolve()
    if outputFileArg and outputFilePath.suffix != ".txt":
        print("Output file must be txt!")
        return

    errorOutputFileArg = cmdParser.value(errorOutputFileOpt)
    errorOutputFilePath = Path(errorOutputFileArg).absolute().resolve()
    if errorOutputFileArg and errorOutputFilePath.suffix != ".txt":
        print("Error output file must be txt!")
        return

    roomThresholdArg = cmdParser.value(roomThresholdOpt)
    roomThreshold = None
    if roomThresholdArg:
        try:
            roomThreshold = int(roomThresholdArg)
        except ValueError:
            print("Room threshold must be an integer value!")
            return

    weightThresholdArg = cmdParser.value(weightThresholdOpt)
    weightThreshold = None
    if weightThresholdArg:
        try:
            weightThreshold = float(weightThresholdArg)
        except ValueError:
            print("Weight threshold must be a decimal value!")
            return

    difficultyThresholdArg = cmdParser.value(difficultyThresholdOpt)
    difficultyThreshold = None
    if difficultyThresholdArg:
        try:
            difficultyThreshold = int(difficultyThresholdArg)
        except ValueError:
            print("Difficulty threshold must be an integer value!")
            return

    groupRoomThresholdArg = cmdParser.value(groupRoomThresholdOpt)
    groupRoomThreshold = 1
    if groupRoomThresholdArg:
        try:
            groupRoomThreshold = int(groupRoomThresholdArg)
        except ValueError:
            print("Group room threshold must be an integer value!")
            return

    statisticsGroupArg = cmdParser.isSet(statisticsGroupOpt)
    ignoreSTBArg = cmdParser.isSet(ignoreSTBOpt)
    ignoreXMLArg = cmdParser.isSet(ignoreXMLOpt)
    disableModsArg = cmdParser.isSet(disableModsOpt)
    printGroupEntitiesArg = cmdParser.isSet(printGroupEntitiesOpt)
    groupFilesArg = cmdParser.isSet(groupFilesOpt)

    fileGroups = {}
    fileToGroup = {}
    lastFilesList = None
    for arg in positionals:
        if not groupFilesArg:
            filesList = recurseGetFiles(Path(arg), ignoreSTBArg, ignoreXMLArg)
            for file in filesList:
                fileGroups[file] = [file]
                fileToGroup[file] = file
        else:
            if lastFilesList:
                for file in lastFilesList:
                    fileToGroup[file] = arg

                if arg in fileGroups:
                    fileGroups[arg].extend(lastFilesList)
                else:
                    fileGroups[arg] = lastFilesList

                lastFilesList = None
            else:
                lastFilesList = recurseGetFiles(Path(arg), ignoreSTBArg, ignoreXMLArg)

    if lastFilesList:
        print("Groups and file names do not line up!")
        return

    version = getGameVersion()
    xmlLookups = MainLookup(version, settings.value("Verbose") == "1")
    if not disableModsArg:
        xmlLookups.loadMods(listModFolders(findInstallPath(), False), False)

    roomCountHeader = "Room Count:\n\n"
    roomCount = ""
    entityStats = "Entity Statistics:\n\n"
    roomErrors = ""

    entityConfigToDat = {}

    totalRoomCount, totalEntityCount = 0, 0

    groupNames = []

    for group in fileGroups:
        print("----")
        print("Group:", group)
        filesList = fileGroups[group]

        groupCount = 0
        groupEntityCount = 0
        for file in filesList:
            print("Path:", file)

            path = Path(file)

            if not path.exists():
                print("Does not exist! Skipping!")
                continue
            if path.suffix != ".xml" and path.suffix != ".stb":
                print("Must be xml or stb! Skipping!")
                continue
            elif (path.suffix == ".xml" and ignoreXMLArg) or (
                path.suffix == ".stb" and ignoreSTBArg
            ):
                printf(f"Ignoring {path.suffix} file!")
                continue

            print("Reading file...")

            roomFile = None
            if path.suffix == ".xml":
                roomFile = cvt.xmlToCommon(path)
            else:
                roomFile = cvt.stbToCommon(path)

            print("Getting entity statistics")
            (
                entityConfigToDat,
                numEntitiesInRooms,
                errors,
                roomsMatched,
            ) = getRoomEntityStats(
                roomFile.rooms,
                path,
                group,
                entityConfigToDat,
                xmlLookups,
                statisticsGroupArg,
                weightThreshold,
                difficultyThreshold,
            )
            groupCount += roomsMatched
            groupEntityCount += numEntitiesInRooms
            roomErrors += errors

        totalRoomCount += groupCount
        totalEntityCount += groupEntityCount

        roomCount += (
            f"{group}: {groupCount} rooms, containing {groupEntityCount} entities\n"
        )

        if groupEntityCount > 1:
            groupNames.append(group)

    print("----")
    print("All done! Preparing readout..")

    roomCountHeader += f"Read {totalRoomCount} total rooms, containing {totalEntityCount} total entities, from {len(fileGroups)} groups.\n\n"
    roomCount = roomCountHeader + roomCount

    groupOut = {}
    entityOut = {}
    for config in entityConfigToDat.keys():
        dat = entityConfigToDat[config]

        name = None
        if isinstance(config, EntityLookup.TagConfig):
            name = config.label or config.tag
        else:
            name = config.name

        totalRooms = dat["totalrooms"]

        if totalRooms == 0:
            if roomThreshold is None or roomThreshold == 0:
                entityText = f"-- {name}\n0 total rooms!\n\n"
                entityOut[entityText] = 0

            continue

        if roomThreshold is None or totalRooms >= roomThreshold:
            most, mostName = None, None
            least, leastName = None, None
            foundin = ""
            for groupname in dat["totalroomspergroup"]:
                groupcount = dat["totalroomspergroup"][groupname]
                if groupcount != 0:
                    if groupcount >= groupRoomThreshold:
                        if groupname not in groupOut:
                            groupOut[groupname] = {}

                        groupOut[groupname][name] = groupcount

                    foundin += f", {groupname}"
                    if not most or groupcount > most:
                        most = groupcount
                        mostName = groupname
                    if not least or groupcount < least:
                        least = groupcount
                        leastName = groupname

            mostPercent = most / totalRooms
            leastPercent = least / totalRooms

            entityText = f"-- {name}\n"

            if totalRooms == 1:
                entityText += f"{totalRooms} total room"
            else:
                entityText += f"{totalRooms} total rooms"

            totalEntities = dat["totalentities"]
            if totalEntities == 1:
                entityText += f", in which it appears {totalEntities} time"
            else:
                entityText += f", in which it appears {totalEntities} times"

            entityText += f" ({foundin[2:]})\n"

            if mostPercent != 1:
                entityText += f'Most in {mostName}, appearing in {most} rooms ({"{:.0%}".format(mostPercent)} of all rooms are in {mostName})\n'
                entityText += f'Least in {leastName}, appearing in {least} rooms ({"{:.0%}".format(leastPercent)} of all rooms are in {leastName})\n\n'
            else:
                entityText += "\n"

            entityOut[entityText] = totalRooms

    entityOut = {k: v for k, v in sorted(entityOut.items(), key=lambda x: x[1])}
    entityOut = list(entityOut.keys())
    entityOut.reverse()
    entityStats += "".join(entityOut)

    print("----")

    groupStats = ""
    if printGroupEntitiesArg:
        groupStats = "Groups\n\n"
        for name in groupNames:
            groupStats += f"-- {name}\n\n"
            groupEntities = groupOut[name]
            groupEntities = {
                k: v for k, v in sorted(groupEntities.items(), key=lambda x: x[1])
            }
            groupEntities = list(groupEntities.keys())
            groupEntities.reverse()
            for entity in groupEntities:
                groupStats += f"{entity} ({groupOut[name][entity]} appearance{'s' if groupOut[name][entity] != 1 else ''})\n"

            groupStats += "\n"

        groupStats += "\n----\n\n"

    out = f"{roomCount}\n----\n\n{groupStats}{entityStats}"

    if outputFileArg:
        with open(outputFilePath, "w") as file:
            file.write("".join(out))
    else:
        print(out)

    if errorOutputFileArg:
        with open(errorOutputFilePath, "w") as file:
            file.write(roomErrors)


if __name__ == "__main__":
    runmain()
