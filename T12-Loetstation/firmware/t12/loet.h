// =====================================================================
//  T12 Loetstation - Regelung fuer 2 Kolben
//  Wird ueber esphome: includes: eingebunden. Reines C++, keine id()-Aufrufe:
//  die YAML-Lambdas reichen die Werte herein.
// =====================================================================
#pragma once
#include <cmath>
#include <cstdint>

namespace t12 {

// Zustaende eines Kolbens (Reihenfolge = Anzeige-Text/Farbe unten)
enum : uint8_t {
  AUS = 0,
  HEIZT,
  BEREIT,
  KUEHLT,
  STANDBY,
  SCHLAF,
  KEINE_SPITZE,
  F_UEBERTEMP,
  F_AUFHEIZEN,
  F_MESSUNG,
};

struct Kanal {
  float temp = NAN;        // gefilterte Spitzentemperatur in Grad C
  float integ = 0.0f;      // I-Anteil des Reglers
  float duty = 0.0f;       // Tastverhaeltnis 0..MAX_DUTY
  uint8_t zustand = AUS;
  bool fehler = false;     // verriegelt, bis der Kolben aus- und wieder eingeschaltet wird
  uint32_t wache_ms = 0;   // Aufheiz-Waechter: seit wann volle Leistung
  float wache_temp = 0.0f; // Temperatur beim Start des Waechters
};

inline Kanal K[2];
inline uint32_t bewegt_ms[2] = {0, 0};  // letzte Bewegung am Griff (oder Bedienung)
inline uint32_t ein_ms[2] = {0, 0};     // Einschaltdauer im aktuellen Zyklus
inline float t_kalt = 25.0f;            // Kaltstelle (Gehaeuse, MCP9700 an ADS1115 A2)

// ---- Messkette ----
// OpAmp MCP6V27: Verstaerkung 1 + 220k/1k = 221
constexpr float VERSTAERKUNG = 221.0f;
// Startwert fuer das T12-Thermoelement (~21 uV/K). Die genaue Steigung
// kommt ueber "Faktor" in den Einstellungen (Kalibrierung mit Spitzenthermometer).
constexpr float GRAD_PRO_MV = 47.6f;
// Spitze fehlt / Thermoelement offen: 1M Pull-up zieht den OpAmp an 3,3 V
constexpr float SPITZE_FEHLT_V = 3.20f;

// ---- Sicherheit / Regelung ----
constexpr float MAX_TEMP = 480.0f;     // darueber sofort Fehler
constexpr float MAX_DUTY = 0.90f;      // Rest des 100-ms-Zyklus = Messfenster
constexpr uint32_t ZYKLUS_MS = 100;
constexpr float KP = 0.04f;            // pro Kelvin Abweichung
constexpr float KI = 0.0015f;          // pro Kelvin und Zyklus
constexpr float I_MAX = 0.5f;

inline const char *text(uint8_t z) {
  switch (z) {
    case HEIZT:        return "HEIZT";
    case BEREIT:       return "BEREIT";
    case KUEHLT:       return "KÜHLT AB";
    case STANDBY:      return "STANDBY";
    case SCHLAF:       return "SCHLÄFT";
    case KEINE_SPITZE: return "KEINE SPITZE";
    case F_UEBERTEMP:  return "FEHLER ÜBERTEMP.";
    case F_AUFHEIZEN:  return "FEHLER HEIZT NICHT";
    case F_MESSUNG:    return "FEHLER MESSUNG";
    default:           return "AUS";
  }
}

inline uint32_t farbe(uint8_t z) {
  switch (z) {
    case HEIZT:        return 0xFF8C00;  // orange
    case BEREIT:       return 0x3CC85A;  // gruen
    case KUEHLT:       return 0x4FC3F7;  // hellblau
    case STANDBY:      return 0x4A90E2;  // blau
    case SCHLAF:       return 0x7E7EC8;  // violett
    case KEINE_SPITZE: return 0xFFC107;  // gelb
    case F_UEBERTEMP:
    case F_AUFHEIZEN:
    case F_MESSUNG:    return 0xE53935;  // rot
    default:           return 0x8C8C8C;  // grau
  }
}

// Kolben eingeschaltet: Fehler quittieren, Regler zuruecksetzen, als "bewegt" werten
inline void einschalten(int i, uint32_t jetzt) {
  K[i].fehler = false;
  K[i].integ = 0.0f;
  K[i].wache_ms = 0;
  K[i].zustand = AUS;
  bewegt_ms[i] = jetzt;
}

// OpAmp-Ausgangsspannung (V) -> Spitzentemperatur
inline float temperatur(float v, float offset, float faktor_prozent) {
  float mv_spitze = v * 1000.0f / VERSTAERKUNG;
  return t_kalt + mv_spitze * GRAD_PRO_MV * (faktor_prozent / 100.0f) + offset;
}

// Ein Regelschritt (alle 100 ms, im Messfenster bei ausgeschalteter Heizung).
// v = OpAmp-Spannung in V (NAN bei I2C-Fehler). Rueckgabe: Tastverhaeltnis 0..MAX_DUTY
inline float schritt(int i, bool ein, float v, float soll, float offset, float faktor,
                     float standby_t, float standby_min, float schlaf_min, uint32_t jetzt) {
  Kanal &k = K[i];
  k.duty = 0.0f;

  // --- Messen ---
  if (std::isnan(v)) {
    k.temp = NAN;
    if (ein) { k.fehler = true; k.zustand = F_MESSUNG; } else k.zustand = AUS;
    return 0.0f;
  }
  bool spitze = v < SPITZE_FEHLT_V;
  if (spitze) {
    float t = temperatur(v, offset, faktor);
    k.temp = std::isnan(k.temp) ? t : k.temp * 0.6f + t * 0.4f;  // leicht glaetten
  } else {
    k.temp = NAN;
  }

  // --- Aus / Fehler / keine Spitze ---
  if (!ein) { k.zustand = AUS; k.integ = 0.0f; k.fehler = false; k.wache_ms = 0; return 0.0f; }
  if (k.fehler) return 0.0f;
  if (!spitze) { k.zustand = KEINE_SPITZE; k.integ = 0.0f; k.wache_ms = 0; return 0.0f; }
  if (k.temp > MAX_TEMP) { k.fehler = true; k.zustand = F_UEBERTEMP; return 0.0f; }

  // --- Standby / Schlafen (Zeit seit der letzten Bewegung am Griff) ---
  uint32_t ruhe = jetzt - bewegt_ms[i];
  if (schlaf_min > 0.0f && ruhe > (uint32_t) (schlaf_min * 60000.0f)) {
    k.zustand = SCHLAF; k.integ = 0.0f; k.wache_ms = 0;
    return 0.0f;  // wacht von selbst auf, sobald der Griff bewegt wird
  }
  float ziel = soll;
  bool standby = false;
  if (standby_min > 0.0f && ruhe > (uint32_t) (standby_min * 60000.0f) && standby_t < soll) {
    ziel = standby_t;
    standby = true;
  }

  // --- PI-Regler mit Vollgas beim Aufheizen ---
  float e = ziel - k.temp;
  float d;
  if (e > 30.0f) {
    d = 1.0f;
    k.integ = 0.0f;
  } else if (e < -20.0f) {
    d = 0.0f;
    k.integ = 0.0f;
  } else {
    k.integ += KI * e;
    if (k.integ < 0.0f) k.integ = 0.0f;
    if (k.integ > I_MAX) k.integ = I_MAX;
    d = KP * e + k.integ;
  }
  if (d < 0.0f) d = 0.0f;
  if (d > MAX_DUTY) d = MAX_DUTY;

  // --- Aufheiz-Waechter: aus kalt mit voller Leistung, aber keine Erwaermung ---
  if (d >= MAX_DUTY && k.temp < 150.0f) {
    if (k.wache_ms == 0) { k.wache_ms = jetzt; k.wache_temp = k.temp; }
    else if (jetzt - k.wache_ms > 15000 && k.temp - k.wache_temp < 20.0f) {
      k.fehler = true; k.zustand = F_AUFHEIZEN;
      return 0.0f;
    }
  } else {
    k.wache_ms = 0;
  }

  k.duty = d;
  if (standby) k.zustand = STANDBY;
  else if (std::fabs(e) <= 5.0f) k.zustand = BEREIT;
  else k.zustand = (e > 0.0f) ? HEIZT : KUEHLT;
  return d;
}

}  // namespace t12
