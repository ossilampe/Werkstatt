# Modul-Firmware selbst bauen

Die fertige Datei ist [`t12_uart_v4.bin`](t12_uart_v4.bin). Wer sie selbst übersetzen will:

1. **STM32CubeIDE 1.12.1** installieren (mit dieser Version wurde die Firmware entwickelt):
   [Spiegel beim Autor](https://github.com/deividAlfa/stm32_soldering_iron_controller/releases/tag/CubeIDE_v1.12.1) – das Setup ist von STMicroelectronics signiert.
   Installationsordner `C:\ST\STM32CubeIDE_1.12.1`.
2. Quellcode holen:
   `git clone --depth 1 https://github.com/deividAlfa/stm32_soldering_iron_controller.git`
3. ST-Treiberpaket **STM32Cube FW_F1 V1.8.5** nach `%USERPROFILE%\STM32Cube\Repository\STM32Cube_FW_F1_V1.8.5` legen
   (`git clone --depth 1 --branch v1.8.5 https://github.com/STMicroelectronics/STM32CubeF1.git STM32Cube_FW_F1_V1.8.5`).
   Sonst bleibt CubeMX im Kommandozeilenmodus beim versteckten Download hängen.
4. Board-Dateien in die Wurzel kopieren: Inhalt von `BOARDS/KSGER/v2/STM32F101/` → Projektwurzel
   (das macht auch `Building_script.bat` mit Option 1).
5. Code erzeugen (CubeMX, in der Projektwurzel):
   `java -jar <CubeIDE>\plugins\com.st.stm32cube.common.mx_*\STM32CubeMX.jar -q cubemx_script`
   (vorher `STM32SolderingStation.ioc` sichern und danach zurückkopieren – CubeMX verändert sie).
6. Unsere Dateien dazu:
   - `quellcode/uart_remote.c` → `Core/Src/`, `quellcode/uart_remote.h` → `Core/Inc/`
   - Patch anwenden: `git apply quellcode/aenderungen_user_main_settings.patch`
7. Übersetzen:
   `stm32cubeidec.exe --launcher.suppressErrors -nosplash -application org.eclipse.cdt.managedbuilder.core.headlessbuild -data <Arbeitsordner> -import <Projekt> -build STM32SolderingStation/SSD1306_Release`
   → `SSD1306_Release/STM32SolderingStation.bin`

Hinweise
- Unter Windows aus Claude/anderen Shells: `.bat` mit vollem Pfad aufrufen (`NoDefaultCurrentDirectoryInExePath`).
- In `uart_remote.h` schaltet `#define T12_UART_REMOTE` die UART-Fernsteuerung ein; auskommentiert entsteht wieder die normale OLED-Firmware.
- Versionen: v1 erste UART-Version · v2 Einstellungen lesen/schreiben · v3 Boost/Standby-Fehler behoben · v4 Laufzeit der Betriebsart (Zeitlinie).
