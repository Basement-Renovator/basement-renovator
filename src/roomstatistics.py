"""
Generates a readout of various room file and entity usage statistics
"""
from pathlib import Path

import os
import sys
import inspect

import roomconvert as cvt
import xml.etree.cElementTree as ET

from PyQt5.QtCore import QCommandLineOption, QCommandLineParser, QSettings
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
):
    totalEntities = 0
    errors = ""
    for currRoom in rooms:
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

    return entityConfigToDat, totalEntities, errors


def recurseGetFiles(path):
    filesList = []
    if path.is_dir():
        for path2 in path.iterdir():
            filesList.extend(recurseGetFiles(path2))
    elif path.suffix == ".xml":
        filesList.append(path)

    return filesList


def runmain():
    app = QApplication(sys.argv)

    cmdParser = QCommandLineParser()
    cmdParser.setApplicationDescription(
        "Room file & entity usage statistics utility script for Basement Renovator. Takes a set of file paths."
    )
    cmdParser.addHelpOption()

    cmdParser.addPositionalArgument("file", "xml room files to read")

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

    statisticsGroupOpt = QCommandLineOption(
        "statisticsGroups",
        "whether to group entities with a StatisticsGroup tag together",
    )
    cmdParser.addOption(statisticsGroupOpt)

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

    statisticsGroupArg = cmdParser.isSet(statisticsGroupOpt)
    groupFilesArg = cmdParser.isSet(groupFilesOpt)

    fileGroups = {}
    fileToGroup = {}
    lastFilesList = None
    for arg in positionals:
        if not groupFilesArg:
            filesList = recurseGetFiles(Path(arg))
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
                lastFilesList = recurseGetFiles(Path(arg))

    if lastFilesList:
        print("Groups and file names do not line up!")
        return

    version = getGameVersion()
    xmlLookups = MainLookup(version, settings.value("Verbose") == "1")
    if settings.value("DisableMods") != "1":
        xmlLookups.loadMods(listModFolders(findInstallPath(), False), False)

    roomCountHeader = "Room Count:\n\n"
    roomCount = ""
    entityStats = "Entity Statistics:\n\n"
    roomErrors = ""

    entityConfigToDat = {}

    totalRoomCount, totalEntityCount = 0, 0

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
            if path.suffix != ".xml":
                print("Must be xml! Skipping!")
                continue

            print("Reading file...")

            roomFile = cvt.xmlToCommon(path)
            groupCount += len(roomFile.rooms)

            print("Getting entity statistics")
            entityConfigToDat, numEntitiesInRooms, errors = getRoomEntityStats(
                roomFile.rooms,
                path,
                group,
                entityConfigToDat,
                xmlLookups,
                statisticsGroupArg,
            )
            groupEntityCount += numEntitiesInRooms
            roomErrors += errors

        totalRoomCount += groupCount
        totalEntityCount += groupEntityCount

        roomCount += (
            f"{group}: {groupCount} rooms, containing {groupEntityCount} entities\n"
        )

    print("----")
    print("All done! Preparing readout..")

    roomCountHeader += f"Read {totalRoomCount} total rooms, containing {totalEntityCount} total entities, from {len(fileGroups)} groups.\n\n"
    roomCount = roomCountHeader + roomCount

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
                entityText += f'Most in {mostName}, appearing in {most} rooms ({"{:.0%}".format(mostPercent)} of all rooms on the floor)\n'
                entityText += f'Least in {leastName}, appearing in {least} rooms ({"{:.0%}".format(leastPercent)} of all rooms on the floor)\n\n'
            else:
                entityText += "\n"

            entityOut[entityText] = totalRooms

    entityOut = {k: v for k, v in sorted(entityOut.items(), key=lambda x: x[1])}
    entityOut = list(entityOut.keys())
    entityOut.reverse()
    entityStats += "".join(entityOut)

    print("----")

    out = f"{roomCount}\n----\n\n{entityStats}"

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
