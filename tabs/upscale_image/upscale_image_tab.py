"""
Pestaña para redimensionar imágenes.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QVBoxLayout, QCheckBox,
    QFileDialog, QMessageBox
)

from utils.image_operations import resize_images, add_white_background_to_images

logger = logging.getLogger(__name__)


class UpscaleImageTab(QWidget):
    """Pestaña para redimensionar y procesar imágenes."""

    def __init__(self):
        super().__init__()
        self.upscale_folder_path = ""
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        self.upscale_select_folder_button = QPushButton("Select Folder")
        self.upscale_select_folder_button.clicked.connect(self.upscale_select_folder)

        self.resolution_entry = QLineEdit()
        self.resolution_entry.setPlaceholderText("Resolution (e.g., 1216,1216)")

        self.add_white_bg_checkbox = QCheckBox("Add White Background to PNGs")

        self.upscale_button = QPushButton("Upscale Images")
        self.upscale_button.clicked.connect(self.upscale_images)

        self.add_white_background_button = QPushButton("Add White Background")
        self.add_white_background_button.clicked.connect(self.add_white_background)

        layout = QVBoxLayout()
        layout.addWidget(self.upscale_select_folder_button)
        layout.addWidget(self.resolution_entry)
        layout.addWidget(self.add_white_bg_checkbox)
        layout.addWidget(self.upscale_button)
        layout.addWidget(self.add_white_background_button)

        self.setLayout(layout)

    def upscale_select_folder(self):
        """Selecciona la carpeta con las imágenes."""
        folder_selected = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_selected:
            self.upscale_folder_path = folder_selected
            logger.info(f"Selected folder for upscale: {folder_selected}")

    def upscale_images(self):
        """Redimensiona las imágenes."""
        if not self.upscale_folder_path:
            QMessageBox.warning(self, "No Folder Selected", "Please select a folder first.")
            return

        resolution_text = self.resolution_entry.text()
        if not resolution_text:
            QMessageBox.warning(self, "No Resolution", "Please enter a resolution.")
            return

        try:
            width, height = map(int, resolution_text.split(','))
            resolution = (width, height)
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Resolution",
                "Please enter a valid resolution (e.g., 1216,1216)."
            )
            return

        add_white_bg = self.add_white_bg_checkbox.isChecked()

        try:
            resize_images(self.upscale_folder_path, resolution, add_white_bg)
            QMessageBox.information(self, "Upscale Complete", "Images have been upscaled successfully.")
            logger.info(f"Upscaled images in {self.upscale_folder_path} to {resolution}")
        except Exception as e:
            logger.error(f"Error upscaling images: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def add_white_background(self):
        """Añade fondo blanco a imágenes PNG con transparencia."""
        if not self.upscale_folder_path:
            QMessageBox.warning(self, "No Folder Selected", "Please select a folder first.")
            return

        try:
            add_white_background_to_images(self.upscale_folder_path)
            QMessageBox.information(self, "Process Complete", "White background added to PNG images.")
            logger.info(f"Added white background to PNGs in {self.upscale_folder_path}")
        except Exception as e:
            logger.error(f"Error adding white background: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

