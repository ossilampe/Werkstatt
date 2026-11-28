"""Erzeugt Schaltplan und Bildschirm-Ansichten als SVG."""
import random
from pathlib import Path

OUT = Path(__file__).resolve().parents[1]
OUT.mkdir(parents=True, exist_ok=True)
FONT = "font-family='DejaVu Sans, Arial, sans-serif'"


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, t, size=14, anchor="start", fill="#222", weight="normal"):
    return (f"<text x='{x}' y='{y}' font-size='{size}' text-anchor='{anchor}' "
            f"fill='{fill}' font-weight='{weight}' {FONT}>{esc(t)}</text>")


def line(pts, color="#222", w=2.5, dash=None):
    d = " ".join(f"{x},{y}" for x, y in pts)
    da = f" stroke-dasharray='{dash}'" if dash else ""
    return (f"<polyline points='{d}' fill='none' stroke='{color}' stroke-width='{w}' "
            f"stroke-linejoin='round' stroke-linecap='round'{da}/>")


def rect(x, y, w, h, fill, stroke="#333", rx=8, sw=2):
    return f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='{rx}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>"


def dot(x, y, r=4, c="#222"):
    return f"<circle cx='{x}' cy='{y}' r='{r}' fill='{c}'/>"


def button_symbol(x1, x2, y, color="#222"):
    """Taster (Schließer) zwischen x1 und x2 auf Höhe y."""
    m = (x1 + x2) / 2
    return "".join([
        f"<circle cx='{x1}' cy='{y}' r='4' fill='white' stroke='{color}' stroke-width='2'/>",
        f"<circle cx='{x2}' cy='{y}' r='4' fill='white' stroke='{color}' stroke-width='2'/>",
        line([(x1 - 2, y - 10), (x2 + 2, y - 10)], color, 2.5),
        line([(m, y - 10), (m, y - 20)], color, 2),
        line([(m - 7, y - 20), (m + 7, y - 20)], color, 2.5),
    ])


# ------------------------------------------------------------------
# Schaltplan
# ------------------------------------------------------------------
def wiring():
    W, H = 1100, 720
    s = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}'>",
         f"<rect width='{W}' height='{H}' fill='white'/>",
         text(W / 2, 30, "Digitales Mikroskop – Verdrahtung", 22, "middle", weight="bold")]

    # --- obere Reihe: Komponenten ---
    s.append(rect(40, 60, 170, 70, "#fdf2d0"))
    s.append(text(125, 90, "Netzteil", 15, "middle", weight="bold"))
    s.append(text(125, 112, "USB-C 5,1 V / 3 A", 13, "middle"))

    s.append(rect(40, 165, 170, 95, "#e3e9f5"))
    s.append(text(125, 195, "HQ-Kamera", 15, "middle", weight="bold"))
    s.append(text(125, 217, "IMX477, 12,3 MP", 13, "middle"))
    s.append(text(125, 237, "+ Mikroskop-Objektiv", 13, "middle"))

    s.append(rect(330, 55, 330, 210, "#2e7d4f", "#1d5234"))
    s.append(text(495, 155, "Raspberry Pi 4", 20, "middle", "white", "bold"))
    # 40-Pin-Leiste oben
    s.append(rect(380, 64, 230, 26, "#1a1a1a", "#000", 3))
    for i in range(20):
        s.append(dot(388 + i * 11.3, 71, 2.6, "#d4af37"))
        s.append(dot(388 + i * 11.3, 83, 2.6, "#d4af37"))
    s.append(text(495, 108, "40-Pin GPIO (Pin 1 links)", 12, "middle", "white"))
    # Ports
    s.append(rect(320, 80, 22, 34, "#bbb", "#555", 3))
    s.append(text(350, 102, "USB-C", 11, "start", "white"))
    s.append(rect(395, 200, 60, 14, "#f0f0f0", "#555", 2))
    s.append(text(425, 232, "CAMERA (CSI)", 11, "middle", "white"))
    s.append(rect(600, 150, 14, 60, "#f0f0f0", "#555", 2))
    s.append(text(590, 245, "DISPLAY (DSI)", 11, "end", "white"))

    s.append(rect(810, 55, 250, 150, "#222", "#000"))
    s.append(rect(825, 68, 220, 124, "#3d5a80", "#3d5a80", 3))
    s.append(text(935, 125, "7\" Touch Display", 16, "middle", "white", "bold"))
    s.append(text(935, 147, "800 × 480, DSI", 13, "middle", "white"))
    s.append(rect(880, 205, 110, 26, "#2e7d4f", "#1d5234", 4))
    s.append(text(935, 223, "Adapterplatine", 11, "middle", "white"))

    # Verbindungen oben
    s.append(line([(210, 97), (320, 97)], "#c0392b", 4))
    s.append(line([(210, 212), (300, 212), (300, 207), (395, 207)], "#e67e22", 8))
    s.append(text(255, 198, "Flachband CSI", 11, "middle", "#e67e22"))
    s.append(line([(614, 180), (760, 180), (760, 218), (880, 218)], "#e67e22", 8))
    s.append(text(705, 170, "Flachband DSI", 11, "middle", "#e67e22"))

    # --- Detail Pinleiste ---
    y0, dy = 330, 34
    xo, xe = 530, 570
    s.append(text(550, 305, "GPIO-Leiste (Draufsicht, Pins 1–20)", 14, "middle", weight="bold"))
    s.append(rect(510, y0 - 18, 80, 10 * dy, "#1a1a1a", "#000", 4))
    pins = [("3V3", "5V"), ("GPIO2", "5V"), ("GPIO3", "GND"), ("GPIO4", "GPIO14"),
            ("GND", "GPIO15"), ("GPIO17", "GPIO18"), ("GPIO27", "GND"),
            ("GPIO22", "GPIO23"), ("3V3", "GPIO24"), ("GPIO10", "GND")]
    used = {2, 6, 9, 11, 13, 14, 15, 16}

    def pin_color(name):
        if name == "5V":
            return "#c0392b"
        if name == "3V3":
            return "#e67e22"
        if name == "GND":
            return "#555"
        return "#27ae60"

    for r, (lo, le) in enumerate(pins):
        y = y0 + r * dy
        for col, name, x, anchor, lx in ((0, lo, xo, "end", 500), (1, le, xe, "start", 600)):
            n = 2 * r + 1 + col
            c = pin_color(name)
            hl = n in used
            s.append(f"<circle cx='{x}' cy='{y}' r='12' fill='{c}' stroke='{'#f1c40f' if hl else '#000'}' stroke-width='{3 if hl else 1}'/>")
            s.append(text(x, y + 4, str(n), 10, "middle", "white", "bold"))
            s.append(text(lx, y + 5, name, 13, anchor, "#222" if hl else "#999",
                          "bold" if hl else "normal"))

    def py(n):
        return y0 + ((n - 1) // 2) * dy

    # linke Taster (GND-Sammelschiene über Pin 9)
    bus_x = 140
    s.append(line([(440, py(9)), (bus_x, py(9))], "#555", 2.5))
    s.append(line([(bus_x, py(9)), (bus_x, py(15))], "#555", 3))
    for n, gpio, label in ((11, "GPIO17", "Zoom +"), (13, "GPIO27", "Zoom −"), (15, "GPIO22", "Foto")):
        y = py(n)
        s.append(line([(440, y), (300, y)], "#27ae60", 2.5))
        s.append(button_symbol(250, 300, y))
        s.append(line([(250, y), (bus_x, y)], "#555", 2.5))
        s.append(dot(bus_x, y))
        s.append(text(bus_x - 12, y + 5, label, 14, "end", weight="bold"))
    s.append(dot(bus_x, py(9)))
    s.append(text(bus_x - 12, py(9) + 5, "GND", 13, "end", "#555"))
    s.append(text(275, py(15) + 34, "Taster S1–S3 (Schließer)", 12, "middle", "#555"))

    # rechter Taster (Reset) gegen GND Pin 14
    bus_r = 940
    y16, y14 = py(16), py(14)
    s.append(line([(660, y16), (800, y16)], "#27ae60", 2.5))
    s.append(button_symbol(800, 850, y16))
    s.append(line([(850, y16), (bus_r, y16), (bus_r, y14), (660, y14)], "#555", 2.5))
    s.append(dot(bus_r, y16))
    s.append(text(bus_r + 12, y16 + 5, "Reset 1:1", 14, "start", weight="bold"))
    s.append(text(825, y16 + 34, "Taster S4", 12, "middle", "#555"))

    # Display-Stromversorgung von Pin 2 (5V) und Pin 6 (GND)
    s.append(line([(650, py(2)), (1010, py(2)), (1010, 231)], "#c0392b", 3))
    s.append(line([(660, py(6)), (1040, py(6)), (1040, 231), (990, 231), (990, 226)], "#333", 3))
    s.append(line([(1010, 231), (1010, 226)], "#c0392b", 3))
    s.append(text(1025, py(2) - 8, "5V → Display", 12, "end", "#c0392b"))
    s.append(text(1040, py(6) - 8, "GND → Display", 12, "end", "#333"))
    s.append(text(895, 262, "Jumper 5V/GND (nur falls Display", 11, "middle", "#555"))
    s.append(text(895, 277, "nicht separat per USB versorgt)", 11, "middle", "#555"))

    # Legende
    ly = 670
    s.append(line([(40, ly), (900, ly)], "#ddd", 1))
    items = [("#27ae60", "GPIO (Eingang, interner Pull-up)"), ("#555", "GND"),
             ("#c0392b", "5 V"), ("#e67e22", "Flachbandkabel")]
    x = 40
    for c, t in items:
        s.append(f"<rect x='{x}' y='{ly + 14}' width='22' height='10' fill='{c}'/>")
        s.append(text(x + 30, ly + 24, t, 12))
        x += 260
    s.append(text(40, ly + 46, "Keine Widerstände nötig: die Software schaltet die internen Pull-ups ein. "
                  "Taster drücken = Pin wird auf GND gezogen.", 12, "start", "#555"))
    s.append("</svg>")
    (OUT / "schaltplan.svg").write_text("\n".join(s))


# ------------------------------------------------------------------
# Bildschirm-Ansichten
# ------------------------------------------------------------------
def fake_sample(x, y, w, h, seed=3, clip_id="c"):
    """Fiktives Mikroskopbild: Zellen."""
    rnd = random.Random(seed)
    s = [f"<clipPath id='{clip_id}'><rect x='{x}' y='{y}' width='{w}' height='{h}'/></clipPath>",
         f"<g clip-path='url(#{clip_id})'>",
         f"<rect x='{x}' y='{y}' width='{w}' height='{h}' fill='#e9dcc4'/>"]
    for _ in range(int(w * h / 4200)):
        cx, cy = x + rnd.uniform(-20, w + 20), y + rnd.uniform(-20, h + 20)
        r = rnd.uniform(18, 42) * w / 640
        s.append(f"<ellipse cx='{cx:.0f}' cy='{cy:.0f}' rx='{r:.0f}' ry='{r * rnd.uniform(.7, 1):.0f}' "
                 f"fill='#d9b8c9' fill-opacity='0.55' stroke='#9c5a83' stroke-width='2'/>")
        s.append(f"<circle cx='{cx + rnd.uniform(-5, 5):.0f}' cy='{cy + rnd.uniform(-5, 5):.0f}' "
                 f"r='{r * .3:.0f}' fill='#6b2f5b' fill-opacity='0.8'/>")
    s.append("</g>")
    return "".join(s)


def ui_button(x, y, w, h, label, fill="#2b2b2b", size=22, fg="white", border="#555"):
    return (rect(x, y, w, h, fill, border, 12, 2) +
            text(x + w / 2, y + h / 2 + size * 0.36, label, size, "middle", fg, "bold"))


def screen_frame(inner):
    W, H = 880, 560
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}'>"
            f"<rect width='{W}' height='{H}' fill='white'/>"
            f"<rect x='10' y='10' width='860' height='540' rx='22' fill='#111'/>"
            f"<g transform='translate(40,40)'><rect width='800' height='480' fill='black'/>{inner}</g></svg>")


def main_screen():
    s = [fake_sample(0, 0, 640, 480, clip_id="m")]
    x, w = 648, 144
    s.append(text(720, 30, "Zoom 2.4×", 14, "middle", "#ccc"))
    y = 46
    for label, h, fill, size in (("Zoom +", 76, "#2b2b2b", 24), ("Zoom −", 76, "#2b2b2b", 24),
                                 ("1:1", 52, "#2b2b2b", 24), ("Bild", 52, "#2b2b2b", 24),
                                 ("Foto", 110, "#1f6f3f", 24), ("Beenden", 36, "#3a2020", 16)):
        s.append(ui_button(x, y, w, h, label, fill, size))
        y += h + 7
    (OUT / "ansicht_hauptbild.svg").write_text(screen_frame("".join(s)))


def slider_row(y, name, frac, value, enabled=True):
    c = "white" if enabled else "#777"
    gx, gw = 102, 160
    s = [text(8, y + 5, name, 14, "start", c),
         f"<rect x='{gx}' y='{y - 4}' width='{gw}' height='8' rx='4' fill='#555'/>",
         f"<rect x='{gx}' y='{y - 4}' width='{gw * frac:.0f}' height='8' rx='4' fill='{'#4a90d9' if enabled else '#555'}'/>",
         f"<circle cx='{gx + gw * frac:.0f}' cy='{y}' r='13' fill='{'white' if enabled else '#666'}'/>",
         text(332, y + 5, value, 14, "end", c)]
    return "".join(s)


def settings_screen():
    pw = 800 - 340
    ph = pw * 3 / 4
    s = [fake_sample(0, (480 - ph) / 2, pw, ph, clip_id="p")]
    g = ["<g transform='translate(460,0)'>",
         text(8, 26, "Bild-Einstellungen", 18, "start", "white", "bold")]
    rows = [("Helligkeit", .55, "+0.10"), ("Kontrast", .30, "1.20"),
            ("Sättigung", .40, "1.20"), ("Schärfe", .19, "1.5")]
    y = 60
    for n, f, v in rows:
        g.append(slider_row(y, n, f, v)); y += 40
    g.append(ui_button(8, y - 12, 158, 40, "Belichtung: Auto", size=14))
    g.append(ui_button(174, y - 12, 158, 40, "WB: Fixiert", size=14))
    y += 48
    g.append(slider_row(y, "Belicht.-Korr.", .56, "+0.5 EV")); y += 40
    g.append(slider_row(y, "Belicht.-Zeit", .54, "10 ms", False)); y += 40
    g.append(slider_row(y, "Verstärkung", .07, "2.0×", False))
    g.append(ui_button(8, 426, 158, 46, "Standard", size=16))
    g.append(ui_button(174, 426, 158, 46, "Fertig", "#1f6f3f", 16))
    g.append("</g>")
    (OUT / "ansicht_einstellungen.svg").write_text(screen_frame("".join(s) + "".join(g)))


wiring()
main_screen()
settings_screen()
print("ok")
