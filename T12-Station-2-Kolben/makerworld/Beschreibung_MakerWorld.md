# MakerWorld – Texte zum Einfügen

## Titel

T12-Lötstation mit 3,5″-Touch-Display (ESP32-S3) für 2 Kolben – Gehäuse

## Kurzbeschreibung (Summary)

Gehäuse für eine selbstgebaute T12-Lötstation für zwei Kolben: Waveshare ESP32-S3 3,5″-Touch-Display, Drehknopf, zwei Kolbenablagen, Lüftergitter. Firmware, Schaltpläne und komplette Anleitung auf GitHub.

---

## Beschreibung (Deutsch)

**T12-Lötstation für zwei Kolben – mit Touch-Display, Drehknopf, Sprachausgabe und Home Assistant**

Dieses Gehäuse gehört zu meiner selbstgebauten T12-Lötstation. Die Regelung übernehmen zwei günstige, fertige T12-Steuerplatinen (STM32 „Ver21S“), die eine eigene Firmware bekommen und per UART von einem **Waveshare ESP32-S3-Touch-LCD-3.5** gesteuert werden. Am Modul selbst wird nichts mehr bedient – alles läuft über den Touchscreen und den Drehknopf.

**Was die Station kann**
- 2 Kolben gleichzeitig, große Ist-/Soll-Anzeige, Status in Farbe (heizt, bereit, Standby, schläft, kühlt ab)
- Kachel antippen = auswählen, zweimal = ein/aus; nach Stromausfall bleibt alles aus
- Drehknopf: ±5 °C, kurz drücken = Kolben wechseln, lang = Menü
- Standby, Schlafen und Kalt-Boost; Zeitlinie am Rand zeigt die Zeit bis Standby/Schlafen
- Spitzenprofile aus Home Assistant (Name, 3 Temperaturen, Standby-Werte) – nach dem Spitzenwechsel erscheint automatisch die Auswahl
- Deutsche Sprachausgabe („Kolben A bereit“, „kühlt ab“, „keine Spitze“ …)
- Temperaturgeregelter Netzteil-Lüfter (DS18B20), Anschluss für eine Absaugung mit IR-Handsensor
- Läuft auch ohne WLAN; Profile bleiben im ESP gespeichert

**Gedruckte Teile**
| Teil | Größe |
|---|---|
| Frame unten | 250 × 60 × 169 mm |
| Frame oben (mit Ausschnitten für 2 Kolbenablagen) | 250 × 50 × 169 mm |
| Front (schräg, Display-Ausschnitt, Lautsprecher-Gitter, Loch für Drehgeber) | 250 × 116 × 101 mm |
| Drehknopf | Ø 30 × 22 mm |

**Druckhinweise**
- Die Teile sind 250 mm breit → Druckbett mit mindestens 256 mm (z. B. Bambu Lab X1C / P1S)
- Material: PETG oder ASA empfohlen (Wärme von Netzteil und Kolbenablagen)
- Fusion-360-Datei liegt bei – damit lässt sich das Gehäuse anpassen (z. B. schmaler für einen Kolben)

**Benötigte Elektronik (Auszug)**
- Waveshare ESP32-S3-Touch-LCD-3.5 (nicht die Version „3.5B“)
- 2 × T12-Steuerplatine STM32 Ver21S (KSGER-v2-Bauform) + 2 Drähte Umbau
- Netzteil 24 V ≥ 6 A, 2 × LM2596 (5 V Display, 12 V Lüfter)
- Drehgeber KY-040, DS18B20, 12-V-Lüfter, 2 × IRLML6344, 2 × SB 120
- T12-Griffe (z. B. FX9501), Kolbenablagen, GX12-Buchsen
- ST-Link V2 zum Flashen der Module

**Anleitung, Firmware und Schaltpläne**
Die komplette Anleitung (Umbau der Module, Flashen, Verdrahtung, ESPHome, Spitzenprofile, alle Menüs) liegt als PDF bei und auf GitHub:
https://github.com/ossilampe/Werkstatt/tree/main/T12-Station-2-Kolben

Variante für **einen** Kolben (gleiches Gehäuse): https://github.com/ossilampe/Werkstatt/tree/main/T12-Station-1-Kolben

*Das Gehäuse für die Absaugung (Lüfter + IR-Sensor) folgt.*

Grundlage der Modul-Firmware: deividAlfa/stm32_soldering_iron_controller (GPL).

---

## Description (English)

**T12 soldering station for two irons – touch display, rotary knob, voice output and Home Assistant**

Enclosure for my DIY T12 soldering station. Two cheap ready-made T12 controller boards (STM32 "Ver21S") run a custom firmware and are controlled over UART by a **Waveshare ESP32-S3-Touch-LCD-3.5**. Everything is operated via touchscreen and the rotary knob.

**Features:** 2 irons, large temperature display with colour status, tap a tile to select / tap again to switch on/off, standby/sleep/boost with countdown bar, tip profiles from Home Assistant, German voice output, temperature-controlled PSU fan, connector for a fume extractor with IR hand sensor, works offline.

**Printed parts:** frame bottom (250 × 60 × 169 mm), frame top with cut-outs for 2 iron holders (250 × 50 × 169 mm), slanted front with display opening (250 × 116 × 101 mm), knob (Ø 30 × 22 mm).

**Printing:** parts are 250 mm wide → build plate ≥ 256 mm (e.g. Bambu Lab X1C / P1S). PETG or ASA recommended. Fusion 360 source file included.

**Full guide, firmware and wiring diagrams** (German): included as PDF and on GitHub:
https://github.com/ossilampe/Werkstatt/tree/main/T12-Station-2-Kolben

*Enclosure for the fume extractor follows.*

---

## Tags

T12, Lötstation, soldering station, ESP32, ESP32-S3, ESPHome, Home Assistant, Waveshare, touch display, workshop, Werkstatt, electronics

## Hochzuladende Dateien

- `gehaeuse/stl/Frame_unten.stl`, `Frame_oben.stl`, `Front.stl`, `Drehknopf.stl`
- `gehaeuse/fusion/Loetstation_ESP32_Touch_3_5zoll.f3d`
- `makerworld/T12-Station_Anleitung.pdf` (Anleitung)
- Bilder: `gehaeuse/bilder/foto_front.jpg` (Titelbild), `foto_station.jpg`, `render_vorne.png`, `render_seite.png`, `render_hinten.png`
