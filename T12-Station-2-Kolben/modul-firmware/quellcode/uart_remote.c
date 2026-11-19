/*
 * uart_remote.c  -  Fernsteuerung der T12-Station ueber UART (ESP32 / ESPHome)
 *
 * T12-Loetstation (Werkstatt-Projekt), Erweiterung der Firmware von deividAlfa.
 *
 * Hardware (KSGER v2 / "Ver21S"):
 *   USART3 TX = PB10  -> OLED-Pad "SCL" (Draht zu Chip-Pin 21)
 *   USART3 RX = PB11  <- OLED-Pad "SDA" (Draht zu Chip-Pin 22)
 *   115200 Baud, 8N1, 3,3-V-Pegel. GND gemeinsam, VCC NICHT verbinden.
 *
 * Befehle ESP -> Modul (ASCII, Zeilenende \n oder \r):
 *   S <temp>    Solltemperatur in degC setzen (wird auf Min/Max des Profils begrenzt)
 *   E 1|0       Kolben ein (1) / aus (0). Aus = Schlafmodus, Griff weckt NICHT auf.
 *   M <n>       Betriebsart: 0 Schlaf, 1 Standby, 2 Betrieb, 3 Boost (nur wenn ein)
 *   P           nur Lebenszeichen
 *   ?           sofort eine Statuszeile senden
 *   G           Einstellungen lesen -> "$CFG,..." (siehe unten)
 *   C <n> <w>   Einstellung n auf Wert w setzen (nur im RAM), Antwort "$CFG,..."
 *                 0 Standby-Temperatur degC   1 Standby nach s (0 = aus)   2 Schlafen nach s
 *                 3 Boost +degC               4 Boost-Dauer s
 *   W           Einstellungen dauerhaft im Flash speichern -> "$SAVED"
 *
 * Einstellungen: $CFG,<stby_temp>,<stby_s>,<sleep_s>,<boost_temp>,<boost_s>,<min_temp>,<max_temp>
 *   Jede gueltige Zeile setzt die 30-s-Ueberwachung zurueck.
 *
 * Status Modul -> ESP alle 200 ms (eine Zeile):
 *   $T12,<ist>,<soll>,<ziel>,<leistung%>,<modus>,<fehler>,<vin_x10>,<ntc_x10>,<griff_s>,<ein>,<link>,<modus_s>
 *     ist/soll/ziel  degC (ziel = aktuelle Zieltemperatur, z.B. Standby-Temperatur)
 *     modus          0 Schlaf, 1 Standby, 2 Betrieb, 3 Boost, 4 Kaltboost
 *     fehler         Bitmaske: 1 keine Spitze, 2 NTC hoch, 4 NTC tief, 8 Unterspannung, 16 Safe-Mode, 128 aktiv
 *     vin_x10        Versorgungsspannung * 10
 *     ntc_x10        Temperatur im Griff/Kaltstelle * 10
 *     griff_s        Sekunden seit der letzten Griffbewegung (max. 9999)
 *     ein            1 = vom ESP eingeschaltet
 *     link           1 = ESP hat sich in den letzten 30 s gemeldet
 *     modus_s        Sekunden seit Beginn der aktuellen Betriebsart (Griffbewegung startet neu);
 *                    daraus berechnet der ESP die Zeit bis Standby/Schlafen (ab v4)
 *   Antwort auf Fehler im Befehl: "$ERR,<zeile>"
 */
#include "uart_remote.h"
#ifdef T12_UART_REMOTE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "main.h"
#include "iron.h"
#include "settings.h"
#include "tempsensors.h"
#include "voltagesensors.h"
#include "adc_global.h"
#include "buzzer.h"

#define RX_LINE_MAX   32
#define TX_BUF_SIZE   256                          // Zweierpotenz

static volatile char     rx_line[RX_LINE_MAX];
static volatile uint8_t  rx_len;
static volatile bool     rx_ready;                 // komplette Zeile liegt in rx_cmd
static char              rx_cmd[RX_LINE_MAX];

static volatile uint8_t  tx_buf[TX_BUF_SIZE];
static volatile uint16_t tx_head, tx_tail;

static bool     enabled;                           // vom ESP eingeschaltet
static bool     link_ok;                           // ESP meldet sich
static bool     timeout_done;                      // Standby nach Timeout schon gesetzt
static uint32_t last_rx_ms;
static uint32_t last_report_ms;

/* ------------------------------------------------------------------ USART3 (Register, ohne HAL) */
static void uart_hw_init(void){
  RCC->APB2ENR |= RCC_APB2ENR_IOPBEN;
  RCC->APB1ENR |= RCC_APB1ENR_USART3EN;

  // PB10 TX: AF push-pull 2 MHz (CNF=10 MODE=10 -> 0xA)
  // PB11 RX: Eingang mit Pull-up (CNF=10 MODE=00 -> 0x8, ODR=1)
  // PB12/PB13 (alter OLED-Bus): Eingang hochohmig (0x4), damit sie die Pads nicht treiben
  uint32_t crh = GPIOB->CRH;
  crh &= ~((0xFUL<<8) | (0xFUL<<12) | (0xFUL<<16) | (0xFUL<<20));
  crh |=  ((0xAUL<<8) | (0x8UL<<12) | (0x4UL<<16) | (0x4UL<<20));
  GPIOB->CRH = crh;
  GPIOB->BSRR = (1UL<<11);                         // Pull-up an RX

  uint32_t pclk = HAL_RCC_GetPCLK1Freq();
  USART3->CR1 = 0;
  USART3->BRR = (pclk + UART_REMOTE_BAUD/2) / UART_REMOTE_BAUD;
  USART3->CR2 = 0;
  USART3->CR3 = 0;
  USART3->CR1 = USART_CR1_UE | USART_CR1_TE | USART_CR1_RE | USART_CR1_RXNEIE;

  NVIC_SetPriority(USART3_IRQn, 3);                // niedriger als ADC/Timer der Regelung
  NVIC_EnableIRQ(USART3_IRQn);
}

void USART3_IRQHandler(void){
  uint32_t sr = USART3->SR;
  if(sr & (USART_SR_RXNE | USART_SR_ORE | USART_SR_FE | USART_SR_NE)){
    char c = (char)USART3->DR;                     // liest auch Fehlerflags weg
    if(!(sr & (USART_SR_FE | USART_SR_NE))){
      if(c=='\n' || c=='\r'){
        if(rx_len && !rx_ready){
          memcpy(rx_cmd, (const void*)rx_line, rx_len);
          rx_cmd[rx_len] = 0;
          rx_ready = true;
        }
        rx_len = 0;
      }
      else if(rx_len < RX_LINE_MAX-1){
        rx_line[rx_len++] = c;
      }
      else{
        rx_len = 0;                                // zu lang: verwerfen
      }
    }
  }
  if((USART3->CR1 & USART_CR1_TXEIE) && (sr & USART_SR_TXE)){
    if(tx_tail != tx_head){
      USART3->DR = tx_buf[tx_tail];
      tx_tail = (tx_tail + 1) & (TX_BUF_SIZE-1);
    }
    else{
      USART3->CR1 &= ~USART_CR1_TXEIE;
    }
  }
}

static void uart_send(const char *s){
  while(*s){
    uint16_t next = (tx_head + 1) & (TX_BUF_SIZE-1);
    if(next == tx_tail) break;                     // Puffer voll: Rest verwerfen, nie blockieren
    tx_buf[tx_head] = (uint8_t)*s++;
    tx_head = next;
  }
  USART3->CR1 |= USART_CR1_TXEIE;
}

/* ------------------------------------------------------------------ Status */
static void send_status(void){
  char line[112];
  uint32_t now = HAL_GetTick();
  uint32_t shake_s = (now - getIronLastShakeTime()) / 1000;
  if(shake_s > 9999) shake_s = 9999;
  uint32_t mode_s = (now - getIronCurrentModeTimer()) / 1000;
  if(mode_s > 99999) mode_s = 99999;
  snprintf(line, sizeof(line), "$T12,%d,%u,%u,%d,%u,%u,%u,%d,%lu,%u,%u,%lu\n",
           readLastTipTemperatureCompensated(read_average, mode_Celsius),
           getUserTemperature(),
           getIronTargetTemperature(),
           getCurrentPower(),
           getCurrentMode(),
           getIronErrorFlags().Flags,
           getSupplyVoltage_v_x10(),
           last_NTC_C,
           (unsigned long)shake_s,
           enabled ? 1 : 0,
           link_ok ? 1 : 0,
           (unsigned long)mode_s);
  uart_send(line);
}

/* ------------------------------------------------------------------ Einstellungen */
static void send_cfg(void){
  char line[80];
  profile_settings_t *p = getProfileSettings();
  snprintf(line, sizeof(line), "$CFG,%u,%lu,%lu,%u,%lu,%u,%u\n",
           p->standbyTemperature,
           (unsigned long)(p->standbyTimeout / 1000),
           (unsigned long)(p->sleepTimeout / 1000),
           p->boostTemperature,
           (unsigned long)(p->boostTimeout / 1000),
           p->MinSetTemperature,
           p->MaxSetTemperature);
  uart_send(line);
}

static long clampl(long v, long lo, long hi){ return v < lo ? lo : (v > hi ? hi : v); }

static bool set_cfg(long n, long v){
  profile_settings_t *p = getProfileSettings();
  switch(n){
    case 0: p->standbyTemperature = (uint16_t)clampl(v, 100, p->MaxSetTemperature); break;
    case 1: p->standbyTimeout     = (uint32_t)clampl(v, 0, 3600) * 1000UL;           break;
    case 2: p->sleepTimeout       = (uint32_t)clampl(v, 60, 7200) * 1000UL;          break;
    case 3: p->boostTemperature   = (uint16_t)clampl(v, 0, 100);                     break;
    case 4: p->boostTimeout       = (uint32_t)clampl(v, 10, 600) * 1000UL;           break;
    default: return false;
  }
  if(enabled) setCurrentMode(getCurrentMode(), 0);    // Ziel (z.B. Standby-Temperatur) sofort neu berechnen
  return true;
}

/* ------------------------------------------------------------------ Befehle */
static void set_enabled(bool on){
  // Nur bei Wechsel handeln: der ESP schickt "E 1" alle 2 s als Lebenszeichen. Sonst wuerde
  // jeder Standby/Schlaf sofort wieder aufgeweckt (Fehler in v1/v2). Aufwecken danach per Griff.
  if(on == enabled) return;
  enabled = on;
  if(on){
    if(getCurrentMode() < mode_run) setCurrentMode(mode_run, SHORT_BEEP);
  }
  else{
    setCurrentMode(mode_sleep, SHORT_BEEP);
  }
}

static bool parse_command(char *cmd){
  char *arg = cmd + 1;
  while(*arg==' ') arg++;
  long v = strtol(arg, NULL, 10);

  switch(cmd[0]){
    case 'S': case 's': {
      if(!*arg) return false;
      long lo = getProfileSettings()->MinSetTemperature;
      long hi = getProfileSettings()->MaxSetTemperature;
      if(v < lo) v = lo;
      if(v > hi) v = hi;
      // Nur bei echter Aenderung neu berechnen: setCurrentMode() startet den Zeitzaehler der
      // Betriebsart neu. Der ESP schickt S alle 2 s - sonst endet (Kalt-)Boost nie und
      // Standby/Schlafen wuerden nie ausloesen (Fehler in v1/v2).
      if((uint16_t)v != getUserTemperature()){
        setUserTemperature((int16_t)v);
        if(enabled) setCurrentMode(getCurrentMode(), 0);
      }
      return true;
    }
    case 'E': case 'e':
      if(!*arg) return false;
      set_enabled(v != 0);
      return true;
    case 'M': case 'm':
      if(!*arg || v < mode_sleep || v > mode_boost) return false;
      if(!enabled && v != mode_sleep) return true;         // aus = bleibt aus
      setCurrentMode((uint8_t)v, SHORT_BEEP);
      return true;
    case 'P': case 'p':
      return true;
    case '?':
      send_status();
      return true;
    case 'G': case 'g':
      send_cfg();
      return true;
    case 'C': case 'c': {
      char *end;
      long n = strtol(arg, &end, 10);
      if(end == arg) return false;
      while(*end == ' ') end++;
      if(!*end) return false;
      if(!set_cfg(n, strtol(end, NULL, 10))) return false;
      send_cfg();
      return true;
    }
    case 'W': case 'w':
      saveSettings(save_profile, no_reboot);          // ~1 KB Puffer, Heizung waehrend des Schreibens aus
      uart_send("$SAVED\n");
      return true;
    default:
      return false;
  }
}

/* ------------------------------------------------------------------ Schnittstelle */
void uart_remote_init(void){
  enabled = false;                                 // nach Stromausfall immer AUS
  link_ok = false;
  timeout_done = true;
  last_rx_ms = HAL_GetTick();
  last_report_ms = HAL_GetTick();
  uart_hw_init();
  uart_send("$BOOT,T12-UART,4\n");
}

// Ersetzt boot_screen_onExit(): Einstellungen pruefen, Safe-Mode aus, Regelung freigeben
void uart_remote_boot_complete(void){
  ADC_Reset_measures();
  if(getSettings()->setupMode){
    saveSettings(save_settings, no_reboot);
    saveTip(perform_scanFix, 0);
    loadProfile(getCurrentProfile());
    updateTempData(force_update);
    getSettings()->setupMode = 0;
  }
  setIronSafeMode(disable);
  resetIronError();
  setBootCompleteFlag();
  setCurrentMode(mode_sleep, 0);                   // Start immer im Schlafmodus, bis der ESP einschaltet
}

void uart_remote_handle(void){
  uint32_t now = HAL_GetTick();

  if(rx_ready){
    char cmd[RX_LINE_MAX];
    strcpy(cmd, rx_cmd);
    rx_ready = false;
    if(parse_command(cmd)){
      last_rx_ms = now;
      link_ok = true;
      timeout_done = false;
    }
    else{
      char err[RX_LINE_MAX + 8];
      snprintf(err, sizeof(err), "$ERR,%s\n", cmd);
      uart_send(err);
    }
  }

  // ESP stumm: nach 30 s Standby (einmalig), danach greift die normale Schlafzeit
  if(link_ok && (now - last_rx_ms) > UART_REMOTE_TIMEOUT_MS){
    link_ok = false;
  }
  if(!link_ok && !timeout_done){
    timeout_done = true;
    if(getCurrentMode() >= mode_run) setCurrentMode(mode_standby, MEDIUM_BEEP);
  }

  // Aus heisst aus: auch Griffbewegung darf nicht aufwecken
  if(!enabled && getCurrentMode() != mode_sleep){
    setCurrentMode(mode_sleep, 0);
  }

  if((now - last_report_ms) >= UART_REMOTE_REPORT_MS){
    last_report_ms = now;
    send_status();
  }
}

#endif /* T12_UART_REMOTE */
