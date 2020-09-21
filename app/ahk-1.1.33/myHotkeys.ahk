#SingleInstance force

~Esc::      ; Double press Esc to close the active window
    if (A_ThisHotkey <> A_PriorHotkey or A_TimeSincePriorHotkey > 300)
            return
    WinGetClass, class, A
    if (class ~= "Progman|WorkerW|Shell_TrayWnd")
        return
    WinClose, A
return

^Esc::      ; Double press Ctl + Esc to put windows to hyberate
    if (A_ThisHotkey <> A_PriorHotkey or A_TimeSincePriorHotkey > 300)
        return
    DllCall("PowrProf\SetSuspendState", "int", 1, "int", 1, "int", 1)
return

#f::        ; Win + f to start searching by everything
    EnvGet, everythingPath, everythingPath
    run %everythingPath%
return

#u::        ; Win + u to open youtube
    run www.youtube.com
return

#!Up::      ; Win + Alt + Arrow up to increase the volume
    Send {Volume_Up}
return

#!Down::    ; Win + Alt + Arrow down to decrease the volume
    Send {Volume_Down}
return

#!Left::    ; Win + Alt + Arrow left to play previous
    Send {Media_Prev}
return

#!Right::   ; Win + Alt + Arrow right to play next
    Send {Media_Next}
return


; *************************************** Functions for File Explorer ***************************************** ;
Explorer_GetPath(hwnd="")
{
    if !(window := Explorer_GetWindow(hwnd))
        return ErrorLevel := "ERROR"
    if (window="desktop")
        return A_Desktop
    path := window.LocationURL
    path := RegExReplace(path, "ftp://.*@","ftp://")
    StringReplace, path, path, file:///
    StringReplace, path, path, /, \, All

    ; thanks to polyethene
    Loop
        If RegExMatch(path, "i)(?<=%)[\da-f]{1,2}", hex)
            StringReplace, path, path, `%%hex%, % Chr("0x" . hex), All
        Else Break
    return path
}
Explorer_GetAll(hwnd="")
{
    return Explorer_Get(hwnd)
}
Explorer_GetSelected(hwnd="")
{
    return Explorer_Get(hwnd,true)
}

Explorer_GetWindow(hwnd="")
{
    ; thanks to jethrow for some pointers here
    WinGet, process, processName, % "ahk_id" hwnd := hwnd? hwnd:WinExist("A")
    WinGetClass class, ahk_id %hwnd%

    if (process!="explorer.exe")
        return
    if (class ~= "(Cabinet|Explore)WClass")
    {
        for window in ComObjCreate("Shell.Application").Windows
            if (window.hwnd==hwnd)
                return window
    }
    else if (class ~= "Progman|WorkerW")
        return "desktop" ; desktop found
}
Explorer_Get(hwnd="",selection=false)
{
    if !(window := Explorer_GetWindow(hwnd))
        return ErrorLevel := "ERROR"
    if (window="desktop")
    {
        ControlGet, hwWindow, HWND,, SysListView321, ahk_class Progman
        if !hwWindow ; #D mode
            ControlGet, hwWindow, HWND,, SysListView321, A
        ControlGet, files, List, % ( selection ? "Selected":"") "Col1",,ahk_id %hwWindow%
        base := SubStr(A_Desktop,0,1)=="\" ? SubStr(A_Desktop,1,-1) : A_Desktop
        Loop, Parse, files, `n, `r
        {
            path := base "\" A_LoopField
            IfExist %path% ; ignore special icons like Computer (at least for now)
                ret .= path "`n"
        }
    }
    else
    {
        if selection
            collection := window.document.SelectedItems
        else
            collection := window.document.Folder.Items
        for item in collection
            ret .= item.path "`n"
    }
    return Trim(ret,"`n")
}
; ************************************************************************************************************* ;



$space::    ; Double click space to open target with notepad++
    if (SelctionMode)
        MouseClick
    else
        send {space}

    if (A_ThisHotkey <> A_PriorHotkey or A_TimeSincePriorHotkey > 300)
        return
    WinGet, process, processName, A
    if (process != "explorer.exe")
        return
    sel := Explorer_GetSelected()
    FileGetAttrib, Attributes, %sel%
    IfInString, Attributes, A
        EnvGet, nppPath, nppPath
        run %nppPath% "%sel%"
return

~^c::    ; Double press control c to copy the target's path to clipboard
    if (A_ThisHotkey <> A_PriorHotkey or A_TimeSincePriorHotkey > 300)
        return
    WinGet, process, processName, A
    if (process != "explorer.exe")
        return
    sel := Explorer_GetSelected()
    if (! sel )
    {
        path := Explorer_GetPath()
        clipboard = %path%
        return
    }
    clipboard = %sel%
return

Brightness(IndexMove)
{
    VarSetCapacity(SupportedBrightness, 256, 0)
    VarSetCapacity(SupportedBrightnessSize, 4, 0)
    VarSetCapacity(BrightnessSize, 4, 0)
    VarSetCapacity(Brightness, 3, 0)
    hLCD := DllCall("CreateFile", Str, "\\.\LCD", UInt, 0xC0000000, UInt, 3, UInt, 0, UInt, 3, UInt, 0, UInt, 0)
    if hLCD != -1
    {
        DevVideo := 0x00000023, BuffMethod := 0, Fileacces := 0
        NumPut(3, Brightness, 0, "UChar")
        NumPut(0, Brightness, 1, "UChar")
        NumPut(0, Brightness, 2, "UChar")
        V := DevVideo<<16 | 0x498 | BuffMethod<<14 | Fileacces
        DllCall("DeviceIoControl", UInt, hLCD, UInt, V, UInt, 0, UInt, 0, UInt, &Brightness, UInt, 3, UInt, &BrightnessSize, UInt, 0)
        DllCall("DeviceIoControl", UInt, hLCD, UInt, V-4, UInt, 0, UInt, 0, UInt, &SupportedBrightness, UInt, 256, UInt, &SupportedBrightnessSize, UInt, 0)
        ACBrightness := NumGet(Brightness, 1, "UChar")
        ACIndex := 0
        DCBrightness := NumGet(Brightness, 2, "UChar")
        DCIndex := 0
        BufferSize := NumGet(SupportedBrightnessSize, 0, "UInt")
        MaxIndex := BufferSize-1
        Loop, %BufferSize%
        {
            ThisIndex := A_Index-1
            ThisBrightness := NumGet(SupportedBrightness, ThisIndex, "UChar")
            if ACBrightness = %ThisBrightness%
            ACIndex := ThisIndex
            if DCBrightness = %ThisBrightness%
            DCIndex := ThisIndex
        }
        if DCIndex >= %ACIndex%
        BrightnessIndex := DCIndex
        else
        BrightnessIndex := ACIndex
        BrightnessIndex += IndexMove
        if BrightnessIndex > %MaxIndex%
        BrightnessIndex := MaxIndex
        if BrightnessIndex < 0
        BrightnessIndex := 0
        NewBrightness := NumGet(SupportedBrightness, BrightnessIndex, "UChar")
        NumPut(3, Brightness, 0, "UChar")
        NumPut(NewBrightness, Brightness, 1, "UChar")
        NumPut(NewBrightness, Brightness, 2, "UChar")
        DllCall("DeviceIoControl", UInt, hLCD, UInt, V+4, UInt, &Brightness, UInt, 3, UInt, 0, UInt, 0, UInt, 0, Uint, 0)
        DllCall("CloseHandle", UInt, hLCD)
        return BrightnessIndex
    }
}
