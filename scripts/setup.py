
import winreg
from pathlib import Path

from scripts.share.util import gs
from scripts.share.util import printf


def setup7z():
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
    
    # Setup file extension with 7z
    folder = "7z-19.00"
    printf("Setup %s..." % folder)
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
        winreg.SetValue(winreg.HKEY_CLASSES_ROOT,
                        r"7-Zip.%s\DefaultIcon" % ext,
                        winreg.REG_SZ,
                        str(appDir/"7z.dll") + ",%d" % iconIdx)
        winreg.SetValue(winreg.HKEY_CLASSES_ROOT,
                        r"7-Zip.%s\shell\open\command" % ext,
                        winreg.REG_SZ,
                        '"%s" "%%1"' % str(appDir/"7zFM.exe"))

    # Setup the context menu
    clsid = "23170F69-40C1-278A-1000-000100020000"
    winreg.SetValue(winreg.HKEY_CLASSES_ROOT,
                    r"CLSID\{%s}" % clsid,
                    winreg.REG_SZ,
                    "7-Zip Shell Extension")
    key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT,
                          r"CLSID\{%s}\InprocServer32" % clsid)
    winreg.SetValue(winreg.HKEY_CLASSES_ROOT,
                    r"CLSID\{%s}\InprocServer32" % clsid,
                    winreg.REG_SZ,
                    str(appDir/"7-zip.dll"))
    winreg.SetValueEx(key, "ThreadingModel", 0, winreg.REG_SZ, "Apartment")
    key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE,
                           r"SOFTWARE\Microsoft\Windows\CurrentVersion\Shell Extensions\Approved")
    winreg.SetValue(winreg.HKEY_CLASSES_ROOT,
                    r"shellex\ContextMenuHandlers\7-Zip",
                    winreg.REG_SZ,
                    "{%s}" % clsid)
    winreg.SetValue(winreg.HKEY_CLASSES_ROOT,
                    r"Folder\shellex\ContextMenuHandlers\7-Zip",
                    winreg.REG_SZ,
                    "{%s}" % clsid)
    winreg.SetValue(winreg.HKEY_CLASSES_ROOT,
                    r"Directory\shellex\ContextMenuHandlers\7-Zip",
                    winreg.REG_SZ,
                    "{%s}" % clsid)
    winreg.SetValue(winreg.HKEY_CLASSES_ROOT,
                    r"Directory\shellex\DragDropHandlers\7-Zip",
                    winreg.REG_SZ,
                    "{%s}" % clsid)
    winreg.SetValue(winreg.HKEY_CLASSES_ROOT,
                    r"Drive\shellex\DragDropHandlers\7-Zip",
                    winreg.REG_SZ,
                    "{%s}" % clsid)


def main(argv):
    if not argv:
        printf("Please specifiy the setup target or use all instead")
        return 1
    if argv[0] == "all":
        argv[0] = "7z"
    setupList = argv[0].split(',')
    printf("Running setup...")

    if "7z" in setupList:
        setup7z()
    printf("Setup done!")
    return 0
