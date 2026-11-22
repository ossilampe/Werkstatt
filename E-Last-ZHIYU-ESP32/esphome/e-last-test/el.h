// E-Last ZHIYU ZPB30A1 mit freier Firmware herm/ZPB30A1_Firmware
// Zeilen-Parser fuer die VAL:-Telemetrie und Sende-Warteschlange
// Protokoll laut software/uart.c (Commit fe93bfe):
//  - Parser der Last startet "uninitialized" -> erst nach '!' werden Befehle angenommen
//  - jeder Befehl: Zeichen + Ziffern + '\n', Ausfuehrung erst im Hauptprogramm
//    -> zwischen zwei Befehlen Pause (hier 100 ms), sonst geht der erste verloren
//  - Antwort "CMD:<c><param>" bzw. "ERR:<ASCII-Code> <param> <code>"
//  - alle 200 ms: "VAL: D 0 T 253 Vi 12034 Vl     0 Vs     0 I   500 mWs 0 mAs 0\r\n"
#pragma once
#include <string>
#include <deque>
#include <vector>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <cmath>
#include "esphome/core/hal.h"
#include "esphome/core/log.h"
#include "esphome/components/uart/uart.h"

namespace el {

static const char *const TAG = "elast";

struct Zustand {
  char st = '?';          // D aus, A aktiv geregelt, U aktiv nicht geregelt
  int err = -1;           // Fehler der Last 0..9
  float temp = NAN;       // Kuehlkoerper in Grad C
  int vi = 0, vl = 0, vs = 0, iset = 0;   // mV 12 V, mV Last, mV Sense, mA Sollwert
  uint32_t mws = 0, mas = 0;
  uint32_t mws0 = 0, mas0 = 0;            // Nullpunkt fuer Ah/Wh
  bool null_setzen = true;
  uint32_t letzte_val = 0;
  uint32_t val_zaehler = 0;
  bool war_online = false;
  std::string antwort = "-";   // letzte CMD:/ERR:-Zeile (aufbereitet)
  std::string roh = "-";       // letzte VAL-Zeile
  std::string fremd = "-";     // letzte sonstige Zeile
  int modus = 0;               // 0 CC, 1 CW, 2 CR, 3 CV
  float soll[4] = {0.50f, 5.0f, 10.0f, 5.0f};   // A, W, Ohm, V
  int schritt = 1;             // 0 grob, 1 mittel, 2 fein
  std::string rx;
  std::deque<std::string> tx;
};
inline Zustand z;

inline const char *const MODUS[4] = {"CC", "CW", "CR", "CV"};
inline const char *const EINHEIT[4] = {"A", "W", "Ω", "V"};
inline const float SCHRITT[4][3] = {{1.0f, 0.1f, 0.01f}, {10.0f, 1.0f, 0.1f}, {10.0f, 1.0f, 0.1f}, {1.0f, 0.1f, 0.01f}};
inline const int NK_SCHRITT[4][3] = {{0, 1, 2}, {0, 0, 1}, {0, 0, 1}, {0, 1, 2}};
inline const float MINW[4] = {0.2f, 0.1f, 0.1f, 0.5f};
inline const float MAXW[4] = {10.0f, 60.0f, 150.0f, 30.0f};
inline const int NK[4] = {2, 1, 1, 2};
inline const char *const FEHLER[10] = {"OK", "POL", "OVP", "OVLD", "PWR", "TEMP", "SUP", "TIME", "INT", "CMD"};
inline const char *const FEHLER_TXT[10] = {"kein Fehler", "Eingang verpolt", "Überspannung", "Überlast (Quelle schafft Strom nicht)",
                                          "Leistung > 65 W", "Übertemperatur", "12 V zu niedrig", "Timer verloren",
                                          "interner Fehler", "ungültiger Befehl"};
inline const char *const UART_ERR[6] = {"ok", "Modus ungültig", "außerhalb Bereich", "keine Ziffer", "intern", "unbekannter Befehl"};

inline bool online() { return z.val_zaehler > 0 && (esphome::millis() - z.letzte_val) < 1500; }
inline bool aktiv() { return online() && (z.st == 'A' || z.st == 'U'); }

// Zahl mit Komma und Einheit
inline std::string fmt(float v, int nk, const char *einheit) {
  char b[32];
  if (std::isnan(v)) snprintf(b, sizeof(b), "--%s%s", einheit[0] ? " " : "", einheit);
  else snprintf(b, sizeof(b), "%.*f%s%s", nk, v, einheit[0] ? " " : "", einheit);
  for (char *p = b; *p; p++) if (*p == '.') *p = ',';
  return b;
}

inline void parse(std::string l) {
  while (!l.empty() && (l.back() == '\r' || l.back() == ' ')) l.pop_back();
  if (l.empty()) return;
  // Stoerbytes vor dem Zeilenanfang (z. B. nach dem Einschalten) abschneiden
  {
    size_t p = std::string::npos;
    for (const char *k : {"VAL:", "CMD:", "ERR:"}) { size_t q = l.find(k); if (q < p) p = q; }
    if (p != std::string::npos && p > 0) l.erase(0, p);
  }
  if (l.rfind("VAL:", 0) == 0) {
    std::vector<std::string> t;
    std::string w;
    for (size_t i = 4; i <= l.size(); i++) {
      char c = i < l.size() ? l[i] : ' ';
      if (c == ' ' || c == '\t') { if (!w.empty()) { t.push_back(w); w.clear(); } }
      else w += c;
    }
    if (t.size() < 2) { z.fremd = l; return; }
    z.st = t[0][0];
    z.err = atoi(t[1].c_str());
    for (size_t i = 2; i + 1 < t.size(); i += 2) {
      const std::string &k = t[i];
      const char *v = t[i + 1].c_str();
      if (k == "T") z.temp = atoi(v) / 10.0f;
      else if (k == "Vi") z.vi = atoi(v);
      else if (k == "Vl") z.vl = atoi(v);
      else if (k == "Vs") z.vs = atoi(v);
      else if (k == "I") z.iset = atoi(v);
      else if (k == "mWs") z.mws = strtoul(v, nullptr, 10);
      else if (k == "mAs") z.mas = strtoul(v, nullptr, 10);
    }
    // Zaehler der Last nach deren Neustart wieder bei 0 -> Nullpunkt mitziehen
    if (z.null_setzen || z.mas < z.mas0 || z.mws < z.mws0) {
      z.mas0 = z.mas; z.mws0 = z.mws; z.null_setzen = false;
    }
    z.letzte_val = esphome::millis();
    z.val_zaehler++;
    z.roh = l;
    if (z.val_zaehler % 25 == 1) ESP_LOGI(TAG, "%s", l.c_str());
  } else if (l.rfind("ERR:", 0) == 0) {
    int c = 0, p = 0, e = 0;
    sscanf(l.c_str() + 4, "%d %d %d", &c, &p, &e);
    char b[80];
    snprintf(b, sizeof(b), "ERR %c%d: %s", (c >= 32 && c < 127) ? c : '?', p, (e >= 0 && e < 6) ? UART_ERR[e] : "?");
    z.antwort = b;
    ESP_LOGW(TAG, "%s  (%s)", l.c_str(), b);
  } else if (l.rfind("CMD:", 0) == 0) {
    z.antwort = l;
    ESP_LOGI(TAG, "%s", l.c_str());
  } else {
    z.fremd = l;
    ESP_LOGI(TAG, "andere Zeile: %s", l.c_str());
  }
}

inline void lies(esphome::uart::UARTComponent *u) {
  uint8_t c;
  int n = 0;
  while (u->available() && n++ < 512) {
    if (!u->read_byte(&c)) break;
    if (c == '\n') { parse(z.rx); z.rx.clear(); }
    else if (c != '\r' && (c < 32 || c > 126)) continue;   // nur druckbares ASCII (sonst bricht die HA-API wegen UTF-8 ab)
    else if (c != '\r' && (c < 32 || c > 126)) continue;   // nur druckbares ASCII (sonst bricht die HA-API wegen UTF-8 ab)
    else if (z.rx.size() < 200) z.rx += (char) c;
    else z.rx.clear();
  }
}

// ein Befehl pro Aufruf (Intervall 100 ms), immer mit '!' davor (setzt den Parser der Last zurueck)
inline void sende(esphome::uart::UARTComponent *u) {
  if (z.tx.empty()) return;
  std::string s = "!" + z.tx.front() + "\n";
  ESP_LOGI(TAG, "-> %s", z.tx.front().c_str());
  z.tx.pop_front();
  u->write_str(s.c_str());
}

inline void push(const std::string &s) { if (z.tx.size() < 20) z.tx.push_back(s); }

inline std::string soll_befehl(int m) {
  char b[16];
  float v = z.soll[m];
  switch (m) {
    case 0: snprintf(b, sizeof(b), "c%d", (int) lroundf(v * 1000.0f)); break;   // mA
    case 1: snprintf(b, sizeof(b), "w%d", (int) lroundf(v * 1000.0f)); break;   // mW
    case 2: snprintf(b, sizeof(b), "r%d", (int) lroundf(v * 100.0f)); break;    // 10 mOhm
    default: snprintf(b, sizeof(b), "v%d", (int) lroundf(v * 1000.0f)); break;  // mV
  }
  return b;
}

inline void setze_modus(int m) {
  if (m < 0 || m > 3) return;
  if (aktiv() && m != z.modus) push("S");   // Moduswechsel nur bei ausgeschalteter Last
  z.modus = m;
  char b[4];
  snprintf(b, sizeof(b), "M%d", m);
  push(b);
  push(soll_befehl(m));
}

inline void aendere_soll(int richtung) {
  int m = z.modus;
  float s = SCHRITT[m][z.schritt];
  float v = roundf((z.soll[m] + richtung * s) / s) * s;
  if (v < MINW[m]) v = MINW[m];
  if (v > MAXW[m]) v = MAXW[m];
  z.soll[m] = v;
}

inline void ein() {
  if (!online()) return;
  char b[4];
  snprintf(b, sizeof(b), "M%d", z.modus);
  push(b);
  push(soll_befehl(z.modus));
  push("R");
}

inline void aus() { push("S"); }

}  // namespace el
