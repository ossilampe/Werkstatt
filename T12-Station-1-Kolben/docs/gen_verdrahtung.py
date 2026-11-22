"""Komplettes Verdrahtungsblatt der T12-Station (für die Werkstatt zum Ausdrucken).

Teil 1: Schaltplan Lüfter / Absaugung / DS18B20 (aus luefter_schaltplan.svg)
Teil 2: Stiftleiste des Waveshare-Displays (2 × 16) mit Belegung
Teil 3: Tabelle aller Anschlüsse (GPIO -> Teil -> Anschluss am Teil)

Aufruf: python gen_verdrahtung.py 2   (bzw. 1 für einen Kolben)  -> verdrahtung_komplett.svg
Vorher gen_luefter_schaltplan.py laufen lassen.
"""
import os
import re
import sys

ANZ = int(sys.argv[1]) if len(sys.argv) > 1 else 2
HIER = os.path.dirname(os.path.abspath(__file__))
B = 1200
FONT = "font-family=\"'Segoe UI',Arial,sans-serif\""
SCHWARZ, ROT, BLAU, GRUEN, LILA, ORANGE, TUERKIS, GRAU = "#111111", "#C62828", "#1565C0", "#2E7D32", "#6A1B9A", "#E65100", "#00838F", "#777777"
el = []


def T(x, y, t, s=15, f=SCHWARZ, a="start", b=False):
    el.append('<text x="%g" y="%g" font-size="%g" fill="%s" text-anchor="%s" %s%s>%s</text>'
              % (x, y, s, f, a, FONT, ' font-weight="700"' if b else "", t.replace("&", "&amp;")))


def R(x, y, w, h, fill, stroke="none", sw=0, rx=0):
    el.append('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" stroke="%s" stroke-width="%g"/>'
              % (x, y, w, h, rx, fill, stroke, sw))


# ---------------------------------------------------------------- Teil 1: Lüfter-Schaltplan einbetten
plan = open(os.path.join(HIER, "luefter_schaltplan.svg"), encoding="utf-8").read()
m = re.search(r'viewBox="0 0 (\d+) (\d+)"', plan)
pw, ph = int(m.group(1)), int(m.group(2))
mt = re.search(r'data-teilung="(\d+)"', plan)
teilung = int(mt.group(1)) if mt else None     # Schaltplan auf 2 Blätter aufteilen
innen = plan[plan.index(">") + 1: plan.rindex("</svg>")]
el.append('<svg x="0" y="0" width="%d" height="%d" viewBox="0 0 %d %d">%s</svg>' % (pw, ph, pw, ph, innen))
y0 = ph + 20
el.append('<line x1="30" y1="%d" x2="%d" y2="%d" stroke="#BBBBBB" stroke-width="2" stroke-dasharray="8 6"/>' % (y0 - 10, B - 30, y0 - 10))

# ---------------------------------------------------------------- Teil 2: Stiftleiste
T(30, y0 + 30, "Waveshare ESP32-S3-Touch-LCD-3.5 – Stiftleiste hinten (2 × 16, RM 2,54)", 24, SCHWARZ, b=True)
T(30, y0 + 54, "Ansicht von hinten auf die Leiste, Pin 1 oben links (wie im Waveshare-Pinout). "
               "Farbe = was angeschlossen wird, grau = frei, durchgestrichen = nicht benutzen.", 14, GRAU)

B_AN = ANZ == 2
belegung = {
    1: ("BAT", None, "Akku (nicht benutzt)", "x"),
    2: ("5V", ROT, "5 V vom LM2596 (Display)", "p"),
    3: ("GND", SCHWARZ, "GND gemeinsam", "p"),
    4: ("GND", SCHWARZ, "GND", "p"),
    5: ("GPIO21", LILA, "DS18B20 DQ (+4,7 kΩ nach 3V3)", "u"),
    6: ("GPIO19", None, "USB D− (nicht benutzen)", "x"),
    7: ("GPIO38", BLAU if B_AN else None, "Modul B → Pad SDA (ESP TX)" if B_AN else "frei (Modul B entfällt)", "u" if B_AN else "f"),
    8: ("GPIO20", None, "USB D+ (nicht benutzen)", "x"),
    9: ("GPIO39", BLAU if B_AN else None, "Modul B ← Pad SCL (ESP RX)" if B_AN else "frei (Modul B entfällt)", "u" if B_AN else "f"),
    10: ("GPIO11", None, "frei", "f"),
    11: ("GPIO40", GRUEN, "Drehgeber CLK", "u"),
    12: ("GPIO10", None, "frei", "f"),
    13: ("GPIO41", GRUEN, "Drehgeber DT", "u"),
    14: ("GPIO9", None, "frei", "f"),
    15: ("GPIO42", GRUEN, "Drehgeber SW (Taster)", "u"),
    16: ("GPIO17", ORANGE, "Modul A → Pad SDA (ESP TX)", "u"),
    17: ("GPIO45", None, "Startpin – nicht benutzen", "x"),
    18: ("GPIO18", ORANGE, "Modul A ← Pad SCL (ESP RX)", "u"),
    19: ("GPIO46", None, "Startpin – nicht benutzen", "x"),
    20: ("BOOT", None, "BOOT-Taste GPIO0", "x"),
    21: ("GPIO47", TUERKIS, "Netzteil-Lüfter: 100 Ω → Gate Q1", "u"),
    22: ("RST", None, "Reset", "x"),
    23: ("GPIO48", TUERKIS, "Absaugung: 100 Ω → Gate Q2", "u"),
    24: ("PWR", None, "Ein-Taste", "x"),
    25: ("GPIO43", None, "frei (TXD)", "f"),
    26: ("GPIO7", GRAU, "I²C SCL – intern (Touch), nicht belegen", "x"),
    27: ("GPIO44", "#AD1457", "IR-Sensor: 1 kΩ → GX12-5 Pin 4", "u"),
    28: ("GPIO8", GRAU, "I²C SDA – intern (Touch), nicht belegen", "x"),
    29: ("GND", SCHWARZ, "GND", "p"),
    30: ("GND", SCHWARZ, "GND", "p"),
    31: ("3V3", ROT, "3,3 V: Drehgeber +, DS18B20 VDD", "p"),
    32: ("3V3", ROT, "3,3 V: IR-Sensor (GX12-5 Pin 3)", "p"),
}
yl = y0 + 80
LX, RX = 520, 600                       # Mitte der beiden Pinreihen
R(LX - 30, yl - 10, RX - LX + 60, 16 * 34 + 10, "#2B2B2B", rx=6)
for row in range(16):
    for spalte, pin in ((0, 2 * row + 1), (1, 2 * row + 2)):
        name, farbe, text, art = belegung[pin]
        y = yl + row * 34 + 12
        x = LX if spalte == 0 else RX
        el.append('<rect x="%g" y="%g" width="16" height="16" fill="#D4AF37" stroke="#7A6200" stroke-width="1"/>' % (x - 8, y - 8))
        nr_x = x + 14 if spalte == 0 else x - 14          # Nummern zwischen den Pinreihen
        T(nr_x, y + 5, str(pin), 13, "#FFFFFF", "start" if spalte == 0 else "end", True)
        f = farbe or "#9E9E9E"
        if spalte == 0:
            R(LX - 175, y - 13, 120, 26, f if art != "x" else "#E0E0E0", rx=5)
            T(LX - 115, y + 5, name, 14, "#FFFFFF" if art != "x" else "#9E9E9E", "middle", True)
            T(LX - 185, y + 5, text, 14, f if art == "u" or art == "p" else GRAU, "end", art == "u")
            if art == "x":
                el.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#9E9E9E" stroke-width="2"/>' % (LX - 172, y, LX - 58, y))
        else:
            R(RX + 55, y - 13, 120, 26, f if art != "x" else "#E0E0E0", rx=5)
            T(RX + 115, y + 5, name, 14, "#FFFFFF" if art != "x" else "#9E9E9E", "middle", True)
            T(RX + 185, y + 5, text, 14, f if art == "u" or art == "p" else GRAU, "start", art == "u")
            if art == "x":
                el.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#9E9E9E" stroke-width="2"/>' % (RX + 58, y, RX + 172, y))
yt = yl + 16 * 34 + 30
T(30, yt, "Weitere Anschlüsse am Display: Lautsprecher an den 2-poligen MX1.25-Stecker „SPK“ · USB-C nur zum ersten Flashen (oder als 5-V-Versorgung).", 14, GRAU)

# ---------------------------------------------------------------- Teil 3: Tabelle
yt += 30
grenze_23 = yt
el.append('<line x1="30" y1="%d" x2="%d" y2="%d" stroke="#BBBBBB" stroke-width="2" stroke-dasharray="8 6"/>' % (yt, B - 30, yt))
yt += 38
T(30, yt, "Alle Verbindungen", 24, SCHWARZ, b=True)
zeilen = [
    ("Display", "Teil", "Anschluss am Teil", "Hinweis", None),
    ("GPIO17 (Pin 16)", "T12-Modul A", "OLED-Pad SDA (= PB11, RX)", "Umbau: Draht Chip-Pin 22 → Pad SDA", ORANGE),
    ("GPIO18 (Pin 18)", "T12-Modul A", "OLED-Pad SCL (= PB10, TX)", "Umbau: Draht Chip-Pin 21 → Pad SCL", ORANGE),
    ("GND (Pin 3)", "T12-Modul A", "OLED-Pad GND", "OLED-Pad VCC NICHT verbinden", SCHWARZ),
]
if B_AN:
    zeilen += [
        ("GPIO38 (Pin 7)", "T12-Modul B", "OLED-Pad SDA (= PB11, RX)", "gleicher Umbau wie Modul A", BLAU),
        ("GPIO39 (Pin 9)", "T12-Modul B", "OLED-Pad SCL (= PB10, TX)", "", BLAU),
        ("GND (Pin 29)", "T12-Modul B", "OLED-Pad GND", "VCC NICHT verbinden", SCHWARZ),
    ]
zeilen += [
    ("GPIO40 (Pin 11)", "Drehgeber KY-040", "CLK", "dreht falsch herum → CLK/DT tauschen", GRUEN),
    ("GPIO41 (Pin 13)", "Drehgeber KY-040", "DT", "", GRUEN),
    ("GPIO42 (Pin 15)", "Drehgeber KY-040", "SW", "Taster", GRUEN),
    ("3V3 (Pin 31)", "Drehgeber KY-040", "+", "NICHT 5 V", ROT),
    ("GND (Pin 30)", "Drehgeber KY-040", "GND / −", "", SCHWARZ),
    ("GPIO21 (Pin 5)", "DS18B20", "DQ (gelb)", "4,7 kΩ von DQ nach 3V3", LILA),
    ("3V3 (Pin 32)", "DS18B20", "VDD (rot)", "", ROT),
    ("GND (Pin 4)", "DS18B20", "GND (schwarz)", "", SCHWARZ),
    ("GPIO47 (Pin 21)", "Netzteil-Lüfter", "über 100 Ω an Gate Q1", "100 kΩ Gate–GND, SB 120 parallel", TUERKIS),
    ("GPIO48 (Pin 23)", "Absaugung (GX12-5 Pin 1/2)", "über 100 Ω an Gate Q2", "Pin 1 = +12 V (F1), Pin 2 = Drain Q2, SB 120 dazwischen", TUERKIS),
    ("GPIO44 (Pin 27)", "IR-Sensor (GX12-5)", "über 1 kΩ an Pin 4 → OUT", "10 kΩ von GPIO44 nach GND", "#AD1457"),
    ("3V3 (Pin 32)", "IR-Sensor (GX12-5)", "Pin 3 → VCC", "Sensor nur mit 3,3 V betreiben", ROT),
    ("GND (Pin 30)", "IR-Sensor (GX12-5)", "Pin 5 → GND", "", SCHWARZ),
    ("5V (Pin 2)", "LM2596 (Display) 24→5 V", "OUT+", "vor dem Anschließen auf 5,0 V einstellen", ROT),
    ("–", "LM2596 (Lüfter) 24→12 V", "OUT+ → +12 V Lüfter", "auf 12 V einstellen; IN von 24 V", ROT),
    ("GND (Pin 3/29)", "beide LM2596, Netzteil", "OUT− / −", "alle GND verbinden", SCHWARZ),
    ("SPK-Stecker", "Lautsprecher", "2-polig MX1.25", "4–8 Ω, 1–3 W", GRAU),
]
spalten = [(30, 190), (230, 190), (430, 280), (720, 450)]
yt += 20
for i, z in enumerate(zeilen):
    y = yt + i * 28
    kopf = i == 0
    if kopf:
        R(30, y, B - 60, 26, "#333333", rx=4)
    elif i % 2:
        R(30, y, B - 60, 26, "#F5F5F5", rx=2)
    farbe = z[4] or SCHWARZ
    for (x, w), txt, k in zip(spalten, z[:4], range(4)):
        f = "#FFFFFF" if kopf else (farbe if k == 0 else SCHWARZ)
        T(x + 8, y + 18, txt, 14, f, b=kopf or k == 0)
hoehe = yt + len(zeilen) * 28 + 40
T(30, hoehe - 14, "T12-Station %s · Stand 2026-11-20 · github.com/ossilampe/Werkstatt" % ("2 Kolben" if B_AN else "1 Kolben"), 12, GRAU)

svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d"><rect width="%d" height="%d" fill="#FFFFFF"/>'
       % (B, hoehe, B, hoehe, B, hoehe)) + "".join(el) + "</svg>\n"
open(os.path.join(HIER, "verdrahtung_komplett.svg"), "w", encoding="utf-8").write(svg)
print("verdrahtung_komplett.svg", B, "x", hoehe)

# ---------------------------------------------------------------- Druckvorlage: jeder Teil auf ein A4-Blatt quer
# PDF daraus: Edge/Chrome "Drucken -> Als PDF" oder
#   msedge --headless --no-pdf-header-footer --print-to-pdf=verdrahtung_komplett.pdf verdrahtung_druck.html
titel = "T12-Station %s" % ("2 Kolben" if B_AN else "1 Kolben")
teile = ([(0, teilung, "Schaltplan Versorgung, Lüfter, DS18B20"),
          (teilung, y0 - 10, "Absaugung: GX12-5, Kabel, IR-Sensor")] if teilung else
         [(0, y0 - 10, "Schaltplan Lüfter, Absaugung, IR-Sensor, DS18B20")]) + [
         (y0 - 10, grenze_23, "Display-Stiftleiste – was an welchen Pin kommt"),
         (grenze_23, hoehe, "Alle Verbindungen")]
seiten = []
for n, (a, b, name) in enumerate(teile, 1):
    w, h = B - 40, b - a - 5
    # inneres <svg> schneidet auf genau diesen Teil zu (sonst schaut im Rand der Nachbarteil durch)
    seiten.append('<div class="seite"><svg viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid meet">'
                  '<svg x="0" y="0" width="%d" height="%d" viewBox="20 %d %d %d" overflow="hidden">'
                  '<image href="verdrahtung_komplett.svg" x="0" y="0" width="%d" height="%d"/></svg></svg>'
                  '<div class="fuss">%s · Werkstattblatt %d/%d · %s · Stand 2026-11-20</div></div>'
                  % (w, h, w, h, a + 5, w, h, B, hoehe, titel, n, len(teile), name))
html = ("<!doctype html><html><head><meta charset='utf-8'><title>%s – Verdrahtung</title><style>"
        "@page{size:A4 landscape;margin:8mm}html,body{margin:0;padding:0;background:#fff;font-family:Segoe UI,Arial,sans-serif}"
        ".seite{width:281mm;height:193mm;display:flex;flex-direction:column;page-break-after:always;break-after:page}"
        ".seite:last-child{page-break-after:auto;break-after:auto}"
        ".seite svg{flex:1;width:100%%;min-height:0}.fuss{font-size:9pt;color:#777;text-align:right;padding-top:2mm}"
        "</style></head><body>%s</body></html>\n") % (titel, "".join(seiten))
open(os.path.join(HIER, "verdrahtung_druck.html"), "w", encoding="utf-8").write(html)
print("verdrahtung_druck.html", [(a, b) for a, b, _ in teile])
