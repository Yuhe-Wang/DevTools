import os
import sys
import socket
import subprocess
import atexit
import types
import traceback
import shlex
import winreg
from ctypes import windll
from pathlib import Path


class GlobleSettings:
    def __init__(self):
        # Begin default global settings.
        self.ExeName = "go"  # The executable name of minitools exposed to users.
        self.UnstableSubProcessList = ["ssh", "git fetch"]
        self.UnstableSubProcessTimeout = 60  # Unit second
        self.UnstableSubProcessTryTimes = 10

        # COLOR emum. They're used frequently so they're put here for easy access
        self.RED = 1
        self.GREEN = 2
        self.YELLOW = 3
        self.BLUE = 4
        self.MAGENTA = 5
        self.CYAN = 6
        self.WHITE = 7

        # Init the global variables
        self.GV = AnyObject("GlobalVariables")
        self.GV.logf = None

        self.commonInit()

    def commonInit(self):
        # Convenient constants that can be calculated
        self.HostName = socket.gethostname()
        self.GitDir = Path(__file__).parent.parent.parent
        # The print may have unicode
        os.environ["PYTHONIOENCODING"] = "UTF-8"
        # Prepare windows color print function
        if os.name == "nt" and not ("TERM" in os.environ and os.environ["TERM"] == "xterm"):
            STD_OUTPUT_HANDLE = -11
            stdoutHandle = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            # Color order (same as tput): RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE
            colorList = [0x0004, 0x0002, 0x0006, 0x0001, 0x0005, 0x0003, 0x0007]
            self.SetConsoleTextAttribute = lambda colorIndex: \
                windll.kernel32.SetConsoleTextAttribute(stdoutHandle, colorList[colorIndex-1])
        else:
            self.SetConsoleTextAttribute = None
        # May need to clean up something for normal or ctrl + C exit
        atexit.register(self.exitHandler)

    def enableLog(self, prefix):
        logDir = self.MergeTempPath/"log"
        if not logDir.exists():
            logDir.mkdir()
        logFile = logDir/(prefix + '_' + dateStr("%Y_%m.log"))
        self.GV.logf = logFile.open('a', encoding="utf-8")
        self.GV.logf.write("\n\n\n\n\n\n[Start time: %s]\n" % dateStr())

    def exitHandler(self):
        if self.GV.logf:
            self.GV.logf.write("\n[End time: %s]\n" % dateStr())
            self.GV.logf.flush()  # Force to flush all content in the buffer to file
            self.GV.logf.close()


class AnyObject:
    def __init__(self, name):
        self.name = name


def cmdToStr(cmd):
    if isinstance(cmd, list):
        strList = []
        for x in cmd:
            if ' ' in x:
                strList.append('"%s"' % x)
            else:
                strList.append(x)
        return ' '.join(strList)
    else:
        return cmd


def calls(cmd, ENV=None, DIR=None, TIMEOUT=None, PRINT=False):
    cmdStr = cmdToStr(cmd)
    if PRINT:
        if cmdStr.startswith("cmd /c"):
            cmdStr = cmdStr[len("cmd /c") + 1:]
        printf(cmdStr)
    if cmdStr.startswith(tuple(gs.UnstableSubProcessList)):
        unstable = True
        if TIMEOUT is None:
            TIMEOUT = gs.UnstableSubProcessTimeout
    else:
        unstable = False
    _env = os.environ.copy()
    if ENV:
        for key in ENV:
            _env[key] = ENV[key]  # Add or override the parent environment variables
    callTimes = 0
    while callTimes < gs.UnstableSubProcessTryTimes:
        callTimes += 1
        try:
            # May fail to create the subprocess
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=_env, cwd=DIR)
            try:
                stdout, stderr = proc.communicate(timeout=TIMEOUT)
                stdout, stderr = stdout.decode("utf-8").rstrip(), stderr.decode("utf-8").rstrip()
            except Exception as e:
                proc.kill()
                proc.communicate()
                stdout = "The subprocess failed to finish normally!"
                stderr = str(e)
            if proc.returncode == 0:
                return stdout
            if not unstable:  # Only call many times for unstable subprocess
                break
        except Exception as e:
            stdout = "Failed to create subprocess"
            stderr = str(e)
            break  # Cannot launch the process, so simply break the loop

    printf("Failed to execute:\n%s" % str(cmd), color=gs.YELLOW)
    printf(stderr, color=gs.YELLOW)
    mtExit(1)


def printf(*objects, sep=' ', end='\n', file=sys.stdout, flush=False, color=None, target=None):
    if target is None:
        target = "both"
    if target in ("both", "screen"):
        if color is not None:
            if gs.SetConsoleTextAttribute:
                gs.SetConsoleTextAttribute(color)
            else:
                print("\033[3%dm" % color, end='')
        print(*objects, sep=sep, end=end, file=file, flush=flush)
        if color is not None:
            if gs.SetConsoleTextAttribute:
                gs.SetConsoleTextAttribute(gs.WHITE)
            else:
                print("\033[37m", end='')
    if target in ("both", "file"):
        if gs.GV.logf and gs.GV.logf is not file:
            print(*objects, sep=sep, end=end, file=gs.GV.logf, flush=True)


def mtExit(status):
    gs.exitHandler()
    os._exit(status)  # pylint: disable=protected-access


def mtAssert(condition):
    ''' Assertion for multithreaded program, which exits the whole process '''
    if not condition:
        printf("\nTraceback (most recent call last):")
        for line in traceback.format_stack()[0:-1]:
            printf(line, end='')
        mtExit(1)


def dateStr(fmt="%Y-%m-%d %X"):
    return datetime.datetime.today().strftime(fmt)


def getProcessCmd(name, filterFunc=None):
    '''
    The name can be full module name or stem name
    It will return the first cmd line matching filterFunc of given process
    filterFunc is a bool function takes in cmd as parameter
    '''
    for proc in psutil.process_iter():
        try:
            procName = proc.name()  # The name() method may throw exception
        except Exception:
            continue
        stemName = Path(procName).stem
        if name in (procName, stemName):
            try:
                cmd = proc.cmdline()
            except Exception:
                cmd = [name]
            if not filterFunc or filterFunc(cmd):
                return cmd
    return []  # Indicating the process is not running


def killProcess(name):
    '''
    The name can be full module name or stem name
    It will kill all processes matching the name
    '''
    for proc in psutil.process_iter():
        try:
            procName = proc.name()
        except Exception:
            continue
        stemName = Path(procName).stem
        if name in (procName, stemName):
            proc.kill()


def killProcessTree(pid, includeParent=True):
    parent = psutil.Process(pid)
    procList = parent.children(recursive=True)
    procList.reverse()  # It modifies procList itself
    if includeParent:
        procList.append(parent)
    try:
        for p in procList:
            p.kill()
        # Wait until all processes terminate
        while procList:
            _, procList = psutil.wait_procs(procList, timeout=5)
    except Exception:
        # Exception that a process may end by itself before being killed
        pass


def funcRemoveReadOnly(_action, name, _exc):
    os.chmod(name, stat.S_IWRITE)
    os.unlink(name)


def removePath(p):
    ''' Remove a file or a directory (also remove readonly file) '''
    try:
        if p.is_dir():
            shutil.rmtree(str(p), onerror=funcRemoveReadOnly)
        elif p.is_file():
            os.chmod(str(p), stat.S_IWRITE)
            p.unlink()
    except Exception as e:
        printf("Failed to delete the path\n" + str(p), color=gs.YELLOW)
        printf(e)
        exit(1)


def copyFile(src, dst):
    ''' dst can be a file or a directory '''
    if dst.is_dir():
        # Get the real dst file path
        dst = dst/src.name
    if dst.is_file():
        # The dst already exists
        if not os.stat(str(dst))[0] & stat.S_IWRITE:
            os.chmod(str(dst), stat.S_IWRITE)
    elif not dst.parent.exists():
        # Make sure the parent directory exists
        dst.parent.mkdir(parents=True)
    shutil.copyfile(str(src), str(dst))


def copyTree(src, dst):
    if dst.exists():
        assert dst.is_dir()
    for childSrc in src.rglob("*"):
        if childSrc.is_file():
            childDst = Path(str(childSrc).replace(str(src), str(dst), 1))
            copyFile(childSrc, childDst)


def copyPath(src, dst):
    ''' Copy a file or a directory (can overwrite readonly files) '''
    try:
        if src.is_dir():
            copyTree(src, dst)
        elif src.is_file():
            copyFile(src, dst)
    except Exception as e:
        printf("Failed to copy %s\n to %s\n" % (str(src), str(dst)), color=gs.YELLOW)
        printf(e)
        exit(1)


def moveFile(src, dst):
    ''' dst can be a file or a directory '''
    if dst.is_dir():
        # Get the real dst file path
        dst = dst/src.name
    if dst.is_file():
        # The dst already exists
        if not os.stat(str(dst))[0] & stat.S_IWRITE:
            os.chmod(str(dst), stat.S_IWRITE)
    elif not dst.parent.exists():
        # Make sure the parent directory exists
        dst.parent.mkdir(parents=True)
    shutil.move(str(src), str(dst))


def isUserAdmin():
    if os.name == 'nt':
        try:
            # WARNING: requires Windows XP SP2 or higher!
            return windll.shell32.IsUserAnAdmin()
        except:
            traceback.print_exc()
            print("Admin check failed, assuming not an admin.")
            return False
    else:
        # Check for root on Posix
        return os.getuid() == 0


def runAsAdmin(cmd, wait=True):
    if os.name != 'nt':
        return 1
    
    import win32api, win32con, win32event, win32process
    from win32com.shell.shell import ShellExecuteEx
    from win32com.shell import shellcon

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

    if wait:
        procHandle = procInfo['hProcess']    
        obj = win32event.WaitForSingleObject(procHandle, win32event.INFINITE)
        rc = win32process.GetExitCodeProcess(procHandle)
    else:
        rc = 0

    return rc


def regAdd(key, data=None, valueName='', valueType=winreg.REG_SZ, view=winreg.KEY_WOW64_64KEY):
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
    keyHandle = winreg.CreateKeyEx(HKey, subKey, 0, access=winreg.KEY_ALL_ACCESS|view)
    if data:
        winreg.SetValueEx(keyHandle, valueName, 0, valueType, data)


# Must create a setting instance
gs = GlobleSettings()
