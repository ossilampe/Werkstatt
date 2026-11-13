"""DSN exportieren -> Freerouting (ohne Oberflaeche) -> SES importieren -> Masseflaechen fuellen."""
import os
import subprocess
import sys

import pcbnew

PCB = "t12-loetstation.kicad_pcb"
DSN = "t12-loetstation.dsn"
SES = "t12-loetstation.ses"
FR = os.path.join(os.environ["LOCALAPPDATA"], "freerouting", "freerouting.exe")
OX, OY, W, H = 50.0, 50.0, 150.0, 105.0


def mm(v):
    return pcbnew.FromMM(v)


def export():
    b = pcbnew.LoadBoard(PCB)
    for t in list(b.GetTracks()):
        b.Remove(t)
    zs = [b.GetArea(i) for i in range(b.GetAreaCount())]
    for z in zs:
        if not z.GetIsRuleArea():
            b.Remove(z)
    b.Save(PCB)
    ok = pcbnew.ExportSpecctraDSN(b, DSN)
    print("DSN:", ok)


def run(passes):
    if os.path.exists(SES):
        os.remove(SES)
    cmd = [FR, "-de", DSN, "-do", SES, "-mp", str(passes), "-l", "de", "--gui.enabled=false"]
    print(" ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    tail = (r.stdout + r.stderr).strip().splitlines()[-15:]
    print("\n".join(tail))
    print("SES vorhanden:", os.path.exists(SES))


def zone(b, layer, net):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(net)
    z.SetLocalClearance(mm(0.4))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.4))
    z.SetThermalReliefSpokeWidth(mm(0.6))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    o.NewOutline()
    for x, y in ((0.6, 0.6), (W - 0.6, 0.6), (W - 0.6, H - 0.6), (0.6, H - 0.6)):
        o.Append(mm(OX + x), mm(OY + y))
    b.Add(z)


def importses():
    b = pcbnew.LoadBoard(PCB)
    ok = pcbnew.ImportSpecctraSES(b, SES)
    print("SES import:", ok)
    for t in b.GetTracks():   # Freerouting erzeugt an Pads manchmal 0,15-mm-Stummel
        if t.GetClass() == "PCB_TRACK" and t.GetWidth() < mm(0.2):
            t.SetWidth(mm(0.2))
    gnd = b.FindNet("GND")
    # Heizstrom-Rueckleitung (je 3 A): Masse-Pads der Klemmen voll an die Flaeche, keine Waermefallen-Stege
    for fp in b.GetFootprints():
        if fp.GetReference() in ("J1", "J2", "J3"):
            for pd in fp.Pads():
                if pd.GetNetname() == "GND":
                    pd.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    zone(b, pcbnew.B_Cu, gnd)
    zone(b, pcbnew.F_Cu, gnd)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(PCB)
    print("Leiterbahnen:", len(b.GetTracks()))


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    if step in ("export", "all"):
        export()
    if step in ("run", "all"):
        run(int(sys.argv[2]) if len(sys.argv) > 2 else 40)
    if step in ("import", "all"):
        importses()
