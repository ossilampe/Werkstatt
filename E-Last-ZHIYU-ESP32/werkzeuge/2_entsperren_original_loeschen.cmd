@echo off
chcp 65001 >nul
rem ---------------------------------------------------------------
rem  ACHTUNG: schaltet den Ausleseschutz (ROP) aus.
rem  Der STM8 löscht dabei die Original-Firmware UNWIDERRUFLICH.
rem  Ein Zurück zur ZHIYU-Firmware gibt es danach nicht.
rem ---------------------------------------------------------------
set STVP="C:\Program Files (x86)\STMicroelectronics\st_toolset\stvp\STVP_CmdLine.exe"
cd /d "%~dp0..\firmware"
echo.
echo Die Original-Firmware der Last wird jetzt endgültig gelöscht.
choice /c JN /m "Wirklich fortfahren (J/N)"
if errorlevel 2 goto ende
%STVP% -BoardName=ST-LINK -Port=USB -ProgMode=SWIM -Device=STM8S005K6 -no_progProg -no_progData -FileOption=option_rop_off.hex -no_verif -no_loop -no_log -verbose -no_warn_protect
echo.
echo Eine Meldung "complementary bytes" ist hier normal. Weiter mit 3_firmware_flashen.cmd
:ende
pause
