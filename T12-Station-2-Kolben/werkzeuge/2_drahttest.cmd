@echo off
rem ===========================================================================
rem  T12-Station: prueft die zwei Umbau-Draehte (OLED-Pad SCL -> PB10, OLED-Pad SDA -> PB11)
rem  Erwartet:  SDA=1 SCL=0 -> PB10=0 PB11=1  /  SDA=0 SCL=1 -> PB10=1 PB11=0
rem             SDA=0 SCL=0 -> 0 0           /  SDA=1 SCL=1 -> 1 1
rem  Bleibt ein Wert immer 0: Bruecke nach GND (Pin 23) oder Draht ab.
rem ===========================================================================
set OCD=C:\Werkzeuge\xpack-openocd-0.12.0-7
"%OCD%\bin\openocd.exe" -s "%OCD%\openocd\scripts" -f interface/stlink-hla.cfg -c "transport select hla_swd" -c "set FLASH_SIZE 0x20000" -f target/stm32f1x.cfg -f "%~dp0drahttest_pb10_pb11.cfg"
pause
