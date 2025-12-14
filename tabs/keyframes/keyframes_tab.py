"""
Pestaña para extraer keyframes de videos.
"""
import os
import shutil
import logging
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QLabel, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox
)

from utils.keyframes import (
    ensure_dir, extract_gif_frames, extract_webm_key_frames
)

logger = logging.getLogger(__name__)


class KeyframesTab(QWidget):
    """Pestaña para extraer keyframes de archivos GIF y WebM."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        self.keyframes_video_path_label = QLabel("Video Path:")
        self.keyframes_video_path_lineedit = QLineEdit()
        self.keyframes_video_browse_button = QPushButton("Browse Video")
        self.keyframes_video_browse_button.clicked.connect(self.select_keyframes_video)

        self.keyframes_output_folder_label = QLabel("Output Folder:")
        self.keyframes_output_folder_lineedit = QLineEdit()
        self.keyframes_output_folder_browse_button = QPushButton("Browse Output Folder")
        self.keyframes_output_folder_browse_button.clicked.connect(
            self.select_keyframes_output_folder
        )

        self.keyframes_run_button = QPushButton("Extract Key Frames")
        self.keyframes_run_button.clicked.connect(self.run_keyframes_extraction)

        layout = QVBoxLayout()
        layout.addWidget(self.keyframes_video_path_label)
        hlayout_video = QHBoxLayout()
        hlayout_video.addWidget(self.keyframes_video_path_lineedit)
        hlayout_video.addWidget(self.keyframes_video_browse_button)
        layout.addLayout(hlayout_video)

        layout.addWidget(self.keyframes_output_folder_label)
        hlayout_output = QHBoxLayout()
        hlayout_output.addWidget(self.keyframes_output_folder_lineedit)
        hlayout_output.addWidget(self.keyframes_output_folder_browse_button)
        layout.addLayout(hlayout_output)

        layout.addWidget(self.keyframes_run_button)
        self.setLayout(layout)

    def select_keyframes_video(self):
        """Selecciona el archivo de video."""
        video_file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.gif *.webm)"
        )
        if video_file:
            self.keyframes_video_path_lineedit.setText(video_file)
            logger.info(f"Selected video: {video_file}")

    def select_keyframes_output_folder(self):
        """Selecciona la carpeta de salida."""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.keyframes_output_folder_lineedit.setText(folder)
            logger.info(f"Selected output folder: {folder}")

    def run_keyframes_extraction(self):
        """Ejecuta la extracción de keyframes."""
        video_path = self.keyframes_video_path_lineedit.text().strip()
        output_folder = self.keyframes_output_folder_lineedit.text().strip()

        if not video_path or not os.path.exists(video_path):
            QMessageBox.warning(self, "Error", "Please select a valid video file.")
            return

        if not output_folder:
            QMessageBox.warning(self, "Error", "Please select an output folder.")
            return

        # Crear las carpetas Output y Success dentro del folder de salida
        output_dir = os.path.join(output_folder, "Output")
        success_dir = os.path.join(output_folder, "Success")
        ensure_dir(output_dir)
        ensure_dir(success_dir)

        ext = os.path.splitext(video_path)[1].lower()
        try:
            logger.info(f"Extracting keyframes from {video_path}")
            if ext == ".gif":
                extract_gif_frames(video_path, output_dir)
            elif ext == ".webm":
                extract_webm_key_frames(video_path, output_dir)
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Unsupported video format. Only GIF and WEBM are supported."
                )
                return

            # Mover el video original a la carpeta Success
            shutil.move(video_path, os.path.join(success_dir, os.path.basename(video_path)))
            QMessageBox.information(self, "Success", "Key frames extracted successfully.")
            logger.info(f"Keyframes extracted successfully from {video_path}")
        except FileNotFoundError:
            error_msg = "FFmpeg not found. Please install FFmpeg to extract WebM keyframes."
            logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
        except Exception as e:
            logger.error(f"Error extracting keyframes: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

