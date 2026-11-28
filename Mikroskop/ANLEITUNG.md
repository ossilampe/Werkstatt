# Mikroskop-App – Einrichtung (Raspberry Pi OS Bookworm)

## 1. Pakete
Auf Raspberry Pi OS meist schon vorhanden, sonst:

    sudo apt update
    sudo apt install python3-picamera2 python3-pyqt5 python3-opengl python3-gpiozero cifs-utils

## 2. App kopieren und testen

    mkdir -p ~/mikroskop
    cp mikroskop.py ~/mikroskop/
    chmod +x ~/mikroskop/mikroskop.py
    python3 ~/mikroskop/mikroskop.py

Vorher die alte Software beenden – die Kamera kann nur ein Programm gleichzeitig nutzen.

## 3. SMB-Freigabe einhängen
Zugangsdaten ablegen:

    sudo nano /etc/smb-mikroskop
      username=DEINUSER
      password=DEINPASSWORT
    sudo chmod 600 /etc/smb-mikroskop
    sudo mkdir -p /mnt/mikroskop

In `/etc/fstab` eine Zeile ergänzen (Server/Freigabe anpassen, `uid` = dein Benutzer, meist 1000):

    //192.168.1.10/Mikroskop  /mnt/mikroskop  cifs  credentials=/etc/smb-mikroskop,uid=1000,gid=1000,iocharset=utf8,vers=3.0,nofail,_netdev,x-systemd.automount,x-systemd.idle-timeout=600  0  0

Dann:

    sudo systemctl daemon-reload
    ls /mnt/mikroskop        # hängt die Freigabe automatisch ein

Ist der Server offline, landen Fotos in `~/Bilder/Mikroskop` und werden beim nächsten Foto automatisch nachgeschoben.

## 4. Taster anschließen
Jeder Taster zwischen GPIO-Pin und GND (interner Pull-up, keine Widerstände nötig).

| Funktion | GPIO (BCM) | Pin |
|---|---|---|
| Zoom + (halten = weiter) | 17 | 11 |
| Zoom − (halten = weiter) | 27 | 13 |
| Foto | 22 | 15 |
| Reset 1:1 | 23 | 16 |
| GND | – | 9, 14, 20 … |

Andere Pins: oben im Skript unter `GPIO_PINS` ändern.

## 5. Autostart und alte Software abschalten
Die alte Software findest du meist hier:

    ls ~/.config/autostart/
    cat ~/.config/labwc/autostart ~/.config/wayfire.ini 2>/dev/null | grep -i exec
    crontab -l
    systemctl list-units --type=service | grep -iE "micro|cam"

Dort den alten Eintrag entfernen bzw. auskommentieren und die neue App eintragen:

    mkdir -p ~/.config/autostart
    cp mikroskop.desktop ~/.config/autostart/

## Bedienung
- **Zoom +/−**: Button antippen oder gedrückt halten (bis 8×)
- **Verschieben**: im gezoomten Bild mit dem Finger wischen
- **1:1**: zurück zum Gesamtbild
- **Bild**: öffnet die Bild-Einstellungen (Live-Bild bleibt sichtbar, wird nur kleiner)
  - Helligkeit, Kontrast, Sättigung (0 = Schwarzweiß), Schärfe
  - Belichtung Auto mit Korrektur in EV – oder Manuell mit Belichtungszeit (0,1–500 ms) und Verstärkung
  - Weißabgleich: Auto, Tageslicht, Bewölkt, Innen, Leuchtstoff, Kunstlicht, Glühlampe, **Fixiert** (friert die aktuellen Farben ein)
  - Werte werden in `~/.config/mikroskop.json` gespeichert und beim Start geladen; „Standard“ setzt alles zurück
- **Foto**: speichert genau den sichtbaren Ausschnitt (2028×1520 JPEG) auf den Server
- Tastatur: `+` `−` `0` Leertaste, Pfeiltasten, `Esc`

Einstellungen (Zoomstufe, Pfade, Pins, lokale Kopie behalten) stehen oben in `mikroskop.py`.
