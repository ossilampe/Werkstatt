"""Erzeugt t12-loetstation.kicad_sch aus design.py (Netze als Labels an den Pins)."""
import datetime
import uuid

import design
import libs
from sexp import Sym, dump, find, find_all

S = Sym
GRID = 1.27
PROJECT = "t12-loetstation"
OUT = PROJECT + ".kicad_sch"
PAGE_W, PAGE_H = 594.0, 420.0  # A2 quer
MARGIN = 15.0


def uid():
    return str(uuid.uuid4())


def snap(v):
    return round(v / GRID) * GRID


def font(size=1.27, bold=False):
    f = [S("font"), [S("size"), size, size]]
    if bold:
        f.append([S("bold"), S("yes")])
    return f


def effects(size=1.27, justify=None, hide=False, bold=False):
    e = [S("effects"), font(size, bold)]
    if justify:
        e.append([S("justify")] + [S(j) for j in justify.split()])
    return e


def label_len(net):
    return len(net) * 1.05 + 1.5


# ---------- Einheiten je Bauteil (Multi-Unit-Symbole wie der Doppel-OpAmp) ----------
def units_of(p):
    pins = libs.pins(p["lib_id"])
    units = sorted({u for (u, *_r) in pins if u > 0}) or [0]
    out = []
    for u in units:
        up = [x for x in pins if x[0] in (u, 0)] if u else pins
        if u == 0 or any(x[0] == u for x in pins):
            out.append((u if u else 1, up))
    # Einheiten ohne angeschlossene Pins weglassen geht nicht (Symbol braucht alle) -> alle zeichnen
    return out


def bbox(upins, pins_nets):
    xs, ys = [-2.54, 2.54], [-2.54, 2.54]
    for (_u, num, _n, x, y, a, _t) in upins:
        net = pins_nets.get(num)
        L = label_len(net) if net else 1.5
        xs.append(x); ys.append(-y)
        a = int(a) % 360
        if a == 0:
            xs.append(x - L)
        elif a == 180:
            xs.append(x + L)
        elif a == 90:
            ys.append(-y + L)
        elif a == 270:
            ys.append(-y - L)
    return min(xs), min(ys), max(xs), max(ys)


def main():
    root_uuid = uid()
    items = []
    lib_ids = []

    # Bloecke sammeln
    blocks = {}
    for p in design.PARTS:
        blocks.setdefault(p["block"], []).append(p)

    # Platzierung: Bloecke spaltenweise, Bauteile im Block zeilenweise
    block_w = 182.0
    col_x = MARGIN
    col_y = MARGIN + 10
    for bname in sorted(blocks):
        parts = blocks[bname]
        # Teile vorbereiten
        entries = []
        for p in parts:
            for (unit, upins) in units_of(p):
                bb = bbox(upins, p["pins"])
                entries.append((p, unit, upins, bb))
        # Block-Hoehe vorab berechnen
        x = 0.0
        y = 10.0
        row_h = 0.0
        placed = []
        for (p, unit, upins, bb) in entries:
            w = bb[2] - bb[0] + 9
            h = bb[3] - bb[1] + 11
            if x + w > block_w - 4 and x > 0:
                x = 0.0
                y += row_h
                row_h = 0.0
            placed.append((p, unit, upins, bb, x - bb[0] + 4, y - bb[1] + 4))
            x += w
            row_h = max(row_h, h)
        notes = ["%s: %s" % (p["ref"], p["desc"]) for p in parts
                 if p["desc"] and not p["ref"].startswith("#")]
        bh = y + row_h + 4 + 3.2 * len(notes)
        if col_y + bh > PAGE_H - MARGIN:
            col_x += block_w + 8
            col_y = MARGIN + 10
        bx, by = col_x, col_y
        col_y += bh + 8

        # Rahmen + Titel
        items.append([S("rectangle"), [S("start"), bx, by], [S("end"), bx + block_w, by + bh],
                      [S("stroke"), [S("width"), 0.25], [S("type"), S("dash")]],
                      [S("fill"), [S("type"), S("none")]], [S("uuid"), uid()]])
        items.append([S("text"), bname, [S("exclude_from_sim"), S("no")],
                      [S("at"), bx + 2, by + 6, 0], effects(2.54, "left bottom", bold=True), [S("uuid"), uid()]])
        for i, n in enumerate(notes):
            items.append([S("text"), n, [S("exclude_from_sim"), S("no")],
                          [S("at"), bx + 3, by + y + row_h + 5 + 3.2 * i, 0], effects(1.5, "left bottom"),
                          [S("uuid"), uid()]])

        for (p, unit, upins, bb, ox, oy) in placed:
            sx, sy = snap(bx + ox), snap(by + oy)
            items.append(symbol_instance(p, unit, upins, sx, sy, root_uuid))
            for (_u, num, _n, px, py, a, _t) in upins:
                cx, cy = sx + px, sy - py
                net = p["pins"].get(num)
                if net:
                    la = (int(a) + 180) % 360
                    just = "left bottom" if la in (0, 90) else "right bottom"
                    items.append([S("label"), net, [S("at"), cx, cy, la], effects(1.27, just), [S("uuid"), uid()]])
                elif not p["ref"].startswith("H"):
                    items.append([S("no_connect"), [S("at"), cx, cy], [S("uuid"), uid()]])
            if p["lib_id"] not in lib_ids:
                lib_ids.append(p["lib_id"])

    lib_symbols = [S("lib_symbols")] + [libs.symbol(l) for l in lib_ids]
    today = datetime.date.today().isoformat()
    sch = [S("kicad_sch"), [S("version"), S("20250610")], [S("generator"), "eeschema"],
           [S("generator_version"), "10.0"], [S("uuid"), root_uuid], [S("paper"), "A2"],
           [S("title_block"), [S("title"), "T12 Lötstation - 2 Kolben"], [S("date"), today],
            [S("rev"), "1.0"], [S("company"), "ESP-Home-Projekte"],
            [S("comment"), 1, "Waveshare ESP32-S3-Touch-LCD-3.5, ADS1115-Modul, MCP6V27"],
            [S("comment"), 2, "Erzeugt mit pcb/gen_sch.py aus pcb/design.py"]],
           lib_symbols] + items + [
        [S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]],
        [S("embedded_fonts"), S("no")]]
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(dump(sch) + "\n")
    print("geschrieben:", OUT, "Bauteile:", len(design.PARTS))


def prop_at(lib_id, key, sx, sy):
    p = libs.prop(lib_id, key)
    if p is None:
        return [S("at"), sx, sy, 0], None
    at = find(p, "at")
    eff = find(p, "effects")
    return [S("at"), sx + float(at[1]), sy - float(at[2]), float(at[3]) if len(at) > 3 else 0], eff


def symbol_instance(p, unit, upins, sx, sy, root_uuid):
    lib_id = p["lib_id"]
    node = [S("symbol"), [S("lib_id"), lib_id], [S("at"), sx, sy, 0], [S("unit"), unit],
            [S("exclude_from_sim"), S("no")], [S("in_bom"), S("no") if p["ref"].startswith(("#", "H")) else S("yes")],
            [S("on_board"), S("no") if p["ref"].startswith("#") else S("yes")], [S("dnp"), S("no")],
            [S("uuid"), uid()]]
    fields = [("Reference", p["ref"], False), ("Value", p["value"], p["ref"].startswith("#")),
              ("Footprint", p["fp"], True), ("Datasheet", "", True), ("Description", p["desc"], True)]
    if p["lcsc"]:
        fields.append(("LCSC", p["lcsc"], True))
    for key, val, hidden in fields:
        at, eff = prop_at(lib_id, key, sx, sy)
        if key == "Reference" and p["ref"].startswith("#"):
            hidden = True
        pr = [S("property"), key, val, at]
        if hidden:
            pr.append([S("hide"), S("yes")])
        pr.append(eff if eff is not None and key in ("Reference", "Value") else effects())
        node.append(pr)
    for (_u, num, *_r) in upins:
        node.append([S("pin"), num, [S("uuid"), uid()]])
    node.append([S("instances"), [S("project"), PROJECT,
                                  [S("path"), "/" + root_uuid, [S("reference"), p["ref"]], [S("unit"), unit]]]])
    return node


if __name__ == "__main__":
    main()
