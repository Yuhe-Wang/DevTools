import os
import winreg
from pathlib import Path

from scripts.share.util import gs
from scripts.share.util import call
from scripts.share.util import printf
from scripts.share.util import copyPath
from scripts.share.util import removePath
from scripts.share.util import killProcess

from scripts.share.winutil import regQuery
from scripts.share.winutil import regAdd
from scripts.share.winutil import regAddList
from scripts.share.winutil import regDelete
from scripts.share.winutil import installFont
from scripts.share.winutil import addContextMenu
from scripts.share.winutil import setOpenWith


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
    for p in (gs.GitDir/"res/fonts").iterdir():
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
        setOpenWith(ext, str(appDir/"7zFM.exe"),
                    icon="%s,%d" % (str(appDir/"7z.dll"), iconDict[ext]),
                    regKeyName="7-Zip.%s" % ext)

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
    regAddList(r"HKCR\CLSID\{%s}\InprocServer32" % clsid, [
               ('@', str(appDir/"NppShell_06.dll")),
               ("ThreadingModel", "Apartment")])
    regAddList(r"HKCR\CLSID\{%s}\Settings" % clsid, [
               ("Title", "Edit with &Notepad++"),
               ("Path", str(appDir/"notepad++.exe")),
               ("Custom", ''),
               ("ShowIcon", 1),
               ("Dynamic",  1),
               ("Maxtext",  25)])
    regAdd(r"HKCR\*\shellex\ContextMenuHandlers\ANotepad++64", '@', "{%s}" % clsid)
    srcDir = gs.GitDir/"backup/Notepad++"
    dstDir = Path(os.environ["appdata"])/"Notepad++"
    if srcDir.is_dir():
        copyPath(srcDir, dstDir)


def backup():
    printf("Backup the notepad++ settings")
    srcDir = Path(os.environ["appdata"])/"Notepad++"
    dstDir = gs.GitDir/"backup/Notepad++"
    if srcDir.is_dir():
        copyPath(srcDir, dstDir)
        removePath(gs.GitDir/"backup/Notepad++/session.xml")  # No need to back up session

    printf("Backup the ConEmu settings")
    folder = "conemu-20.7.13"
    srcPath = gs.GitDir/"app"/folder/"ConEmu.xml"
    dstDir = gs.GitDir/"backup/conemu"
    if srcPath.is_file():
        copyPath(srcPath, dstDir)

    printf("Backup the Sumatra PDF settings")
    folder = "sumatra-3.2"
    srcPath = gs.GitDir/"app"/folder/"SumatraPDF-settings.txt"
    dstDir = gs.GitDir/"backup/sumatra"
    if srcPath.is_file():
        copyPath(srcPath, dstDir)

    printf("Backup done!")


def optimizeWin10():
    printf("Optimize win10 settings...")
    # 隐藏任务栏搜索按钮/搜索框
    restartExplorer = False
    if regAdd(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Search",
              "SearchboxTaskbarMode", 0):
        restartExplorer = True
    # <ExplorerNotify Type="Custom" msg="1A" lParam="TraySettings"/>

    # 隐藏多任务按钮
    if regAdd(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
              "ShowTaskViewButton", 0):
        restartExplorer = True
    # <ExplorerNotify Type="Custom" msg="1A" lParam="TraySettings"/>

    # 从不合并任务栏
    regAdd(r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarGlomLevel", 2)

    # 隐藏任务栏上的人脉
    if (regAdd(r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People",
               "PeopleBand", 0) or
        regAdd(r"HKEY_CURRENT_USER\Software\Policies\Microsoft\Windows\Explorer",
               "HidePeopleBar", 1)):
        restartExplorer = True
    # <Activate Restart="Explorer">

    # 显示开始菜单、任务栏、操作中心和标题栏的颜色
    if regAdd(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize", "ColorPrevalence", 1):
        restartExplorer = True
    if regAdd(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\DWM", "ColorPrevalence", 1):
        restartExplorer = True
    # <ExplorerNotify Type="Custom" msg="111" wParam="#A220" Explorer="True">

    # 使开始菜单、任务栏、操作中心透明
    regAdd(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", 1)
    # 关闭商店应用推广
    regAdd(r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
           "PreInstalledAppsEnabled", 0)
    # 关闭锁屏时的Windows 聚焦推广
    regAdd(r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
           "RotatingLockScreenEnable", 0)
    # 关闭游戏录制工具
    regAdd(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", 0)
    # 关闭多嘴的小娜
    regAdd(r"HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\Windows Search", "AllowCortana", 0)
    # 打开资源管理器时显示此电脑
    regAdd(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "LaunchTo", 1)
    # 显示所有文件扩展名
    if regAdd(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "HideFileExt", 0):
        restartExplorer = True
    # <ExplorerNotify Type="Custom" msg="111" wParam="#A220" Explorer="True">

    # 隐藏快捷方式小箭头
    if regAdd(r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons",
              "29", r"%systemroot%\Blank.ico", winreg.REG_EXPAND_SZ):
        copyPath(gs.GitDir/"res/icon/blank.ico", Path(os.environ["systemroot"]))
        restartExplorer = True

    # 创建快捷方式时不添 快捷方式 文字
    if regAdd(r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer",
              "Link", bytes.fromhex("00000000")):
        restartExplorer = True

    # 收起资源管理器功能区 ribbon
    if regAdd(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Ribbon",
              "MinimizedStateTabletModeOff", 1):
        restartExplorer = True
    # <ExplorerNotify Type="Custom" msg="111" wParam="#A220" Explorer="True">

    # 禁止自动播放
    if regAdd(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\AutoplayHandlers",
              "DisableAutoplay", 1):
        restartExplorer = True
    # <ExplorerNotify Type="Custom" msg="111" wParam="#A220" Explorer="True)

    # 在桌面显示我的电脑
    if regAdd(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel",
              "{20D04FE0-3AEA-1069-A2D8-08002B30309D}", 0):
        restartExplorer = True
    # <ExplorerNotify Type="AssocChanged>
    # 在桌面显示回收站
    if regAdd(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel",
              "{645FF040-5081-101B-9F08-00AA002F954E}", 0):
        restartExplorer = True
    # <ExplorerNotify Type="AssocChanged>
    # 在桌面显示控制面板
    if regAdd(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel",
              "{5399E694-6CE5-4D6C-8FCE-1D8870FDCBA0}", 0):
        restartExplorer = True
    # <ExplorerNotify Type="AssocChanged>
    # 在桌面显示用户文件夹
    # if regAdd(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel",
    #           "{59031a47-3f72-44a7-89c5-5595fe6b30ee}", 0):
    #     restartExplorer = True
    # <ExplorerNotify Type="AssocChanged>
    # 在桌面显示网络
    # if regAdd(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel",
    #           "{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}", 0):
    #     restartExplorer = True
    # <ExplorerNotify Type="AssocChanged>

    # 启用自动换行
    regAdd(r"HKEY_CURRENT_USER\Software\Microsoft\Notepad", "fWrap", 1)
    # 始终显示状态栏
    regAdd(r"HKEY_CURRENT_USER\Software\Microsoft\Notepad", "StatusBar", 1)

    # 禁用客户体验改善计划
    regAdd(r"HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\SQMClient\Windows", "CEIPEnable", 0)

    # 启用 Windows 照片查看器
    regAddList(r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows Photo Viewer\Capabilities\FileAssociations", [
               (".jpg", "PhotoViewer.FileAssoc.Tiff"),
               (".png", "PhotoViewer.FileAssoc.Tiff"),
               (".jpeg", "PhotoViewer.FileAssoc.Tiff"),
               (".bmp", "PhotoViewer.FileAssoc.Tiff"),
               (".jpe", "PhotoViewer.FileAssoc.Tiff"),
               (".jfif", "PhotoViewer.FileAssoc.Tiff"),
               (".dib", "PhotoViewer.FileAssoc.Tiff"),
               (".ico", "PhotoViewer.FileAssoc.Tiff"),
               (".gif", "PhotoViewer.FileAssoc.Tiff"),
               (".tga", "PhotoViewer.FileAssoc.Tiff")])

    # Set accent color
    regAdd(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\DWM", "AccentColor", 0x00748501)
    regDelete(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\DWM", "AccentColorInactive")

    addContextMenu("cmdhere", "Open CMD here (&Q)", 'cmd.exe /s /k pushd "%V"', icon="cmd.exe")

    if restartExplorer:
        # Windows 10 will automatically start explorer after the process was killed
        killProcess("Explorer")


def setupConEmu():
    folder = "conemu-20.7.13"
    printf("Setup %s..." % folder)
    # Copy the config
    srcDir = gs.GitDir/"backup/conemu"
    dstDir = gs.GitDir/"app"/folder
    if srcDir.is_dir():
        copyPath(srcDir, dstDir)
    # Setup the reg
    regAddList(r"HKCU\SOFTWARE\ConEmu", [
               ("DefTerm-Enabled", 1),
               ("DefTerm-NoInjects", 0),
               ("DefTerm-NewWindow", 0),
               ("DefTerm-DebugLog", 0),
               ("DefTerm-Confirm", 2),
               ("DefTerm-Flags", 34470),
               ("DefTerm-ConEmuExe", str(dstDir/"ConEmu64.exe"),),
               ("DefTerm-BaseDir", str(dstDir),),
               ("DefTerm-CfgFile", ''),
               ("DefTerm-Config", ''),
               ("DefTerm-AppList", ["explorer.exe"])])

    # Startup cmd
    startupCmd = '"%s" -SetDefTerm -Detached -MinTSA' % str(dstDir/"ConEmu64.exe")
    regAdd(r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
           "ConEmuDefaultTerminal", startupCmd)
    # Run setup once
    call(startupCmd, DETACH=True)


def setupAutoHotKey():
    folder = "ahk-1.1.33"
    printf("Setup %s..." % folder)
    exePath = gs.GitDir/"app"/folder/"AutoHotkeyU64.exe"
    setOpenWith("ahk", str(exePath), icon=str(exePath) + ",1", regKeyName="AutoHotkeyScript")


def setupSumatraPdf():
    folder = "sumatra-3.0"
    printf("Setup %s..." % folder)
    exePath = gs.GitDir/"app"/folder/"SumatraPDF.exe"
    regAdd(r"HKCR\Applications\SumatraPDF.exe\DefaultIcon", '@', str(exePath) + ",1")
    regAdd(r"HKCR\Applications\SumatraPDF.exe\Shell\Open\Command", '@', '"%s" "%%1" %%*' % str(exePath))
    regAdd(r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.pdf\OpenWithList", "a", "SumatraPDF")
    # Copy the config
    srcDir = gs.GitDir/"backup/sumatra"
    dstDir = gs.GitDir/"app"/folder
    if srcDir.is_dir():
        copyPath(srcDir, dstDir)


def main(argv):
    if not argv:
        printf("Please specifiy the setup target or use all instead")
        return 1
    if argv[0] == "backup":
        backup()
        return 0

    if argv[0] == "all":
        argv[0] = "7z,python,notepad++,font,optimize,conemu,ahk,pdf"
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
    if "optimize" in setupList:
        optimizeWin10()
    if "conemu" in setupList:
        setupConEmu()
    if "ahk" in setupList:
        setupAutoHotKey()
    if "pdf" in setupList:
        setupSumatraPdf()
    printf("Setup done!")
    return 0
