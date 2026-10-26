import os
import math
from typing import Any, NamedTuple


class vec2[T](NamedTuple):
    x: T
    y: T


def printf(*args):
    print(*args, flush=True)


def printSectionBreak():
    printf("-".join(["" for i in range(50)]))


def bitFill(count: int) -> int:
    return (1 << count) - 1


def bitGet(bits: int, startBit: int, count: int) -> int:
    bits = bits >> startBit
    bits &= bitFill(count)
    return bits


def bitSet(bits: int, sourceBits: int, startBit: int, count: int) -> int:
    sourceBits = bitGet(sourceBits, 0, count) << startBit
    bits &= ~(bitFill(count) << startBit)
    return bits | sourceBits


def linuxPathSensitivityTraining(path: str) -> str | None:
    path = path.replace("\\", "/")

    directory, file = os.path.split(os.path.normpath(path))

    if not os.path.isdir(directory):
        if os.path.isdir(directory.lower()):
            directory = directory.lower()
        else:
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


def checkFloat(s: Any) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def checkInt(s: Any) -> bool:
    if checkFloat(s):
        return int(s) == float(s)

    return False


def vectorFromAngle(angle: float) -> tuple[float, float]:
    radians = angle * (math.pi / 180)
    return math.cos(radians), math.sin(radians)


def angleFromVector(x: float, y: float) -> float:
    return math.atan2(y, x) * (180 / math.pi)
