"""
Pestaña de búsqueda de tags en archivos.
"""
import os
import shutil
import logging
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QLabel, QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QCheckBox,
    QSplitter, QTextEdit
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from utils.file_operations import find_files_with_phrase

logger = logging.getLogger(__name__)


class SearchTagsTab(QWidget):
    """Pestaña para buscar archivos por tags y gestionarlos."""

    def __init__(self):
        super().__init__()
        self.folder_path = ""
        self.result_count = 0
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Widgets
        self.select_folder_button = QPushButton("Select Folder")
        self.select_folder_button.clicked.connect(self.select_folder)

        self.search_entry = QLineEdit()
        self.search_entry.returnPressed.connect(self.search)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search)

        self.result_label = QLabel("Results Found: 0")

        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all)

        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.clicked.connect(self.deselect_all)

        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_files)

        self.move_button = QPushButton("Move")
        self.move_button.clicked.connect(self.move_files)

        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_files)

        self.convert_button = QPushButton("Convert to PNG")
        self.convert_button.clicked.connect(self.convert_webp_to_png)

        self.search_subfolders = QCheckBox("Search in Subfolders")

        self.show_text_checkbox = QCheckBox("Show Text Content")
        self.show_text_checkbox.stateChanged.connect(self.toggle_text_content)

        # Tree widget to display files
        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["File Name"])
        self.tree.itemClicked.connect(self.display_image_preview)

        # Image preview area
        self.image_label = QLabel()
        self.image_label.setFixedSize(400, 400)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid black;")

        # Text content display area
        self.text_content = QTextEdit()
        self.text_content.setReadOnly(True)
        self.text_content.setVisible(False)

        # Layouts
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.select_folder_button)
        top_layout.addWidget(self.search_entry)
        top_layout.addWidget(self.search_button)
        top_layout.addWidget(self.result_label)

        middle_layout = QHBoxLayout()
        middle_layout.addWidget(self.select_all_button)
        middle_layout.addWidget(self.deselect_all_button)
        middle_layout.addWidget(self.delete_button)
        middle_layout.addWidget(self.move_button)
        middle_layout.addWidget(self.copy_button)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.convert_button)
        bottom_layout.addWidget(self.search_subfolders)
        bottom_layout.addWidget(self.show_text_checkbox)

        # Splitter para separar el tree y la previsualización
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.tree)

        right_side_layout = QVBoxLayout()
        right_side_layout.addWidget(self.image_label)
        right_side_layout.addWidget(self.text_content)

        right_side_widget = QWidget()
        right_side_widget.setLayout(right_side_layout)

        splitter.addWidget(right_side_widget)
        splitter.setSizes([300, 400])

        tab_layout = QVBoxLayout()
        tab_layout.addLayout(top_layout)
        tab_layout.addWidget(splitter)
        tab_layout.addLayout(middle_layout)
        tab_layout.addLayout(bottom_layout)

        self.setLayout(tab_layout)

    def select_folder(self):
        """Selecciona la carpeta donde buscar."""
        folder_selected = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_selected:
            self.folder_path = folder_selected
            logger.info(f"Selected folder: {folder_selected}")

    def search(self):
        """Realiza la búsqueda de archivos."""
        if not self.folder_path:
            QMessageBox.warning(self, "No Folder Selected", "Please select a folder first.")
            return

        files = find_files_with_phrase(
            self.folder_path,
            self.search_entry.text(),
            self.search_subfolders.isChecked()
        )
        self.update_treeview(files)
        self.result_count = len(files)
        self.result_label.setText(f"Results Found: {self.result_count}")

    def update_treeview(self, files):
        """Actualiza el árbol de archivos."""
        self.tree.clear()
        for file in files:
            item = QTreeWidgetItem([file])
            item.setCheckState(0, Qt.Unchecked)
            self.tree.addTopLevelItem(item)
        self.image_label.clear()
        self.text_content.clear()

    def select_all(self):
        """Selecciona todos los archivos."""
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item.setCheckState(0, Qt.Checked)

    def deselect_all(self):
        """Deselecciona todos los archivos."""
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item.setCheckState(0, Qt.Unchecked)

    def get_selected_items(self):
        """Obtiene los archivos seleccionados."""
        selected_files = []
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if item.checkState(0) == Qt.Checked:
                selected_files.append(item.text(0))
        return selected_files

    def delete_files(self):
        """Elimina los archivos seleccionados."""
        selected_files = self.get_selected_items()
        if not selected_files:
            QMessageBox.warning(self, "No Files Selected", "Please select files to delete.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete the selected files?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            deleted_count = 0
            for file_path in selected_files:
                try:
                    os.remove(file_path)
                    for ext in ['.jpg', '.png']:
                        img_file_path = os.path.splitext(file_path)[0] + ext
                        if os.path.exists(img_file_path):
                            os.remove(img_file_path)
                    deleted_count += 1
                    logger.info(f"Deleted file: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {e}")

            QMessageBox.information(self, "Delete Complete", f"{deleted_count} files deleted successfully.")
            self.search()

    def move_files(self):
        """Mueve los archivos seleccionados a una nueva carpeta."""
        selected_files = self.get_selected_items()
        if not selected_files:
            QMessageBox.warning(self, "No Files Selected", "Please select files to move.")
            return

        from PySide6.QtWidgets import QInputDialog
        new_folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter the name of the new folder:")
        if ok and new_folder_name:
            new_folder_path = os.path.join(self.folder_path, new_folder_name)
            os.makedirs(new_folder_path, exist_ok=True)

            moved_count = 0
            for file_path in selected_files:
                try:
                    shutil.move(file_path, new_folder_path)
                    for ext in ['.jpg', '.png']:
                        img_file_path = os.path.splitext(file_path)[0] + ext
                        if os.path.exists(img_file_path):
                            shutil.move(img_file_path, new_folder_path)
                            break
                    moved_count += 1
                    logger.info(f"Moved file: {file_path} to {new_folder_path}")
                except Exception as e:
                    logger.error(f"Error moving {file_path}: {e}")

            QMessageBox.information(self, "Move Complete", f"{moved_count} files moved successfully.")
            self.search()

    def copy_files(self):
        """Copia los archivos seleccionados a una nueva carpeta."""
        selected_files = self.get_selected_items()
        if not selected_files:
            QMessageBox.warning(self, "No Files Selected", "Please select files to copy.")
            return

        from PySide6.QtWidgets import QInputDialog
        new_folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter the name of the new folder:")
        if ok and new_folder_name:
            new_folder_path = os.path.join(self.folder_path, new_folder_name)
            os.makedirs(new_folder_path, exist_ok=True)

            copied_count = 0
            for file_path in selected_files:
                try:
                    shutil.copy(file_path, new_folder_path)
                    for ext in ['.jpg', '.png']:
                        img_file_path = os.path.splitext(file_path)[0] + ext
                        if os.path.exists(img_file_path):
                            shutil.copy(img_file_path, new_folder_path)
                            break
                    copied_count += 1
                    logger.info(f"Copied file: {file_path} to {new_folder_path}")
                except Exception as e:
                    logger.error(f"Error copying {file_path}: {e}")

            QMessageBox.information(self, "Copy Complete", f"{copied_count} files copied successfully.")

    def convert_webp_to_png(self):
        """Convierte archivos WebP/WebM a PNG."""
        if not self.folder_path:
            QMessageBox.warning(self, "No Folder Selected", "Please select a folder first.")
            return

        from utils.image_operations import convert_webp_to_png as convert_func
        convert_func(self.folder_path)
        QMessageBox.information(self, "Conversion Complete", "All .webp files have been converted to .png.")

    def display_image_preview(self, item):
        """Muestra la previsualización de la imagen."""
        txt_file_path = item.text(0)
        base_name = os.path.splitext(txt_file_path)[0]

        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        image_found = False
        for ext in image_extensions:
            img_file_path = base_name + ext
            if os.path.exists(img_file_path):
                pixmap = QPixmap(img_file_path)
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                image_found = True
                break

        if not image_found:
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("No image found for this file.")

        if self.show_text_checkbox.isChecked():
            self.load_text_content(base_name)
        else:
            self.text_content.clear()

    def load_text_content(self, base_name):
        """Carga el contenido del archivo de texto."""
        txt_file_path = base_name + ".txt"
        if os.path.exists(txt_file_path):
            try:
                with open(txt_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_content.setPlainText(content)
            except Exception as e:
                logger.error(f"Error reading text file {txt_file_path}: {e}")
                self.text_content.setPlainText("Error reading text content.")
        else:
            self.text_content.setPlainText("No text content found.")

    def toggle_text_content(self):
        """Muestra u oculta el contenido de texto."""
        self.text_content.setVisible(self.show_text_checkbox.isChecked())
        selected_items = self.tree.selectedItems()
        if selected_items:
            self.display_image_preview(selected_items[0])

