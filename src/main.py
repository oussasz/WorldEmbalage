from __future__ import annotations
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from pathlib import Path
from config.logging_config import logger
from database.connection import init_db
from ui.main_window import MainWindow
from ui.styles import StyleManager
from config.settings import settings
from sqlalchemy.exc import OperationalError
from config.database import engine
from ui.splash import SplashScreen
import signal


def main():
    logger.info("Démarrage de l'application World Embalage")
    logger.info("Base de données DSN (masqué utilisateur@hôte/db): {}@{}/{}", settings.db_user, settings.db_host, settings.db_name)
    # Quick connection test before creating tables
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))  # type: ignore[name-defined]
    except NameError:
        from sqlalchemy import text  # lazy import to keep earlier code concise
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as e:
        logger.error("Impossible de se connecter à la base de données: {}", e)
        logger.error("Dépannage: 1) Vérifiez la connexion mysql: mysql -u {} -p -h {} -P {} 2) Si échec: ALTER USER '{}'@'localhost' IDENTIFIED WITH mysql_native_password BY 'StrongPassword123'; FLUSH PRIVILEGES;", settings.db_user, settings.db_host, settings.db_port, settings.db_user)
        return
    init_db()

    app = QApplication(sys.argv)
    
    # Graceful Ctrl+C (SIGINT) handling to avoid core dump during splash
    def _handle_sigint(signal_num, frame):
        try:
            app.quit()
        except Exception:
            pass
    try:
        signal.signal(signal.SIGINT, _handle_sigint)
    except Exception:
        pass
    app.setApplicationName("World Embalage")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("World Embalage")

    # Set global app icon from LOGO.jpg if available
    logo_path = Path(__file__).resolve().parent.parent / 'LOGO.jpg'
    if logo_path.exists():
        app.setWindowIcon(QIcon(str(logo_path)))

    # Apply theme first
    StyleManager.apply_white_theme(app) 

    # Show splash screen with timer-based auto-close
    splash = SplashScreen(logo_path)
    splash.show()
    
    # Create and prepare main window
    window = MainWindow()
    if logo_path.exists():
        window.setWindowIcon(QIcon(str(logo_path)))
    window.resize(1400, 800)

    # Use QTimer to launch main window after splash
    _launch_state = {"launched": False}
    def launch_main_window():
        # Guard against double-launch from both timer and splash signal
        if _launch_state.get("launched"):
            return
        _launch_state["launched"] = True
        logger.info("Lancement de la fenêtre principale...")
        try:
            splash.close()
        except Exception:
            pass
        # Start maximized to fill screen, while keeping window controls (minimize/restore/close)
        try:
            from PyQt6.QtCore import Qt, QTimer
            # Set the window state to maximized first (helps some WMs)
            try:
                window.setWindowState(window.windowState() | Qt.WindowState.WindowMaximized)
            except Exception:
                pass
            # Show and then apply showMaximized (order matters on some Linux WMs)
            window.show()
            try:
                window.showMaximized()
            except Exception:
                pass
            # Apply a zero-delay re-maximize to catch any late layout/WM adjustments
            try:
                QTimer.singleShot(0, window.showMaximized)
            except Exception:
                pass
        except Exception:
            window.show()
        try:
            window.raise_()
            window.activateWindow()
        except Exception:
            pass
        logger.info("Fenêtre principale lancée")

    # Start splash and schedule main window launch
    splash.start()
    
    # Alternative: use QTimer as backup
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(launch_main_window)
    timer.start(3000)  # 3 seconds fallback
    
    # Also connect to splash signal
    splash.signals.finished.connect(launch_main_window)

    # Extra enforcement for some Linux window managers: re-apply maximized shortly after show
    def _enforce_maximize():
        try:
            window.setWindowState(window.windowState() | Qt.WindowState.WindowMaximized)
            window.showMaximized()
        except Exception:
            pass
    QTimer.singleShot(50, _enforce_maximize)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()

