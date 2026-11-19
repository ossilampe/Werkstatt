@echo off
rem ===========================================================================
rem  T12-Station: UART-Firmware auf das Modul schreiben (mit Pruefung)
rem  Der Chip wird NICHT komplett geloescht -> Kalibrierung/Einstellungen bleiben erhalten.
rem  Vorher: OLED abziehen, ST-Link anschliessen, 24 V AUS.
rem ===========================================================================
set OCD=C:\Werkzeuge\xpack-openocd-0.12.0-7
set BIN=%~dp0..\modul-firmware\t12_uart_v4.bin
"%OCD%\bin\openocd.exe" -s "%OCD%\openocd\scripts" -f interface/stlink-hla.cfg -c "transport select hla_swd" -c "set FLASH_SIZE 0x20000" -f target/stm32f1x.cfg -c "init; reset halt; program {%BIN%} 0x08000000 verify; reset run; exit"
echo.
echo  Steht oben "** Verified OK **", ist die Firmware drauf.
pause
