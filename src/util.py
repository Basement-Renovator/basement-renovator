import math
import os
from pathlib import Path
from typing import Any, NamedTuple

# BR's modules and data files are all relative to the repo root
BR_ROOT = Path(__file__).resolve().parent.parent


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
