"""Zeichnet Vorschaubilder der Display-Seiten (480 x 320, wie in der Firmware) als SVG.

Masse, Farben und Texte entsprechen firmware/t12-loetstation.yaml und t12/loet.h.
Seiten mit "(geplant)" gibt es in der Firmware noch nicht.
Aufruf: python gen_menues.py  -> schreibt die SVG-Dateien in diesen Ordner.
"""
import os

W, H = 480, 320
OR, GR, BG, KACHEL, KNOPF = "#FF8C00", "#8C8C8C", "#000000", "#1F1F1F", "#3A3A3A"
ZUSTAND = {"HEIZT": "#FF8C00", "BEREIT": "#3CC85A", "KÜHLT AB": "#4FC3F7", "STANDBY": "#4A90E2",
           "SCHLÄFT": "#7E7EC8", "KEINE SPITZE": "#FFC107", "AUS": GR}
FONT = "font-family=\"'Montserrat','Segoe UI',Arial,sans-serif\""


class Seite:
    def __init__(self, name, titel):
        self.name, self.titel, self.el = name, titel, []

    def rect(self, x, y, w, h, fill, r=0, stroke=None, sw=0, opa=1):
        s = ' stroke="%s" stroke-width="%g"' % (stroke, sw) if stroke else ""
        self.el.append('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" fill-opacity="%g"%s/>'
                       % (x, y, w, h, r, fill, opa, s))

    def text(self, x, y, t, size=18, fill="#FFFFFF", anchor="start", bold=False):
        b = ' font-weight="600"' if bold else ""
        t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.el.append('<text x="%g" y="%g" font-size="%g" fill="%s" text-anchor="%s" %s%s>%s</text>'
                       % (x, y, size, fill, anchor, FONT, b, t))

    def knopf(self, x, y, w, h, t, fill=KNOPF, color="#FFFFFF", size=18):
        self.rect(x, y, w, h, fill, 8)
        self.text(x + w / 2, y + h / 2 + size * 0.36, t, size, color, "middle")

    def schalter(self, x, y, an):
        self.rect(x, y, 50, 26, OR if an else "#555555", 13)
        self.el.append('<circle cx="%g" cy="%g" r="10" fill="#FFFFFF"/>' % (x + (37 if an else 13), y + 13))

    def regler(self, x, y, w, wert):
        self.rect(x, y, w, 10, "#333333", 5)
        self.rect(x, y, w * wert / 100.0, 10, OR, 5)
        self.el.append('<circle cx="%g" cy="%g" r="11" fill="#FFFFFF" stroke="%s" stroke-width="3"/>'
                       % (x + w * wert / 100.0, y + 5, OR))

    def kopf(self, titel, zurueck=True, rechts=None):
        self.text(10, 26, titel, 20, OR)
        if zurueck:
            self.knopf(W - 118, 2, 110, 32, "< Zurück", size=17)
        elif rechts:
            self.text(W - 10, 24, rechts, 14, GR, "end")

    def svg(self):
        rand = 14
        kopf = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%d %d %d %d" width="%d" height="%d">'
                % (-rand, -rand, W + 2 * rand, H + 2 * rand + 26, (W + 2 * rand) * 1.5, (H + 2 * rand + 26) * 1.5))
        gehaeuse = ('<rect x="%d" y="%d" width="%d" height="%d" rx="16" fill="#2B2B2B"/>'
                    '<rect x="0" y="0" width="%d" height="%d" fill="%s"/>'
                    % (-rand, -rand, W + 2 * rand, H + 2 * rand, W, H, BG))
        unter = ('<text x="%g" y="%g" font-size="13" fill="#666666" text-anchor="middle" %s>%s</text>'
                 % (W / 2, H + rand + 19, FONT, self.titel.replace("&", "&amp;")))
        return kopf + gehaeuse + "".join(self.el) + unter + "</svg>\n"


def kachel(s, x, name, ein, ist, soll, zustand, leistung, gewaehlt, ist_grau=False):
    s.rect(x, 36, 228, 228, KACHEL, 10, OR if gewaehlt else KACHEL, 3)
    s.text(x + 12, 64, name, 20, GR)
    s.knopf(x + 228 - 80, 42, 72, 34, "EIN" if ein else "AUS", "#2E7D32" if ein else KNOPF)
    s.text(x + 114, 146, ist, 64, GR if ist_grau else "#FFFFFF", "middle", True)
    s.text(x + 114, 186, soll, 26, "#FFFFFF", "middle")
    s.text(x + 114, 216, zustand, 18, ZUSTAND.get(zustand, GR), "middle")
    s.rect(x + 12, 232, 198, 14, "#333333", 7)
    if leistung:
        s.rect(x + 12, 232, 198 * leistung / 100.0, 14, OR, 7)


def festwerte(s):
    for i, t in enumerate(("280 °C", "330 °C", "380 °C")):
        s.knopf(8 + i * 118, 272, 110, 42, t)
    s.knopf(362, 272, 110, 42, "Menü", color=OR)


def hauptseite():
    s = Seite("01-hauptseite", "Hauptseite – beide Kolben in Betrieb, Kolben A gewählt (Drehgeber stellt A)")
    s.kopf("T12 Lötstation", False, "Absaugung 60 %   Gehäuse 31 °C")
    kachel(s, 8, "Kolben A", True, "312°", "Soll 330 °C", "HEIZT", 72, True)
    kachel(s, 244, "Kolben B", True, "331°", "Soll 330 °C", "BEREIT", 18, False)
    festwerte(s)
    return s


def standby():
    s = Seite("02-standby", "Kolben in der Ablage – A im Standby (180 °C), B schläft nach 10 min")
    s.kopf("T12 Lötstation", False, "Absaugung aus   Gehäuse 28 °C")
    kachel(s, 8, "Kolben A", True, "181°", "Soll 330 °C", "STANDBY", 9, True)
    kachel(s, 244, "Kolben B", True, "46°", "Soll 330 °C", "SCHLÄFT", 0, False, True)
    festwerte(s)
    return s


def menue():
    s = Seite("03-menue", "Menü (langer Druck auf den Drehgeber oder „Menü“) – geplant")
    s.kopf("Menü")
    kacheln = (("Kolben &", "Standby", "Standby 180 °C · Offset", OR),
               ("Lüfter &", "Absaugung", "Absaugung 60 % · NT 38 °C", "#4FC3F7"),
               ("Ton &", "Sprache", "Lautstärke 70 % · Ansagen an", "#3CC85A"),
               ("System", "", "WLAN · Firmware · Info", GR))
    for i, (z1, z2, info, farbe) in enumerate(kacheln):
        x, y = 8 + (i % 2) * 236, 42 + (i // 2) * 138
        s.rect(x, y, 228, 130, KACHEL, 10)
        s.rect(x, y, 6, 130, farbe, 3)
        s.text(x + 20, y + 40, z1.replace("&amp;", "&"), 24, "#FFFFFF", bold=True)
        if z2:
            s.text(x + 20, y + 70, z2, 24, "#FFFFFF", bold=True)
        s.text(x + 20, y + 112, info, 14, GR)
    return s


def einstellungen():
    s = Seite("04-einstellungen", "Kolben & Standby – Zeile antippen, dann Drehgeber oder −/+ (vorhanden)")
    s.kopf("Einstellungen")
    zeilen = (("Standby-Temperatur", "180 °C"), ("Standby nach", "2 min"), ("Schlafen nach", "10 min"),
              ("Kolben A  Offset", "+0 K"), ("Kolben A  Faktor", "1,00"), ("Kolben B  Offset", "−3 K"),
              ("Kolben B  Faktor", "1,02"))
    for i, (name, wert) in enumerate(zeilen):
        y = 40 + i * 40
        akt = i == 0
        s.rect(8, y, 464, 36, "#3A2A10" if akt else KACHEL, 8, OR if akt else KACHEL, 2)
        s.text(20, y + 24, name, 18)
        s.text(8 + 464 - 110, y + 24, wert, 18, OR if akt else "#FFFFFF", "end")
        s.knopf(8 + 464 - 98, y + 4, 44, 28, "−")
        s.knopf(8 + 464 - 50, y + 4, 44, 28, "+")
    return s


def luefter():
    s = Seite("05-luefter-absaugung", "Lüfter & Absaugung – geplant")
    s.kopf("Lüfter & Absaugung")
    # Absaugung
    s.rect(8, 42, 464, 132, KACHEL, 10)
    s.text(20, 70, "Absaugung (Buchse vorne)", 18, GR)
    s.text(460, 70, "60 %", 22, OR, "end", True)
    s.regler(32, 88, 400, 60)
    s.text(20, 134, "Automatisch, wenn Kolben in der Hand", 16)
    s.schalter(410, 116, True)
    s.text(20, 162, "Nachlauf", 16)
    s.text(460, 162, "10 s", 16, GR, "end")
    # Netzteil-Luefter mit Kennlinie
    s.rect(8, 182, 464, 132, KACHEL, 10)
    s.text(20, 208, "Netzteil-Lüfter (DS18B20)", 18, GR)
    s.text(20, 244, "38 °C", 30, "#FFFFFF", bold=True)
    s.text(20, 272, "Drehzahl 42 %", 16, "#4FC3F7")
    s.text(20, 298, "aus unter 35 °C", 13, GR)
    gx, gy, gw, gh = 232, 218, 226, 84          # Kennlinie 25..60 degC, 0..100 %
    s.rect(gx, gy, gw, gh, "#151515", 4)

    def px(t, p):
        return gx + (t - 25) / 35.0 * gw, gy + gh - p / 100.0 * gh
    pts = [px(25, 0), px(35, 0), px(35, 30), px(50, 100), px(60, 100)]
    s.el.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="3"/>'
                % (" ".join("%g,%g" % p for p in pts), "#4FC3F7"))
    cx, cy = px(38, 30 + 70 * 3 / 15.0)
    s.el.append('<circle cx="%g" cy="%g" r="6" fill="%s"/>' % (cx, cy, OR))
    for t in (30, 40, 50):
        x, _ = px(t, 0)
        s.text(x, gy + gh - 4, "%d°" % t, 11, "#666666", "middle")
    return s


def ton():
    s = Seite("06-ton-sprache", "Ton & Sprache – Lautsprecher des Displays (ES8311), geplant")
    s.kopf("Ton & Sprache")
    s.rect(8, 42, 464, 70, KACHEL, 10)
    s.text(20, 68, "Lautstärke", 18, GR)
    s.text(460, 68, "70 %", 20, OR, "end", True)
    s.regler(32, 88, 400, 70)
    zeilen = (("Pieptöne (Tasten, bereit)", True), ("Sprachausgabe", True),
              ("Ansage „Kolben A / B bereit“", True), ("Ansage Standby / Schlafen", False),
              ("Ansage Fehler / keine Spitze", True))
    for i, (t, an) in enumerate(zeilen):
        y = 120 + i * 36
        s.rect(8, y, 464, 32, KACHEL, 8)
        s.text(20, y + 22, t, 16)
        s.schalter(410, y + 3, an)
    return s


def warnung():
    s = hauptseite()
    s.name, s.titel = "07-warnung", "Meldung mit Sprachansage: „Kolben B – keine Spitze erkannt“"
    s.rect(0, 0, W, H, "#000000", 0, opa=0.65)
    s.rect(60, 70, 360, 180, "#262626", 14, "#FFC107", 3)
    s.text(240, 112, "Kolben B", 22, GR, "middle")
    s.text(240, 150, "KEINE SPITZE", 30, "#FFC107", "middle", True)
    s.text(240, 182, "Heizung abgeschaltet – Spitze einsetzen", 15, "#FFFFFF", "middle")
    s.knopf(180, 200, 120, 38, "OK", OR, "#000000", 20)
    return s


if __name__ == "__main__":
    ziel = os.path.dirname(os.path.abspath(__file__))
    for f in (hauptseite, standby, menue, einstellungen, luefter, ton, warnung):
        s = f()
        with open(os.path.join(ziel, s.name + ".svg"), "w", encoding="utf-8") as fh:
            fh.write(s.svg())
        print(s.name)
