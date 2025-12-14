"""
Pestaña para fusionar caracteres de dos directorios.
"""
import os
import logging
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QTextEdit, QCheckBox,
    QFileDialog, QMessageBox, QGridLayout
)
from PIL import Image

logger = logging.getLogger(__name__)


class FuseCharactersTab(QWidget):
    """Pestaña para fusionar imágenes y textos de dos directorios."""

    def __init__(self):
        super().__init__()
        self.fuse_dir1 = ""
        self.fuse_dir2 = ""
        self.fuse_output_dir = ""
        self.template = ""
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        self.dir1_button = QPushButton("Select Directory 1")
        self.dir1_button.clicked.connect(self.select_fuse_dir1)

        self.dir2_button = QPushButton("Select Directory 2")
        self.dir2_button.clicked.connect(self.select_fuse_dir2)

        self.output_dir_button = QPushButton("Select Output Directory")
        self.output_dir_button.clicked.connect(self.select_fuse_output_dir)

        self.template_label = QLabel("Template Text:")
        self.template_edit = QTextEdit()

        self.add_white_bg_checkbox_fuse = QCheckBox("Add White Background")

        self.fuse_button = QPushButton("Fuse Characters")
        self.fuse_button.clicked.connect(self.fuse_data)

        layout = QGridLayout()
        layout.addWidget(self.dir1_button, 0, 0)
        layout.addWidget(self.dir2_button, 0, 1)
        layout.addWidget(self.output_dir_button, 0, 2)
        layout.addWidget(self.template_label, 1, 0, 1, 3)
        layout.addWidget(self.template_edit, 2, 0, 1, 3)
        layout.addWidget(self.add_white_bg_checkbox_fuse, 3, 0)
        layout.addWidget(self.fuse_button, 3, 1)

        self.setLayout(layout)

    def select_fuse_dir1(self):
        """Selecciona el primer directorio."""
        folder_selected = QFileDialog.getExistingDirectory(self, "Select Directory 1")
        if folder_selected:
            self.fuse_dir1 = folder_selected
            logger.info(f"Selected directory 1: {folder_selected}")

    def select_fuse_dir2(self):
        """Selecciona el segundo directorio."""
        folder_selected = QFileDialog.getExistingDirectory(self, "Select Directory 2")
        if folder_selected:
            self.fuse_dir2 = folder_selected
            logger.info(f"Selected directory 2: {folder_selected}")

    def select_fuse_output_dir(self):
        """Selecciona el directorio de salida."""
        folder_selected = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder_selected:
            self.fuse_output_dir = folder_selected
            logger.info(f"Selected output directory: {folder_selected}")

    def fuse_data(self):
        """Fusiona las imágenes y textos de los dos directorios."""
        if not all([self.fuse_dir1, self.fuse_dir2, self.fuse_output_dir]):
            QMessageBox.warning(self, "Missing Directories", "Please select all directories.")
            return

        self.template = self.template_edit.toPlainText()
        if not self.template:
            QMessageBox.warning(self, "No Template", "Please enter a template.")
            return

        output_dir_path = self.fuse_output_dir
        os.makedirs(output_dir_path, exist_ok=True)

        dir1_path = self.fuse_dir1
        dir2_path = self.fuse_dir2

        img_extensions = ['.jpg', '.png']

        files_dir1 = sorted(
            [f for f in os.listdir(dir1_path) if f.endswith(tuple(img_extensions))],
            key=lambda x: os.path.splitext(x)[0]
        )
        files_dir2 = sorted(
            [f for f in os.listdir(dir2_path) if f.endswith(tuple(img_extensions))],
            key=lambda x: os.path.splitext(x)[0]
        )

        max_length = max(len(files_dir1), len(files_dir2))

        files_dir1 *= (max_length // len(files_dir1)) + 1
        files_dir2 *= (max_length // len(files_dir2)) + 1

        processed_count = 0
        try:
            for i in range(max_length):
                file_name1, ext1 = os.path.splitext(files_dir1[i % len(files_dir1)])
                file_name2, ext2 = os.path.splitext(files_dir2[i % len(files_dir2)])

                img_path1 = os.path.join(dir1_path, files_dir1[i % len(files_dir1)])
                img_path2 = os.path.join(dir2_path, files_dir2[i % len(files_dir2)])

                img1 = Image.open(img_path1)
                img2 = Image.open(img_path2)

                if i % 2 == 0:
                    combined_img = self.join_images(img1, img2)
                else:
                    combined_img = self.join_images(img2, img1)

                combined_img_path = os.path.join(output_dir_path, f"{i+1}.jpg")
                combined_img.save(combined_img_path)

                self.fuse_texts(file_name1, file_name2, dir1_path, dir2_path, output_dir_path, i+1)
                processed_count += 1

            QMessageBox.information(
                self,
                "Fusion Complete",
                f"Fusion completed for {processed_count} images."
            )
            logger.info(f"Fused {processed_count} image pairs from {dir1_path} and {dir2_path}")
        except Exception as e:
            logger.error(f"Error fusing characters: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def join_images(self, img1, img2):
        """Une dos imágenes horizontalmente."""
        if self.add_white_bg_checkbox_fuse.isChecked():
            if img1.mode == 'RGBA':
                background = Image.new('RGB', img1.size, (255, 255, 255))
                background.paste(img1, mask=img1.split()[3])
                img1 = background
            if img2.mode == 'RGBA':
                background = Image.new('RGB', img2.size, (255, 255, 255))
                background.paste(img2, mask=img2.split()[3])
                img2 = background

        new_height = min(img1.height, img2.height)
        img1_new_width = int((new_height / img1.height) * img1.width)
        img2_new_width = int((new_height / img2.height) * img2.width)

        img1_resized = img1.resize((img1_new_width, new_height))
        img2_resized = img2.resize((img2_new_width, new_height))

        combined_img = Image.new(
            'RGB',
            (img1_new_width + img2_new_width, new_height),
            (255, 255, 255) if self.add_white_bg_checkbox_fuse.isChecked() else None
        )
        combined_img.paste(img1_resized, (0, 0))
        combined_img.paste(img2_resized, (img1_new_width, 0))

        return combined_img

    def fuse_texts(self, file_name1, file_name2, dir1, dir2, output_dir, index):
        """Fusiona los textos de dos archivos usando el template."""
        txt_path1 = os.path.join(dir1, f"{file_name1}.txt")
        txt_path2 = os.path.join(dir2, f"{file_name2}.txt")

        description_first_directory = ""
        description_second_directory = ""

        try:
            if os.path.exists(txt_path1):
                with open(txt_path1, 'r', encoding='utf-8') as f:
                    description_first_directory = f.read()

            if os.path.exists(txt_path2):
                with open(txt_path2, 'r', encoding='utf-8') as f:
                    description_second_directory = f.read()

            combined_text = self.template.format(
                description_first_directory=description_first_directory,
                description_second_directory=description_second_directory
            )

            new_txt_path = os.path.join(output_dir, f"{index}.txt")
            with open(new_txt_path, 'w', encoding='utf-8') as f:
                f.write(combined_text)
        except Exception as e:
            logger.error(f"Error fusing texts for {index}: {e}")

