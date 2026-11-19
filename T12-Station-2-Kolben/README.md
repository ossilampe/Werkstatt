# T12-Lötstation mit 2 Kolben

Lötstation für **T12-Spitzen** mit großem Touch-Display, Drehgeber, deutscher Sprachausgabe, temperaturgeregeltem Netzteil-Lüfter, Anschluss für eine Absaugung und **Spitzenprofilen aus Home Assistant**.

Die eigentliche Regelung macht eine **fertige, günstige T12-Steuerplatine** (STM32), die eine **eigene Firmware** bekommt und per UART vom ESP32-Display gesteuert wird. Am Modul selbst wird nichts mehr bedient – alles läuft über Touch und Drehgeber.

> **Stand 20.11.2026:** Getestet mit **einem** Modul an Kolben A (Heizen, Regeln, Standby, alle Menüs, Ansagen, Profile). Kolben B nutzt dieselbe Firmware und Verdrahtung auf GPIO 38/39, ist aber noch nicht mit echtem zweiten Modul geprüft. Lüfter/Absaugung/DS18B20 sind programmiert, die Hardware dafür ist noch nicht aufgebaut.

> Die Variante mit 1 Kolben steht im Ordner [`T12-Station-1-Kolben`](../T12-Station-1-Kolben).  Die Variante mit eigener Platine (KiCad, JLCPCB) liegt in [`T12-Loetstation`](../T12-Loetstation).

![Hauptseite](docs/01-hauptseite.svg)

## Inhalt

1. [Funktionen](#funktionen)
2. [Teile und Hilfsmittel](#teile-und-hilfsmittel)
3. [Umbau am Modul (2 Drähte)](#umbau-am-modul-2-drähte)
4. [Modul flashen](#modul-flashen)
5. [Anschlussplan](#anschlussplan)
6. [ESPHome installieren](#esphome-installieren)
7. [Spitzenprofile (Home Assistant)](#spitzenprofile-home-assistant)
8. [Bedienung und Menüs](#bedienung-und-menüs)
9. [Protokoll Modul ↔ ESP](#protokoll-modul--esp)
10. [Fehlersuche](#fehlersuche)
11. [Gehäuse](#gehäuse)
12. [Dateien](#dateien)

## Funktionen

- Zwei Kacheln A und B, Ist-/Solltemperatur groß, Leistungsbalken, Status in Farbe (HEIZT, BEREIT, STANDBY, SCHLÄFT, KÜHLT AB, KEINE SPITZE, Fehler)
- **Kachel antippen:** 1× = auswählen, 2× = ein/aus (keine extra Tasten). Nach Stromausfall sind alle Kolben **aus**
- Schmale **Zeitlinie am Kachelrand**: gelb = Zeit bis Standby, blau = Zeit bis Schlafen – läuft von oben nach unten ab, Griffbewegung füllt sie wieder
- **Drehgeber:** drehen = ±5 °C, kurz drücken = Kolben A/B wechseln, lang = Menü. 3 s nach dem letzten Dreh: Wert gespeichert + Ansage „Temperatur gespeichert“
- 3 **Festwert-Tasten** – mit Spitzenprofil die 3 Temperaturen der eingesetzten Spitze
- **Spitzenprofile** aus einer einfachen Datei in Home Assistant; nach einem Spitzenwechsel erscheint automatisch die Auswahl
- Einschalten **ohne Kolben/Spitze gesperrt** – Hinweis im Display und Ansage
- **Standby/Schlafen/Boost** im Modul, einstellbar im Menü; Kalt-Boost (kurz +50 °C beim Aufheizen) mit Anzeige „Soll 280 (330) °C“
- **Ansagen** (deutsche Stimme): bereit, kühlt ab, schläft, keine Spitze, Fehler, Verbindung unterbrochen, Temperatur gespeichert, Lötstation bereit
- **Netzteil-Lüfter** nach DS18B20 (Start-/Volllast-Temperatur einstellbar), **Absaugung** Auto (läuft, solange ein Kolben bewegt wird + Nachlauf), immer an, aus
- Menüs springen nach **20 s** ohne Bedienung zur Hauptseite zurück
- Sicherheit: das Modul regelt selbst; meldet sich der ESP 30 s nicht, geht es in Standby; Übertemperatur/Fehler schaltet das Modul ab
- Home Assistant: Temperaturen A/B, Netzteil-Temperatur, Lüfter, Absaugung, Mediaplayer „Ansage“

## Teile und Hilfsmittel

| Teil | Hinweis | Link |
|---|---|---|
| 2 × T12-Steuerplatine **STM32 Ver21S** (KSGER-v2-Bauform, je ca. 28 €) – je Kolben eine | STM32F103C8, **4-poliger OLED-Anschluss** (VCC GND SCL SDA). Chip muss echter STM32 oder CKS32 sein (GD32/CH32 machen ADC-Probleme) | [Amazon](https://www.amazon.de/dp/B0F4X2F72V) |
| Waveshare **ESP32-S3-Touch-LCD-3.5** | 480×320, Touch, Lautsprecher-Verstärker, PSRAM. **Nicht** die Version „3.5B“ | [Amazon](https://www.amazon.de/dp/B0F6TM959R) · [Doku](https://docs.waveshare.com/ESP32-S3-Touch-LCD-3.5) |
| Netzteil 24 V | ≥ 6 A (2 × 75 W + Lüfter) | – |
| T12-Griff(e) + Spitzen | z. B. FX9501-Griff mit Neigungsschalter | – |
| Drehgeber-Modul KY-040 | CLK, DT, SW, +, − | – |
| 2 × LM2596 Step-down | 24→5 V (Display), 24→12 V (Lüfter) | – |
| DS18B20 + 4,7 kΩ | Netzteil-Temperatur | – |
| 2 × AO3400 + 2 × SS14 + 100 Ω + 100 kΩ | Lüfter-Schalter (low-side, 25 kHz PWM) | – |
| Lautsprecher | an den MX1.25-Lautsprecherstecker des Displays | – |
| Kabel | Dupont-Litzen 22 AWG, dünner Kupferlackdraht 0,1–0,2 mm für den Umbau | – |

**Werkzeug / Software**

| Was | Wofür | Download |
|---|---|---|
| ST-Link V2 (Nachbau genügt) | Modul flashen (SWD) | – |
| xPack OpenOCD 0.12.0 | Flash-Programm (ohne Installation) | [GitHub Releases](https://github.com/xpack-dev-tools/openocd-xpack/releases) |
| ESPHome (Device Builder in Home Assistant) | Display-Firmware | [esphome.io](https://esphome.io) |
| feine Lötspitze, Flussmittel, Lupe | Umbau mit 0,5-mm-Pinabstand | – |
| *optional* STM32CubeIDE 1.12.1 | Modul-Firmware selbst bauen | [Spiegel beim Autor](https://github.com/deividAlfa/stm32_soldering_iron_controller/releases/tag/CubeIDE_v1.12.1) |

## Umbau am Modul (2 Drähte)

Die OLED-Pads des Moduls hängen an Software-Pins (PB12/PB13). Die serielle Schnittstelle USART3 des STM32 liegt aber auf **PB10/PB11** – die sind auf der Platine nicht verbunden. Zwei dünne Drähte legen sie auf die OLED-Pads:

| von Chip-Pin | an OLED-Pad | Bedeutung |
|---|---|---|
| **Pin 21 = PB10** | **SCL** | Modul **sendet** (TX) |
| **Pin 22 = PB11** | **SDA** | Modul **empfängt** (RX) |

Die Pins liegen auf der Chip-Seite unter **R2** (zum AMS1117), **3. und 4. Pin von oben**. Pin 1 ist der Punkt unten links.

![Pins am Chip](docs/umbau_chip_pins.jpg)

- Kupferlackdraht 0,1–0,2 mm, Enden mit heißem Kolben abisolieren und verzinnen
- viel Flussmittel, Draht nur kurz an den Pin halten, **keine Brücke** – besonders nicht zu **Pin 23 (GND)** daneben
- Drähte mit einem Tropfen Heißkleber fixieren, mit Lupe kontrollieren
- Empfehlung: in die 4 OLED-Pads eine **Buchsenleiste** löten – dann steckt dort wahlweise das OLED oder das Kabel zum ESP

Die Leiterbahnen zu PB12/PB13 müssen **nicht** getrennt werden: die UART-Firmware schaltet diese Pins hochohmig.

| Rückseite | Vorderseite |
|---|---|
| ![Rückseite](docs/board_rueckseite.jpg) | ![Vorderseite](docs/board_vorderseite.jpg) |

**Drähte prüfen** (ST-Link angeschlossen): [`werkzeuge/2_drahttest.cmd`](werkzeuge/2_drahttest.cmd) schaltet die Pads über den Chip und liest PB10/PB11 zurück. Erwartet wird `SDA=1 SCL=0 → PB10=0 PB11=1` und umgekehrt.

## Modul flashen

**Anschluss ST-Link V2 (Nachbau, 10-polig)** an die 4 SWD-Löcher des Moduls (Aufdruck „SWD“/„STM32“). **24 V aus**, OLED ab bzw. abgezogen:

| ST-Link | Modul |
|---|---|
| Pin 2 SWCLK | SWCLK |
| Pin 4 SWDIO | SWDIO |
| Pin 6 GND | GND |
| Pin 8 **3,3 V** | 3,3 V (VCC) – **nicht 5 V!** |

GND und 3,3 V findest du mit dem Durchgangsprüfer (GND = Masse, 3,3 V = Kühlfahne des AMS1117). Bleibt die Verbindung aus: SWDIO und SWCLK tauschen.

1. [xPack OpenOCD](https://github.com/xpack-dev-tools/openocd-xpack/releases) entpacken, in den `.cmd`-Dateien unter [`werkzeuge/`](werkzeuge) den Pfad `OCD=` anpassen
2. **Original sichern:** [`1_original_sichern.cmd`](werkzeuge/1_original_sichern.cmd) – liest zweimal und vergleicht (geht nur, wenn der Ausleseschutz aus ist; bei unseren Modulen war er aus)
3. *(nach dem Umbau)* **Drähte prüfen:** [`2_drahttest.cmd`](werkzeuge/2_drahttest.cmd)
4. **Firmware schreiben:** [`3_modul_flashen.cmd`](werkzeuge/3_modul_flashen.cmd) → muss „**Verified OK**“ melden. Der Chip wird **nicht** komplett gelöscht, Kalibrierung/Einstellungen bleiben
5. Zurück zum Original: [`4_original_zurueck.cmd`](werkzeuge/4_original_zurueck.cmd)

**Wichtig:** Viele ST-Link-Nachbauten haben eine alte Firmware (V2J21…). Dann geht nur der „HLA“-Modus – genau den nutzen die Skripte (`interface/stlink-hla.cfg`, `transport select hla_swd`). Der Chip meldet nur 64 KB, die Firmware braucht aber den zweiten 64-KB-Block – daher `set FLASH_SIZE 0x20000`.

**Erst-Einrichtung (empfohlen):** Vor dem Umbau einmal die offene Firmware von deividAlfa ([KSGER_v2_OLED](https://github.com/deividAlfa/stm32_soldering_iron_controller/releases)) mit OLED aufspielen und im Menü die Spitze **kalibrieren**. Diese Einstellungen übernimmt die UART-Firmware. Die Datei [`modul-firmware/t12_uart_v4.bin`](modul-firmware/t12_uart_v4.bin) ist diese Firmware mit unserer UART-Erweiterung; wie man sie selbst baut, steht in [`modul-firmware/BAUEN.md`](modul-firmware/BAUEN.md).

## Anschlussplan

![Anschlussplan](docs/anschlussplan.svg)

| Waveshare-Leiste | an |
|---|---|
| GPIO 17 (Pin 16) | Modul A Pad **SDA** |
| GPIO 18 (Pin 18) | Modul A Pad **SCL** |
| GPIO 38 (Pin 7) | Modul B Pad **SDA** |
| GPIO 39 (Pin 9) | Modul B Pad **SCL** |
| GND (Pin 3/29) | GND der Module, Drehgeber, DS18B20, Lüfter |
| GPIO 40 / 41 / 42 (Pin 11/13/15) | Drehgeber CLK / DT / SW |
| 3V3 (Pin 31/32) | Drehgeber +, DS18B20 VDD + 4,7 kΩ |
| GPIO 21 (Pin 5) | DS18B20 DATA |
| GPIO 47 (Pin 21) | Netzteil-Lüfter (über AO3400) |
| GPIO 48 (Pin 23) | Absaugung (über AO3400) |
| 5V (Pin 2) | LM2596 5 V (oder USB-C) |

- **VCC der Module NICHT verbinden** – jedes Modul bekommt seine 3,3 V selbst aus den 24 V. Nur GND gemeinsam.
- Beide Seiten arbeiten mit 3,3 V, kein Pegelwandler nötig. Sind TX/RX vertauscht, einfach die zwei Leitungen am ESP tauschen.
- Drehgeber-Modul: **+ an 3,3 V**, nicht 5 V. Dreht er falsch herum: CLK und DT tauschen.

## ESPHome installieren

1. Den Inhalt von [`esphome/`](esphome) nach `/config/esphome/` kopieren: `t12-loetstation.yaml` und den Ordner `t12/` (Hilfsdatei `t12.h` + Sprachdateien `sound/*.wav`)
2. In `t12-loetstation.yaml` oben anpassen: `ha_url` (Adresse deines Home Assistant)
3. `secrets.yaml` braucht `wifi_ssid` und `wifi_password`
4. Profildatei nach `/config/www/t12_profile.yaml` kopieren (siehe unten)
5. Im Device Builder **Install** – beim ersten Mal per USB, danach drahtlos

Getestet mit **ESPHome 2026.11** (ESP-IDF, LVGL 9). Die Sprachdateien wurden mit der Windows-Stimme „Hedda“ erzeugt (16 kHz, mono) – eigene WAVs mit gleichem Namen gehen auch.

## Spitzenprofile (Home Assistant)

Eine einfache Textdatei in Home Assistant: **`/config/www/t12_profile.yaml`** (im Datei-Editor unter `www`). Die Station holt sie über `http://<home-assistant>:8123/local/t12_profile.yaml` – beim Start, alle 10 Minuten und mit **Menü → Festwerte → Neu laden**.

```yaml
# - Name, Temperatur 1, Temperatur 2, Temperatur 3   (°C)
- BC2, 330, 300, 360
- K, 350, 320, 380
- D24, 340, 310, 370
```

| Feld | Bedeutung |
|---|---|
| Name | max. 16 Zeichen, erscheint in der Kachel („A · BC2“) |
| Temperatur 1 | wird beim Auswählen als **Solltemperatur** gesetzt |
| Temperatur 1–3 | liegen dann auf den **drei Festwert-Tasten** |

Regeln: eine Zeile pro Spitze, max. 20 Spitzen, Temperaturen 150–450 °C, Zeilen mit `#` werden ignoriert. Fehlt Temperatur 2/3, wird Temperatur 1 genommen.

**Downloads:** [`t12_profile.yaml`](esphome/www/t12_profile.yaml) (Beispiele + Testwerte) · [`t12_profile_test.yaml`](esphome/www/t12_profile_test.yaml) (nur Testwerte TEST 1–3: 250/260/270, 300/310/320, 355/365/375 – gut am Display erkennbar)

**So testest du:** Testdatei als `t12_profile.yaml` nach `/config/www/` kopieren → Menü → Festwerte → „Neu laden“ → „3 Spitzen aus Home Assistant“. Dann Spitze ziehen und wieder einstecken → Auswahl erscheint → „TEST 1“ wählen → Soll 250 °C, Tasten 250/260/270, Kachel „A · TEST 1“.

Profile ausschalten: Menü → Festwerte → „Spitzenprofile aus HA“. Dann gelten die drei eigenen Festwerte.

## Bedienung und Menüs

### Hauptseite
Kachel antippen: 1× wählen (oranger Rahmen), 2× ein/aus. Oben rechts in der Kachel EIN/AUS, unten Leistung. Die Linie am Rand zeigt die Zeit bis Standby (gelb).

![Hauptseite](docs/01-hauptseite.svg)

### Standby
Im Standby steht das Ziel in Klammern, die Linie wird blau (Zeit bis Schlafen). Griff bewegen weckt den Kolben.

![Standby](docs/02-hauptseite-standby.svg)

### Menü
Über die Taste „Menü“ oder Drehgeber lang drücken. Alle Menüs springen nach 20 s zurück.

![Menü](docs/03-menue.svg)

### Kolben & Standby
Standby-Temperatur, Standby nach, Schlafen nach, Boost und Boost-Dauer – die Werte stehen im Modul und werden beim Verlassen gespeichert. Oben A/B für den Kolben.

![Kolben & Standby](docs/04-kolben-standby.svg)

### Lüfter & Absaugung
Absaugung Auto/immer an/aus, Drehzahl, Nachlauf; Netzteil-Lüfter ab Temperatur X, volle Drehzahl ab Y.

![Lüfter & Absaugung](docs/05-luefter-absaugung.svg)

### Ton & Sprache
Lautstärke, Pieptöne, Sprachausgabe und die einzelnen Ansagen; „Test“ spielt eine Ansage.

![Ton & Sprache](docs/06-ton-sprache.svg)

### Festwerte
Drei eigene Festwerte (ohne Profil), Spitzenprofile an/aus, neu laden und Spitze von Hand wählen.

![Festwerte](docs/07-festwerte.svg)

### System
Verbindung, Spannung, Griff-Temperatur und Fehler der Module, Firmware-Stand, WLAN-Adresse.

![System](docs/08-system.svg)

### Profilauswahl
Erscheint nach einem Spitzenwechsel: Drehgeber dreht die Liste, Drücken übernimmt. Auch per Touch.

![Profilauswahl](docs/09-profilauswahl.svg)

### Einschaltsperre
Ohne Kolben oder Spitze lässt sich nicht einschalten – Hinweis und Ansage.

![Einschaltsperre](docs/10-hinweis-keine-spitze.svg)

Die Bilder werden mit [`docs/gen_bilder.py`](docs/gen_bilder.py) erzeugt (Maße und Farben wie in der Firmware).

## Protokoll Modul ↔ ESP

UART 115200 8N1, Textzeilen. Ausführlich im Kopf von [`modul-firmware/quellcode/uart_remote.c`](modul-firmware/quellcode/uart_remote.c).

| ESP → Modul | Bedeutung |
|---|---|
| `S 330` | Solltemperatur |
| `E 1` / `E 0` | ein / aus (aus = Schlaf, Griff weckt nicht) |
| `M n` | Betriebsart 0 Schlaf · 1 Standby · 2 Betrieb · 3 Boost |
| `G` | Einstellungen lesen → `$CFG,…` |
| `C n w` | Einstellung n setzen (0 Standby-°C, 1 Standby s, 2 Schlafen s, 3 Boost +°C, 4 Boost s) |
| `W` | Einstellungen im Flash speichern → `$SAVED` |
| `P` / `?` | Lebenszeichen / Status sofort |

Modul → ESP alle 200 ms: `$T12,ist,soll,ziel,leistung,modus,fehler,vin_x10,ntc_x10,griff_s,ein,link,modus_s`

Der ESP schickt alle 2 s Solltemperatur und EIN/AUS als Lebenszeichen. Das Modul übernimmt sie **nur bei Änderung** (sonst würden Boost-, Standby- und Schlafzeit ständig neu starten).

## Fehlersuche

| Problem | Lösung |
|---|---|
| OpenOCD „unable to connect“ | SWDIO/SWCLK tauschen; 3,3 V angeschlossen? |
| „only supports deprecated HLA“ | ST-Link-Firmware alt → Skripte nutzen schon HLA |
| Display: „keine Verbindung zum Modul“ | GND verbunden? TX/RX am ESP tauschen; UART-Firmware drauf? |
| Temperatur kurz ~50 °C zu hoch | Kalt-Boost (10 s), Anzeige „Soll 280 (330)“ – normal |
| „lese Einstellungen …“ bleibt | Modul-Firmware älter als v2 → `t12_uart_v4.bin` flashen |
| Zeitlinie fehlt | Modul-Firmware älter als v4 |
| „keine Profile geladen“ | `ha_url` prüfen; Datei unter `/config/www/`? Im Browser `http://<HA>:8123/local/t12_profile.yaml` öffnen |

## Gehäuse

Folgt: eigenes 3D-Druck-Gehäuse (Fusion + STL) im Ordner [`gehaeuse/`](gehaeuse).

## Dateien

```
T12-Station-2-Kolben/
├─ esphome/
│  ├─ t12-loetstation.yaml      ESPHome-Konfiguration (anzahl_kolben: "2")
│  ├─ t12/t12.h                Hilfsfunktionen (Protokoll, Zustände, Profile)
│  ├─ t12/sound/*.wav          Ansagen und Töne
│  └─ www/t12_profile*.yaml    Profildatei + Testdatei
├─ modul-firmware/
│  ├─ t12_uart_v4.bin          fertige Modul-Firmware
│  ├─ quellcode/               uart_remote.c/.h + Patch für user_main.c/settings.c
│  └─ BAUEN.md                 selbst übersetzen
├─ werkzeuge/                  OpenOCD-Skripte: sichern, Drahttest, flashen, zurück
├─ docs/                       Bilder, Anschlussplan, Bild-Generator
└─ gehaeuse/                   folgt (Fusion, STL, Fotos)
```

Grundlage der Modul-Firmware: [deividAlfa/stm32_soldering_iron_controller](https://github.com/deividAlfa/stm32_soldering_iron_controller) (GPL). Unsere Erweiterung (UART-Fernsteuerung) liegt als eigene Dateien + Patch bei.
