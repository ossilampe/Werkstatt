"""T12 Loetstation - Bauteil- und Netzliste (eine Quelle fuer Schaltplan und Platine).

Jedes Bauteil: ref, lib_id, value, footprint, {pin: netz}, block, lcsc (fuer JLC-Bestueckung, None = selbst loeten)
Netz None = nicht angeschlossen (No-Connect).
"""

R0805 = "Resistor_SMD:R_0805_2012Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
SOT23 = "Package_TO_SOT_SMD:SOT-23"
TB = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-%d-5.08_1x%02d_P5.08mm_Horizontal"
XH = "Connector_JST:JST_XH_B%dB-XH-A_1x%02d_P2.50mm_Vertical"
WIRE2 = "Connector_Wire:SolderWire-0.5sqmm_1x02_P4.6mm_D0.9mm_OD2.1mm"

PARTS = []


def part(ref, lib_id, value, fp, pins, block, lcsc=None, desc=""):
    PARTS.append(dict(ref=ref, lib_id=lib_id, value=value, fp=fp, pins=pins,
                      block=block, lcsc=lcsc, desc=desc))


def R(ref, value, a, b, block, lcsc=None):
    part(ref, "Device:R", value, R0805, {"1": a, "2": b}, block, lcsc)


def C(ref, value, a, b, block, lcsc=None):
    part(ref, "Device:C", value, C0805, {"1": a, "2": b}, block, lcsc)


# ------------------------------------------------------------------ Einspeisung
B = "1 Einspeisung 24 V"
part("J1", "Connector:Screw_Terminal_01x05", "24V Einspeisung", TB % (5, 5),
     {"1": "+24V_L", "2": "+24V_A", "3": "+24V_B", "4": "GND", "5": "PE"}, B,
     desc="1 +24V Logik, 2 +24V Kolben A (nach Sicherung), 3 +24V Kolben B (nach Sicherung), 4 GND, 5 Schutzleiter")
part("C1", "Device:C_Polarized", "470uF 50V", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm",
     {"1": "+24V_L", "2": "GND"}, B)
C("C2", "100nF", "+24V_L", "GND", B, "C49678")
part("JP1", "Jumper:SolderJumper_2_Open", "PE-GND", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
     {"1": "PE", "2": "GND"}, B, desc="offen = Schutzleiter getrennt von GND")
for n, net in (("1", "+24V_L"), ("2", "+24V_A"), ("3", "+24V_B"), ("4", "GND")):
    part("#FLG0" + n, "power:PWR_FLAG", "PWR_FLAG", "", {"1": net}, B)

# ------------------------------------------------------------------ Spannungen
B = "2 Spannungswandler"
part("J20", "Connector_Generic:Conn_01x02", "LM2596 5V Eingang", WIRE2, {"1": "+24V_L", "2": "GND"}, B)
part("J21", "Connector_Generic:Conn_01x02", "LM2596 5V Ausgang", WIRE2, {"1": "+5V", "2": "GND"}, B)
part("J22", "Connector_Generic:Conn_01x02", "LM2596 12V Eingang", WIRE2, {"1": "+24V_L", "2": "GND"}, B)
part("J23", "Connector_Generic:Conn_01x02", "LM2596 12V Ausgang", WIRE2, {"1": "+12V", "2": "GND"}, B)
part("C3", "Device:C_Polarized", "100uF 25V", "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm", {"1": "+5V", "2": "GND"}, B)
part("C4", "Device:C_Polarized", "100uF 25V", "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm", {"1": "+12V", "2": "GND"}, B)
part("U1", "Regulator_Linear:AMS1117-3.3", "AMS1117-3.3", "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
     {"1": "GND", "2": "+3V3", "3": "+5V"}, B, lcsc="C6186")
C("C5", "10uF", "+5V", "GND", B, "C15850")
C("C6", "10uF", "+3V3", "GND", B, "C15850")
C("C7", "100nF", "+3V3", "GND", B, "C49678")
part("#FLG05", "power:PWR_FLAG", "PWR_FLAG", "", {"1": "+5V"}, B)
part("#FLG06", "power:PWR_FLAG", "PWR_FLAG", "", {"1": "+12V"}, B)


# ------------------------------------------------------------------ Heizung + Messung je Kolben
def kanal(k, n, gpio_heiz, opamp_unit):
    """k = 'A'/'B', n = Nummernbasis fuer Referenzen."""
    B = ("3 Kolben A" if k == "A" else "4 Kolben B")
    v24 = "+24V_" + k
    part("Q%d" % (n + 1), "Transistor_FET:Q_PMOS_GDS", "IRF5305", "Package_TO_SOT_THT:TO-220-3_Vertical",
         {"1": "GATE_" + k, "2": "HP_" + k, "3": v24}, B, desc="P-MOSFET Heizung, Plus-Seite")
    R("R%d" % (n + 1), "10k", v24, "GATE_" + k, B, "C17414")
    part("D%d" % (n + 1), "Device:D_Zener", "15V", "Diode_SMD:D_MiniMELF",
         {"1": v24, "2": "GATE_" + k}, B, lcsc="C181074", desc="Gate-Schutz")
    R("R%d" % (n + 2), "10k", "GATE_" + k, "DRV_" + k, B, "C17414")
    part("Q%d" % (n + 2), "Transistor_BJT:Q_NPN_BEC", "MMBT3904", SOT23,
         {"1": "BASE_" + k, "2": "GND", "3": "DRV_" + k}, B, lcsc="C20526")
    R("R%d" % (n + 3), "1k", gpio_heiz, "BASE_" + k, B, "C17513")
    R("R%d" % (n + 4), "10k", "BASE_" + k, "GND", B, "C17414")
    # Klemme Kolben
    part("J%d" % (n // 10 + 0), "Connector:Screw_Terminal_01x05", "Kolben " + k, TB % (5, 5),
         {"1": "HP_" + k, "2": "GND", "3": "PE", "4": "SW_" + k, "5": "GND"}, B,
         desc="1 Heizung+, 2 Heizung-, 3 Erde Spitze, 4 Griffschalter, 5 Schalter GND")
    # Griffschalter-Eingang
    R("R%d" % (n + 5), "1k", "SW_" + k, "GRIFF_" + k, B, "C17513")
    R("R%d" % (n + 6), "10k", "GRIFF_" + k, "+3V3", B, "C17414")
    C("C%d" % (n + 1), "10nF", "GRIFF_" + k, "GND", B, "C1710")
    # Messung
    R("R%d" % (n + 7), "47k", "HP_" + k, "MESS_" + k, B, "C17713")
    part("D%d" % (n + 2), "Diode:BAT54S", "BAT54S", SOT23,
         {"1": "GND", "2": "+3V3", "3": "MESS_" + k}, B, lcsc="C47546", desc="Klemmung Messeingang")
    # Pull-up VOR dem 47k (an der Spitze): mit Spitze nur 3,3 uA * 8 Ohm = 26 uV Versatz,
    # ohne Spitze zieht er den Eingang auf 3,3 V (Erkennung "keine Spitze")
    R("R%d" % (n + 8), "1M", "HP_" + k, "+3V3", B, "C17514")
    # 1 nF: Zeitkonstante 47 us -> nach Heizung-aus in < 1 ms eingeschwungen
    C("C%d" % (n + 2), "1nF", "MESS_" + k, "GND", B, "C46653")
    R("R%d" % (n + 9), "1k", "FB_" + k, "GND", B, "C17513")
    R("R%d" % (n + 10), "220k", "FB_" + k, "ADC_" + k, B, "C17556")
    C("C%d" % (n + 3), "100pF", "FB_" + k, "ADC_" + k, B, "C1790")
    if opamp_unit == 1:
        return {"3": "MESS_" + k, "2": "FB_" + k, "1": "ADC_" + k}
    return {"5": "MESS_" + k, "6": "FB_" + k, "7": "ADC_" + k}


op = {}
op.update(kanal("A", 100, "HEIZ_A", 1))
op.update(kanal("B", 200, "HEIZ_B", 2))
# J10 / J20 kollidiert -> Kolben-Klemmen umbenennen
for p in PARTS:
    if p["value"] == "Kolben A":
        p["ref"] = "J2"
    if p["value"] == "Kolben B":
        p["ref"] = "J3"

B = "5 Messverstaerker / ADC"
op.update({"4": "GND", "8": "+3V3"})
part("U2", "Amplifier_Operational:Opamp_Dual", "MCP6V27-E/SN", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     op, B, lcsc="C636392", desc="Auto-Zero OpAmp, Verstaerkung 221")
C("C8", "100nF", "+3V3", "GND", B, "C49678")
# ADS1115 direkt aufgeloetet (TSSOP/MSOP-10), Adresse 0x48 (ADDR an GND), A3 unbenutzt an GND
part("U4", "Analog_ADC:ADS1115IDGS", "ADS1115IDGSR", "Package_SO:TSSOP-10_3x3mm_P0.5mm",
     {"1": "GND", "2": None, "3": "GND", "4": "ADC_A", "5": "ADC_B", "6": "KALT", "7": "GND",
      "8": "+3V3", "9": "SDA", "10": "SCL"}, B, lcsc="C37593", desc="16-Bit-ADC, I2C 0x48")
C("C10", "100nF", "+3V3", "GND", B, "C49678")
part("U3", "Sensor_Temperature:MCP9700x-ETT", "MCP9700-E/TO", "Package_TO_SOT_THT:TO-92_Inline_Wide",
     {"1": "+3V3", "2": "KALT", "3": "GND"}, B, desc="Kaltstelle, nahe Kolben-Klemmen")
C("C9", "100nF", "+3V3", "GND", B, "C49678")

# ------------------------------------------------------------------ Luefter
B = "6 Luefter 12 V"
for k, n, gpio, desc in (("NT", 300, "LUEFTER", "Netzteil-Luefter"), ("ABS", 310, "ABSAUG", "Absaugung")):
    part("Q%d" % n, "Transistor_FET:Q_NMOS_GSD", "AO3400A", SOT23,
         {"1": "G_" + k, "2": "GND", "3": "FAN_" + k}, B, lcsc="C20917", desc=desc)
    R("R%d" % n, "100", gpio, "G_" + k, B, "C17408")
    R("R%d" % (n + 1), "100k", "G_" + k, "GND", B, "C149504")
    part("D%d" % n, "Device:D_Schottky", "SS14", "Diode_SMD:D_SMA",
         {"1": "+12V" if k == "NT" else "+12V_ABS", "2": "FAN_" + k}, B, lcsc="C2480", desc="Freilauf")
part("J6", "Connector_Generic:Conn_01x03", "Luefter Netzteil", "Connector_Molex:Molex_KK-254_AE-6410-03A_1x03_P2.54mm_Vertical",
     {"1": "FAN_NT", "2": "+12V", "3": None}, B, desc="3-Pin-Luefter: 1 GND(geschaltet), 2 +12V, 3 Tacho (frei)")
part("F1", "Device:Fuse", "1A T", "Fuse:Fuseholder_TR5_Littelfuse_No560_No460",
     {"1": "+12V", "2": "+12V_ABS"}, B, desc="Kleinstsicherung TR5")
part("J7", "Connector:Screw_Terminal_01x02", "Absaugung", TB % (2, 2),
     {"1": "+12V_ABS", "2": "FAN_ABS"}, B, desc="zur Cinch-Buchse: 1 +12V (Mitte), 2 Minus (geschaltet)")

# ------------------------------------------------------------------ Peripherie
B = "7 Bedienung / Fuehler"
part("J8", "Connector_Generic:Conn_01x03", "DS18B20", XH % (3, 3), {"1": "+3V3", "2": "DS_DATA", "3": "GND"}, B)
R("R320", "4.7k", "DS_DATA", "+3V3", B, "C17673")
part("J9", "Connector_Generic:Conn_01x05", "Drehgeber", XH % (5, 5),
     {"1": "ENC_A", "2": "ENC_B", "3": "GND", "4": "ENC_SW", "5": "GND"}, B, desc="A, B, C(GND), Taster, Taster GND")
for i, net in enumerate(("ENC_A", "ENC_B", "ENC_SW")):
    R("R%d" % (330 + i), "10k", net, "+3V3", B, "C17414")
    C("C%d" % (330 + i), "10nF", net, "GND", B, "C1710")

# ------------------------------------------------------------------ Display
B = "8 Verbindung Display (Waveshare ESP32-S3 3,5)"
part("J10", "Connector_Generic:Conn_01x04", "Display Versorgung/I2C", XH % (4, 4),
     {"1": "+5V", "2": "GND", "3": "SDA", "4": "SCL"}, B, desc="5V(Pin2), GND, SDA GPIO8, SCL GPIO7")
part("J11", "Connector_Generic:Conn_01x06", "Display Ausgaenge", XH % (6, 6),
     {"1": "HEIZ_A", "2": "HEIZ_B", "3": "LUEFTER", "4": "ABSAUG", "5": "DS_DATA", "6": "GND"}, B,
     desc="GPIO38, GPIO39, GPIO47, GPIO48, GPIO21, GND")
part("J12", "Connector_Generic:Conn_01x06", "Display Eingaenge", XH % (6, 6),
     {"1": "ENC_A", "2": "ENC_B", "3": "ENC_SW", "4": "GRIFF_A", "5": "GRIFF_B", "6": "GND"}, B,
     desc="GPIO40, GPIO41, GPIO42, GPIO17, GPIO18, GND")

# ------------------------------------------------------------------ Mechanik
for i in range(1, 5):
    part("H%d" % i, "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", {}, "9 Mechanik")

# Netz -> Display-Signalnamen fuer Bedruckung
GPIO = {"HEIZ_A": "IO38", "HEIZ_B": "IO39", "LUEFTER": "IO47", "ABSAUG": "IO48", "DS_DATA": "IO21",
        "ENC_A": "IO40", "ENC_B": "IO41", "ENC_SW": "IO42", "GRIFF_A": "IO17", "GRIFF_B": "IO18",
        "SDA": "IO8", "SCL": "IO7"}


def nets():
    out = {}
    for p in PARTS:
        for pin, net in p["pins"].items():
            if net:
                out.setdefault(net, []).append((p["ref"], pin))
    return out


# ------------------------------------------------------------------ bedrahtete Steckverbinder, von JLC bestueckt
# Schraubklemmen Kangnex WJ500V-5.08 (Bauform wie Phoenix MKDS 1,5), JST XH original
THT_LCSC = {"J1": "C42377750", "J2": "C42377750", "J3": "C42377750", "J7": "C8465",
            "J8": "C144394", "J9": "C157991", "J10": "C144395", "J11": "C144397", "J12": "C144397"}
for p in PARTS:
    if p["ref"] in THT_LCSC:
        p["lcsc"] = THT_LCSC[p["ref"]]


if __name__ == "__main__":
    refs = [p["ref"] for p in PARTS]
    dup = {r for r in refs if refs.count(r) > 1}
    print("Bauteile:", len(PARTS), "doppelte Referenzen:", dup or "keine")
    for net, conns in sorted(nets().items()):
        flag = "  <-- nur 1 Anschluss!" if len(conns) < 2 else ""
        print("%-10s %s%s" % (net, " ".join("%s.%s" % c for c in conns), flag))
