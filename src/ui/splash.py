from __future__ import annotations
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer, QEasingCurve, QPropertyAnimation, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget, QProgressBar


class SplashFinishedSignal(QObject):
    finished = pyqtSignal()


class SplashScreen(QWidget):
    """Custom splash / loading screen with logo and tagline."""
    def __init__(self, logo_path: Path, parent=None):
        super().__init__(parent)  # regular window (white background)
        # Remove translucent / frameless for a standard white window look
        self.setWindowTitle("World Embalage - Chargement")
        self.signals = SplashFinishedSignal()
        self._build_ui(logo_path)
        self._progress = 0

    def _build_ui(self, logo_path: Path):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 20)
        layout.setSpacing(16)

        # Logo
        logo_label = QLabel()
        if logo_path.exists():
            pm = QPixmap(str(logo_path))
            if not pm.isNull():
                pm = pm.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(pm)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        title = QLabel("WORLD EMBALAGE")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:26px; font-weight:700; letter-spacing:1px; color:#222;")
        layout.addWidget(title)

        tagline = QLabel("made by BRAHMI Oussama")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet("font-size:13px; color:#4A90E2; font-weight:500;")
        layout.addWidget(tagline)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setObjectName("splashProgress")
        layout.addWidget(self.progress)

        self.info_label = QLabel("Initialisation ...")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("font-size:12px; color:#555;")
        layout.addWidget(self.info_label)

        self._apply_style()
        self.resize(420, 460)
        self._center_on_screen()

    def _apply_style(self):
        self.setStyleSheet(
            """
            QWidget { background:#FFFFFF; }
            #splashProgress { background:#E6ECF1; border:1px solid #D3DAE0; border-radius:4px; }
            #splashProgress::chunk { background:#4A90E2; border-radius:4px; }
            """
        )

    def _center_on_screen(self):
        scr = self.screen()
        if scr:
            geo = scr.availableGeometry()
            self.move(geo.center().x() - self.width() // 2, geo.center().y() - self.height() // 2)

    def start(self, simulated_steps: int = 8, interval_ms: int = 250):
        self._progress = 0
        self.progress.setValue(0)
        self._steps_total = simulated_steps
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._timer.start(interval_ms)

    def _advance(self):
        self._progress += 1
        percent = int(self._progress / self._steps_total * 100)
        self.progress.setValue(percent)
        self.info_label.setText({
            1: "Chargement configuration ...",
            2: "Connexion base de données ...",
            3: "Initialisation modèles ...",
            4: "Préparation interface ...",
            5: "Chargement services ...",
            6: "Application du thème ...",
            7: "Finalisation ...",
        }.get(self._progress, "Prêt"))
        if self._progress >= self._steps_total:
            self._timer.stop()
            self._finish()

    def _finish(self):
        print("Splash finishing...")  # Debug print
        # Emit signal immediately, no fade animation for debugging
        self.signals.finished.emit()
        print("Signal emitted")  # Debug print
        self.close()

    def _emit_finished(self):
        # Backup method (not used in simplified version)
        self.signals.finished.emit()
        self.close()

__all__ = ["SplashScreen"]
