# T12 Lötstation – Bestellung bei JLCPCB

Platine: 150 × 105 mm, 2 Lagen, 1,6 mm, Stand v1.1 (2026-11-13, Messeingang korrigiert)

## Dateien
| Datei | Wofür |
|---|---|
| `T12-Loetstation_Gerber.zip` | Platine (Kupfer, Lötstopp, Bedruckung, Bohrungen) – **immer** |
| `T12-Loetstation_BOM.csv` | Stückliste mit LCSC-Nummern – nur für Bestückung |
| `T12-Loetstation_CPL.csv` | Position/Drehung der SMD-Teile – nur für Bestückung |
| `Selbst_loeten.csv` | bedrahtete Teile, die du selbst lötest |

## Preis A – unbestückt
1. https://cart.jlcpcb.com/ → **Add gerber file** → `T12-Loetstation_Gerber.zip`
2. Prüfen: Layers 2, Dimensions 150 × 105 mm (wird erkannt)
3. Quantity 5, PCB Thickness 1.6, Color nach Wunsch, Surface Finish **HASL (lead free)**
4. „PCB Assembly“ **aus** lassen → Preis ablesen

## Preis B – SMD bestückt
1–3 wie oben, dann:

4. **PCB Assembly** einschalten (geht erst, wenn die Gerber-Datei hochgeladen ist) → PCBA Type *Economic*, Assembly Side **Top Side**, PCBA Qty z. B. 2.
   Hier gibt es noch **kein** Upload-Feld für BOM/CPL – das kommt erst im nächsten Schritt.
5. Rechts in der Preisübersicht auf **NEXT** (statt „Save to Cart“) → Gerber-Vorschau bestätigen → **NEXT**
6. Jetzt erscheint „Add BOM File“ / „Add CPL File“: `T12-Loetstation_BOM.csv` und `T12-Loetstation_CPL.csv` hochladen → **Process BOM & CPL**
7. Teileliste prüfen: alle 21 Positionen müssen ein Häkchen haben
8. **Vorschau / Placement**: Drehung prüfen, vor allem
   - U2 MCP6V27 (SOIC-8), U4 ADS1115 (TSSOP-10), U1 AMS1117: Punkt/Pin 1 auf der Markierung im Bestückungsdruck
   - D101/D201 Z-Diode, D300/D310 SS14: Ring (Kathode) zur Strichmarkierung
   - Transistoren/BAT54S (SOT-23): 3 Pins müssen auf den 3 Pads liegen
   Falsch gedrehte Teile in der Vorschau mit „Rotate“ korrigieren.
9. **Next** → Preis ablesen. Erst „Save to Cart“/„Place Order“ würde bestellen.

Hinweis: 4 Teile sind „Extended“ (MCP6V27, ADS1115, BAT54S, Z-Diode 15 V) – JLC berechnet dafür je ca. 3 $ Rüstgebühr.

## Selbst löten (bedrahtet)
J1/J2/J3 Schraubklemme 5-pol. RM 5,08 · J7 Schraubklemme 2-pol. RM 5,08 · J8 XH 3-pol. · J9 XH 5-pol. · J10 XH 4-pol. · J11/J12 XH 6-pol. (stehend) ·
Q101/Q201 IRF5305 · C1 470 µF/50 V · C3/C4 100 µF/25 V · U3 MCP9700 (TO-92) ·
F1 Sicherungshalter TR5 + 1 A T · J6 Lüfterstecker KK 2,54 3-pol. ·
J20–J23 Kabel zu den LM2596-Modulen · JP1 Lötbrücke (offen lassen)

## Kabel zu den JST-XH-Buchsen (separat kaufen, je ca. 20 cm)
| Buchse | Pole | Gegenstück |
|---|---|---|
| J8 DS18B20 | 3 | XHP-3 mit Litze, anderes Ende an den Fühler löten |
| J9 Drehgeber | 5 | XHP-5 mit Litze, anderes Ende an den Encoder löten |
| J10 Display 5V/GND/SDA/SCL | 4 | XHP-4 mit Litze, Display-Seite Dupont-Buchse 2,54 |
| J11 Display Ausgänge | 6 | XHP-6 mit Litze, Display-Seite Dupont-Buchse 2,54 |
| J12 Display Eingänge | 6 | XHP-6 mit Litze, Display-Seite Dupont-Buchse 2,54 |
