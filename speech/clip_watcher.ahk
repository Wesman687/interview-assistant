#Persistent
SetTimer, CheckClipboard, 500  ; Check clipboard every 500ms
return

CheckClipboard:
    if (ClipboardChanged()) {
        Run, C:\Scripts\send_screenshot.bat, , Hide  ; Open BAT file silently
    }
return

ClipboardChanged() {
    static oldClip
    if (Clipboard = oldClip)
        return false
    oldClip := Clipboard
    return true
}