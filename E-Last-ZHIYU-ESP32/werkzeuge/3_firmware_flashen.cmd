@echo off
chcp 65001 >nul
rem ---------------------------------------------------------------
rem  Schreibt die freie Firmware (herm/ZPB30A1_Firmware, Commit fe93bfe)
rem  in den Programmspeicher und leert das EEPROM. Mit Prüfung.
rem  Option Bytes werden hier NICHT angefasst (siehe Schritt 4).
rem ---------------------------------------------------------------
set STVP="C:\Program Files (x86)\STMicroelectronics\st_toolset\stvp\STVP_CmdLine.exe"
cd /d "%~dp0..\firmware"
%STVP% -BoardName=ST-LINK -Port=USB -ProgMode=SWIM -Device=STM8S005K6 -FileProg=electronic_load.hex -FileData=eeprom_leer.hex -no_progOption -verif -no_loop -no_log -verbose -no_warn_protect
echo.
echo Erwartet: PROGRAM MEMORY und DATA MEMORY "successfully verified".
echo Danach unbedingt Schritt 4 (Option Bytes mit AFR7 = BEEP).
pause
