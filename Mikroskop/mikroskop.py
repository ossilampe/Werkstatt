#!/usr/bin/env python3
"""
Digitales Mikroskop
Raspberry Pi 4 + Raspberry Pi HQ-Kamera + offizielles 7"-Touchdisplay

Funktionen
- Live-Bild im Vollbild mit Touch-Buttons (Zoom +/-, 1:1, Foto, Bild, Beenden)
- Verschieben des Ausschnitts durch Wischen auf dem Bild (wenn gezoomt)
- Physische Taster an GPIO (Zoom +/- mit Gedrückthalten, Foto, Reset)
- Foto = aktueller (gezoomter) Bildausschnitt -> SMB-Freigabe
  Ist der Server nicht erreichbar, wird lokal zwischengespeichert und
  beim nächsten erfolgreichen Foto automatisch nachgeladen.
- Bild-Einstellungen: Helligkeit, Kontrast, Sättigung, Schärfe,
  Belichtungskorrektur, manuelle Belichtungszeit + Verstärkung, Weißabgleich
  (inkl. "Fixiert"). Werte werden gespeichert und beim Start geladen.

Tastatur: +  -  0 (Reset)  Leertaste (Foto)  Pfeiltasten (Verschieben)
          B (Bild-Einstellungen)  Esc (Beenden)
"""

import json
import os
import shutil
import threading
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt, QObject, QEvent, QTimer, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
                             QPushButton, QLabel, QSlider, QStackedWidget)
from libcamera import controls
from picamera2 import Picamera2
from picamera2.previews.qt import QGlPicamera2

# ------------------------------------------------------------------
# Einstellungen
# ------------------------------------------------------------------
SMB_DIR = Path("/mnt/mikroskop")                 # Mountpunkt der SMB-Freigabe
QUEUE_DIR = Path.home() / "Bilder" / "Mikroskop"  # lokaler Zwischenspeicher
SETTINGS_FILE = Path.home() / ".config" / "mikroskop.json"
KEEP_LOCAL_COPY = False                           # True = Bild auch lokal behalten

CAMERA_SIZE = (2028, 1520)   # HQ-Kamera Binning-Modus, 4:3, flüssig auf dem Pi 4
ZOOM_STEP = 1.25             # Faktor pro Tastendruck
ZOOM_MAX = 8.0               # maximaler Digitalzoom
PAN_STEP = 0.15              # Verschiebung pro Pfeiltaste (Anteil des Ausschnitts)
JPEG_QUALITY = 95

# GPIO-Pins (BCM-Nummern). Taster jeweils zwischen Pin und GND.
GPIO_PINS = {
    "zoom_in": 17,    # Pin 11
    "zoom_out": 27,   # Pin 13
    "snapshot": 22,   # Pin 15
    "reset": 23,      # Pin 16
}

DISPLAY_W, DISPLAY_H = 800, 480
BUTTON_COL_W = 160           # Buttonleiste rechts -> Bild 640x480 (4:3)
SETTINGS_COL_W = 340         # Einstellungsleiste -> Bild schrumpft, bleibt sichtbar

# Standardwerte der Bild-Einstellungen
DEFAULTS = {
    "Brightness": 0.0,       # -1 .. 1
    "Contrast": 1.0,         # 0 .. 4
    "Saturation": 1.0,       # 0 .. 3   (0 = Schwarzweiß)
    "Sharpness": 1.0,        # 0 .. 8
    "ExposureValue": 0.0,    # -4 .. 4 EV (nur bei Auto-Belichtung)
    "AeEnable": True,        # Auto-Belichtung
    "ExposureTime": 10000,   # µs (nur manuell)
    "AnalogueGain": 1.0,     # 1 .. 16 (nur manuell)
    "Awb": "Auto",           # Weißabgleich-Modus oder "Locked"
    "ColourGains": None,     # (rot, blau) bei "Locked"
}

# Weißabgleich-Modi: (Anzeige, libcamera-Name)
AWB_MODES = [
    ("Auto", "Auto"),
    ("Tageslicht", "Daylight"),
    ("Bewölkt", "Cloudy"),
    ("Innen", "Indoor"),
    ("Leuchtstoff", "Fluorescent"),
    ("Kunstlicht", "Tungsten"),
    ("Glühlampe", "Incandescent"),
    ("Fixiert", "Locked"),   # aktuelle Farbwerte einfrieren
]

# Belichtungszeit-Regler logarithmisch: 0..100 -> 100 µs .. 500 ms
EXP_MIN_US, EXP_MAX_US = 100, 500_000


def exp_from_slider(i):
    return EXP_MIN_US * (EXP_MAX_US / EXP_MIN_US) ** (i / 100)


def exp_to_slider(us):
    import math
    us = min(max(us, EXP_MIN_US), EXP_MAX_US)
    return round(100 * math.log(us / EXP_MIN_US) / math.log(EXP_MAX_US / EXP_MIN_US))


def fmt_exposure(us):
    return f"{us / 1000:.1f} ms" if us < 10_000 else f"{us / 1000:.0f} ms"


# ------------------------------------------------------------------
# Zoom-/Ausschnittsteuerung über ScalerCrop (Zoom direkt im ISP)
# ------------------------------------------------------------------
class ZoomController:
    def __init__(self, picam2):
        self.picam2 = picam2
        self.x0, self.y0, self.full_w, self.full_h = picam2.camera_properties["ScalerCropMaximum"]
        self.zoom = 1.0
        self.cx = 0.5
        self.cy = 0.5

    def visible_size(self):
        return self.full_w / self.zoom, self.full_h / self.zoom

    def _apply(self):
        w, h = self.visible_size()
        half_x = w / 2 / self.full_w
        half_y = h / 2 / self.full_h
        self.cx = min(max(self.cx, half_x), 1 - half_x)
        self.cy = min(max(self.cy, half_y), 1 - half_y)
        x = self.x0 + self.cx * self.full_w - w / 2
        y = self.y0 + self.cy * self.full_h - h / 2
        self.picam2.set_controls({"ScalerCrop": (int(x), int(y), int(w), int(h))})

    def zoom_in(self):
        self.zoom = min(self.zoom * ZOOM_STEP, ZOOM_MAX)
        self._apply()

    def zoom_out(self):
        self.zoom = max(self.zoom / ZOOM_STEP, 1.0)
        self._apply()

    def reset(self):
        self.zoom, self.cx, self.cy = 1.0, 0.5, 0.5
        self._apply()

    def pan(self, dx_frac, dy_frac):
        w, h = self.visible_size()
        self.cx += dx_frac * w / self.full_w
        self.cy += dy_frac * h / self.full_h
        self._apply()


# ------------------------------------------------------------------
# Bild-Einstellungen: Zustand, Speichern, Anwenden
# ------------------------------------------------------------------
class ImageSettings:
    def __init__(self, picam2):
        self.picam2 = picam2
        self.state = dict(DEFAULTS)
        try:
            saved = json.loads(SETTINGS_FILE.read_text())
            self.state.update({k: v for k, v in saved.items() if k in DEFAULTS})
        except Exception:
            pass

    def save(self):
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(self.state, indent=2))
        except Exception as e:
            print(f"Einstellungen nicht gespeichert: {e}")

    def reset(self):
        self.state = dict(DEFAULTS)
        self.apply()

    def apply(self):
        s = self.state
        c = {k: float(s[k]) for k in ("Brightness", "Contrast", "Saturation",
                                      "Sharpness", "ExposureValue")}
        c["AeEnable"] = bool(s["AeEnable"])
        if s["AeEnable"]:
            # Auto: bis 10 fps herunter, wenn es dunkel ist
            c["FrameDurationLimits"] = (25_000, 100_000)
        else:
            exp = int(s["ExposureTime"])
            c["ExposureTime"] = exp
            c["AnalogueGain"] = float(s["AnalogueGain"])
            # Bildrate muss lange Belichtungen zulassen
            c["FrameDurationLimits"] = (25_000, max(25_000, exp + 2_000))
        if s["Awb"] == "Locked" and s["ColourGains"]:
            c["AwbEnable"] = False
            c["ColourGains"] = tuple(float(g) for g in s["ColourGains"])
        else:
            if s["Awb"] == "Locked":
                s["Awb"] = "Auto"
            c["AwbEnable"] = True
            c["AwbMode"] = getattr(controls.AwbModeEnum, s["Awb"])
        self.picam2.set_controls(c)


# ------------------------------------------------------------------
# Touchfreundlicher Schieberegler
# ------------------------------------------------------------------
SLIDER_STYLE = """
QSlider::groove:horizontal { height: 8px; background: #555; border-radius: 4px; }
QSlider::sub-page:horizontal { background: #4a90d9; border-radius: 4px; }
QSlider::handle:horizontal { background: white; width: 28px; height: 28px;
                             margin: -10px 0; border-radius: 14px; }
QSlider::handle:horizontal:disabled { background: #666; }
"""


class SliderRow(QWidget):
    """Zeile: Name | Regler | Wert. Intern 0..steps, umgerechnet über to_val/from_val."""
    changed = pyqtSignal(float)

    def __init__(self, title, steps, to_val, from_val, fmt):
        super().__init__()
        self.to_val, self.from_val, self.fmt = to_val, from_val, fmt
        self.name = QLabel(title)
        self.name.setFixedWidth(92)
        self.value = QLabel()
        self.value.setFixedWidth(62)
        self.value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, steps)
        self.slider.setStyleSheet(SLIDER_STYLE)
        self.slider.setMinimumHeight(36)
        self.slider.valueChanged.connect(self._on_change)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.name)
        row.addWidget(self.slider, 1)
        row.addWidget(self.value)

    def _on_change(self, i):
        v = self.to_val(i)
        self.value.setText(self.fmt(v))
        self.changed.emit(v)

    def set_value(self, v):
        self.slider.blockSignals(True)
        self.slider.setValue(self.from_val(v))
        self.slider.blockSignals(False)
        self.value.setText(self.fmt(v))

    def setEnabled(self, on):
        super().setEnabled(on)
        color = "white" if on else "#777"
        self.name.setStyleSheet(f"color: {color};")
        self.value.setStyleSheet(f"color: {color};")


def linear_row(title, lo, hi, step, fmt="{:.2f}"):
    steps = round((hi - lo) / step)
    return SliderRow(title, steps,
                     to_val=lambda i: lo + i * step,
                     from_val=lambda v: round((v - lo) / step),
                     fmt=lambda v: fmt.format(v))


class SettingsPanel(QWidget):
    done = pyqtSignal()

    def __init__(self, settings, get_metadata):
        super().__init__()
        self.settings = settings
        self.get_metadata = get_metadata
        self.save_timer = QTimer(self, singleShot=True, interval=1000,
                                 timeout=settings.save)

        title = QLabel("Bild-Einstellungen")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.rows = {
            "Brightness": linear_row("Helligkeit", -1.0, 1.0, 0.05, "{:+.2f}"),
            "Contrast": linear_row("Kontrast", 0.0, 4.0, 0.05),
            "Saturation": linear_row("Sättigung", 0.0, 3.0, 0.05),
            "Sharpness": linear_row("Schärfe", 0.0, 8.0, 0.1, "{:.1f}"),
            "ExposureValue": linear_row("Belicht.-Korr.", -4.0, 4.0, 0.1, "{:+.1f} EV"),
            "ExposureTime": SliderRow("Belicht.-Zeit", 100, exp_from_slider,
                                      exp_to_slider, fmt_exposure),
            "AnalogueGain": linear_row("Verstärkung", 1.0, 16.0, 0.1, "{:.1f}×"),
        }
        for key, row in self.rows.items():
            row.changed.connect(lambda v, k=key: self._set(k, v))

        self.btn_ae = QPushButton()
        self.btn_ae.clicked.connect(self.toggle_ae)
        self.btn_awb = QPushButton()
        self.btn_awb.clicked.connect(self.next_awb)
        btn_default = QPushButton("Standard")
        btn_default.clicked.connect(self.reset)
        btn_done = QPushButton("Fertig")
        btn_done.setObjectName("foto")
        btn_done.clicked.connect(self.done.emit)
        for b in (self.btn_ae, self.btn_awb, btn_default, btn_done):
            b.setObjectName(b.objectName() or "small")
            b.setMinimumHeight(40)
            b.setFocusPolicy(Qt.NoFocus)

        toggles = QHBoxLayout()
        toggles.addWidget(self.btn_ae)
        toggles.addWidget(self.btn_awb)
        bottom = QHBoxLayout()
        bottom.addWidget(btn_default)
        bottom.addWidget(btn_done)

        col = QVBoxLayout(self)
        col.setContentsMargins(8, 6, 8, 6)
        col.setSpacing(3)
        col.addWidget(title)
        for key in ("Brightness", "Contrast", "Saturation", "Sharpness"):
            col.addWidget(self.rows[key])
        col.addLayout(toggles)
        for key in ("ExposureValue", "ExposureTime", "AnalogueGain"):
            col.addWidget(self.rows[key])
        col.addStretch(1)
        col.addLayout(bottom)
        self.refresh()

    # Anzeige an den Zustand anpassen
    def refresh(self):
        s = self.settings.state
        for key, row in self.rows.items():
            row.set_value(s[key])
        ae = s["AeEnable"]
        self.btn_ae.setText("Belichtung: Auto" if ae else "Belichtung: Manuell")
        self.rows["ExposureValue"].setEnabled(ae)
        self.rows["ExposureTime"].setEnabled(not ae)
        self.rows["AnalogueGain"].setEnabled(not ae)
        label = next(d for d, k in AWB_MODES if k == s["Awb"])
        self.btn_awb.setText(f"WB: {label}")

    def _set(self, key, value):
        self.settings.state[key] = value
        self.settings.apply()
        self.save_timer.start()

    def toggle_ae(self):
        s = self.settings.state
        if s["AeEnable"]:
            # Beim Umschalten auf Manuell die aktuellen Auto-Werte übernehmen
            meta = self.get_metadata()
            if meta:
                s["ExposureTime"] = meta.get("ExposureTime", s["ExposureTime"])
                s["AnalogueGain"] = min(max(meta.get("AnalogueGain", 1.0), 1.0), 16.0)
        s["AeEnable"] = not s["AeEnable"]
        self.settings.apply()
        self.refresh()
        self.save_timer.start()

    def next_awb(self):
        s = self.settings.state
        keys = [k for _, k in AWB_MODES]
        nxt = keys[(keys.index(s["Awb"]) + 1) % len(keys)]
        if nxt == "Locked":
            meta = self.get_metadata()
            gains = meta.get("ColourGains") if meta else None
            if gains:
                s["ColourGains"] = list(gains)
            else:
                nxt = keys[0]
        s["Awb"] = nxt
        self.settings.apply()
        self.refresh()
        self.save_timer.start()

    def reset(self):
        self.settings.reset()
        self.refresh()
        self.save_timer.start()


# ------------------------------------------------------------------
# Brücke: GPIO- und Upload-Threads -> Qt-Hauptthread
# ------------------------------------------------------------------
class Bridge(QObject):
    action = pyqtSignal(str)
    status = pyqtSignal(str)


def setup_gpio(bridge):
    try:
        from gpiozero import Button
    except ImportError:
        print("gpiozero nicht verfügbar – physische Tasten deaktiviert")
        return []
    buttons = []
    for name, pin in GPIO_PINS.items():
        try:
            repeat = name in ("zoom_in", "zoom_out")
            b = Button(pin, pull_up=True, bounce_time=0.05,
                       hold_time=0.4, hold_repeat=repeat)
            b.when_pressed = lambda n=name: bridge.action.emit(n)
            if repeat:
                b.when_held = lambda n=name: bridge.action.emit(n)
            buttons.append(b)
        except Exception as e:
            print(f"GPIO {pin} ({name}) nicht nutzbar: {e}")
    return buttons


# ------------------------------------------------------------------
# Hauptfenster
# ------------------------------------------------------------------
STYLE = """
QWidget { background: black; color: white; font-size: 15px; }
QPushButton {
    background: #2b2b2b; color: white; border: 2px solid #555;
    border-radius: 12px; font-size: 24px; font-weight: bold;
}
QPushButton:pressed { background: #4a90d9; border-color: #4a90d9; }
QPushButton#foto { background: #1f6f3f; }
QPushButton#foto:pressed { background: #2fae5f; }
QPushButton#quit, QPushButton#small { font-size: 16px; }
QPushButton#quit { background: #3a2020; }
QLabel#status { color: #ccc; font-size: 14px; }
"""


class MicroscopeWindow(QWidget):
    def __init__(self, picam2):
        super().__init__()
        self.picam2 = picam2
        self.bridge = Bridge()
        self.capturing = False
        self.pending_file = None
        self.drag_pos = None
        self.latest_meta = {}
        self.zoom = ZoomController(picam2)
        self.settings = ImageSettings(picam2)

        # Metadaten jedes Bildes merken (für Auto->Manuell und WB fixieren)
        picam2.post_callback = self._store_metadata

        self.setWindowTitle("Mikroskop")
        self.setStyleSheet(STYLE)

        # Kamerabild
        self.preview = QGlPicamera2(picam2, width=DISPLAY_W - BUTTON_COL_W,
                                    height=DISPLAY_H, keep_ar=True)
        self.preview.done_signal.connect(self.capture_done)
        self.preview.installEventFilter(self)

        # Seite 1: Hauptbuttons
        self.status = QLabel("Zoom 1.0×")
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setMinimumHeight(34)
        self.status_timer = QTimer(self, singleShot=True, timeout=self._update_status)

        main_page = QWidget()
        col = QVBoxLayout(main_page)
        col.setContentsMargins(8, 6, 8, 8)
        col.setSpacing(7)
        col.addWidget(self.status)
        for text, slot, stretch, repeat, obj in (
                ("Zoom +", self.zoom_in, 3, True, None),
                ("Zoom −", self.zoom_out, 3, True, None),
                ("1:1", self.reset, 2, False, None),
                ("Bild", self.open_settings, 2, False, None),
                ("Foto", self.snapshot, 4, False, "foto"),
                ("Beenden", self.close, 1, False, "quit")):
            col.addWidget(self._button(text, slot, repeat, obj), stretch)

        # Seite 2: Bild-Einstellungen
        self.settings_panel = SettingsPanel(self.settings, lambda: self.latest_meta)
        self.settings_panel.done.connect(self.close_settings)

        self.side = QStackedWidget()
        self.side.addWidget(main_page)
        self.side.addWidget(self.settings_panel)
        self.side.setFixedWidth(BUTTON_COL_W)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.preview, 1)
        layout.addWidget(self.side)

        self.bridge.action.connect(self.on_action)
        self.bridge.status.connect(self.show_message)
        self.gpio_buttons = setup_gpio(self.bridge)

    def _store_metadata(self, request):
        try:
            self.latest_meta = request.get_metadata()
        except Exception:
            pass

    def _button(self, text, slot, repeat=False, obj=None):
        b = QPushButton(text)
        if obj:
            b.setObjectName(obj)
        if repeat:
            b.setAutoRepeat(True)
            b.setAutoRepeatDelay(400)
            b.setAutoRepeatInterval(150)
        b.clicked.connect(slot)
        b.setFocusPolicy(Qt.NoFocus)
        return b

    # --- Seitenleiste umschalten ------------------------------------
    def open_settings(self):
        self.settings_panel.refresh()
        self.side.setFixedWidth(SETTINGS_COL_W)
        self.side.setCurrentIndex(1)

    def close_settings(self):
        self.settings.save()
        self.side.setCurrentIndex(0)
        self.side.setFixedWidth(BUTTON_COL_W)

    def toggle_settings(self):
        if self.side.currentIndex() == 0:
            self.open_settings()
        else:
            self.close_settings()

    # --- Aktionen ---------------------------------------------------
    def on_action(self, name):
        {"zoom_in": self.zoom_in, "zoom_out": self.zoom_out,
         "reset": self.reset, "snapshot": self.snapshot}[name]()

    def zoom_in(self):
        self.zoom.zoom_in(); self._update_status()

    def zoom_out(self):
        self.zoom.zoom_out(); self._update_status()

    def reset(self):
        self.zoom.reset(); self._update_status()

    def _update_status(self):
        if not self.status_timer.isActive():
            self.status.setText(f"Zoom {self.zoom.zoom:.1f}×")

    def show_message(self, text, ms=3000):
        self.status.setText(text)
        self.status_timer.start(ms)

    # --- Foto -------------------------------------------------------
    def snapshot(self):
        if self.capturing:
            return
        self.capturing = True
        QUEUE_DIR.mkdir(parents=True, exist_ok=True)
        name = datetime.now().strftime("mikro_%Y-%m-%d_%H-%M-%S.jpg")
        self.pending_file = QUEUE_DIR / name
        self.show_message("Foto …", 1500)
        self.picam2.capture_file(str(self.pending_file),
                                 signal_function=self.preview.signal_done)

    def capture_done(self, job):
        try:
            self.picam2.wait(job)
        except Exception as e:
            self.show_message(f"Fehler: {e}", 5000)
            self.capturing = False
            return
        self.capturing = False
        threading.Thread(target=self.upload, args=(self.pending_file,), daemon=True).start()

    def upload(self, path):
        try:
            if not os.path.isdir(SMB_DIR):
                raise OSError("Freigabe nicht eingehängt")
            files = sorted(QUEUE_DIR.glob("mikro_*.jpg"))
            for f in files:
                shutil.copy2(f, SMB_DIR / f.name)
                if not KEEP_LOCAL_COPY:
                    f.unlink()
            extra = len(files) - 1
            msg = "Gespeichert ✓" + (f" (+{extra})" if extra > 0 else "")
            self.bridge.status.emit(msg)
        except Exception as e:
            print(f"SMB-Upload fehlgeschlagen: {e}")
            self.bridge.status.emit("Server offline – lokal gespeichert")

    # --- Wischen zum Verschieben -------------------------------------
    def eventFilter(self, obj, ev):
        if obj is self.preview:
            t = ev.type()
            if t == QEvent.MouseButtonPress:
                self.drag_pos = ev.pos()
                return True
            if t == QEvent.MouseMove and self.drag_pos is not None:
                d = ev.pos() - self.drag_pos
                self.drag_pos = ev.pos()
                self.zoom.pan(-d.x() / self.preview.width(), -d.y() / self.preview.height())
                return True
            if t == QEvent.MouseButtonRelease:
                self.drag_pos = None
                return True
        return super().eventFilter(obj, ev)

    def keyPressEvent(self, ev):
        keys = {
            Qt.Key_Plus: self.zoom_in, Qt.Key_Minus: self.zoom_out,
            Qt.Key_0: self.reset, Qt.Key_Space: self.snapshot,
            Qt.Key_B: self.toggle_settings, Qt.Key_Escape: self.close,
            Qt.Key_Left: lambda: self.zoom.pan(-PAN_STEP, 0),
            Qt.Key_Right: lambda: self.zoom.pan(PAN_STEP, 0),
            Qt.Key_Up: lambda: self.zoom.pan(0, -PAN_STEP),
            Qt.Key_Down: lambda: self.zoom.pan(0, PAN_STEP),
        }
        if ev.key() in keys:
            keys[ev.key()]()

    def closeEvent(self, ev):
        self.settings.save()
        for b in self.gpio_buttons:
            b.close()
        super().closeEvent(ev)


def main():
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": CAMERA_SIZE, "format": "XBGR8888"}, buffer_count=4)
    picam2.configure(config)
    picam2.options["quality"] = JPEG_QUALITY

    app = QApplication([])
    win = MicroscopeWindow(picam2)
    picam2.start()
    win.settings.apply()   # gespeicherte Bild-Einstellungen laden
    win.showFullScreen()
    app.setOverrideCursor(Qt.BlankCursor)
    try:
        app.exec_()
    finally:
        picam2.stop()


if __name__ == "__main__":
    main()
