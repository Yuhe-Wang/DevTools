import os
import winreg
import ctypes
from pathlib import Path

import win32con
import win32event
import win32process
import win32net
from win32com.shell.shell import ShellExecuteEx
from win32com.shell import shellcon

from scripts.share.util import cmdToStr
from scripts.share.util import copyPath


def isUserAdmin():
    groups = win32net.NetUserGetLocalGroups(os.environ["logonserver"], os.getlogin())
    isadmin = False
    for group in groups:
        if group.lower().startswith("admin"):
            isadmin = True
            break
    return isadmin


def isAdminProcess():
    return ctypes.windll.shell32.IsUserAnAdmin()


def runAsAdmin(cmd, wait=True, show=False):
    if not isUserAdmin():
        return 1  # Cannot run as admin
    if isinstance(cmd, str):
        splits = cmd.split()
        exeFile = splits[0]
        params = ' '.join(splits[1:])
    else:
        exeFile = cmd[0]
        params = cmdToStr(cmd[1:])

    if show:
        showWindow = win32con.SW_SHOW
    else:
        showWindow = win32con.SW_HIDE
    procInfo = ShellExecuteEx(nShow=showWindow,
                              fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                              lpVerb="runas",
                              lpFile=exeFile,
                              lpParameters=params)

    rc = 0
    if wait:
        procHandle = procInfo['hProcess']
        win32event.WaitForSingleObject(procHandle, win32event.INFINITE)
        rc = win32process.GetExitCodeProcess(procHandle)

    return rc


HKeyDict = {
    "HKCR": winreg.HKEY_CLASSES_ROOT,
    "HKCU": winreg.HKEY_CURRENT_USER,
    "HKLM": winreg.HKEY_LOCAL_MACHINE,
    "HKU": winreg.HKEY_USERS,
    "HKCC": winreg.HKEY_CURRENT_CONFIG,

    "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
    "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
    "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
    "HKEY_USERS": winreg.HKEY_USERS,
    "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG
}


def splitRegKey(key):
    idx = key.find("\\")
    if idx != -1:
        HKey = HKeyDict[key[0:idx]]
        subKey = key[idx + 1:]
    else:
        HKey = HKeyDict[key]
        subKey = ''
    return HKey, subKey


def regAdd(key, valueName='@', value=None, valueType=None, view=winreg.KEY_WOW64_64KEY):
    HKey, subKey = splitRegKey(key)
    changed = False
    try:
        keyHandle = winreg.OpenKeyEx(HKey, subKey, 0, access=winreg.KEY_ALL_ACCESS | view)
    except OSError:
        keyHandle = winreg.CreateKeyEx(HKey, subKey, 0, access=winreg.KEY_ALL_ACCESS | view)
        changed = True

    if value is not None:  # Need to write a value
        if valueType is None:  # Deduct the value type automatically
            if isinstance(value, str):
                valueType = winreg.REG_SZ
            elif isinstance(value, int):
                valueType = winreg.REG_DWORD
            elif isinstance(value, list):
                valueType = winreg.REG_MULTI_SZ
            elif isinstance(value, (bytes, bytearray)):
                valueType = winreg.REG_BINARY
        if valueName == '@':
            valueName = ''
        if not changed:
            try:
                oldValue, oldValueType = winreg.QueryValueEx(keyHandle, valueName)
                if value != oldValue or valueType != oldValueType:
                    changed = True
            except OSError:
                changed = True
        if changed:
            winreg.SetValueEx(keyHandle, valueName, 0, valueType, value)
    keyHandle.Close()
    return changed


def regAddList(key, valueList, view=winreg.KEY_WOW64_64KEY):
    changed = False
    for entry in valueList:
        valueName = entry[0]
        value = entry[1]
        valueType = None
        if len(entry) >= 3:
            valueType = entry[2]
        if regAdd(key, valueName, value, valueType, view):
            changed = True
    return changed


def regQuery(key, valueName='@', view=winreg.KEY_WOW64_64KEY):
    value = None
    valueType = None
    HKey, subKey = splitRegKey(key)
    with winreg.OpenKeyEx(HKey, subKey, 0, access=winreg.KEY_READ | view) as keyHandle:
        if valueName == '@':
            valueName = ''
        value, valueType = winreg.QueryValueEx(keyHandle, valueName)
    return (value, valueType)


def deleteRegKeyRecursively(HKey, subKey, view=winreg.KEY_WOW64_64KEY):
    # Delete all the sub keys first
    keyExist = False
    with winreg.OpenKeyEx(HKey, subKey, 0, access=winreg.KEY_ALL_ACCESS | view) as keyHandle:
        keyExist = True
        index = 0
        while True:
            try:
                subKeyName = winreg.EnumKey(keyHandle, index)
                deleteRegKeyRecursively(HKey, subKey + '\\' + subKeyName)
            except OSError:
                break
            index += 1
    # Then delete this key
    if keyExist:
        if view == winreg.KEY_WOW64_64KEY:
            winreg.DeleteKeyEx(HKey, subKey, access=view, reserved=0)
        else:
            winreg.DeleteKey(HKey, subKey)


def regDelete(key, valueName=None, view=winreg.KEY_WOW64_64KEY):
    HKey, subKey = splitRegKey(key)
    if valueName is None:
        deleteRegKeyRecursively(HKey, subKey, view)
    else:  # Only delete one value
        if valueName == '@':
            valueName = ''  # Delete the default value
        with winreg.OpenKeyEx(HKey, subKey, 0, access=winreg.KEY_ALL_ACCESS | view) as keyHandle:
            try:
                winreg.DeleteValue(keyHandle, valueName)
            except OSError:
                pass


def installFont(fontPath):
    # Don't copy if it has been installed
    copyPath(fontPath, Path(os.environ["WINDIR"])/"Fonts", overwrite=False)
    regAdd(r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts", fontPath.name, "%s (TrueType)" % fontPath.stem)


def addContextMenu(entry, description, cmd, icon=None,
                   contexts=('*', "Directory\\background", "Directory", "Drive")):
    '''
    entry is the context menu item in register, i.e. cmdhere
    description is the words displayed
    icon is the icon resource path. Can be exe, dll, or icon image
    cmd is the command to execute
    contexts can be a string or string list/tuple.
    Example: addContextMenu("cmdhere", "Open CMD here (&Q)", "cmd.exe", icon="cmd.exe")
    '''
    if isinstance(contexts, str):
        contexts = [contexts]
    for context in contexts:
        regAdd(r"HKCR\%s\shell\%s" % (context, entry), '@', description)
        if icon:
            regAdd(r"HKCR\%s\shell\%s" % (context, entry), "icon", icon)
        regAdd(r"HKCR\%s\shell\%s\command" % (context, entry), '@', cmd)


def setOpenWith(ext, exe, icon=None, regKeyName=None):
    if regKeyName is None:
        regKeyName = "%sfile" % ext
    regAdd(r"HKCR\.%s" % ext, '@', regKeyName)
    if icon:
        regAdd(r"HKCR\%s\DefaultIcon" % regKeyName, '@', icon)
    regAdd(r"HKCR\%s\shell\open\command" % regKeyName, '@', '"%s" "%%1"' % exe)
