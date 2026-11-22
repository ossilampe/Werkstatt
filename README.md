# Werkstatt

Eigene Geräte und Platinen für die Werkstatt, mit Schaltplan, Platinendaten und Firmware.

| Projekt | Hardware | Wofür | Stand |
|---|---|---|---|
| [T12-Station-2-Kolben](T12-Station-2-Kolben) | Waveshare ESP32-S3 Touch-LCD 3,5″ + 2 × fertige T12-Steuerplatine (STM32 Ver21S) mit eigener UART-Firmware | Lötstation für 2 T12-Kolben: Touch + Drehgeber, Spitzenprofile aus Home Assistant, Sprachausgabe, Lüfter, Absaugung | läuft im 3D-Druck-Gehäuse (mit 1 Modul getestet), Absaugung folgt |
| [T12-Station-1-Kolben](T12-Station-1-Kolben) | wie oben, 1 × T12-Steuerplatine | dieselbe Station für einen Kolben | Konfiguration fertig, Gehäuse wie 2 Kolben |
| [T12-Loetstation](T12-Loetstation) | Waveshare ESP32-S3 Touch-LCD 3,5″ + eigene Platine (KiCad, JLCPCB) | erster Entwurf mit eigener Platine für 2 Kolben | Platine v1.1 fertig, pausiert |

**Hinweis:** WLAN-Daten und Passwörter kommen per `!secret` aus der eigenen `secrets.yaml`. Eine Vorlage liegt jeweils als `secrets.yaml.example` im Projektordner.
