/*
 * uart_remote.h  -  Fernsteuerung der T12-Station ueber UART (ESP32 / ESPHome)
 *
 * T12-Loetstation (Werkstatt-Projekt). Ersetzt OLED und Drehknopf:
 *   USART3: PB10 = TX (OLED-Pad SCL), PB11 = RX (OLED-Pad SDA), 115200 8N1, 3,3 V
 *   PB12/PB13 (frueher Software-I2C fuer das OLED) werden hochohmig geschaltet.
 *
 * Protokoll: siehe uart_remote.c (Kopf).
 * Auskommentieren = normale OLED-Firmware.
 */
#ifndef INC_UART_REMOTE_H_
#define INC_UART_REMOTE_H_

#define T12_UART_REMOTE

#ifdef T12_UART_REMOTE
#include <stdint.h>
#include <stdbool.h>

#define UART_REMOTE_BAUD          115200
#define UART_REMOTE_REPORT_MS     200       // Statuszeile alle 200 ms
#define UART_REMOTE_TIMEOUT_MS    30000     // ESP stumm -> Standby (Nutzerwunsch 2026-11-19)

void uart_remote_init(void);                // nach MX-Init und restoreSettings()
void uart_remote_boot_complete(void);       // ersetzt boot_screen_onExit()
void uart_remote_handle(void);              // aus mainCycle() statt oled_handle()
#endif

#endif /* INC_UART_REMOTE_H_ */
