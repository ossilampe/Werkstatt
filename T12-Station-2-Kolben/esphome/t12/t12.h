// T12 Lötstation – Hilfsfunktionen für die ESPHome-Oberfläche
// Zwei KSGER-v2-Module mit UART-Firmware (Werkstatt/T12-Loetstation/modul/firmware-uart)
#pragma once
#include <string>
#include <vector>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include "esphome/core/hal.h"
#include "esphome/core/log.h"

namespace t12 {

// Einstellungen im Modul ($CFG): Standby-Temp, Standby s, Schlafen s, Boost +°C, Boost s, Min, Max
enum { CFG_STBY_T = 0, CFG_STBY_S, CFG_SLEEP_S, CFG_BOOST_T, CFG_BOOST_S, CFG_MIN, CFG_MAX, CFG_N };

struct Kolben {
  // vom Modul gemeldet ($T12,ist,soll,ziel,leistung,modus,fehler,vin_x10,ntc_x10,griff_s,ein,link[,modus_s])
  int ist = 0, soll = 0, ziel = 0, pwr = 0, modus = 0, fehler = 0;
  int vin = 0, ntc = 0, griff = 9999, ein = 0, link = 0;
  int modus_s = -1;           // s seit Beginn der Betriebsart (-1 = Modul-Firmware vor v4)
  uint32_t last = 0;          // millis() der letzten gültigen Zeile
  int cfg[CFG_N] = {0};
  bool cfg_ok = false;        // $CFG empfangen
  bool cfg_geaendert = false; // im RAM geändert, noch nicht gespeichert
  int prof_cfg[3] = {-1, -1, -1};  // vom Spitzenprofil gewünscht: Standby °C, Standby s, Schlafen s (-1 = Modulwert lassen)
  // Wunsch des Bedieners (ESP ist der Chef)
  bool w_ein = false;         // nach Neustart immer AUS
  int code_alt = -1;          // letzter Zustand (für Ansagen)
  bool spitze_weg = false;    // "keine Spitze" gesehen -> nach dem Einsetzen Profil abfragen
};

inline Kolben K[2];
inline int anzahl = 2;       // 1 oder 2 Kolben (substitution anzahl_kolben)
constexpr int HEISS = 60;     // ab hier gilt die Spitze nach dem Ausschalten als "kühlt ab" (°C)
inline int auswahl = 0;       // 0 = A, 1 = B (Drehgeber stellt diesen Kolben)
inline int cfg_kolben = 0;    // Kolben auf der Einstellungsseite

inline bool online(int i) { return K[i].last != 0 && (esphome::millis() - K[i].last) < 2000; }

// ---------------------------------------------------------------- LVGL: nur bei Änderung neu zeichnen
// (jedes set_text / set_style löst sonst ein Neuzeichnen aus - das bremst den Touch)
inline void setze_text(lv_obj_t *o, const char *t) {
  const char *alt = lv_label_get_text(o);
  if (alt != nullptr && strcmp(alt, t) == 0) return;
  lv_label_set_text(o, t);
}
inline uint32_t rgb(lv_color_t c) { return lv_color_to_u32(c) & 0xFFFFFF; }
inline void setze_farbe(lv_obj_t *o, uint32_t hex) {
  if (rgb(lv_obj_get_style_text_color(o, LV_PART_MAIN)) == hex) return;
  lv_obj_set_style_text_color(o, lv_color_hex(hex), 0);
}
inline void setze_bg(lv_obj_t *o, uint32_t hex) {
  if (rgb(lv_obj_get_style_bg_color(o, LV_PART_MAIN)) == hex) return;
  lv_obj_set_style_bg_color(o, lv_color_hex(hex), 0);
}
inline void setze_rahmen(lv_obj_t *o, uint32_t hex) {
  if (rgb(lv_obj_get_style_border_color(o, LV_PART_MAIN)) == hex) return;
  lv_obj_set_style_border_color(o, lv_color_hex(hex), 0);
}
inline void sichtbar(lv_obj_t *o, bool ja) {
  if (lv_obj_has_flag(o, LV_OBJ_FLAG_HIDDEN) != ja) return;
  if (ja) lv_obj_remove_flag(o, LV_OBJ_FLAG_HIDDEN); else lv_obj_add_flag(o, LV_OBJ_FLAG_HIDDEN);
}

// Eine Zeile vom Modul auswerten
inline void zeile(int i, const std::vector<uint8_t> &bytes) {
  std::string s(bytes.begin(), bytes.end());
  while (!s.empty() && (s.back() == '\n' || s.back() == '\r')) s.pop_back();
  Kolben &k = K[i];
  if (s.rfind("$T12,", 0) == 0) {
    int v[12];
    int n = sscanf(s.c_str() + 5, "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d", &v[0], &v[1], &v[2], &v[3], &v[4],
                   &v[5], &v[6], &v[7], &v[8], &v[9], &v[10], &v[11]);
    if (n < 11) {
      ESP_LOGW("t12", "Modul %c: Zeile unlesbar: %s", 'A' + i, s.c_str());
      return;
    }
    k.ist = v[0]; k.soll = v[1]; k.ziel = v[2]; k.pwr = v[3]; k.modus = v[4]; k.fehler = v[5];
    k.vin = v[6]; k.ntc = v[7]; k.griff = v[8]; k.ein = v[9]; k.link = v[10];
    k.modus_s = (n >= 12) ? v[11] : -1;          // ab Modul-Firmware v4
    k.last = esphome::millis();
  } else if (s.rfind("$CFG,", 0) == 0) {
    int v[CFG_N];
    if (sscanf(s.c_str() + 5, "%d,%d,%d,%d,%d,%d,%d", &v[0], &v[1], &v[2], &v[3], &v[4], &v[5], &v[6]) == CFG_N) {
      for (int n = 0; n < CFG_N; n++) k.cfg[n] = v[n];
      k.cfg_ok = true;
    }
  } else if (s == "$SAVED") {
    k.cfg_geaendert = false;
    ESP_LOGI("t12", "Modul %c: Einstellungen gespeichert", 'A' + i);
  } else if (!s.empty()) {
    ESP_LOGI("t12", "Modul %c: %s", 'A' + i, s.c_str());
    if (s.rfind("$BOOT", 0) == 0) k.cfg_ok = false;   // Modul neu gestartet -> Einstellungen neu lesen
  }
}

inline std::vector<uint8_t> text(const char *t) { return std::vector<uint8_t>(t, t + strlen(t)); }

// Befehle an das Modul: Solltemperatur + Ein/Aus (dient zugleich als Lebenszeichen)
inline std::vector<uint8_t> befehl(int i, int soll) {
  Kolben &k = K[i];
  char b[128];
  int n = snprintf(b, sizeof(b), "S %d\nE %d\n", soll, k.w_ein ? 1 : 0);
  if (online(i) && !k.cfg_ok)
    n += snprintf(b + n, sizeof(b) - n, "G\n");                              // Einstellungen nachfordern
  else if (online(i))
    for (int c = 0; c < 3; c++)                                               // Werte aus dem Spitzenprofil
      if (k.prof_cfg[c] >= 0 && k.cfg[c] != k.prof_cfg[c])
        n += snprintf(b + n, sizeof(b) - n, "C %d %d\n", c, k.prof_cfg[c]);
  return text(b);
}

// Zustandscode: 0 offline, 1 aus, 2 schläft, 3 standby, 4 heizt, 5 bereit, 6 boost, 7 keine Spitze, 8 Fehler, 9 kühlt ab
inline int code(int i) {
  const Kolben &k = K[i];
  if (!online(i)) return 0;
  if (k.fehler & 1) return 7;
  if (k.fehler) return 8;
  if (!k.ein) return 1;
  switch (k.modus) {
    case 0: return 2;
    case 1: return 3;
    case 3: case 4: return 6;
    default:
      if (abs(k.ist - k.ziel) <= 5) return 5;
      return k.ist > k.ziel ? 9 : 4;
  }
}

// Zustandstext und Farbe für die Kachel
inline const char *status(int i, uint32_t &farbe) {
  const Kolben &k = K[i];
  switch (code(i)) {
    case 0: farbe = 0x8C8C8C; return "NICHT VERBUNDEN";
    // noch heiß nach AUS / Schlafen / Standby: "kühlt ab" anzeigen
    case 1: if (k.ist > HEISS) { farbe = 0x4FC3F7; return "AUS – KÜHLT AB"; }
            farbe = 0x8C8C8C; return "AUS";
    case 2: if (k.ist > HEISS) { farbe = 0x4FC3F7; return "SCHLÄFT – KÜHLT AB"; }
            farbe = 0x7E7EC8; return "SCHLÄFT";
    case 3: if (k.ist > k.ziel + 10) { farbe = 0x4FC3F7; return "STANDBY – KÜHLT AB"; }
            farbe = 0x4A90E2; return "STANDBY";
    case 4: farbe = 0xFF8C00; return "HEIZT";
    case 5: farbe = 0x3CC85A; return "BEREIT";
    case 6: farbe = 0xFF8C00; return "BOOST";
    case 7: farbe = 0xFFC107; return "KEINE SPITZE";
    case 9: farbe = 0x4FC3F7; return "KÜHLT AB";
    default:
      farbe = 0xE53935;
      if (k.fehler & 2) return "FEHLER NTC HOCH";
      if (k.fehler & 4) return "FEHLER NTC TIEF";
      if (k.fehler & 8) return "UNTERSPANNUNG";
      return "FEHLER";
  }
}

// Restzeit bis Standby (gelb) bzw. Schlafen (blau) als Anteil 0..1; false = nichts anzeigen
inline bool restzeit(int i, float &anteil, uint32_t &farbe) {
  const Kolben &k = K[i];
  if (!online(i) || !k.ein || !k.cfg_ok || k.modus_s < 0 || k.fehler) return false;
  int gesamt;
  if (k.modus == 2 && k.cfg[CFG_STBY_S] > 0) { gesamt = k.cfg[CFG_STBY_S]; farbe = 0xFFC107; }    // Betrieb -> Standby
  else if (k.modus == 2 || k.modus == 1)     { gesamt = k.cfg[CFG_SLEEP_S]; farbe = 0x4A90E2; }   // -> Schlafen
  else return false;                                                                              // Boost, Schlaf
  if (gesamt <= 0) return false;
  int rest = gesamt - k.modus_s;
  if (rest < 0) rest = 0;
  anteil = (float) rest / gesamt;
  return true;
}

// Kolben "in der Hand": eingeschaltet und Griff innerhalb der letzten s Sekunden bewegt
inline bool in_hand(int i, int s) { return online(i) && K[i].w_ein && K[i].griff < s; }

// ---------------------------------------------------------------- Spitzenprofile
// Aus Home Assistant: /config/www/t12_profile.yaml, Zeilen
//   "- Name, T1, T2, T3[, Standby °C, Standby min, Schlafen min]"
struct Profil {
  std::string name;
  int t[3];
  int cfg[3] = {-1, -1, -1};  // Standby °C, Standby s, Schlafen s (-1 = nicht angegeben)
};
inline std::vector<Profil> profile;
inline int popup = -1;        // Kolben, für den gerade die Profilauswahl offen ist (-1 = keine)

inline std::string trim(const std::string &s) {
  size_t a = s.find_first_not_of(" \t\r\"'");
  size_t b = s.find_last_not_of(" \t\r\"'");
  return a == std::string::npos ? "" : s.substr(a, b - a + 1);
}

// ---- Kopie der Profile im Flash (NVS): gilt, wenn Home Assistant beim Einschalten nicht erreichbar ist
constexpr int PROFIL_MAX = 20;
struct ProfilFlash {
  uint8_t anzahl;
  struct {
    char name[17];
    int16_t t[3];
    int16_t cfg[3];
  } p[PROFIL_MAX];
};
inline esphome::ESPPreferenceObject &profil_pref() {
  static esphome::ESPPreferenceObject pref = esphome::global_preferences->make_preference<ProfilFlash>(0x54313250UL, true);
  return pref;
}
inline ProfilFlash profil_flash_packen() {
  ProfilFlash f;
  memset(&f, 0, sizeof(f));
  f.anzahl = (uint8_t) std::min((int) profile.size(), PROFIL_MAX);
  for (int j = 0; j < f.anzahl; j++) {
    strncpy(f.p[j].name, profile[j].name.c_str(), 16);
    for (int c = 0; c < 3; c++) { f.p[j].t[c] = profile[j].t[c]; f.p[j].cfg[c] = profile[j].cfg[c]; }
  }
  return f;
}
// nur schreiben, wenn sich etwas geändert hat (schont den Flash)
inline void profile_speichern() {
  ProfilFlash neu = profil_flash_packen(), alt;
  if (profil_pref().load(&alt) && memcmp(&neu, &alt, sizeof(neu)) == 0) return;
  if (profil_pref().save(&neu)) esphome::global_preferences->sync();
  ESP_LOGI("t12", "Spitzenprofile im Flash gespeichert (%d)", neu.anzahl);
}
// beim Start: Profile aus dem Flash holen (HA liefert später ggf. neuere)
inline int profile_aus_flash() {
  ProfilFlash f;
  if (!profil_pref().load(&f) || f.anzahl == 0 || f.anzahl > PROFIL_MAX) return 0;
  std::vector<Profil> neu;
  for (int j = 0; j < f.anzahl; j++) {
    Profil q;
    f.p[j].name[16] = 0;
    q.name = f.p[j].name;
    for (int c = 0; c < 3; c++) { q.t[c] = f.p[j].t[c]; q.cfg[c] = f.p[j].cfg[c]; }
    neu.push_back(q);
  }
  profile = neu;
  ESP_LOGI("t12", "%d Spitzenprofile aus dem Flash", f.anzahl);
  return f.anzahl;
}

// Datei auswerten; gibt die Zahl der Profile zurück (alte Liste bleibt bei Fehler erhalten)
inline int profile_laden(const std::string &text) {
  std::vector<Profil> neu;
  size_t pos = 0;
  while (pos < text.size() && (int) neu.size() < PROFIL_MAX) {
    size_t ende = text.find('\n', pos);
    if (ende == std::string::npos) ende = text.size();
    std::string z = trim(text.substr(pos, ende - pos));
    pos = ende + 1;
    if (z.empty() || z[0] == '#') continue;
    if (z[0] == '-') z = trim(z.substr(1));
    size_t k1 = z.find(',');
    if (k1 == std::string::npos) continue;
    Profil p;
    p.name = trim(z.substr(0, k1));
    if (p.name.empty() || p.name.size() > 16) continue;
    int st = -1, sm = -1, sl = -1;
    int n = sscanf(z.c_str() + k1 + 1, " %d , %d , %d , %d , %d , %d", &p.t[0], &p.t[1], &p.t[2], &st, &sm, &sl);
    if (n < 1) continue;
    for (int j = n; j < 3; j++) p.t[j] = p.t[0];
    bool ok = true;
    for (int j = 0; j < 3; j++) if (p.t[j] < 150 || p.t[j] > 450) ok = false;
    if (!ok) continue;
    // optionale Standby-Werte; ungültige oder fehlende bleiben -1 (Modulwert bleibt)
    if (n >= 4 && st >= 100 && st <= 300) p.cfg[0] = st;
    if (n >= 5 && sm >= 0 && sm <= 60) p.cfg[1] = sm * 60;          // 0 = nie Standby
    if (n >= 6 && sl >= 1 && sl <= 120) p.cfg[2] = sl * 60;
    neu.push_back(p);
  }
  if (!neu.empty()) { profile = neu; profile_speichern(); }
  ESP_LOGI("t12", "%d Spitzenprofile geladen", (int) neu.size());
  return (int) neu.size();
}

inline std::string profil_liste() {
  std::string s;
  for (size_t j = 0; j < profile.size(); j++) {
    if (j) s += "\n";
    char b[64];
    snprintf(b, sizeof(b), "%s  (%d °C)", profile[j].name.c_str(), profile[j].t[0]);
    if (profile[j].cfg[0] >= 0) snprintf(b + strlen(b) - 1, sizeof(b) - strlen(b) + 1, " / %d)", profile[j].cfg[0]);
    s += b;
  }
  return s;
}

inline const Profil *profil(int idx) {
  return (idx >= 0 && idx < (int) profile.size()) ? &profile[idx] : nullptr;
}

// Standby-Wünsche des gewählten Profils übernehmen (p = nullptr: Profile aus -> Modulwerte lassen)
inline void profil_cfg(int i, const Profil *p) {
  for (int c = 0; c < 3; c++) K[i].prof_cfg[c] = p ? p->cfg[c] : -1;
}

// Wert kommt gerade aus dem Spitzenprofil?
inline bool cfg_vom_profil(int i, int n) { return n < 3 && K[i].prof_cfg[n] >= 0; }

// Spitzenwechsel: "keine Spitze" und danach wieder eine Spitze -> Kolbennummer, sonst -1
inline int spitzen_wechsel() {
  for (int i = 0; i < anzahl; i++) {
    Kolben &k = K[i];
    if (!online(i)) continue;
    if (k.fehler & 1) { k.spitze_weg = true; continue; }
    if (k.spitze_weg) { k.spitze_weg = false; return i; }
  }
  return -1;
}

}  // namespace t12
