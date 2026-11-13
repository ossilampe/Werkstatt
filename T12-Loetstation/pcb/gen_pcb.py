"""Erzeugt t12-loetstation.kicad_pcb (Platzierung, Netze, Kontur, Bedruckung) + Netzklassen in .kicad_pro."""
import json
import os

import pcbnew

import design

FPDIR = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
OUT = "t12-loetstation.kicad_pcb"
PRO = "t12-loetstation.kicad_pro"
W, H = 150.0, 105.0          # Platinengroesse
OX, OY = 50.0, 50.0          # Lage im KiCad-Koordinatensystem
VERSION = "v1.1"


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


# ---------------------------------------------------------------- feste Positionen (x, y, Drehung)
# Klemmen oben: Drehung 180 -> Kabeleinfuehrung zur Platinenkante, Pin 1 rechts
FIXED = {
    "J1": (6, 30, -90),     # Einspeisung linke Kante, Pins nach unten
    "J2": (40, 6, 180),     # Kolben A
    "J3": (78, 6, 180),     # Kolben B
    "U3": (46.5, 4.5, 0),   # Kaltstelle direkt zwischen den Kolben-Klemmen
    "Q101": (24, 21, 0),
    "Q201": (62, 21, 0),
    "U4": (88, 44, 90),      # ADS1115 direkt aufgeloetet
    "J10": (144, 12, -90),
    "J11": (144, 27, -90),
    "J12": (144, 47, -90),
    "J9": (144, 67, -90),
    "J8": (144, 86, -90),
    "C1": (16, 64, 0),
    "J20": (8, 76, 0), "J21": (26, 76, 0), "J22": (8, 90, 0), "J23": (26, 90, 0),
    "J7": (118, 98.5, 0),   # Absaugung, Kabel nach unten
    "F1": (102, 92, 0),
    "J6": (86, 96, 0),
    "H1": (4, 4, 0), "H2": (146, 4, 0), "H3": (4, 101, 0), "H4": (146, 101, 0),
}

# ---------------------------------------------------------------- Gruppen, automatisch in Rechtecke gepackt
GROUPS = [
    (["R105", "R106", "C101"], (8, 16, 21, 26.5)),
    (["R101", "D101", "R102", "Q102", "R103", "R104"], (21, 27, 48, 38.5)),
    (["R205", "R206", "C201"], (46, 16, 59, 26.5)),
    (["R201", "D201", "R202", "Q202", "R203", "R204"], (51, 27, 78, 38.5)),
    (["R107", "D102", "R108", "C102", "R109", "R110", "C103", "U2", "C8",
      "R209", "R210", "C203", "R207", "D202", "R208", "C202", "C9"], (30, 39, 77, 57)),
    (["C2", "JP1"], (13, 42, 28, 52)),
    (["C10"], (84, 36, 96, 41)),
    (["U1", "C5", "C6", "C7", "C3", "C4"], (44, 62, 78, 82)),
    (["Q300", "R300", "R301", "D300", "Q310", "R310", "R311", "D310"], (80, 53, 132, 69)),
    (["R320", "R330", "C330", "R331", "C331", "R332", "C332"], (80, 70, 132, 82)),
]

# ---------------------------------------------------------------- Beschriftung der Anschluesse
PINLABELS = {
    "J1": ["+24V Logik", "+24V A", "+24V B", "GND", "PE"],
    "J2": ["H+", "H-", "PE", "SW", "GND"],
    "J3": ["H+", "H-", "PE", "SW", "GND"],
    "J6": ["-", "+", "T"],
    "J7": ["+12V", "-"],
    "J8": ["3V3", "DQ IO21", "GND"],
    "J9": ["A", "B", "C GND", "SW", "GND"],
    "J10": ["5V", "GND", "SDA IO8", "SCL IO7"],
    "J11": ["IO38 Heiz A", "IO39 Heiz B", "IO47 Luefter", "IO48 Absaug", "IO21 DS18B20", "GND"],
    "J12": ["IO40 Enc A", "IO41 Enc B", "IO42 Taster", "IO17 Griff A", "IO18 Griff B", "GND"],
    "J20": ["+", "-"], "J21": ["+", "-"], "J22": ["+", "-"], "J23": ["+", "-"],
}
TITLES = {
    "J1": "EINSPEISUNG 24V", "J2": "KOLBEN A", "J3": "KOLBEN B", "J6": "LUEFTER NT",
    "J7": "ABSAUGUNG 12V", "J8": "DS18B20", "J9": "DREHGEBER", "J10": "DISPLAY 1",
    "J11": "DISPLAY 2", "J12": "DISPLAY 3", "J20": "LM2596 5V IN", "J21": "5V OUT",
    "J22": "LM2596 12V IN", "J23": "12V OUT", "F1": "1A T",
}

NETCLASSES = {
    # name: (Leiterbahn mm, Abstand mm, Netze)
    "Heizung": (2.0, 0.4, ["+24V_A", "+24V_B", "HP_A", "HP_B"]),
    "Versorgung": (1.0, 0.3, ["+24V_L", "+12V", "+12V_ABS", "+5V", "FAN_NT", "FAN_ABS"]),
    "Masse": (0.4, 0.2, ["GND"]),
    "Mittel": (0.4, 0.2, ["+3V3", "PE"]),
}


def load_fp(fpid):
    lib, name = fpid.split(":")
    return pcbnew.FootprintLoad(os.path.join(FPDIR, lib + ".pretty"), name)


def courtyard(fp):
    c = fp.GetCourtyard(pcbnew.F_CrtYd)
    return c.BBox() if c.OutlineCount() else fp.GetBoundingBox(False)


def silk(board, text, x, y, size=1.0, angle=0, just="center", layer=pcbnew.F_SilkS, bold=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(0.2 if bold or size >= 1.5 else 0.15))
    t.SetPosition(pt(x, y))
    t.SetTextAngleDegrees(angle)
    t.SetHorizJustify({"left": pcbnew.GR_TEXT_H_ALIGN_LEFT, "right": pcbnew.GR_TEXT_H_ALIGN_RIGHT,
                       "center": pcbnew.GR_TEXT_H_ALIGN_CENTER}[just])
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    board.Add(t)
    return t


def line(board, x1, y1, x2, y2, layer=pcbnew.F_SilkS, w=0.15):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pt(x1, y1))
    s.SetEnd(pt(x2, y2))
    s.SetLayer(layer)
    s.SetWidth(mm(w))
    board.Add(s)


def rect(board, x1, y1, x2, y2, layer=pcbnew.F_SilkS, w=0.15):
    for a, b, c, d in ((x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)):
        line(board, a, b, c, d, layer, w)


def main():
    board = pcbnew.BOARD()
    nets = {}
    for name in sorted(design.nets()):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni

    fps = {}
    for p in design.PARTS:
        if not p["fp"]:
            continue
        fp = load_fp(p["fp"])
        fp.SetReference(p["ref"])
        fp.SetValue(p["value"])
        fp.SetFPIDAsString(p["fp"])
        if p["lcsc"]:
            fp.SetField("LCSC", p["lcsc"])
            f = fp.GetField("LCSC")
            if f:
                f.SetVisible(False)
        for pad in fp.Pads():
            net = p["pins"].get(pad.GetNumber())
            if net:
                pad.SetNet(nets[net])
        board.Add(fp)
        fps[p["ref"]] = fp
        # Wert auf F.Fab lassen, Referenz klein auf Bestueckungsdruck
        ref = fp.Reference()
        ref.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        ref.SetTextThickness(mm(0.12))
        if p["ref"].startswith("H"):
            ref.SetVisible(False)

    # feste Teile
    for ref, (x, y, rot) in FIXED.items():
        fp = fps[ref]
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pt(x, y))

    # Gruppen packen
    for refs, (x0, y0, x1, y1) in GROUPS:
        cx, cy, row_h = x0, y0, 0.0
        for ref in refs:
            fp = fps[ref]
            fp.SetOrientationDegrees(0)
            fp.SetPosition(pt(0, 0))
            bb = courtyard(fp)
            w = pcbnew.ToMM(bb.GetWidth()) + 1.6
            h = pcbnew.ToMM(bb.GetHeight()) + 2.6
            if cx + w > x1 and cx > x0:
                cx = x0
                cy += row_h
                row_h = 0.0
            if cy + h > y1:
                print("WARNUNG: Gruppe zu voll bei", ref)
            # Ursprung so setzen, dass die Courtyard-Box bei (cx, cy) beginnt
            dx = pcbnew.ToMM(bb.GetLeft()) - OX
            dy = pcbnew.ToMM(bb.GetTop()) - OY
            fp.SetPosition(pt(cx - dx + 0.8, cy - dy + 1.8))
            cx += w
            row_h = max(row_h, h)

    # Kontur
    rect(board, 0, 0, W, H, pcbnew.Edge_Cuts, 0.1)
    # Sperrrand 1 mm: keine Leiterbahnen/Vias direkt an der Kante (Freerouting kennt den Kantenabstand nicht)
    for (x1, y1, x2, y2) in ((0, 0, W, 1.0), (0, H - 1.0, W, H), (0, 0, 1.0, H), (W - 1.0, 0, W, H)):
        ka = pcbnew.ZONE(board)
        ka.SetIsRuleArea(True)
        ka.SetDoNotAllowTracks(True)
        ka.SetDoNotAllowVias(True)
        ka.SetDoNotAllowZoneFills(False)
        ka.SetDoNotAllowPads(False)
        ka.SetDoNotAllowFootprints(False)
        ka.SetLayerSet(pcbnew.LSET.AllCuMask())
        o = ka.Outline()
        o.NewOutline()
        for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
            o.Append(mm(OX + x), mm(OY + y))
        board.Add(ka)

    # Bedruckung: Anschlussnamen an jedem Pad
    for ref, labels in PINLABELS.items():
        fp = fps[ref]
        rot = fp.GetOrientationDegrees() % 360
        bb = courtyard(fp)
        for pad in fp.Pads():
            i = int(pad.GetNumber()) - 1
            if i >= len(labels):
                continue
            px = pcbnew.ToMM(pad.GetPosition().x) - OX
            py = pcbnew.ToMM(pad.GetPosition().y) - OY
            if ref in ("J10", "J11", "J12", "J9", "J8"):            # rechte Kante -> Text links daneben
                silk(board, labels[i], pcbnew.ToMM(bb.GetLeft()) - OX - 0.6, py, 1.0, 0, "right")
            elif ref == "J1":                                          # linke Kante -> Text rechts
                silk(board, labels[i], pcbnew.ToMM(bb.GetRight()) - OX + 0.6, py, 1.0, 0, "left")
            elif ref in ("J2", "J3"):                                  # oben -> Text darunter
                silk(board, labels[i], px, pcbnew.ToMM(bb.GetBottom()) - OY + 1.2, 1.0)
            else:                                                      # sonst ueber dem Pad
                silk(board, labels[i], px, pcbnew.ToMM(bb.GetTop()) - OY - 0.8, 1.0)
    for ref, title in TITLES.items():
        fp = fps[ref]
        fp.Reference().SetVisible(False)
        title = ref + " " + title
        bb = courtyard(fp)
        x = (pcbnew.ToMM(bb.GetLeft()) + pcbnew.ToMM(bb.GetRight())) / 2 - OX
        if ref in ("J10", "J11", "J12", "J9", "J8"):
            silk(board, title, pcbnew.ToMM(bb.GetLeft()) - OX - 9, pcbnew.ToMM(bb.GetTop()) - OY - 0.6, 1.0)
        elif ref == "J1":
            silk(board, "24V EIN", 1.5, pcbnew.ToMM(bb.GetBottom()) - OY + 1.8, 1.2, 0, "left", bold=True)
        elif ref in ("J2", "J3"):
            silk(board, title, x, pcbnew.ToMM(bb.GetBottom()) - OY + 2.8, 1.2, bold=True)
        else:
            silk(board, title, x, pcbnew.ToMM(bb.GetTop()) - OY - 2.6, 1.0)

    silk(board, "ADS1115", pcbnew.ToMM(fps["U4"].GetPosition().x) - OX, pcbnew.ToMM(fps["U4"].GetPosition().y) - OY + 4.2, 0.9)

    # Titel und Hinweise
    silk(board, "T12 LOETSTATION  2 KOLBEN  " + VERSION, 75, 102.3, 1.5, bold=True)
    silk(board, "Waveshare ESP32-S3 3.5  |  ADS1115  |  MCP6V27", 75, 99.6, 0.9)
    silk(board, "PE-GND", pcbnew.ToMM(fps["JP1"].GetPosition().x) - OX,
         pcbnew.ToMM(fps["JP1"].GetPosition().y) - OY + 2.6, 0.8)
    silk(board, "T12 LOETSTATION " + VERSION, 75, 50, 2.0, layer=pcbnew.B_SilkS, bold=True)

    board.Save(OUT)
    write_pro()
    # Kontrolle: Lage der Anschluesse ausgeben
    for ref in ("J1", "J2", "U4", "J10"):
        fp = fps[ref]
        print(ref, ["%s(%.1f,%.1f)" % (p.GetNumber(), pcbnew.ToMM(p.GetPosition().x) - OX,
                                      pcbnew.ToMM(p.GetPosition().y) - OY) for p in fp.Pads()])
    print("geschrieben:", OUT)


def write_pro():
    base = dict(bus_width=12, clearance=0.2, diff_pair_gap=0.25, diff_pair_via_gap=0.25,
                diff_pair_width=0.2, line_style=0, microvia_diameter=0.3, microvia_drill=0.1,
                pcb_color="rgba(0, 0, 0, 0.000)", schematic_color="rgba(0, 0, 0, 0.000)",
                track_width=0.25, tuning_profile="", via_diameter=0.8, via_drill=0.4, wire_width=6)
    classes = [dict(base, name="Default", priority=2147483647)]
    patterns = []
    for i, (name, (tw, cl, netlist)) in enumerate(NETCLASSES.items()):
        classes.append(dict(base, name=name, track_width=tw, clearance=cl, priority=i,
                            via_diameter=1.0 if tw >= 1 else 0.8, via_drill=0.5 if tw >= 1 else 0.4))
        patterns += [dict(netclass=name, pattern=n) for n in netlist]
    pro = {}
    if os.path.exists(PRO):
        try:
            with open(PRO, encoding="utf-8") as f:
                pro = json.load(f)
        except ValueError:
            pro = {}
    pro.setdefault("meta", {"filename": PRO, "version": 3})
    pro["net_settings"] = {"classes": classes, "meta": {"version": 5}, "net_colors": None,
                           "netclass_assignments": None, "netclass_patterns": patterns}
    rules = pro.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rules", {})
    rules.update(min_clearance=0.2, min_track_width=0.2, min_via_diameter=0.6, min_through_hole_diameter=0.3,
                 min_copper_edge_clearance=0.5, min_hole_clearance=0.25, min_hole_to_hole=0.25,
                 min_text_height=0.8, min_text_thickness=0.12, min_via_annular_width=0.13,
                 min_resolved_spokes=1)
    with open(PRO, "w", encoding="utf-8") as f:
        json.dump(pro, f, indent=2)


if __name__ == "__main__":
    main()
