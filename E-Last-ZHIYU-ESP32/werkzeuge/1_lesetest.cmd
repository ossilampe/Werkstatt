@echo off
chcp 65001 >nul
rem ---------------------------------------------------------------
rem  Lesetest: prüft nur, ob ST-Link und STM8 miteinander reden.
rem  Ändert NICHTS am Chip.
rem  Erwartet bei Original-Firmware: "The device is protected"
rem  Erwartet nach dem Entsperren: Option Bytes werden gelesen
rem ---------------------------------------------------------------
set STVP="C:\Program Files (x86)\STMicroelectronics\st_toolset\stvp\STVP_CmdLine.exe"
cd /d "%~dp0..\firmware"
%STVP% -BoardName=ST-LINK -Port=USB -ProgMode=SWIM -Device=STM8S005K6 -no_progProg -no_progData -no_progOption -readOption -no_verif -no_loop -no_log -verbose -no_warn_protect
echo.
echo "Cannot communicate with the device" = Verdrahtung prüfen (Aufdruck am Stick!), Anzeigeplatine abziehen, keine 12 V.
pause
