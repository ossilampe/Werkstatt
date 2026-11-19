@echo off
rem ===========================================================================
rem  T12-Station: gesicherte Original-Firmware zurueckspielen (original_a.bin aus Schritt 1)
rem  Danach wieder OLED und Drehknopf am Modul benutzen.
rem ===========================================================================
set OCD=C:\Werkzeuge\xpack-openocd-0.12.0-7
"%OCD%\bin\openocd.exe" -s "%OCD%\openocd\scripts" -f interface/stlink-hla.cfg -c "transport select hla_swd" -c "set FLASH_SIZE 0x20000" -f target/stm32f1x.cfg -c "init; reset halt; stm32f1x mass_erase 0; program original_a.bin 0x08000000 verify; reset run; exit"
pause
