"""JLCPCB-Fertigungsdaten: Gerber+Bohrdaten (zip), Stueckliste (BOM) und Bestueckungsdatei (CPL).

Bestueckt werden alle Teile mit LCSC-Nummer: SMD + Schraubklemmen/JST-XH (bedrahtet, Oberseite).
Teile ohne LCSC-Nummer loetest du selbst.
"""
import csv
import os
import re
import shutil
import subprocess
import zipfile
from collections import OrderedDict

import pcbnew

KCLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
PCB = "t12-loetstation.kicad_pcb"
OUT = "jlc"
GERB = os.path.join(OUT, "gerber")

# Drehkorrektur KiCad -> JLC-Bauteilbibliothek (Erfahrungswerte, JLCKicadTools).
# In der JLC-Vorschau trotzdem pruefen!
ROT_FIX = [(r"^SOT-23$", 180), (r"^SOT-223", 180), (r"^SOIC-8", 270), (r"^TSSOP-10", 270)]  # D_SMA: 0 (in JLC-Vorschau geprueft 2026-11-13, 180 war falsch)

# False: Schraubklemmen/JST-XH (bedrahtet) loetest du selbst, JLC setzt nur SMD
BESTUECKE_THT = False

# Herstellerbezeichnung fuer die bedrahteten Steckverbinder (statt "Kolben A" usw.)
MPN = {"C42377750": "WJ500V-5.08-5P", "C8465": "WJ500V-5.08-2P", "C144394": "B3B-XH-A",
       "C157991": "B5B-XH-A", "C144395": "B4B-XH-A", "C144397": "B6B-XH-A"}


def run(args):
    r = subprocess.run([KCLI] + args, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr)
        raise SystemExit("kicad-cli Fehler")


def gerber():
    shutil.rmtree(GERB, ignore_errors=True)
    os.makedirs(GERB)
    layers = "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
    run(["pcb", "export", "gerbers", "--layers", layers, "--subtract-soldermask", "--no-x2",
         "-o", GERB + os.sep, PCB])
    run(["pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm",
         "--excellon-separate-th", "--generate-map", "--map-format", "gerberx2", "-o", GERB + os.sep, PCB])
    z = os.path.join(OUT, "T12-Loetstation_Gerber.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(os.listdir(GERB)):
            zf.write(os.path.join(GERB, f), f)
    print("Gerber:", z, len(os.listdir(GERB)), "Dateien")


def bom_cpl():
    b = pcbnew.LoadBoard(PCB)
    groups = OrderedDict()
    cpl = []
    skipped = []
    for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        lcsc = fp.GetFieldText("LCSC") if fp.HasField("LCSC") else ""
        smd = fp.GetAttributes() & pcbnew.FP_SMD
        if not lcsc or (not smd and not BESTUECKE_THT):
            if not ref.startswith(("H", "#")):
                skipped.append(ref)
            continue
        name = fp.GetFPID().GetLibItemName().wx_str()
        val = fp.GetValue() if fp.GetAttributes() & pcbnew.FP_SMD else MPN.get(lcsc, fp.GetValue())
        key = (val, name, lcsc)
        groups.setdefault(key, []).append(ref)
        pos = fp.GetPosition()
        if not fp.GetAttributes() & pcbnew.FP_SMD:
            # bedrahtet: KiCad-Ursprung liegt auf Pin 1 -> Mitte der Pads nehmen
            xs = [pd.GetPosition().x for pd in fp.Pads()]
            ys = [pd.GetPosition().y for pd in fp.Pads()]
            pos = pcbnew.VECTOR2I((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2)
        rot = fp.GetOrientationDegrees()
        for pat, add in ROT_FIX:
            if re.search(pat, name):
                rot += add
                break
        rot = rot % 360
        cpl.append([ref, "%.3fmm" % pcbnew.ToMM(pos.x), "%.3fmm" % -pcbnew.ToMM(pos.y),
                    "Top" if fp.GetLayer() == pcbnew.F_Cu else "Bottom", "%g" % rot])
    with open(os.path.join(OUT, "T12-Loetstation_BOM.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (val, name, lcsc), refs in groups.items():
            w.writerow([val, ",".join(refs), name, lcsc])
    with open(os.path.join(OUT, "T12-Loetstation_CPL.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerows(cpl)
    print("BOM: %d Sorten, CPL: %d Teile" % (len(groups), len(cpl)))
    print("selbst loeten (bedrahtet / ohne LCSC):", ", ".join(skipped))
    # Liste fuers Selberloeten
    parts = {p.GetReference(): p for p in b.GetFootprints()}
    with open(os.path.join(OUT, "Selbst_loeten.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Referenz", "Wert", "Bauform"])
        for r in skipped:
            p = parts[r]
            w.writerow([r, p.GetValue(), p.GetFPID().GetLibItemName().wx_str()])


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    gerber()
    bom_cpl()
