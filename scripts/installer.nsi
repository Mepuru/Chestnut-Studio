; Chestnut Studio NSIS Installer
; Supports: fresh install, silent upgrade over old version
;
; Build:
;   makensis /DVERSION=2.4.0 /DSOURCE_DIR="D:\path\to\main.dist" installer.nsi
;
; Output: ChestnutStudio-{VERSION}-Setup-x86_64_v1.exe

!define PRODUCT_NAME "Chestnut Studio"
!define PUBLISHER "Chestnut Studio"

!ifndef VERSION
  !error "VERSION not defined -- pass /DVERSION=x.x.x"
!endif
!ifndef SOURCE_DIR
  !error "SOURCE_DIR not defined -- pass /DSOURCE_DIR=path"
!endif

Name "${PRODUCT_NAME} ${VERSION}"
OutFile "..\dist\ChestnutStudio-${VERSION}-Setup-x86_64_v1.exe"
InstallDir "$PROGRAMFILES64\${PRODUCT_NAME}"
InstallDirRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "InstallLocation"

RequestExecutionLevel admin
SetCompressor /SOLID lzma

!include "MUI2.nsh"
!include "FileFunc.nsh"

; -- UI --
!define MUI_ABORTWARNING
!define MUI_LANGDLL_ALLLANGUAGES
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Japanese"

; -- Version upgrade check --
Function .onInit
  ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString"
  StrCmp $R0 "" done

  ; Previous installation detected - silently uninstall before proceeding
  ; _?=$INSTDIR ensures the uninstaller runs from its own directory so it can self-delete
  ExecWait '$R0 /S _?=$INSTDIR'

  done:
FunctionEnd

; -- Install sections --

Section "Chestnut Studio (required)" SecMain
  SectionIn RO
  SetOutPath "$INSTDIR"

  ; Copy all build output preserving subdirectory structure
  File /r "${SOURCE_DIR}\*.*"

  ; Start Menu shortcut
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\main.exe"

  ; Uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Registry - Add/Remove Programs
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "Publisher" "${PUBLISHER}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayVersion" "${VERSION}"
  WriteRegDWord HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "NoModify" 1
  WriteRegDWord HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "NoRepair" 1
SectionEnd

Section "Desktop Shortcut" SecDesktop
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\main.exe"
SectionEnd

; -- Uninstall section --
Section "Uninstall" SecUninstall
  ; Start Menu
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk"
  RMDir "$SMPROGRAMS\${PRODUCT_NAME}"

  ; Desktop shortcut
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"

  ; Application files
  RMDir /r "$INSTDIR"

  ; Registry
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
SectionEnd
