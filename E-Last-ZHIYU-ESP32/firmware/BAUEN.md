# Firmware selbst bauen

Die Datei `electronic_load.hex` in diesem Ordner ist fertig zum Flashen. Selbst bauen musst du nur, wenn du eine neuere Version der freien Firmware nutzen oder etwas ändern willst.

## Quelle und Lizenz

- Projekt: [herm/ZPB30A1_Firmware](https://github.com/herm/ZPB30A1_Firmware) (GPL-3.0, siehe `LICENSE-herm-GPL-3.0.txt`)
- Gebaut aus Commit [`fe93bfe`](https://github.com/herm/ZPB30A1_Firmware/commit/fe93bfea171ececacc97fbbe3fa23c805111e56d) vom 06.11.2026 („fix(ui): reserve the last menu stack slot for the error menu“), **ohne eigene Änderungen**.
- Die Hex-Datei ist ein unverändertes Kompilat dieses Quelltexts. Den vollständigen Quelltext gibt es unter dem Link oben.

## Werkzeuge (Windows)

| Werkzeug | Bezug |
|---|---|
| SDCC 4.5.0 (Small Device C Compiler) | `winget install --id SDCC.SDCC -e` |
| Git | git-scm.com |
| Git Bash | kommt mit Git; darin laufen die Befehle unten |

`make` wird nicht gebraucht. Unter Windows bricht `make clear_eeprom` im Makefile des Projekts ohnehin ab (fehlende Regel `clear_eeprom_windows`), deshalb ruft man SDCC direkt auf.

## Bauen

```bash
git clone https://github.com/herm/ZPB30A1_Firmware.git
cd ZPB30A1_Firmware/software
git checkout fe93bfe            # oder weglassen für den neuesten Stand
export PATH="/c/Program Files/SDCC/bin:$PATH"
mkdir -p build
for f in electronic_load tm1650 uart utils fan ui systick load settings adc beeper menu_items calibration; do
  sdcc -c -mstm8 --std-sdcc11 --opt-code-speed -D STM8S005 $f.c -o build/$f.rel
done
cd build
sdcc -mstm8 --std-sdcc11 --opt-code-speed electronic_load.rel tm1650.rel uart.rel utils.rel fan.rel ui.rel \
     systick.rel load.rel settings.rel adc.rel beeper.rel menu_items.rel calibration.rel -o electronic_load.ihx
packihx electronic_load.ihx > electronic_load.hex
```

Ergebnis: `software/build/electronic_load.hex` (ca. 37 KB als Text, ca. 13 KB Programm). Warnungen von SDCC sind normal.

Kommen in einer neueren Version Quelldateien hinzu, müssen sie in beiden Listen oben ergänzt werden (siehe `SRCS` im `Makefile`).

## Die anderen Dateien in diesem Ordner

| Datei | Inhalt | Wofür |
|---|---|---|
| `option_rop_off.hex` | Option Bytes mit ROP = 0 (Ausleseschutz aus) | Schritt 2: entsperren, löscht dabei die Original-Firmware |
| `option_afr7.hex` | Option Bytes Werkseinstellung, aber **OPT2 = 0x80 / NOPT2 = 0x7F** (AFR7 = BEEP) | Schritt 4: verhindert den Dauer-Reset der freien Firmware |
| `eeprom_leer.hex` | 128 Byte EEPROM mit 0x00 | Schritt 3: alte Einstellungen löschen (entspricht `make clear_eeprom`) |
