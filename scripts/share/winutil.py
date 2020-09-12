import os
import traceback
import winreg
from ctypes import windll
from pathlib import Path

import win32con
import win32event
import win32process
from win32com.shell.shell import ShellExecuteEx
from win32com.shell import shellcon

from util import cmdToStr
from util import copyPath


def isUserAdmin():
    try:
        # WARNING: requires Windows XP SP2 or higher!
        return windll.shell32.IsUserAnAdmin()
    except Exception:
        traceback.print_exc()
        print("Admin check failed, assuming not an admin.")
        return False


def runAsAdmin(cmd, wait=True):
    if isinstance(cmd, str):
        splits = cmd.split()
        exeFile = splits[0]
        params = ' '.join(splits[1:])
    else:
        exeFile = cmd[0]
        params = cmdToStr(cmd[1:])

    procInfo = ShellExecuteEx(nShow=win32con.SW_HIDE,
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


def splitRegKey(key):
    HKeyDict = {
        "HKCR": winreg.HKEY_CLASSES_ROOT,
        "HKCU": winreg.HKEY_CURRENT_USER,
        "HKLM": winreg.HKEY_LOCAL_MACHINE,
        "HKU": winreg.HKEY_USERS,
        "HKCC": winreg.HKEY_CURRENT_CONFIG
    }
    idx = key.find("\\")
    if idx != -1:
        HKey = HKeyDict[key[0:idx]]
        subKey = key[idx + 1:]
    else:
        HKey = HKeyDict[key]
        subKey = ''
    return HKey, subKey


def regAdd(key, value=None, valueName='', valueType=winreg.REG_SZ, view=winreg.KEY_WOW64_64KEY):
    HKey, subKey = splitRegKey(key)
    keyHandle = winreg.CreateKeyEx(HKey, subKey, 0, access=winreg.KEY_ALL_ACCESS | view)
    if value:
        winreg.SetValueEx(keyHandle, valueName, 0, valueType, value)


def regQuery(key, valueName='', view=winreg.KEY_WOW64_64KEY):
    '''
    return value, valueType
    '''
    HKey, subKey = splitRegKey(key)
    keyHandle = winreg.OpenKeyEx(HKey, subKey, 0, access=winreg.KEY_READ | view)
    return winreg.QueryValueEx(keyHandle, valueName)


def installFont(fontPath):
    copyPath(fontPath, Path(os.environ["WINDIR"])/"Fonts")
    regAdd(r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts", fontPath.name, "%s (TrueType)" % fontPath.stem)
