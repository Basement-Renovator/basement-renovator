import os


def printf(*args):
    print(*args, flush=True)


def bitFill(count):
    return (1 << count) - 1


def bitGet(bits, startBit, count):
    bits = bits >> startBit
    bits &= bitFill(count)
    return bits


def bitSet(bits, sourceBits, startBit, count):
    sourceBits = bitGet(sourceBits, 0, count) << startBit
    bits &= ~(bitFill(count) << startBit)
    return bits | sourceBits


def linuxPathSensitivityTraining(path):

    path = path.replace("\\", "/")

    directory, file = os.path.split(os.path.normpath(path))

    if not os.path.isdir(directory):
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


def checkNum(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
