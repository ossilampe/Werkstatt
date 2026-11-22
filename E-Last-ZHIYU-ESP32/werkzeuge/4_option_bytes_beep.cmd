@echo off
chcp 65001 >nul
rem ---------------------------------------------------------------
rem  Option Bytes mit OPT2 = 0x80 (AFR7 = BEEP) schreiben.
rem  Ohne diesen Schritt bleibt die Last dunkel (Dauer-Reset), weil
rem  die Firmware AFR7 beim Start selbst setzen will und dabei das
rem  Komplement-Byte verdirbt.
rem
rem  Sicherer Weg, der bei uns funktioniert hat: STVP-Oberfläche,
rem  Reiter OPTION BYTE, Standardwerte lassen (AFR7 = BEEP),
rem  Program -> Current tab -> "OPTION BYTE successfully verified".
rem  Dieses Skript ist die Kommandozeilen-Variante derselben Datei.
rem ---------------------------------------------------------------
set STVP="C:\Program Files (x86)\STMicroelectronics\st_toolset\stvp\STVP_CmdLine.exe"
cd /d "%~dp0..\firmware"
%STVP% -BoardName=ST-LINK -Port=USB -ProgMode=SWIM -Device=STM8S005K6 -no_progProg -no_progData -FileOption=option_afr7.hex -verif -no_loop -no_log -verbose -no_warn_protect
echo.
echo Kommt hier "complementary bytes" statt "successfully verified":
echo Option Bytes in der STVP-Oberfläche schreiben (siehe README, Schritt 4).
pause
