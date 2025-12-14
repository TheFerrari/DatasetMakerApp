"""
Punto de entrada principal de la aplicación Dataset Maker.
"""
import sys
import logging
from PySide6.QtWidgets import QApplication

from config.logging_config import setup_logging, get_logger
from core.main_window import MainWindow

# Configurar logging
setup_logging()
logger = get_logger(__name__)


def main():
    """Función principal de la aplicación."""
    try:
        logger.info("Starting Dataset Maker App")
        
        app = QApplication(sys.argv)
        
        window = MainWindow()
        window.apply_fusion_theme(app)
        window.show()
        
        logger.info("Application started successfully")
        
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"Fatal error starting application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

