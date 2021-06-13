import os


def printf(*args):
    print(*args, flush=True)


def bitGet(bits, bitStart, bitCount):
    value = 0
    for i in range(bitCount):
        bit = 1 << (bitStart + i)
        if bits & bit:
            value |= 1 << i

    return value


def bitSet(bits, value, bitStart, bitCount):
    for i in range(bitCount):
        bit = 1 << i
        if value & bit:
            bits |= 1 << (bitStart + i)
        else:
            bits &= ~(1 << (bitStart + i))

    return bits


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
