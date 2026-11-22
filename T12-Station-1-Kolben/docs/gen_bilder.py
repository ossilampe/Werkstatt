"""Zeichnet die Bildschirmseiten der T12-Station (480 x 320) und den Anschlussplan als SVG.

Positionen, Farben und Texte entsprechen esphome/t12-loetstation.yaml.
Aufruf:  python gen_bilder.py 2   (zwei Kolben)   bzw.   python gen_bilder.py 1   (ein Kolben)
Die SVG-Dateien landen im selben Ordner wie dieses Skript.
"""
import os
import sys

ANZ = int(sys.argv[1]) if len(sys.argv) > 1 else 2
W, H = 480, 320
OR, GR, KACHEL, KNOPF = "#FF8C00", "#8C8C8C", "#1F1F1F", "#3A3A3A"
GELB, BLAU, GRUEN, HBLAU, ROT, VIOL = "#FFC107", "#4A90E2", "#3CC85A", "#4FC3F7", "#E53935", "#C77DFF"
FONT = "font-family=\"'Roboto','Segoe UI',Arial,sans-serif\""
MONO = "font-family=\"'Roboto Mono','Consolas',monospace\""


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Seite:
    def __init__(self, name, titel):
        self.name, self.titel, self.el = name, titel, []

    def rect(self, x, y, w, h, fill, r=0, stroke=None, sw=0, opa=1):
        st = ' stroke="%s" stroke-width="%g"' % (stroke, sw) if stroke else ""
        self.el.append('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" fill-opacity="%g"%s/>'
                       % (x, y, w, h, r, fill, opa, st))

    def text(self, x, y, t, size=20, fill="#FFFFFF", anchor="start", bold=False, mono=False):
        b = ' font-weight="600"' if bold else ""
        self.el.append('<text x="%g" y="%g" font-size="%g" fill="%s" text-anchor="%s" %s%s>%s</text>'
                       % (x, y, size, fill, anchor, MONO if mono else FONT, b, esc(t)))

    def knopf(self, x, y, w, h, t, fill=KNOPF, color="#FFFFFF", size=20):
        self.rect(x, y, w, h, fill, 8)
        self.text(x + w / 2, y + h / 2 + size * 0.36, t, size, color, "middle")

    def schalter(self, x, y, an):
        self.rect(x, y, 56, 28, OR if an else "#555555", 14)
        self.el.append('<circle cx="%g" cy="%g" r="11" fill="#FFFFFF"/>' % (x + (42 if an else 14), y + 14))

    def zurueck(self):
        self.knopf(W - 128, 0, 124, 40, "< Zurück", size=16)

    def zeile(self, y, h, name, wert, plusminus=True, wert_farbe="#FFFFFF"):
        self.rect(8, y, 464, h, KACHEL, 8)
        self.text(20, y + h / 2 + 7, name, 20)
        if plusminus:
            self.text(8 + 464 - 116, y + h / 2 + 7, wert, 20, wert_farbe, "end")
            self.knopf(8 + 464 - 106, y + (h - 36) / 2, 48, 36, "−")
            self.knopf(8 + 464 - 54, y + (h - 36) / 2, 48, 36, "+")
        else:
            self.text(8 + 464 - 12, y + h / 2 + 7, wert, 20, wert_farbe, "end")

    def svg(self):
        r = 14
        kopf = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%d %d %d %d" width="%d" height="%d">'
                % (-r, -r, W + 2 * r, H + 2 * r + 26, (W + 2 * r) * 1.5, (H + 2 * r + 26) * 1.5))
        geh = ('<rect x="%d" y="%d" width="%d" height="%d" rx="16" fill="#2B2B2B"/>'
               '<rect x="0" y="0" width="%d" height="%d" fill="#000000"/>' % (-r, -r, W + 2 * r, H + 2 * r, W, H))
        unter = ('<text x="%g" y="%g" font-size="13" fill="#777777" text-anchor="middle" %s>%s</text>'
                 % (W / 2, H + r + 19, FONT, esc(self.titel)))
        return kopf + geh + "".join(self.el) + unter + "</svg>\n"


# ---------------------------------------------------------------- Hauptseite
def kachel(s, x, w, name, ein, ist, soll, status, farbe, leistung, gewaehlt, linie=None, ist_grau=False):
    s.rect(x, 36, w, 228, KACHEL, 10, OR if gewaehlt else KACHEL, 3)
    s.text(x + 14, 62, name, 20, GR)
    s.text(x + w - 14, 60, "EIN" if ein else "AUS", 16, GRUEN if ein else GR, "end")
    m = x + w / 2
    s.text(m, 146, ist, 64, GR if ist_grau else "#FFFFFF", "middle", True, mono=True)
    s.text(m, 186, soll, 24, "#FFFFFF", "middle")
    s.text(m, 216, status, 16, farbe, "middle")
    s.rect(x + 12, 232, w - 30, 14, "#333333", 7)
    if leistung:
        s.rect(x + 12, 232, (w - 30) * leistung / 100.0, 14, OR, 7)
    if linie:                                     # Restzeit-Linie am Außenrand
        anteil, lfarbe, links = linie
        hl = 222 * anteil
        lx = x + 3 if links else x + w - 8
        s.rect(lx, 39 + 222 - hl, 5, hl, lfarbe, 2)


def tasten(s, werte):
    for i, t in enumerate(werte):
        s.knopf(8 + i * 118, 272, 110, 42, "%d °C" % t)
    s.knopf(362, 272, 110, 42, "Menü", color=OR)


def hauptseite():
    s = Seite("01-hauptseite", "Kachel 1× tippen = wählen, 2× = ein/aus · gelb = Zeit bis Standby")
    s.text(10, 26, "T12 Lötstation", 20, OR)
    s.text(W - 10, 24, "Absaugung 60 %   NT 38 °C", 16, GR, "end")
    if ANZ == 2:
        kachel(s, 8, 228, "A · BC2", True, "331°", "Soll 330 °C", "BEREIT", GRUEN, 18, True, (0.62, GELB, True))
        kachel(s, 244, 228, "Kolben B", False, "112°", "Soll 300 °C", "AUS – KÜHLT AB", HBLAU, 0, False, None)
    else:
        kachel(s, 8, 464, "A · BC2", True, "331°", "Soll 330 °C", "BEREIT", GRUEN, 18, True, (0.62, GELB, True))
    tasten(s, (330, 300, 360))
    return s


def hauptseite_standby():
    s = Seite("02-hauptseite-standby", "Standby: Ziel in Klammern · blau = Zeit bis Schlafen · Griff weckt")
    s.text(10, 26, "T12 Lötstation", 20, OR)
    s.text(W - 10, 24, "NT 36 °C", 16, GR, "end")
    if ANZ == 2:
        kachel(s, 8, 228, "A · BC2", True, "186°", "Soll 330 (180) °C", "STANDBY", BLAU, 6, False, (0.4, BLAU, True))
        kachel(s, 244, 228, "B · K", True, "352°", "Soll 350 °C", "BEREIT", GRUEN, 22, True, (0.85, GELB, False))
        tasten(s, (350, 320, 380))
    else:
        kachel(s, 8, 464, "A · BC2", True, "186°", "Soll 330 (180) °C", "STANDBY", BLAU, 6, True, (0.4, BLAU, True))
        tasten(s, (330, 300, 360))
    return s


# ---------------------------------------------------------------- Menü
def menue():
    s = Seite("03-menue", "Menü: Taste „Menü“ oder Drehgeber lang · nach 20 s zurück")
    s.text(10, 28, "Menü", 20, OR)
    s.zurueck()
    kach = [(8, 42, 228, OR, "Kolben & Standby", "Standby 180 °C"),
            (244, 42, 228, HBLAU, "Lüfter & Absaugung", "Absaugung Auto + Hand · 60 %"),
            (8, 134, 228, GRUEN, "Ton & Sprache", "Lautstärke 70 % · Ansagen an"),
            (244, 134, 228, VIOL, "Festwerte", "280 · 330 · 380 °C · Profile"),
            (8, 226, 464, GR, "System", "Module · WLAN · Firmware")]
    for x, y, w, f, t, info in kach:
        s.rect(x, y, w, 86, KACHEL, 10)
        s.rect(x, y, 6, 86, f, 3)
        s.text(x + 20, y + 32, t, 20)
        s.text(x + 20, y + 70, info, 16, GR)
    return s


def kolben_standby():
    s = Seite("04-kolben-standby", "Werte liegen im Modul, gespeichert beim Verlassen der Seite")
    s.text(10, 28, "Kolben & Standby", 20, OR)
    if ANZ == 2:
        s.knopf(170, 2, 76, 32, "A", OR, "#000000", 16)
        s.knopf(252, 2, 76, 32, "B", size=16)
    s.zurueck()
    for i, (n, w) in enumerate([("Standby-Temperatur", "180 °C"), ("Standby nach", "3 min"), ("Schlafen nach", "10 min"),
                                ("Boost", "+50 °C"), ("Boost-Dauer", "60 s")]):
        s.zeile(42 + i * 50, 44, n, w)
    s.text(12, 310, "im Modul gespeichert", 16, GR)
    return s


def luefter():
    s = Seite("05-luefter-absaugung", "Absaugung: Auto → Hand (IR) → Auto + Hand → Immer an → Aus, je eigener Nachlauf")
    s.text(10, 28, "Lüfter & Absaugung", 20, OR)
    s.zurueck()
    s.rect(8, 42, 464, 36, KACHEL, 8)
    s.text(20, 67, "Absaugung", 20)
    s.knopf(8 + 464 - 176, 45, 170, 30, "Auto + Hand", color=HBLAU)
    s.zeile(80, 36, "Drehzahl", "60 %")
    s.zeile(118, 36, "Nachlauf Kolben", "10 s")
    s.zeile(156, 36, "Nachlauf Hand (IR)", "30 s")
    s.text(14, 212, "Absaugung läuft gerade mit 60 % · Hand erkannt", 16, GR)
    s.zeile(216, 36, "Netzteil-Lüfter ab", "35 °C")
    s.zeile(254, 36, "volle Drehzahl ab", "50 °C")
    s.text(14, 310, "Netzteil 38.4 °C – Lüfter 44 %", 16, GR)
    return s


def ton():
    s = Seite("06-ton-sprache", "Lautsprecher des Displays, Ansagen mit deutscher Stimme")
    s.text(10, 28, "Ton & Sprache", 20, OR)
    s.knopf(200, 2, 120, 32, "Test", size=16)
    s.zurueck()
    s.zeile(42, 40, "Lautstärke", "70 %")
    for i, (t, an) in enumerate([("Pieptöne und Klicks", True), ("Sprachausgabe", True), ("Ansage „Kolben bereit“", True),
                                 ("Ansage Standby / Aus / Schlafen", True), ("Ansage Fehler / keine Spitze", True)]):
        y = 88 + i * 46
        s.rect(8, y, 464, 40, KACHEL, 8)
        s.text(20, y + 27, t, 20)
        s.schalter(8 + 464 - 66, y + 6, an)
    return s


def festwerte():
    s = Seite("07-festwerte", "Eigene Tasten (ohne Profil) und Spitzenprofile aus Home Assistant")
    s.text(10, 28, "Festwerte", 20, OR)
    s.zurueck()
    for i, w in enumerate((280, 330, 380)):
        s.zeile(40 + i * 48, 44, "Taste %d" % (i + 1), "%d °C" % w)
    s.rect(8, 184, 464, 40, KACHEL, 8)
    s.text(20, 211, "Spitzenprofile aus HA", 20)
    s.schalter(8 + 464 - 66, 190, True)
    s.rect(8, 228, 464, 40, KACHEL, 8)
    s.text(20, 254, "7 Spitzen aus Home Assistant", 16, GR)
    s.knopf(8 + 464 - 156, 232, 150, 32, "Neu laden", size=16)
    if ANZ == 2:
        s.knopf(8, 274, 228, 40, "Spitze A wählen", size=16)
        s.knopf(244, 274, 228, 40, "Spitze B wählen", size=16)
    else:
        s.knopf(8, 274, 464, 40, "Spitze wählen", size=16)
    return s


def system():
    s = Seite("08-system", "System: Module, Spannung, Fehler, Firmware, WLAN")
    s.text(10, 28, "System", 20, OR)
    s.zurueck()
    zeilen = ["Modul A: verbunden, 24.1 V, Griff 27 °C", "   Fehler 0, bewegt vor 4 s"]
    if ANZ == 2:
        zeilen += ["Modul B: verbunden, 24.1 V, Griff 26 °C", "   Fehler 0, bewegt vor 51 s"]
    zeilen += ["", "Firmware 2026.11.20", "WLAN 192.168.1.xx"]
    for i, z in enumerate(zeilen):
        s.text(14, 74 + i * 26, z, 20)
    return s


def profilauswahl():
    s = hauptseite()
    s.name, s.titel = "09-profilauswahl", "Nach Spitzenwechsel: Drehgeber wählt, Drücken übernimmt"
    s.rect(0, 0, W, H, "#000000", 0, opa=0.7)
    s.rect(40, 15, 400, 290, "#262626", 14, OR, 3)
    s.text(240, 44, "Kolben A – welche Spitze?", 20, OR, "middle")
    s.rect(70, 58, 340, 172, KACHEL, 6)
    for i, t in enumerate(["TEST 1  (250 °C)", "TEST 2  (300 °C)", "BC2  (330 °C)", "K  (350 °C)"]):
        y = 66 + i * 40
        if i == 2:
            s.rect(72, y, 336, 40, OR, 4)
        s.text(240, y + 29, t, 24, "#000000" if i == 2 else "#BBBBBB", "middle")
    s.knopf(46, 247, 150, 44, "Abbrechen", size=16)
    s.knopf(284, 247, 150, 44, "Übernehmen", OR, "#000000")
    return s


def hinweis():
    s = hauptseite()
    s.name, s.titel = "10-hinweis-keine-spitze", "Ohne Lötkolben/Spitze: Hinweis + Ansage, Kolben bleibt aus"
    s.rect(40, 95, 400, 130, "#262626", 14, GELB, 3)
    s.text(240, 152, "Kolben A: kein Lötkolben", 20, GELB, "middle")
    s.text(240, 180, "oder keine Spitze eingesteckt", 20, GELB, "middle")
    return s


# ---------------------------------------------------------------- Anschlussplan
def anschlussplan():
    b, h = 1100, 790 if ANZ == 2 else 700
    el = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">' % (b, h, b, h),
          '<rect width="%d" height="%d" fill="#FFFFFF"/>' % (b, h)]

    def box(x, y, w, hh, titel, farbe, zeilen=()):
        el.append('<rect x="%d" y="%d" width="%d" height="%d" rx="10" fill="#FAFAFA" stroke="%s" stroke-width="3"/>' % (x, y, w, hh, farbe))
        el.append('<text x="%d" y="%d" font-size="17" font-weight="700" fill="%s" %s>%s</text>' % (x + 12, y + 24, farbe, FONT, esc(titel)))
        for i, z in enumerate(zeilen):
            el.append('<text x="%d" y="%d" font-size="14" fill="#333333" %s>%s</text>' % (x + 12, y + 46 + i * 19, FONT, esc(z)))

    def linie(x1, y1, x2, y2, farbe, text=""):
        el.append('<path d="M%d %d C %d %d %d %d %d %d" fill="none" stroke="%s" stroke-width="3"/>'
                  % (x1, y1, (x1 + x2) / 2, y1, (x1 + x2) / 2, y2, x2, y2, farbe))
        if text:
            el.append('<text x="%d" y="%d" font-size="13" fill="%s" text-anchor="middle" %s>%s</text>'
                      % ((x1 + x2) / 2, (y1 + y2) / 2 - 6, farbe, FONT, esc(text)))

    # Waveshare-Leiste
    pins = [("5V", 2, "#C62828"), ("GND", 3, "#000000"), ("GPIO21", 5, "#6A1B9A"), ("GPIO38", 7, "#1565C0"),
            ("GPIO39", 9, "#1565C0"), ("GPIO40", 11, "#2E7D32"), ("GPIO41", 13, "#2E7D32"), ("GPIO42", 15, "#2E7D32"),
            ("GPIO17", 16, "#E65100"), ("GPIO18", 18, "#E65100"), ("GPIO47", 21, "#00838F"), ("GPIO48", 23, "#00838F"),
            ("GPIO44", 27, "#AD1457"), ("3V3", 31, "#C62828")]
    if ANZ == 1:
        pins = [p for p in pins if p[0] not in ("GPIO38", "GPIO39")]
    box(40, 30, 300, 60 + len(pins) * 40, "Waveshare ESP32-S3 Touch-LCD 3.5", "#333333", ["Stiftleiste hinten (2 × 16, RM 2,54)"])
    py = {}
    for i, (n, nr, f) in enumerate(pins):
        y = 100 + i * 40
        py[n] = y
        el.append('<rect x="250" y="%d" width="90" height="26" rx="5" fill="%s"/>' % (y - 18, f))
        el.append('<text x="295" y="%d" font-size="14" fill="#FFFFFF" text-anchor="middle" font-weight="600" %s>%s</text>' % (y, FONT, n))
        el.append('<text x="240" y="%d" font-size="13" fill="#666" text-anchor="end" %s>Pin %d</text>' % (y, FONT, nr))

    # Module
    box(640, 30, 420, 130, "T12-Modul A (Ver21S, UART-Firmware)", "#E65100",
        ["OLED-Pads J1:  SCL = PB10 (TX)   SDA = PB11 (RX)", "GND verbinden · VCC NICHT verbinden", "24 V an J3 (+) · Kolben am GX12 / J4"])
    linie(340, py["GPIO17"], 640, 95, "#E65100")
    linie(340, py["GPIO18"], 640, 115, "#E65100")
    linie(340, py["GND"], 640, 135, "#000000")
    yb = 180
    if ANZ == 2:
        box(640, yb, 420, 110, "T12-Modul B", "#1565C0", ["SCL → GPIO39 (RX)   SDA ← GPIO38 (TX)", "GND verbinden · VCC NICHT verbinden"])
        linie(340, py["GPIO38"], 640, yb + 45, "#1565C0")
        linie(340, py["GPIO39"], 640, yb + 65, "#1565C0")
        linie(340, py["GND"], 640, yb + 85, "#000000")
        yb += 130
    box(640, yb, 420, 100, "Drehgeber-Modul KY-040", "#2E7D32", ["CLK → GPIO40 · DT → GPIO41 · SW → GPIO42", "+ → 3V3 (nicht 5 V!) · − → GND"])
    for n, dy in (("GPIO40", 40), ("GPIO41", 55), ("GPIO42", 70)):
        linie(340, py[n], 640, yb + dy, "#2E7D32")
    yb += 120
    box(640, yb, 420, 80, "DS18B20 (am Netzteil)", "#6A1B9A", ["DATA → GPIO21 · 4,7 kΩ von DATA nach 3V3", "VDD → 3V3 · GND → GND"])
    linie(340, py["GPIO21"], 640, yb + 45, "#6A1B9A")
    yb += 100
    box(640, yb, 420, 110, "Lüfter 12 V (je IRLML6344 low-side)", "#00838F",
        ["GPIO47 → 100 Ω → Gate (100 kΩ Gate–GND) → Netzteil-Lüfter", "GPIO48 → 100 Ω → Gate → Absaugung (GX12-5 Pin 1/2)", "SB 120 Freilauf parallel zum Lüfter · 12 V aus LM2596"])
    linie(340, py["GPIO47"], 640, yb + 45, "#00838F")
    linie(340, py["GPIO48"], 640, yb + 65, "#00838F")
    yb += 130
    box(640, yb, 420, 80, "IR-Sensor Absaugung (GX12-5 Pin 3–5)", "#AD1457",
        ["OUT → 1 kΩ → GPIO44 · 10 kΩ GPIO44 → GND", "Pin 3 VCC → 3V3 (nicht 5 V!) · Pin 4 OUT · Pin 5 GND"])
    linie(340, py["GPIO44"], 640, yb + 45, "#AD1457")
    # Versorgung
    yv = 100 + len(pins) * 40 + 20
    box(40, yv, 560, 80, "Versorgung", "#C62828",
        ["24 V Netzteil → Modul(e) J3 · LM2596 24→5 V → Waveshare 5V/GND (oder USB-C)",
         "LM2596 24→12 V → Lüfter · alle GND verbunden"])
    linie(340, py["5V"], 600, yv + 40, "#C62828")
    el.append("</svg>\n")
    return "anschlussplan", "".join(el)


if __name__ == "__main__":
    ziel = os.path.dirname(os.path.abspath(__file__))
    for f in (hauptseite, hauptseite_standby, menue, kolben_standby, luefter, ton, festwerte, system, profilauswahl, hinweis):
        s = f()
        open(os.path.join(ziel, s.name + ".svg"), "w", encoding="utf-8").write(s.svg())
        print(s.name)
    n, inhalt = anschlussplan()
    open(os.path.join(ziel, n + ".svg"), "w", encoding="utf-8").write(inhalt)
    print(n)
