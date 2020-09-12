
import winreg
from pathlib import Path

from scripts.share.util import gs
from scripts.share.util import call
from scripts.share.util import printf

from scripts.share.winutil import regQuery
from scripts.share.winutil import regAdd
from scripts.share.winutil import installFont


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
    regAdd(r"HKCU\Environment", "Path", ";".join(pathList))


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
        regAdd(r"HKCR\7-Zip.%s\DefaultIcon" % ext, '@', "%s,%d" % (str(appDir/"7z.dll"), iconIdx))
        regAdd(r"HKCR\7-Zip.%s\shell\open\command" % ext, '@', '"%s" "%%1"' % str(appDir/"7zFM.exe"))

    # Setup the context menu
    regAdd(r"HKCR\CLSID\{%s}" % clsid, '@', "7-Zip Shell Extension")
    regAdd(r"HKCR\CLSID\{%s}\InprocServer32" % clsid, '@', str(appDir/"7-zip.dll"))
    regAdd(r"HKCR\CLSID\{%s}\InprocServer32" % clsid, "ThreadingModel", "Apartment")
    regAdd(r"HKCR\*\shellex\ContextMenuHandlers\7-Zip", '@', "{%s}" % clsid)
    regAdd(r"HKCR\Folder\shellex\ContextMenuHandlers\7-Zip", '@', "{%s}" % clsid)
    regAdd(r"HKCR\Directory\shellex\ContextMenuHandlers\7-Zip", '@', "{%s}" % clsid)
    regAdd(r"HKCR\Directory\shellex\DragDropHandlers\7-Zip", '@', "{%s}" % clsid)
    regAdd(r"HKCR\Drive\shellex\DragDropHandlers\7-Zip", '@', "{%s}" % clsid)
    regAdd(r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Shell Extensions\Approved")


def setupNpp():
    folder = "notepad++-7.8.9"
    printf("Setup %s" % folder)
    appDir = gs.GitDir/"app"/folder
    clsid = "B298D29A-A6ED-11DE-BA8C-A68E55D89593"
    regAdd(r"HKCR\CLSID\{%s}" % clsid, '@', "ANotepad++64")
    regAdd(r"HKCR\CLSID\{%s}\InprocServer32" % clsid, '@', str(appDir/"NppShell_06.dll"))
    regAdd(r"HKCR\CLSID\{%s}\InprocServer32" % clsid, "ThreadingModel", "Apartment")
    regAdd(r"HKCR\CLSID\{%s}\Settings" % clsid, "Title", "Edit with &Notepad++")
    regAdd(r"HKCR\CLSID\{%s}\Settings" % clsid, "Path", str(appDir/"notepad++.exe"))
    regAdd(r"HKCR\CLSID\{%s}\Settings" % clsid, "Custom", "")
    regAdd(r"HKCR\CLSID\{%s}\Settings" % clsid, "ShowIcon", 1, winreg.REG_DWORD)
    regAdd(r"HKCR\CLSID\{%s}\Settings" % clsid, "Dynamic",  1, winreg.REG_DWORD)
    regAdd(r"HKCR\CLSID\{%s}\Settings" % clsid, "Maxtext",  0x19, winreg.REG_DWORD)
    regAdd(r"HKCR\*\shellex\ContextMenuHandlers\ANotepad++64", '@', "{%s}" % clsid)


def main(argv):
    if not argv:
        printf("Please specifiy the setup target or use all instead")
        return 1
    if argv[0] == "all":
        argv[0] = "7z,python,notepad++,font"
    setupList = argv[0].split(',')
    printf("Running setup...")

    if "python" in setupList:
        setupPython()
    if "7z" in setupList:
        setup7z()
    if "font" in setupList:
        setupFont()
    if "notepad++" in setupList:
        setupNpp()
    printf("Setup done!")
    return 0
