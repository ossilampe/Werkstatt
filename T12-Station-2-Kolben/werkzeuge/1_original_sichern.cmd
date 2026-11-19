@echo off
rem ===========================================================================
rem  T12-Station: Original-Firmware des Moduls (STM32F103C8) sichern
rem  Voraussetzung: xPack OpenOCD entpackt, ST-Link V2 am Modul (3,3 V, GND, SWDIO, SWCLK), 24 V AUS
rem  Pfad zu OpenOCD hier anpassen:
rem ===========================================================================
set OCD=C:\Werkzeuge\xpack-openocd-0.12.0-7
set CFG=-s "%OCD%\openocd\scripts" -f interface/stlink-hla.cfg -c "transport select hla_swd" -c "set FLASH_SIZE 0x20000" -f target/stm32f1x.cfg

rem Zweimal lesen und vergleichen - nur dann ist die Sicherung sicher
"%OCD%\bin\openocd.exe" %CFG% -c "init; halt; dump_image original_a.bin 0x08000000 0x20000; resume; exit"
"%OCD%\bin\openocd.exe" %CFG% -c "init; halt; dump_image original_b.bin 0x08000000 0x20000; resume; exit"
fc /b original_a.bin original_b.bin >nul && (
  echo.
  echo  OK: Sicherung zweimal identisch gelesen -> original_a.bin aufbewahren
) || (
  echo.
  echo  ACHTUNG: Die beiden Lesungen unterscheiden sich - Verbindung pruefen und wiederholen!
)
pause
