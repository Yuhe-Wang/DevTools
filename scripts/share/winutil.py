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
    keyHandle = winreg.CreateKeyEx(HKey, subKey, 0, access=winreg.KEY_ALL_ACCESS | view)
    if value is not None:
        if valueName == '@':
            valueName = ''
        if valueType is None:  # Deduct the value type automatically
            if isinstance(value, str):
                valueType = winreg.REG_SZ
            elif isinstance(value, int):
                valueType = winreg.REG_DWORD
            elif isinstance(value, bytes) or isinstance(value, bytearray):
                valueType = winreg.REG_BINARY
        winreg.SetValueEx(keyHandle, valueName, 0, valueType, value)


def regQuery(key, valueName='', view=winreg.KEY_WOW64_64KEY):
    '''
    return value, valueType
    '''
    HKey, subKey = splitRegKey(key)
    keyHandle = winreg.OpenKeyEx(HKey, subKey, 0, access=winreg.KEY_READ | view)
    return winreg.QueryValueEx(keyHandle, valueName)


def installFont(fontPath):
    # Don't copy if it has been installed
    copyPath(fontPath, Path(os.environ["WINDIR"])/"Fonts", overwrite=False)
    regAdd(r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts", fontPath.name, "%s (TrueType)" % fontPath.stem)
