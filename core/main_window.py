"""
Ventana principal de la aplicación.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QTabWidget, QVBoxLayout, QApplication, QStyleFactory
)
from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt

from tabs.search_tags.search_tags_tab import SearchTagsTab
from tabs.upscale_image.upscale_image_tab import UpscaleImageTab
from tabs.fuse_characters.fuse_characters_tab import FuseCharactersTab
from tabs.keyframes.keyframes_tab import KeyframesTab
from tabs.tag_images.tag_images_tab import TagImagesTab

logger = logging.getLogger(__name__)


class MainWindow(QWidget):
    """Ventana principal de la aplicación con sistema de pestañas."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dataset Maker App")
        self.setup_ui()
        logger.info("Main window initialized")

    def setup_ui(self):
        """Configura la interfaz de usuario principal."""
        # Crear el widget de pestañas
        self.tabs = QTabWidget()

        # Crear las pestañas
        self.search_tags_tab = SearchTagsTab()
        self.upscale_image_tab = UpscaleImageTab()
        self.fuse_characters_tab = FuseCharactersTab()
        self.keyframes_tab = KeyframesTab()
        self.tag_images_tab = TagImagesTab()

        # Añadir pestañas al widget
        self.tabs.addTab(self.search_tags_tab, "Search Tags")
        self.tabs.addTab(self.upscale_image_tab, "Upscale Image")
        self.tabs.addTab(self.fuse_characters_tab, "Fuse Characters")
        self.tabs.addTab(self.keyframes_tab, "KeyFrames")
        self.tabs.addTab(self.tag_images_tab, "Tag Images")

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def apply_fusion_theme(self, app):
        """
        Aplica el tema Fusion a la aplicación.
        
        Args:
            app: Instancia de QApplication
        """
        app.setStyle(QStyleFactory.create("Fusion"))

        palette = QPalette()
        palette.setColor(QPalette.Window, Qt.white)
        palette.setColor(QPalette.Base, Qt.lightGray)
        palette.setColor(QPalette.Text, Qt.black)
        palette.setColor(QPalette.ButtonText, Qt.blue)

        app.setPalette(palette)
        logger.info("Fusion theme applied")

