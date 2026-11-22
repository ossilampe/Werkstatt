"""PDF-Anleitung für MakerWorld aus den README-Dateien bauen.

Aufruf:  python gen_anleitung.py <ausgabe.html>
Danach:  msedge --headless --no-pdf-header-footer --print-to-pdf=T12-Station_Anleitung.pdf <ausgabe.html>

Inhalt: Titelseite, README der 2-Kolben-Variante (Links -> GitHub), Gehäuse-README,
Anhang mit dem Werkstattblatt (Schaltplan, Absaugung, Stiftleiste, Verbindungen – je eine Seite).
"""
import html
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HIER)
GITHUB = "https://github.com/ossilampe/Werkstatt/blob/main/T12-Station-2-Kolben/"
GITHUB_ROOT = "https://github.com/ossilampe/Werkstatt/tree/main/"


def datei_url(pfad):
    return "file:///" + os.path.abspath(pfad).replace("\\", "/").replace(" ", "%20")


def slug(t):
    t = re.sub(r"<[^>]+>", "", t).strip().lower()
    t = re.sub(r"[^\w\- ]", "", t)
    return t.replace(" ", "-")


def link_ziel(u, basis):
    if u.startswith(("http://", "https://", "#", "mailto:")):
        return u
    ziel = os.path.normpath(os.path.join(basis, u)).replace("\\", "/")
    rel = os.path.relpath(os.path.join(PROJ, ziel), PROJ).replace("\\", "/")
    if rel.startswith("../"):
        return GITHUB_ROOT + rel[3:]
    return GITHUB + rel


def inline(t, basis):
    # Code-Spans erst durch Platzhalter ersetzen, damit Links/Fett um Code herum funktionieren
    codes = []

    def code(m):
        codes.append("<code>%s</code>" % html.escape(m.group(1)))
        return "\x00%d\x00" % (len(codes) - 1)
    s = re.sub(r"`([^`]+)`", code, t)
    s = html.escape(s, quote=False)

    def bild(m):
        src = os.path.join(PROJ, basis, m.group(2))
        return '<img alt="%s" src="%s">' % (m.group(1), datei_url(src))
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", bild, s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: '<a href="%s">%s</a>' % (link_ziel(m.group(2), basis), m.group(1)), s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], s)


def md(text, basis="", ebene=0, ersetze=None):
    ersetze = ersetze or {}
    zeilen = text.replace("\r\n", "\n").split("\n")
    out, i = [], 0
    while i < len(zeilen):
        z = zeilen[i]
        if z.strip() in ersetze:
            out.append(ersetze[z.strip()]); i += 1; continue
        if z.startswith("```"):
            j = i + 1
            while j < len(zeilen) and not zeilen[j].startswith("```"):
                j += 1
            out.append("<pre>%s</pre>" % html.escape("\n".join(zeilen[i + 1:j])))
            i = j + 1; continue
        m = re.match(r"^(#{1,6}) (.*)$", z)
        if m:
            n = min(6, len(m.group(1)) + ebene)
            out.append('<h%d id="%s">%s</h%d>' % (n, slug(m.group(2)), inline(m.group(2), basis), n))
            i += 1; continue
        if z.startswith("|"):
            rows = []
            while i < len(zeilen) and zeilen[i].startswith("|"):
                rows.append([c.strip() for c in zeilen[i].strip().strip("|").split("|")]); i += 1
            kopf, rest = rows[0], [r for r in rows[1:] if not all(re.match(r"^:?-+:?$", c) for c in r)]
            h = "<table><thead><tr>%s</tr></thead><tbody>" % "".join("<th>%s</th>" % inline(c, basis) for c in kopf)
            h += "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c, basis) for c in r) for r in rest)
            out.append(h + "</tbody></table>"); continue
        if z.startswith(">"):
            q = []
            while i < len(zeilen) and zeilen[i].startswith(">"):
                q.append(zeilen[i][1:].strip()); i += 1
            out.append("<blockquote>%s</blockquote>" % inline(" ".join(q), basis)); continue
        if re.match(r"^\s*([-*]|\d+\.) ", z):
            geordnet = bool(re.match(r"^\s*\d+\. ", z))
            items = []
            while i < len(zeilen) and (re.match(r"^\s*([-*]|\d+\.) ", zeilen[i]) or (zeilen[i].startswith("   ") and zeilen[i].strip())):
                if re.match(r"^\s*([-*]|\d+\.) ", zeilen[i]):
                    items.append(re.sub(r"^\s*([-*]|\d+\.) ", "", zeilen[i]))
                else:
                    items[-1] += " " + zeilen[i].strip()
                i += 1
            tag = "ol" if geordnet else "ul"
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline(t, basis) for t in items), tag)); continue
        if not z.strip():
            i += 1; continue
        p = [z]
        i += 1
        while i < len(zeilen) and zeilen[i].strip() and not re.match(r"^(#|\||>|```|\s*([-*]|\d+\.) )", zeilen[i]):
            p.append(zeilen[i]); i += 1
        inhalt = inline(" ".join(p), basis)
        if re.fullmatch(r"\s*<img[^>]*>\s*", inhalt):
            out.append('<p class="bild">%s</p>' % inhalt)
        else:
            out.append("<p>%s</p>" % inhalt)
    return "\n".join(out)


def svg_ausschnitt(svg_pfad, a, b, breite=1200):
    w, h = breite - 40, b - a - 5
    m = re.search(r'viewBox="0 0 (\d+) (\d+)"', open(svg_pfad, encoding="utf-8").read())
    gw, gh = int(m.group(1)), int(m.group(2))
    return ('<svg class="blatt" viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid meet">'
            '<svg x="0" y="0" width="%d" height="%d" viewBox="20 %d %d %d" overflow="hidden">'
            '<image href="%s" x="0" y="0" width="%d" height="%d"/></svg></svg>'
            % (w, h, w, h, a + 5, w, h, datei_url(svg_pfad), gw, gh))


def main():
    ziel = sys.argv[1]
    readme = open(os.path.join(PROJ, "README.md"), encoding="utf-8").read()
    geh = open(os.path.join(PROJ, "gehaeuse", "README.md"), encoding="utf-8").read()
    hinweis = '<p class="hinweis">→ siehe Anhang „Werkstattblatt“ am Ende dieser Anleitung.</p>'
    haupt = md(readme, "", 0, {"![T12-Station im Gehäuse](gehaeuse/bilder/foto_front.jpg)": "",
                               "![Schaltplan Lüfter](docs/luefter_schaltplan.svg)": hinweis,
                               "![Komplette Verdrahtung](docs/verdrahtung_komplett.svg)": hinweis})
    # Titel der README (h1) durch die Titelseite ersetzen
    haupt = re.sub(r"<h1[^>]*>.*?</h1>", "", haupt, count=1)
    gehaeuse = md(geh, "gehaeuse", 1)

    # Werkstattblatt: Seitengrenzen wie in verdrahtung_druck.html
    druck = open(os.path.join(PROJ, "docs", "verdrahtung_druck.html"), encoding="utf-8").read()
    grenzen = [(int(x), int(y), int(z)) for x, y, z in re.findall(r'viewBox="20 (\d+) (\d+) (\d+)"', druck)]
    titel = re.findall(r"Werkstattblatt \d+/\d+ · ([^<·]+) ·", druck)
    svg = os.path.join(PROJ, "docs", "verdrahtung_komplett.svg")
    blaetter = "".join('<div class="anhang-seite"><h3>%s</h3>%s</div>' % (html.escape(t.strip()), svg_ausschnitt(svg, a - 5, a - 5 + h + 5))
                       for (a, w, h), t in zip(grenzen, titel))

    titelseite = """<div class="titel">
<h1>T12-Lötstation mit Touch-Display</h1>
<p class="unter">ESP32-S3 (Waveshare 3,5″) + fertige T12-Steuerplatinen (STM32 Ver21S) mit eigener Firmware</p>
<img src="%s">
<p class="unter2">Bauanleitung: Umbau und Flashen der Module · Verdrahtung · ESPHome · Spitzenprofile · Menüs · Gehäuse</p>
<p class="quelle">Alle Dateien: <a href="%sT12-Station-2-Kolben">github.com/ossilampe/Werkstatt</a> · <a href="https://makerworld.com/de/models/3663781-t12-lotstation-esp32-s3-touch-display-2-kolben">MakerWorld</a> · Stand 22.11.2026</p>
</div>""" % (datei_url(os.path.join(PROJ, "gehaeuse", "bilder", "foto_front.jpg")), GITHUB_ROOT)

    css = """
@page { size: A4; margin: 14mm 14mm 16mm 14mm; }
@page quer { size: A4 landscape; margin: 8mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 22pt; color: #E65100; margin: 0 0 6pt; }
h2 { font-size: 15pt; color: #E65100; border-bottom: 2px solid #E65100; padding-bottom: 3pt; margin-top: 18pt; break-before: page; }
h3 { font-size: 12pt; margin: 14pt 0 4pt; }
h4 { font-size: 10.5pt; margin: 10pt 0 3pt; }
h2, h3, h4 { break-after: avoid; }
p, li { orphans: 3; widows: 3; }
a { color: #1565C0; text-decoration: none; }
code { font-family: Consolas, monospace; font-size: 9pt; background: #F2F2F2; padding: 0 2pt; border-radius: 2pt; }
pre { font-family: Consolas, monospace; font-size: 8.5pt; background: #F5F5F5; border: 1px solid #DDD; padding: 6pt; white-space: pre-wrap; break-inside: avoid; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0; font-size: 8.8pt; break-inside: auto; }
tr { break-inside: avoid; }
th { background: #333; color: #fff; text-align: left; padding: 3pt 5pt; }
td { border-bottom: 1px solid #E0E0E0; padding: 3pt 5pt; vertical-align: top; }
td img { max-width: 100%; }
blockquote { margin: 8pt 0; padding: 6pt 10pt; background: #FFF3E0; border-left: 4px solid #E65100; }
p.bild { text-align: center; break-inside: avoid; }
p.bild img { max-width: 100%; max-height: 120mm; }
img[src$=".svg"] { max-width: 78%; }
.hinweis { color: #777; font-style: italic; }
.titel { text-align: center; padding-top: 30mm; break-after: page; }
.titel img { width: 100%; margin: 12mm 0; border-radius: 6pt; }
.titel .unter { font-size: 13pt; color: #333; }
.titel .unter2 { font-size: 11pt; color: #555; }
.titel .quelle { font-size: 10pt; color: #777; margin-top: 20mm; }
.anhang { break-before: page; }
.anhang-seite { page: quer; break-before: page; height: 190mm; display: flex; flex-direction: column; }
.anhang-seite h3 { margin: 0 0 3mm; color: #E65100; }
.anhang-seite svg.blatt { flex: 1; width: 100%; min-height: 0; }
"""
    seite = ("<!doctype html><html lang='de'><head><meta charset='utf-8'><title>T12-Lötstation – Anleitung</title>"
             "<style>%s</style></head><body>%s%s<h2 id='gehaeuse-im-detail'>Gehäuse im Detail</h2>%s"
             "<div class='anhang'><h2 style='break-before:avoid'>Anhang: Werkstattblatt</h2>"
             "<p>Schaltplan, Absaugung mit GX12-5-Belegung, Stiftleiste des Displays und alle Verbindungen – je ein Blatt im Querformat.</p></div>%s"
             "</body></html>\n") % (css, titelseite, haupt, re.sub(r"<h2[^>]*>.*?</h2>", "", gehaeuse, count=1), blaetter)
    open(ziel, "w", encoding="utf-8").write(seite)
    print(ziel, len(seite), "Zeichen,", len(grenzen), "Werkstattblätter")


if __name__ == "__main__":
    main()
