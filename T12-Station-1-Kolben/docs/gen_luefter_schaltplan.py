"""Schaltplan Versorgung/Lüfter/Absaugung (GX12-5 + IR-Sensor)/DS18B20 für die T12-Station als SVG (docs/luefter_schaltplan.svg).

Bauteile aus dem Lager: IRLML6344 (N-MOSFET, SOT-23, logic level), SB 120 (Schottky 1 A / 20 V),
100 Ω, 100 kΩ, 4,7 kΩ, 1 kΩ, 10 kΩ, DS18B20, LM2596-Modul, GX12-5 (Absaugung + IR-Sensor), MINI TR 1 A.
"""
import os

B, H = 1200, 1490
el = []
FONT = "font-family=\"'Segoe UI',Arial,sans-serif\""
SCHWARZ, ROT, BLAU, GRUEN, LILA, GRAU = "#111111", "#C62828", "#1565C0", "#2E7D32", "#6A1B9A", "#777777"


def L(*pts, f=SCHWARZ, w=2.2):
    el.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%g" stroke-linejoin="round"/>'
              % (" ".join("%g,%g" % p for p in pts), f, w))


def T(x, y, t, s=15, f=SCHWARZ, a="start", b=False):
    el.append('<text x="%g" y="%g" font-size="%g" fill="%s" text-anchor="%s" %s%s>%s</text>'
              % (x, y, s, f, a, FONT, ' font-weight="700"' if b else "", t.replace("&", "&amp;")))


def punkt(x, y, f=SCHWARZ):
    el.append('<circle cx="%g" cy="%g" r="4.5" fill="%s"/>' % (x, y, f))


def masse(x, y):
    L((x, y), (x, y + 12))
    L((x - 12, y + 12), (x + 12, y + 12), w=2.5)
    L((x - 7, y + 17), (x + 7, y + 17), w=2.2)
    L((x - 3, y + 22), (x + 3, y + 22), w=2)


def widerstand_v(x, y1, y2, name, wert, f=SCHWARZ):     # senkrecht
    m = (y1 + y2) / 2
    L((x, y1), (x, m - 22), f=f)
    el.append('<rect x="%g" y="%g" width="16" height="44" fill="#FFFFFF" stroke="%s" stroke-width="2.2"/>' % (x - 8, m - 22, f))
    L((x, m + 22), (x, y2), f=f)
    T(x + 14, m - 2, name, 13, GRAU)
    T(x + 14, m + 14, wert, 14, f, b=True)


def widerstand_h(x1, x2, y, name, wert, f=SCHWARZ):     # waagerecht
    m = (x1 + x2) / 2
    L((x1, y), (m - 22, y), f=f)
    el.append('<rect x="%g" y="%g" width="44" height="16" fill="#FFFFFF" stroke="%s" stroke-width="2.2"/>' % (m - 22, y - 8, f))
    L((m + 22, y), (x2, y), f=f)
    T(m, y - 14, "%s  %s" % (name, wert), 13, f, "middle", True)


def diode_v(x, y_k, y_a, name):                        # Kathode oben
    m = (y_k + y_a) / 2
    L((x, y_k), (x, m - 12))
    el.append('<polygon points="%g,%g %g,%g %g,%g" fill="#FFFFFF" stroke="%s" stroke-width="2.2"/>'
              % (x - 12, m + 10, x + 12, m + 10, x, m - 10, SCHWARZ))
    L((x - 12, m - 11), (x + 12, m - 11), w=3)
    L((x, m + 10), (x, y_a))
    T(x - 18, m - 2, name, 13, GRAU, "end")
    T(x - 18, m + 14, "SB 120", 14, SCHWARZ, "end", True)


def luefter(x, y, name):                               # Motor-Kreis, Anschlüsse oben/unten
    el.append('<circle cx="%g" cy="%g" r="26" fill="#FFFFFF" stroke="%s" stroke-width="2.4"/>' % (x, y, SCHWARZ))
    T(x, y + 7, "M", 22, SCHWARZ, "middle", True)
    T(x + 34, y - 6, name, 15, SCHWARZ, b=True)
    T(x + 34, y + 12, "12 V, 3-polig", 13, GRAU)
    T(x - 8, y - 32, "+ rot", 12, ROT, "end")
    T(x - 8, y + 44, "− schwarz", 12, SCHWARZ, "end")


def mosfet(x, y, name):                                # Drain oben (x, y-40), Source unten (x, y+40), Gate links (x-40, y)
    L((x, y - 40), (x, y - 18), (x - 14, y - 18))
    L((x, y + 40), (x, y + 18), (x - 14, y + 18))
    L((x - 14, y - 26), (x - 14, y + 26), w=3)
    L((x - 22, y - 20), (x - 22, y + 20), w=2.2)
    L((x - 40, y), (x - 22, y))
    el.append('<polygon points="%g,%g %g,%g %g,%g" fill="%s"/>' % (x - 14, y + 18, x - 4, y + 13, x - 4, y + 23, SCHWARZ))
    T(x + 10, y - 22, "D", 12, GRAU)
    T(x + 10, y + 32, "S", 12, GRAU)
    T(x - 40, y - 8, "G", 12, GRAU, "end")
    T(x + 10, y + 2, name, 13, GRAU)
    T(x + 10, y + 18, "IRLML6344", 14, SCHWARZ, b=True)


def stecker(x, y, name, zeilen, f):
    el.append('<rect x="%g" y="%g" width="150" height="%g" rx="6" fill="#F4F4F4" stroke="%s" stroke-width="2.5"/>'
              % (x, y, 26 + 22 * len(zeilen), f))
    T(x + 8, y + 18, name, 14, f, b=True)
    for i, z in enumerate(zeilen):
        T(x + 8, y + 40 + i * 22, z, 13)


# ---------------------------------------------------------------- Titel
T(30, 38, "T12-Station – Versorgung, Lüfter, Absaugung, IR-Sensor und DS18B20", 24, SCHWARZ, b=True)
T(30, 62, "Alle Teile aus dem Lager: IRLML6344 (N-MOSFET, SOT-23), SB 120 (Schottky 1 A), 100 Ω, 100 kΩ, 4,7 kΩ, 1 kΩ, 10 kΩ, DS18B20, 2 × LM2596, GX12-5, MINI TR 1 A", 14, GRAU)

# ---------------------------------------------------------------- Versorgung
stecker(30, 95, "24 V Netzteil", ["+24 V", "GND"], ROT)
el.append('<rect x="260" y="95" width="170" height="70" rx="8" fill="#FFF3F3" stroke="%s" stroke-width="2.5"/>' % ROT)
T(345, 122, "LM2596 (Lüfter)", 16, ROT, "middle", True)
T(345, 145, "24 V → 12 V einstellen!", 13, ROT, "middle")
L((180, 135), (260, 135), f=ROT)
T(220, 128, "IN+", 12, ROT, "middle")
L((430, 120), (1130, 120), f=ROT, w=3)
T(1135, 125, "+12 V", 15, ROT, b=True)
L((180, 157), (190, 157), (190, 700), f=SCHWARZ)
L((345, 165), (345, 700))
L((60, 700), (1130, 700), w=3)
T(1135, 705, "GND", 15, SCHWARZ, b=True)
T(60, 725, "Alle GND verbinden: Netzteil, beide LM2596, Waveshare (Leiste Pin 3/29), Modul(e)", 13, GRAU)
ORANGE5 = "#E65100"
el.append('<rect x="30" y="185" width="150" height="48" rx="8" fill="#FFF3E0" stroke="%s" stroke-width="2.5"/>' % ORANGE5)
T(105, 205, "LM2596 (Display)", 14, ORANGE5, "middle", True)
T(105, 223, "24 V → 5 V einstellen!", 12, ORANGE5, "middle")
L((55, 165), (55, 185), f=ROT); T(50, 180, "IN+", 10, ROT, "end")
L((155, 165), (155, 185)); T(160, 180, "IN−", 10, SCHWARZ)
L((105, 233), (105, 250), f=ORANGE5, w=3)
T(113, 246, "OUT+ 5 V → Pin 2", 11, ORANGE5, b=True)

# ---------------------------------------------------------------- Waveshare-Leiste
el.append('<rect x="30" y="250" width="150" height="270" rx="8" fill="#F4F4F4" stroke="%s" stroke-width="2.5"/>' % SCHWARZ)
T(40, 272, "Waveshare-Leiste", 14, SCHWARZ, b=True)
for i, (n, pin, f) in enumerate([("GPIO47", 21, BLAU), ("GPIO48", 23, GRUEN), ("GPIO21", 5, LILA), ("3V3", 31, ROT), ("GND", 3, SCHWARZ)]):
    y = 310 + i * 48
    T(40, y + 5, "Pin %d" % pin, 12, GRAU)
    T(170, y + 5, n, 14, f, "end", True)
    punkt(180, y, f)
Y47, Y48, Y21, Y33, YGND = 310, 358, 406, 454, 502
L((180, YGND), (200, YGND), (200, 700))

# ---------------------------------------------------------------- Kanal 1: Netzteil-Lüfter
X1 = 560
punkt(X1, 120, ROT); L((X1, 120), (X1, 200), f=ROT)
luefter(X1, 226, "Netzteil-Lüfter (J6)")
L((X1, 252), (X1, 330))
punkt(X1, 330)
# Freilaufdiode parallel zum Lüfter
L((X1, 175), (X1 - 80, 175), (X1 - 80, 185)); punkt(X1, 175, ROT)
diode_v(X1 - 80, 185, 280, "D1")
L((X1 - 80, 280), (X1 - 80, 290), (X1, 290)); punkt(X1, 290)
mosfet(X1, 370, "Q1")
L((X1, 410), (X1, 700)); punkt(X1, 700)
# Gate
widerstand_h(180, X1 - 40, Y47, "R1", "100 Ω", BLAU)
L((X1 - 40, Y47), (X1 - 40, 370))
punkt(X1 - 60, Y47, BLAU)
L((X1 - 60, Y47), (X1 - 60, 590))
widerstand_v(X1 - 60, 590, 690, "R2", "100 kΩ")
L((X1 - 60, 690), (X1 - 60, 700))
punkt(X1 - 60, 700)
T(X1 + 12, 450, "PWM 25 kHz: aus unter Start-Temperatur,", 13, BLAU)
T(X1 + 12, 467, "30–100 % nach DS18B20", 13, GRAU)

# ---------------------------------------------------------------- Kanal 2: Absaugung über GX12-5 (Pin 1/2)
X2 = 900
punkt(X2, 120, ROT)
L((X2, 120), (X2, 140))
el.append('<rect x="%g" y="140" width="20" height="50" fill="#FFFFFF" stroke="%s" stroke-width="2.2"/>' % (X2 - 10, ROT))
L((X2 - 10, 165), (X2 + 10, 165), f=ROT)
T(X2 + 18, 160, "F1", 13, GRAU)
T(X2 + 18, 177, "MINI TR 1 A träge", 14, ROT, b=True)
L((X2, 190), (X2, 225))
# GX12-5 Buchse vorne: Pin 1 = +12 V, Pin 2 = Lüfter-Minus (geschaltet)
el.append('<rect x="%g" y="222" width="36" height="58" rx="6" fill="#FBEFF4" stroke="#AD1457" stroke-width="2.4"/>' % (X2 - 18))
for nr, y, f in [(1, 236, ROT), (2, 266, SCHWARZ)]:
    el.append('<circle cx="%g" cy="%g" r="9" fill="#FFFFFF" stroke="%s" stroke-width="2"/>' % (X2, y, f))
    T(X2, y + 4, str(nr), 11, f, "middle", True)
L((X2, 225), (X2, 227), f=ROT)
T(X2 + 34, 236, "GX12-5 vorne (Absaugung)", 15, SCHWARZ, b=True)
T(X2 + 34, 254, "Pin 1 = +12 V → Absaug-Lüfter +", 13, ROT)
T(X2 + 34, 271, "Pin 2 = Lüfter − (geschaltet)", 13, SCHWARZ)
L((X2, 275), (X2, 330)); punkt(X2, 330)
punkt(X2, 205, ROT)
L((X2, 205), (X2 - 80, 205), (X2 - 80, 215))
diode_v(X2 - 80, 215, 290, "D2")
L((X2 - 80, 290), (X2 - 80, 300), (X2, 300)); punkt(X2, 300)
T(X2 + 34, 290, "D2 direkt an Pin 1/2 der Buchse löten", 12, GRAU)
T(X2 + 34, 308, "Pin 3–5: IR-Sensor (unten)", 12, "#AD1457")
mosfet(X2, 370, "Q2")
L((X2, 410), (X2, 700)); punkt(X2, 700)
L((180, Y48), (230, Y48)); punkt(230, Y48, GRUEN)
widerstand_h(230, X2 - 40, 430, "R3", "100 Ω", GRUEN)
L((230, Y48), (230, 430))
L((X2 - 40, 430), (X2 - 40, 370))
punkt(X2 - 60, 430, GRUEN)
widerstand_v(X2 - 60, 430, 520, "R4", "100 kΩ")
L((X2 - 60, 520), (X2 - 60, 700))
punkt(X2 - 60, 700)

# ---------------------------------------------------------------- DS18B20
XD = 1060
el.append('<rect x="%g" y="470" width="110" height="90" rx="8" fill="#F7F0FA" stroke="%s" stroke-width="2.5"/>' % (XD, LILA))
T(XD + 55, 492, "DS18B20", 15, LILA, "middle", True)
T(XD + 55, 510, "am Netzteil", 12, GRAU, "middle")
for i, (n, f) in enumerate([("VDD", ROT), ("DQ", LILA)]):
    T(XD + 8, 530 + i * 13, n, 11, f)
T(XD + 40, 553, "GND", 11, SCHWARZ, "middle")
# Leitungen
L((180, Y33), (215, Y33), (215, 545), (XD - 60, 545), (XD - 60, 527), (XD, 527), f=ROT)
L((180, Y21), (205, Y21), (205, 560), (XD - 30, 560), (XD - 30, 540), (XD, 540), f=LILA)
# GND unten aus dem Fühler direkt auf die Masse
L((XD + 40, 560), (XD + 40, 700), w=2.6)
punkt(XD + 40, 560)
punkt(XD + 40, 700)
T(XD + 32, 625, "GND (schwarz)", 13, SCHWARZ, "end", True)
widerstand_v(XD - 45, 470, 527, "R5", "4,7 kΩ", LILA)
L((XD - 45, 470), (XD - 75, 470), (XD - 75, 545), f=ROT)
punkt(XD - 75, 545, ROT)
L((XD - 45, 527), (XD - 45, 560), f=LILA)
punkt(XD - 45, 560, LILA)

# ---------------------------------------------------------------- Hinweise (Hauptschaltplan)
T(30, 758, "Hinweise", 15, SCHWARZ, b=True)
for i, z in enumerate([
        "• IRLML6344: SOT-23, 1 = Gate, 2 = Source, 3 = Drain (wie AO3400) – schaltet sicher mit 3,3 V",
        "• SB 120: Ring (Kathode) an +12 V – schützt den MOSFET vor Spannungsspitzen des Motors",
        "• R2/R4 (100 kΩ) halten die Lüfter aus, solange der ESP startet",
        "• gelbes Lüfterkabel (Drehzahl) bleibt frei · Lüfter J6: 1 = Minus (Drain Q1), 2 = +12 V",
        "• beide LM2596 vor dem Anschließen einstellen: Display 5,0 V, Lüfter 12 V",
        "• Absaugung und IR-Sensor hängen an einer 5-poligen GX12-Buchse vorne – Aufbau siehe nächster Teil"]):
    T(30, 780 + i * 18, z, 13)

# ---------------------------------------------------------------- Absaugung: GX12-5 Buchse -> Kabel -> Absaug-Gehäuse
TEIL = 895                                    # hier beginnt im Druck ein neues Blatt
IR = "#AD1457"
ORANGE_A = "#E65100"
el.append('<line x1="30" y1="%d" x2="1170" y2="%d" stroke="#DDDDDD" stroke-width="1.5" stroke-dasharray="6 5"/>' % (TEIL, TEIL))
T(30, 928, "Absaugung: GX12-5 Buchse an der Station → 5-adriges Kabel → GX12-5 Stecker im Absaug-Gehäuse", 19, IR, b=True)
T(30, 950, "Pin 1/2 = Absaug-Lüfter (12 V, über Q2 geschaltet) · Pin 3–5 = IR-Sensor (3,3 V). Stecker nur bei ausgeschalteter Station stecken oder ziehen.", 13, GRAU)

YP = {1: 1000, 2: 1040, 3: 1090, 4: 1140, 5: 1195}
PIN = {1: ("+12 V", ROT), 2: ("Lüfter −", SCHWARZ), 3: ("3,3 V", ORANGE_A), 4: ("OUT", IR), 5: ("GND", "#1565C0")}

# Waveshare-Anschlüsse für den Sensor
el.append('<rect x="30" y="1045" width="150" height="175" rx="8" fill="#F4F4F4" stroke="%s" stroke-width="2.5"/>' % SCHWARZ)
T(40, 1066, "Waveshare-Leiste", 14, SCHWARZ, b=True)
for n, pin, nr in [("3V3", 32, 3), ("GPIO44", 27, 4), ("GND", 30, 5)]:
    y, f = YP[nr], PIN[nr][1]
    T(40, y + 5, "Pin %d" % pin, 12, GRAU)
    T(170, y + 5, n, 14, f, "end", True)
    punkt(180, y, f)

XB = 540                                      # Buchse an der Station
# Pin 1/2 kommen aus dem Schaltplan oben (F1 und Drain Q2)
T(372, YP[1] + 5, "+12 V hinter F1 (oben)", 13, ROT, "end", True)
T(372, YP[2] + 5, "Drain Q2 (oben)", 13, SCHWARZ, "end", True)
L((380, YP[1]), (XB, YP[1]), f=ROT)
L((380, YP[2]), (XB, YP[2]))
L((180, YP[3]), (XB, YP[3]), f=ORANGE_A)
widerstand_h(180, 400, YP[4], "R6", "1 kΩ", IR)
L((400, YP[4]), (XB, YP[4]), f=IR)
punkt(460, YP[4], IR)
widerstand_v(460, YP[4], YP[5], "R7", "10 kΩ")
punkt(460, YP[5], "#1565C0")
L((180, YP[5]), (XB, YP[5]), f="#1565C0")


def gx12(x, titel):
    el.append('<rect x="%g" y="962" width="160" height="258" rx="10" fill="#FBEFF4" stroke="%s" stroke-width="2.5"/>' % (x, IR))
    T(x + 80, 980, titel, 13, IR, "middle", True)
    for nr in range(1, 6):
        txt, f = PIN[nr]
        el.append('<circle cx="%g" cy="%g" r="10" fill="#FFFFFF" stroke="%s" stroke-width="2.2"/>' % (x + 24, YP[nr], f))
        T(x + 24, YP[nr] + 4, str(nr), 12, f, "middle", True)
        T(x + 42, YP[nr] + 5, txt, 14, f, b=True)


gx12(XB, "Buchse an der Station")

# Kabel
XK = 820
for nr in range(1, 6):
    L((XB + 160, YP[nr]), (XK, YP[nr]), f=PIN[nr][1], w=2.6)
T((XB + 160 + XK) / 2, 1025, "5-adriges Kabel", 12, GRAU, "middle")

# Absaug-Gehäuse
el.append('<rect x="805" y="956" width="375" height="279" rx="12" fill="none" stroke="%s" stroke-width="2" stroke-dasharray="7 5"/>' % GRAU)
T(1170, 974, "im Absaug-Gehäuse", 13, GRAU, "end", True)
XS = XK
gx12(XS, "Stecker am Kabel")
# Lüfter an Pin 1/2
XL = 1010
L((XS + 160, YP[1]), (XL, YP[1]), (XL, 1002), f=ROT)
L((XS + 160, YP[2]), (XL, YP[2]), (XL, 1038))
el.append('<circle cx="%g" cy="1020" r="18" fill="#FFFFFF" stroke="%s" stroke-width="2.4"/>' % (XL, SCHWARZ))
T(XL, 1027, "M", 18, SCHWARZ, "middle", True)
T(XL + 26, 1016, "Absaug-Lüfter 12 V", 13, SCHWARZ, b=True)
T(XL + 26, 1032, "rot +, schwarz −", 12, GRAU)
# IR-Modul an Pin 3-5
XM = 1050
for nr in (3, 4, 5):
    L((XS + 160, YP[nr]), (XM, YP[nr]), f=PIN[nr][1])
el.append('<rect x="%g" y="1072" width="120" height="145" rx="8" fill="#FFFFFF" stroke="%s" stroke-width="2.5"/>' % (XM, IR))
T(XM + 60, 1066, "IR-Modul", 13, IR, "middle", True)
for nr, txt in [(3, "VCC"), (4, "OUT"), (5, "GND")]:
    T(XM + 10, YP[nr] + 5, txt, 14, PIN[nr][1], b=True)
T(XM + 60, 1213, "HIGH bei Hand, ab 10 cm", 10, GRAU, "middle")

# Belegungstabelle
YT = 1262
T(30, YT, "Belegung GX12-5 (Nummern stehen auf dem Isolierkörper von Buchse und Stecker – nach Nummer löten, nicht nach Lage)", 15, SCHWARZ, b=True)
spalten = [(30, 60), (90, 150), (240, 130), (370, 400), (770, 400)]
zeilen = [("Pin", "Ader (Vorschlag)", "Signal", "an der Station (Buchse)", "im Absaug-Gehäuse (Stecker)")]
zeilen += [("1", "rot", "+12 V", "+12 V hinter F1 (MINI TR 1 A), Ring der SB 120", "Absaug-Lüfter + (rot)"),
           ("2", "schwarz", "Lüfter −", "Drain Q2, Anode der SB 120 – NICHT GND", "Absaug-Lüfter − (schwarz)"),
           ("3", "orange", "3,3 V", "Waveshare 3V3 (Pin 32)", "IR-Modul VCC"),
           ("4", "gelb", "OUT", "1 kΩ → GPIO44 (Pin 27), 10 kΩ nach GND", "IR-Modul OUT"),
           ("5", "blau", "GND", "Waveshare GND (Pin 30)", "IR-Modul GND")]
for i, z in enumerate(zeilen):
    y = YT + 14 + i * 28
    if i == 0:
        el.append('<rect x="30" y="%g" width="1140" height="26" rx="4" fill="#333333"/>' % y)
    elif i % 2:
        el.append('<rect x="30" y="%g" width="1140" height="26" rx="2" fill="#F5F5F5"/>' % y)
    farbe = "#FFFFFF" if i == 0 else PIN[i][1]
    for (x, w), txt, k in zip(spalten, z, range(5)):
        T(x + 8, y + 18, txt, 14, farbe if (i == 0 or k in (0, 2)) else SCHWARZ, b=(i == 0 or k in (0, 2)))
T(30, YT + 14 + 6 * 28 + 18, "IR-Modul nur mit 3,3 V betreiben (bei 5 V kämen 5 V an GPIO44). GPIO44 ist RXD – frei, weil der Logger über USB läuft.", 13, GRAU)

el.insert(0, '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" data-teilung="%d"><rect width="%d" height="%d" fill="#FFFFFF"/>'
          % (B, H, B, H, TEIL, B, H))
el.append("</svg>\n")
ziel = os.path.join(os.path.dirname(os.path.abspath(__file__)), "luefter_schaltplan.svg")
open(ziel, "w", encoding="utf-8").write("".join(el))
print(ziel)
