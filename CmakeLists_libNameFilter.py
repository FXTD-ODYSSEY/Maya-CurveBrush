# coding=utf-8

import sys, os

class CmakeMayaBuildPath (object):

    locMayaDir = r""

    @classmethod
    def listAllQtLib (cls):
        # type: (...) -> list[str]
        if os.path.exists(cls.locMayaDir):
            locQtLibDir = os.path.join(cls.locMayaDir, "lib")
            return [os.path.splitext(fileName)[0] for fileName in cls.generateLibFileName(locQtLibDir) if fileName.startswith("Qt")]

    @classmethod
    def generateLibFileName (cls, dirPath):
        for fileName in os.listdir(dirPath):
            tempFilePath = os.path.join(dirPath, fileName)
            if (not os.path.isdir(tempFilePath)) and (fileName.lower().endswith("lib")):
                yield fileName


if __name__ == "__main__":
    CmakeMayaBuildPath.locMayaDir = r"C:\Program Files\Autodesk\Maya2022"
    print(" ".join(CmakeMayaBuildPath.listAllQtLib()))