
import winreg
import os
from pathlib import Path

from scripts.share.util import gs
from scripts.share.util import regQuery
from scripts.share.util import regAdd
from scripts.share.util import installFont
from scripts.share.util import call
from scripts.share.util import calls
from scripts.share.util import printf


def setupPython():
    folder = "python-3.8.5"
    printf("Setup %s..." % folder)
    pathList = [str(gs.GitDir/"app"/folder)]
    # Scan the userPath
    for p in regQuery(r"HKCU\Environment", "Path")[0].split(';'):
        pStrip = p.strip()
        if pStrip:
            pathList.append(pStrip)
            testPath = Path(pStrip)/"python.exe"
            if testPath.is_file():
                ret = call([str(testPath), "--version"])
                if ret[2] == 0 and ret[0].split()[1].startswith("3."):
                    return
    # Scan the local machine path
    for p in regQuery(r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment", "Path")[0].split(';'):
        pStrip = p.strip()
        if pStrip:
            testPath = Path(pStrip)/"python.exe"
            if testPath.is_file():
                ret = call([str(testPath), "--version"])
                if ret[2] == 0 and ret[0].split()[1].startswith("3."):
                    return
    # Cannot find python 3. Add python 3 in this repo to user path
    regAdd(r"HKCU\Environment", ";".join(pathList), "Path")


def setupFont():
    for p in (gs.GitDir/"fonts").iterdir():
        if p.suffix.lower() == ".ttf":
            printf("Installing font %s" % p.name)
            installFont(p)


def setup7z():
    # Setup file extension with 7z
    folder = "7z-19.00"
    printf("Setup %s..." % folder)
    clsid = "23170F69-40C1-278A-1000-000100020000"  # The clsid may be changed with the version
    iconDict = {
        "001": 9,
        "7z": 0,
        "arj": 4,
        "bz2": 2,
        "bzip2": 2,
        "cpio": 12,
        "deb": 11,
        "dmg": 17,
        "fat": 21,
        "gz": 14,
        "gzip": 14,
        "hfs": 18,
        "lha": 6,
        "lzh": 6,
        "lzma": 16,
        "ntfs": 22,
        "rar": 3,
        "rpm": 10,
        "squashfs": 24,
        "swm": 15,
        "tar": 13,
        "taz": 5,
        "tbz": 2,
        "tbz2": 2,
        "tgz": 14,
        "tpz": 14,
        "txz": 23,
        "wim": 15,
        "xar": 19,
        "xz": 23,
        "z": 5,
        "zip": 1
    }

    appDir = gs.GitDir/"app"/folder
    for ext in iconDict:
        winreg.SetValue(winreg.HKEY_CLASSES_ROOT, ".%s" % ext, winreg.REG_SZ, "7-Zip.%s" % ext)
        iconIdx = iconDict[ext]
        regAdd(r"HKCR\7-Zip.%s\DefaultIcon" % ext, "%s,%d" % (str(appDir/"7z.dll"), iconIdx))
        regAdd(r"HKCR\7-Zip.%s\shell\open\command" % ext, '"%s" "%%1"' % str(appDir/"7zFM.exe"))

    # Setup the context menu
    regAdd(r"HKCR\CLSID\{%s}" % clsid, "7-Zip Shell Extension")
    regAdd(r"HKCR\CLSID\{%s}\InprocServer32" % clsid, str(appDir/"7-zip.dll"))
    regAdd(r"HKCR\CLSID\{%s}\InprocServer32" % clsid, "Apartment", "ThreadingModel")
    regAdd(r"HKCR\*\shellex\ContextMenuHandlers\7-Zip", "{%s}" % clsid)
    regAdd(r"HKCR\Folder\shellex\ContextMenuHandlers\7-Zip", "{%s}" % clsid)
    regAdd(r"HKCR\Directory\shellex\ContextMenuHandlers\7-Zip", "{%s}" % clsid)
    regAdd(r"HKCR\Directory\shellex\DragDropHandlers\7-Zip", "{%s}" % clsid)
    regAdd(r"HKCR\Drive\shellex\DragDropHandlers\7-Zip", "{%s}" % clsid)
    regAdd(r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Shell Extensions\Approved")

    '''
    HKCR\.lzma => 7-Zip.lzma
    HKCR\7-Zip.lzma
    HKCR\7-Zip.lzma\DefaultIcon => E:\Tools\app\7z-19.00\7z.dll,16
    HKCR\7-Zip.lzma\shell\open\command => "E:\Tools\app\7z-19.00\7zFM.exe" "%1"

    [HKEY_CLASSES_ROOT\CLSID\{23170F69-40C1-278A-1000-000100020000}]
    @="7-Zip Shell Extension"

    [HKEY_CLASSES_ROOT\CLSID\{23170F69-40C1-278A-1000-000100020000}\InprocServer32]
    @="E:\\Tools\\app\\7z-19.00\\7-zip.dll"
    "ThreadingModel"="Apartment"

    [HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Shell Extensions\Approved]
    "{23170F69-40C1-278A-1000-000100020000}"="7-Zip Shell Extension"

    [HKEY_CLASSES_ROOT\*\shellex\ContextMenuHandlers\7-Zip]
    @="{23170F69-40C1-278A-1000-000100020000}"

    [HKEY_CLASSES_ROOT\Folder\shellex\ContextMenuHandlers\7-Zip]
    @="{23170F69-40C1-278A-1000-000100020000}"

    [HKEY_CLASSES_ROOT\Directory\shellex\ContextMenuHandlers\7-Zip]
    @="{23170F69-40C1-278A-1000-000100020000}"

    [HKEY_CLASSES_ROOT\Directory\shellex\DragDropHandlers\7-Zip]
    @="{23170F69-40C1-278A-1000-000100020000}"

    [HKEY_CLASSES_ROOT\Drive\shellex\DragDropHandlers\7-Zip]
    @="{23170F69-40C1-278A-1000-000100020000}"

    [HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\FileExts\OpenWithList]
    '''


def main(argv):
    if not argv:
        printf("Please specifiy the setup target or use all instead")
        return 1
    if argv[0] == "all":
        argv[0] = "7z,python,font"
    setupList = argv[0].split(',')
    printf("Running setup...")

    if "python" in setupList:
        setupPython()
    if "7z" in setupList:
        setup7z()
    if "font" in setupList:
        setupFont()
    printf("Setup done!")
    return 0
