"""
Pestaña para etiquetar imágenes usando modelos de IA.
"""
import os
import subprocess
import logging
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QLabel, QVBoxLayout, QHBoxLayout,
    QCheckBox, QFileDialog, QMessageBox
)

logger = logging.getLogger(__name__)


class TagImagesTab(QWidget):
    """Pestaña para etiquetar imágenes usando modelos de tagging."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        self.tag_images_folder_label = QLabel("Images Folder:")
        self.tag_images_folder_lineedit = QLineEdit()
        self.tag_images_folder_browse_button = QPushButton("Browse Folder")
        self.tag_images_folder_browse_button.clicked.connect(self.select_tag_images_folder)

        self.caption_extension_label = QLabel("Caption File Extension:")
        self.caption_extension_lineedit = QLineEdit(".txt")

        self.caption_separator_label = QLabel("Caption Separator:")
        self.caption_separator_lineedit = QLineEdit(", ")

        self.recursive_checkbox = QCheckBox("Recursive")
        self.force_download_checkbox = QCheckBox("Force Model Re-download")

        self.tag_images_run_button = QPushButton("Tag Images")
        self.tag_images_run_button.clicked.connect(self.tag_images)

        layout = QVBoxLayout()
        layout.addWidget(self.tag_images_folder_label)
        hlayout_folder = QHBoxLayout()
        hlayout_folder.addWidget(self.tag_images_folder_lineedit)
        hlayout_folder.addWidget(self.tag_images_folder_browse_button)
        layout.addLayout(hlayout_folder)

        layout.addWidget(self.caption_extension_label)
        layout.addWidget(self.caption_extension_lineedit)
        layout.addWidget(self.caption_separator_label)
        layout.addWidget(self.caption_separator_lineedit)
        layout.addWidget(self.recursive_checkbox)
        layout.addWidget(self.force_download_checkbox)
        layout.addWidget(self.tag_images_run_button)
        self.setLayout(layout)

    def select_tag_images_folder(self):
        """Selecciona la carpeta con las imágenes."""
        folder = QFileDialog.getExistingDirectory(self, "Select Images Folder")
        if folder:
            self.tag_images_folder_lineedit.setText(folder)
            logger.info(f"Selected images folder: {folder}")

    def tag_images(self):
        """Ejecuta el proceso de etiquetado de imágenes."""
        folder = self.tag_images_folder_lineedit.text().strip()
        caption_extension = self.caption_extension_lineedit.text().strip()
        caption_separator = self.caption_separator_lineedit.text().strip()
        recursive = self.recursive_checkbox.isChecked()
        force_download = self.force_download_checkbox.isChecked()
        repo_id = "SmilingWolf/wd-eva02-large-tagger-v3"

        if not folder or not os.path.exists(folder):
            QMessageBox.warning(self, "Error", "Please select a valid images folder.")
            return

        # Buscar el script de tagging
        scriptdir = os.path.dirname(os.path.realpath(__file__))
        # Subir dos niveles desde tabs/tag_images/ hasta la raíz
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(scriptdir)))
        script_path = os.path.join(root_dir, "sd-scripts", "finetune", "tag_images_by_wd14_tagger.py")

        if not os.path.exists(script_path):
            QMessageBox.warning(
                self,
                "Error",
                f"Tagging script not found at {script_path}\n"
                "Please ensure sd-scripts is available."
            )
            logger.error(f"Tagging script not found at {script_path}")
            return

        run_cmd = [
            "accelerate", "launch", script_path,
            "--repo_id", repo_id,
            "--caption_extension", caption_extension,
            "--caption_separator", caption_separator,
            "--batch_size", "1",
            "--max_data_loader_n_workers", "1"
        ]
        if recursive:
            run_cmd.append("--recursive")
        if force_download:
            run_cmd.append("--force_download")
        run_cmd.append(folder)

        try:
            logger.info(f"Starting image tagging for folder: {folder}")
            logger.debug(f"Command: {' '.join(run_cmd)}")
            subprocess.run(run_cmd, check=True)
            QMessageBox.information(self, "Success", "Images have been tagged successfully.")
            logger.info("Image tagging completed successfully")
        except subprocess.CalledProcessError as e:
            error_msg = f"Tagging process failed with exit code {e.returncode}"
            logger.error(error_msg)
            QMessageBox.critical(self, "Error", f"An error occurred while tagging images: {error_msg}")
        except FileNotFoundError:
            error_msg = "accelerate command not found. Please install accelerate."
            logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
        except Exception as e:
            logger.error(f"Error tagging images: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while tagging images: {str(e)}")

