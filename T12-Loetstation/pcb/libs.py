"""Symbole aus den KiCad-Bibliotheken laden (inkl. 'extends' aufloesen) und Pins auslesen."""
import copy
import os

from sexp import Sym, find, find_all, parse

KICAD = r"C:\Program Files\KiCad\10.0\share\kicad"
SYMDIR = os.path.join(KICAD, "symbols")
_cache = {}


def _lib(name):
    if name not in _cache:
        with open(os.path.join(SYMDIR, name + ".kicad_sym"), encoding="utf-8") as f:
            root = parse(f.read())
        _cache[name] = {s[1]: s for s in find_all(root, "symbol")}
    return _cache[name]


def symbol(lib_id):
    """Liefert die flache Symbol-Definition mit Namen 'Lib:Name'."""
    lib, name = lib_id.split(":")
    syms = _lib(lib)
    s = copy.deepcopy(syms[name])
    ext = find(s, "extends")
    if ext:
        parent = symbol(lib + ":" + ext[1])
        pname = parent[1].split(":")[1]
        flat = copy.deepcopy(parent)
        # Eigenschaften des Kindes uebernehmen
        child_props = {p[1]: p for p in find_all(s, "property")}
        for i, x in enumerate(flat):
            if isinstance(x, list) and x and x[0] == "property" and x[1] in child_props:
                flat[i] = child_props.pop(x[1])
        for p in child_props.values():
            flat.append(p)
        # Untersymbole umbenennen
        for x in flat:
            if isinstance(x, list) and x and x[0] == "symbol":
                x[1] = x[1].replace(pname + "_", name + "_", 1)
        s = flat
    s[1] = lib_id
    return s


def pins(lib_id):
    """[(unit, number, name, x, y, angle, type)] - Koordinaten im Symbolsystem (y nach oben)."""
    s = symbol(lib_id)
    base = lib_id.split(":")[1]
    out = []
    for sub in find_all(s, "symbol"):
        suffix = sub[1][len(base) + 1:]
        unit, style = (int(v) for v in suffix.split("_"))
        if style > 1:
            continue
        for p in find_all(sub, "pin"):
            at = find(p, "at")
            out.append((unit, find(p, "number")[1], find(p, "name")[1],
                        float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0, str(p[1])))
    return out


def prop(lib_id, key):
    for p in find_all(symbol(lib_id), "property"):
        if p[1] == key:
            return p
    return None


if __name__ == "__main__":
    import sys
    for lid in sys.argv[1:]:
        print("==", lid)
        for pin in sorted(pins(lid)):
            print("  unit %d  pin %-3s %-6s at (%g, %g) %g  %s" % pin)
