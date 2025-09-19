from __future__ import annotations
import sys
from PyQt6.QtWidgets import QApplication
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
    def launch_main_window():
        logger.info("Lancement de la fenêtre principale...")
        splash.close()
        window.show()
        window.raise_()
        window.activateWindow()
        logger.info("Fenêtre principale lancée")

    # Start splash and schedule main window launch
    splash.start()
    
    # Alternative: use QTimer as backup
    from PyQt6.QtCore import QTimer
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(launch_main_window)
    timer.start(3000)  # 3 seconds fallback
    
    # Also connect to splash signal
    splash.signals.finished.connect(launch_main_window)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()

