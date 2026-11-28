# Werkstatt

Eigene Geräte und Platinen für die Werkstatt, mit Schaltplan, Platinendaten und Firmware.

| Projekt | Hardware | Wofür | Stand |
|---|---|---|---|
| [T12-Station-2-Kolben](T12-Station-2-Kolben) | Waveshare ESP32-S3 Touch-LCD 3,5″ + 2 × fertige T12-Steuerplatine (STM32 Ver21S) mit eigener UART-Firmware | Lötstation für 2 T12-Kolben: Touch + Drehgeber, Spitzenprofile aus Home Assistant, Sprachausgabe, Lüfter, Absaugung | läuft im 3D-Druck-Gehäuse (mit 1 Modul getestet), Absaugung folgt |
| [T12-Station-1-Kolben](T12-Station-1-Kolben) | wie oben, 1 × T12-Steuerplatine | dieselbe Station für einen Kolben | Konfiguration fertig, Gehäuse wie 2 Kolben |
| [T12-Loetstation](T12-Loetstation) | Waveshare ESP32-S3 Touch-LCD 3,5″ + eigene Platine (KiCad, JLCPCB) | erster Entwurf mit eigener Platine für 2 Kolben | Platine v1.1 fertig, pausiert |
| [E-Last-ZHIYU-ESP32](E-Last-ZHIYU-ESP32) | Elektronische Last ZHIYU ZPB30A1 (60 W) mit freier Firmware + Waveshare ESP32-S3 Touch-LCD 3,5″ | Last per Display und Home Assistant steuern; geplant: Akkutest, Rampentest mit Protokoll | geflasht, Display zeigt Live-Daten; Befehle und Kalibrierung offen |
| [Labornetzteil-XY6020L](Labornetzteil-XY6020L) | 60-V/20-A-Netzteil + XY6020L (Modbus) + Waveshare ESP32-S3 Touch-LCD 3,5″ | Labornetzteil 0–60 V / 0–20 A mit Touch, Schutzgrenzen, Home Assistant | Entwurf: Konfiguration v1 geschrieben, noch nicht aufgebaut |
| [Mikroskop](Mikroskop) | Raspberry Pi 4 + HQ-Kamera + offizielles 7″-Touchdisplay + 4 Taster | Digitales Mikroskop: Zoom bis 8×, Verschieben per Wischen, Bild-Einstellungen, Foto auf SMB-Freigabe | App geschrieben, auf echter Hardware noch nicht getestet |

**Gehäuse der T12-Station zum Drucken:** [MakerWorld](https://makerworld.com/de/models/3663781-t12-lotstation-esp32-s3-touch-display-2-kolben)

**Hinweis:** WLAN-Daten und Passwörter kommen per `!secret` aus der eigenen `secrets.yaml`. Eine Vorlage liegt jeweils als `secrets.yaml.example` im Projektordner.
