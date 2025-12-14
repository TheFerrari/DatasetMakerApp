"""
Pestaña de editor masivo de tags.
"""
import os
import re
import json
import shutil
import logging
from collections import defaultdict
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QLabel, QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QCheckBox,
    QSpinBox, QTextEdit, QGroupBox
)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)

# Archivo para guardar tags eliminadas
SAVED_TAGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "bulk_tag_editor_saved_tags.json")


class BulkTagEditorTab(QWidget):
    """Pestaña para editar tags masivamente en archivos de caption."""

    def __init__(self):
        super().__init__()
        self.folder_path = ""
        self.tag_data = {}  # {(namespace, tag): count}
        self.file_tags = {}  # {file_path: [list of (namespace, tag)]}
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Grupo de selección de carpeta
        folder_group = QGroupBox("Carpeta")
        folder_layout = QHBoxLayout()
        self.folder_lineedit = QLineEdit()
        self.folder_lineedit.setPlaceholderText("Selecciona una carpeta...")
        self.browse_button = QPushButton("Examinar...")
        self.browse_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_lineedit)
        folder_layout.addWidget(self.browse_button)
        folder_group.setLayout(folder_layout)

        # Opciones de escaneo
        options_group = QGroupBox("Opciones de Escaneo")
        options_layout = QVBoxLayout()
        
        self.recursive_checkbox = QCheckBox("Recursivo")
        self.recursive_checkbox.setChecked(True)
        
        min_count_layout = QHBoxLayout()
        min_count_layout.addWidget(QLabel("Frecuencia mínima para mostrar:"))
        self.min_count_spinbox = QSpinBox()
        self.min_count_spinbox.setMinimum(1)
        self.min_count_spinbox.setMaximum(1000)
        self.min_count_spinbox.setValue(5)
        min_count_layout.addWidget(self.min_count_spinbox)
        min_count_layout.addStretch()
        
        options_layout.addWidget(self.recursive_checkbox)
        options_layout.addLayout(min_count_layout)
        options_group.setLayout(options_layout)

        # Tags prohibidos
        banned_group = QGroupBox("Tags Prohibidos")
        banned_layout = QVBoxLayout()
        banned_label = QLabel("Un tag por línea o separados por comas:")
        self.banned_tags_text = QTextEdit()
        self.banned_tags_text.setMaximumHeight(100)
        self.banned_tags_text.setPlaceholderText("tag1\ntag2\ntag3")
        
        # Botón para cargar tags anteriores
        load_previous_button = QPushButton("Cargar Tags Anteriores")
        load_previous_button.clicked.connect(self.load_previous_tags)
        
        banned_layout.addWidget(banned_label)
        banned_layout.addWidget(self.banned_tags_text)
        banned_layout.addWidget(load_previous_button)
        banned_group.setLayout(banned_layout)

        # Botón de carga
        self.load_button = QPushButton("Cargar Tags")
        self.load_button.clicked.connect(self.load_tags)

        # Tree widget para tags
        tree_group = QGroupBox("Tags Agrupados por Namespace")
        tree_layout = QVBoxLayout()
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Tag", "Frecuencia"])
        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(1, 100)
        tree_layout.addWidget(self.tree)
        tree_group.setLayout(tree_layout)

        # Botones de acción
        buttons_layout = QHBoxLayout()
        self.dry_run_button = QPushButton("Dry Run")
        self.dry_run_button.clicked.connect(self.dry_run)
        self.apply_button = QPushButton("Aplicar Cambios")
        self.apply_button.clicked.connect(self.apply_changes)
        self.rename_button = QPushButton("Renombrar Archivos de Caption")
        self.rename_button.clicked.connect(self.rename_caption_files)
        buttons_layout.addWidget(self.dry_run_button)
        buttons_layout.addWidget(self.apply_button)
        buttons_layout.addWidget(self.rename_button)

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.addWidget(folder_group)
        main_layout.addWidget(options_group)
        main_layout.addWidget(banned_group)
        main_layout.addWidget(self.load_button)
        main_layout.addWidget(tree_group, stretch=1)
        main_layout.addLayout(buttons_layout)
        
        self.setLayout(main_layout)

    def select_folder(self):
        """Selecciona la carpeta donde buscar archivos .txt."""
        folder_selected = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if folder_selected:
            self.folder_path = folder_selected
            self.folder_lineedit.setText(folder_selected)
            logger.info(f"Carpeta seleccionada: {folder_selected}")
            # Cargar tags anteriores automáticamente
            self.load_previous_tags(silent=True)

    def parse_tag_line(self, line):
        """
        Parsea una línea de tag y retorna (namespace, tag).
        
        Args:
            line: Línea de texto del archivo
            
        Returns:
            Tupla (namespace, tag) o None si la línea está vacía
        """
        line = line.strip()
        if not line:
            return None
        
        # Si contiene ':', dividir en el primer ':'
        if ':' in line:
            parts = line.split(':', 1)
            namespace = parts[0].strip()
            tag = parts[1].strip()
            return (namespace, tag)
        else:
            # Sin namespace, usar 'general'
            return ('general', line)

    def normalize_tag(self, tag):
        """
        Normaliza un tag para comparación (strip espacios).
        
        Args:
            tag: String del tag
            
        Returns:
            Tag normalizado
        """
        return tag.strip()

    def get_banned_tags(self):
        """
        Obtiene la lista de tags prohibidos del textbox.
        
        Returns:
            Set de tags normalizados
        """
        text = self.banned_tags_text.toPlainText().strip()
        if not text:
            return set()
        
        # Separar por líneas o comas
        tags = []
        for line in text.split('\n'):
            line = line.strip()
            if ',' in line:
                tags.extend([t.strip() for t in line.split(',')])
            else:
                if line:
                    tags.append(line)
        
        # Normalizar y eliminar duplicados
        return {self.normalize_tag(tag) for tag in tags if tag}

    def save_removed_tags(self, unchecked_tags, banned_tags):
        """
        Guarda las tags eliminadas en un archivo JSON.
        
        Args:
            unchecked_tags: Set de tuplas (namespace, tag) no marcadas
            banned_tags: Set de tags prohibidos normalizados
        """
        try:
            # Obtener solo los valores de tag (sin namespace) de unchecked_tags
            removed_tag_values = set()
            for namespace, tag in unchecked_tags:
                # Agregar el tag sin namespace
                removed_tag_values.add(tag)
            
            # Combinar con banned_tags
            all_removed_tags = removed_tag_values.union(banned_tags)
            
            # Cargar tags existentes si el archivo existe
            existing_tags = set()
            if os.path.exists(SAVED_TAGS_FILE):
                try:
                    with open(SAVED_TAGS_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        existing_tags = set(data.get('tags', []))
                except Exception as e:
                    logger.warning(f"Error leyendo archivo de tags guardadas: {e}")
            
            # Combinar tags existentes con las nuevas
            all_tags = existing_tags.union(all_removed_tags)
            
            # Guardar en JSON
            data = {
                'tags': sorted(list(all_tags)),  # Ordenar para consistencia
                'last_updated': datetime.now().isoformat()
            }
            
            # Crear directorio si no existe
            file_dir = os.path.dirname(SAVED_TAGS_FILE)
            if file_dir:
                os.makedirs(file_dir, exist_ok=True)
            
            with open(SAVED_TAGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Tags eliminadas guardadas: {len(all_removed_tags)} nuevas, {len(all_tags)} totales")
            
        except Exception as e:
            logger.error(f"Error guardando tags eliminadas: {e}")

    def load_previous_tags(self, silent=False):
        """
        Carga las tags eliminadas previamente guardadas en el textbox de tags prohibidas.
        
        Args:
            silent: Si True, no muestra mensaje de confirmación
        """
        try:
            if not os.path.exists(SAVED_TAGS_FILE):
                if not silent:
                    QMessageBox.information(
                        self,
                        "Sin Tags Guardadas",
                        "No se encontraron tags guardadas anteriormente."
                    )
                return
            
            with open(SAVED_TAGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                saved_tags = data.get('tags', [])
            
            if not saved_tags:
                if not silent:
                    QMessageBox.information(
                        self,
                        "Sin Tags Guardadas",
                        "No hay tags guardadas para cargar."
                    )
                return
            
            # Obtener tags actuales del textbox
            current_text = self.banned_tags_text.toPlainText().strip()
            current_tags = set()
            if current_text:
                for line in current_text.split('\n'):
                    line = line.strip()
                    if ',' in line:
                        current_tags.update([t.strip() for t in line.split(',') if t.strip()])
                    elif line:
                        current_tags.add(line)
            
            # Combinar con tags guardadas
            all_tags = current_tags.union(saved_tags)
            
            # Actualizar textbox
            tags_text = '\n'.join(sorted(all_tags))
            self.banned_tags_text.setPlainText(tags_text)
            
            if not silent:
                QMessageBox.information(
                    self,
                    "Tags Cargadas",
                    f"Se cargaron {len(saved_tags)} tags guardadas.\n"
                    f"Total en el textbox: {len(all_tags)} tags."
                )
            
            logger.info(f"Tags anteriores cargadas: {len(saved_tags)} tags")
            
        except Exception as e:
            logger.error(f"Error cargando tags anteriores: {e}")
            if not silent:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Error al cargar tags anteriores: {str(e)}"
                )

    def scan_txt_files(self):
        """
        Escanea archivos .txt en la carpeta seleccionada.
        
        Returns:
            Lista de rutas de archivos .txt encontrados
        """
        if not self.folder_path or not os.path.exists(self.folder_path):
            return []
        
        txt_files = []
        recursive = self.recursive_checkbox.isChecked()
        
        def scan_directory(directory):
            try:
                for item in os.listdir(directory):
                    full_path = os.path.join(directory, item)
                    if os.path.isdir(full_path) and recursive:
                        scan_directory(full_path)
                    elif item.endswith('.txt') and os.path.isfile(full_path):
                        txt_files.append(full_path)
            except PermissionError as e:
                logger.warning(f"Permiso denegado en {directory}: {e}")
            except Exception as e:
                logger.error(f"Error escaneando {directory}: {e}")
        
        scan_directory(self.folder_path)
        logger.info(f"Encontrados {len(txt_files)} archivos .txt")
        return txt_files

    def load_tags(self):
        """Carga y agrega tags de todos los archivos .txt."""
        if not self.folder_path:
            QMessageBox.warning(self, "Sin Carpeta", "Por favor selecciona una carpeta primero.")
            return
        
        # Limpiar datos anteriores
        self.tag_data = defaultdict(int)
        self.file_tags = {}
        
        txt_files = self.scan_txt_files()
        if not txt_files:
            QMessageBox.information(self, "Sin Archivos", "No se encontraron archivos .txt en la carpeta seleccionada.")
            return
        
        banned_tags = self.get_banned_tags()
        min_count = self.min_count_spinbox.value()
        
        # Procesar cada archivo
        for file_path in txt_files:
            try:
                # Intentar leer con UTF-8, con fallback
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                except UnicodeDecodeError:
                    # Fallback a latin-1 si UTF-8 falla
                    with open(file_path, 'r', encoding='latin-1') as f:
                        lines = f.readlines()
                
                file_tag_list = []
                for line in lines:
                    parsed = self.parse_tag_line(line)
                    if parsed:
                        namespace, tag = parsed
                        normalized_tag = self.normalize_tag(tag)
                        
                        # Verificar si está en la lista de prohibidos
                        # Comparar tanto el tag completo como solo el valor
                        is_banned = False
                        for banned in banned_tags:
                            if normalized_tag.lower() == banned.lower() or tag.lower() == banned.lower():
                                is_banned = True
                                break
                        
                        if not is_banned:
                            key = (namespace, tag)  # Mantener tag original con espacios
                            self.tag_data[key] += 1
                            file_tag_list.append(key)
                
                self.file_tags[file_path] = file_tag_list
                
            except Exception as e:
                logger.error(f"Error leyendo archivo {file_path}: {e}")
        
        # Filtrar por frecuencia mínima
        filtered_tags = {
            k: v for k, v in self.tag_data.items()
            if v >= min_count
        }
        
        # Actualizar tree widget
        self.populate_tree(filtered_tags)
        
        QMessageBox.information(
            self,
            "Carga Completada",
            f"Se cargaron tags de {len(txt_files)} archivos.\n"
            f"Tags únicos mostrados: {len(filtered_tags)}"
        )

    def populate_tree(self, tag_data):
        """Pobla el QTreeWidget con tags agrupados por namespace."""
        self.tree.clear()
        
        # Agrupar por namespace
        namespace_groups = defaultdict(dict)
        for (namespace, tag), count in tag_data.items():
            namespace_groups[namespace][tag] = count
        
        # Crear items del árbol
        for namespace in sorted(namespace_groups.keys()):
            namespace_item = QTreeWidgetItem([namespace, ""])
            namespace_item.setExpanded(True)
            
            # Agregar tags como hijos
            tags_dict = namespace_groups[namespace]
            for tag in sorted(tags_dict.keys()):
                count = tags_dict[tag]
                tag_item = QTreeWidgetItem([tag, str(count)])
                tag_item.setCheckState(0, Qt.Checked)
                tag_item.setData(0, Qt.UserRole, (namespace, tag))  # Guardar datos para referencia
                namespace_item.addChild(tag_item)
            
            self.tree.addTopLevelItem(namespace_item)
        
        logger.info(f"Árbol poblado con {len(namespace_groups)} namespaces")

    def get_unchecked_tags(self):
        """
        Obtiene la lista de tags no marcados en el árbol.
        
        Returns:
            Set de tuplas (namespace, tag)
        """
        unchecked = set()
        root = self.tree.invisibleRootItem()
        
        for i in range(root.childCount()):
            namespace_item = root.child(i)
            for j in range(namespace_item.childCount()):
                tag_item = namespace_item.child(j)
                if tag_item.checkState(0) == Qt.Unchecked:
                    tag_data = tag_item.data(0, Qt.UserRole)
                    if tag_data:
                        # Convertir a tupla si es una lista (PySide6 puede convertir tuplas en listas)
                        if isinstance(tag_data, list):
                            tag_data = tuple(tag_data)
                        unchecked.add(tag_data)
        
        return unchecked

    def create_backup(self, folder_path):
        """
        Crea una carpeta de backup con timestamp.
        
        Args:
            folder_path: Ruta de la carpeta donde crear el backup
            
        Returns:
            Ruta de la carpeta de backup creada, o None si falla
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = os.path.join(folder_path, f"_backup_txt_{timestamp}")
        
        try:
            os.makedirs(backup_folder, exist_ok=True)
            logger.info(f"Carpeta de backup creada: {backup_folder}")
            return backup_folder
        except Exception as e:
            logger.error(f"Error creando carpeta de backup: {e}")
            return None

    def backup_file(self, file_path, backup_folder):
        """
        Hace backup de un archivo a la carpeta de backup.
        
        Args:
            file_path: Ruta del archivo original
            folder_path: Ruta de la carpeta base
            backup_folder: Ruta de la carpeta de backup
        """
        try:
            relative_path = os.path.relpath(file_path, self.folder_path)
            backup_path = os.path.join(backup_folder, relative_path)
            
            # Crear directorios necesarios
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            shutil.copy2(file_path, backup_path)
        except Exception as e:
            logger.warning(f"Error haciendo backup de {file_path}: {e}")

    def write_tags_to_file(self, file_path, tags_to_keep):
        """
        Escribe tags a un archivo en formato de una línea separada por comas.
        
        Args:
            file_path: Ruta del archivo
            tags_to_keep: Lista de tags (strings sin namespace) a escribir
        """
        # Eliminar duplicados manteniendo orden
        seen = set()
        unique_tags = []
        for tag in tags_to_keep:
            normalized = self.normalize_tag(tag)
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique_tags.append(tag)
        
        # Escribir como una línea separada por comas
        content = ", ".join(unique_tags)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.debug(f"Archivo escrito: {file_path}")
        except Exception as e:
            logger.error(f"Error escribiendo archivo {file_path}: {e}")
            raise

    def apply_changes(self):
        """Aplica los cambios: reescribe archivos eliminando tags no marcados y prohibidos."""
        if not self.file_tags:
            QMessageBox.warning(self, "Sin Datos", "Por favor carga los tags primero.")
            return
        
        unchecked_tags = self.get_unchecked_tags()
        banned_tags = self.get_banned_tags()
        
        if not unchecked_tags and not banned_tags:
            QMessageBox.information(self, "Sin Cambios", "No hay tags para eliminar.")
            return
        
        # Confirmar acción
        reply = QMessageBox.question(
            self,
            "Confirmar Cambios",
            f"Se modificarán {len(self.file_tags)} archivos.\n"
            f"Tags a eliminar: {len(unchecked_tags)} no marcados + tags prohibidos.\n\n"
            "¿Deseas continuar?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Crear backup
        backup_folder = self.create_backup(self.folder_path)
        if not backup_folder:
            reply = QMessageBox.question(
                self,
                "Error de Backup",
                "No se pudo crear la carpeta de backup. ¿Deseas continuar de todas formas?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        # Procesar archivos
        modified_count = 0
        error_count = 0
        
        for file_path, file_tag_list in self.file_tags.items():
            try:
                # Hacer backup si existe la carpeta
                if backup_folder:
                    self.backup_file(file_path, backup_folder)
                
                # Filtrar tags a mantener
                tags_to_keep = []
                for namespace, tag in file_tag_list:
                    # Verificar si está desmarcado
                    if (namespace, tag) in unchecked_tags:
                        continue
                    
                    # Verificar si está prohibido
                    normalized_tag = self.normalize_tag(tag)
                    is_banned = False
                    for banned in banned_tags:
                        if normalized_tag.lower() == banned.lower() or tag.lower() == banned.lower():
                            is_banned = True
                            break
                    
                    if not is_banned:
                        # Agregar tag sin namespace
                        tags_to_keep.append(tag)
                
                # Escribir archivo
                self.write_tags_to_file(file_path, tags_to_keep)
                modified_count += 1
                
            except Exception as e:
                logger.error(f"Error procesando {file_path}: {e}")
                error_count += 1
        
        # Guardar tags eliminadas
        self.save_removed_tags(unchecked_tags, banned_tags)
        
        # Mostrar resultado
        message = f"Proceso completado.\n"
        message += f"Archivos modificados: {modified_count}\n"
        if error_count > 0:
            message += f"Errores: {error_count}\n"
        if backup_folder:
            message += f"Backup creado en: {backup_folder}\n"
        message += f"\nTags eliminadas guardadas para futuras sesiones."
        
        QMessageBox.information(self, "Cambios Aplicados", message)
        
        # Recargar tags
        self.load_tags()

    def dry_run(self):
        """Muestra un preview de los cambios que se aplicarían sin modificar archivos."""
        if not self.file_tags:
            QMessageBox.warning(self, "Sin Datos", "Por favor carga los tags primero.")
            return
        
        unchecked_tags = self.get_unchecked_tags()
        banned_tags = self.get_banned_tags()
        
        if not unchecked_tags and not banned_tags:
            QMessageBox.information(self, "Sin Cambios", "No hay tags para eliminar.")
            return
        
        # Contar cambios
        files_to_modify = 0
        total_tags_removed = 0
        
        for file_path, file_tag_list in self.file_tags.items():
            tags_removed = 0
            for namespace, tag in file_tag_list:
                if (namespace, tag) in unchecked_tags:
                    tags_removed += 1
                    continue
                
                normalized_tag = self.normalize_tag(tag)
                is_banned = False
                for banned in banned_tags:
                    if normalized_tag.lower() == banned.lower() or tag.lower() == banned.lower():
                        is_banned = True
                        break
                
                if is_banned:
                    tags_removed += 1
            
            if tags_removed > 0:
                files_to_modify += 1
                total_tags_removed += tags_removed
        
        # Mostrar preview
        message = f"DRY RUN - Preview de Cambios\n\n"
        message += f"Archivos que se modificarían: {files_to_modify} de {len(self.file_tags)}\n"
        message += f"Tags totales a eliminar: {total_tags_removed}\n"
        message += f"Tags no marcados: {len(unchecked_tags)}\n"
        message += f"Tags prohibidos: {len(banned_tags)}\n\n"
        message += "No se realizarán cambios en los archivos."
        
        QMessageBox.information(self, "Dry Run", message)

    def rename_caption_files(self):
        """Renombra archivos de caption de formato MD5.ext.txt a MD5.txt (elimina extensión intermedia)."""
        if not self.folder_path:
            QMessageBox.warning(self, "Sin Carpeta", "Por favor selecciona una carpeta primero.")
            return
        
        # Patrón para archivos MD5.ext.txt
        # Ejemplo: abcdef0123456789.png.txt -> abcdef0123456789.txt
        md5_pattern = re.compile(r'^([a-f0-9]{32})\.([a-zA-Z0-9]+)\.txt$', re.IGNORECASE)
        
        txt_files = self.scan_txt_files()
        files_to_rename = []
        for f in txt_files:
            basename = os.path.basename(f)
            if md5_pattern.match(basename):
                files_to_rename.append(f)
        
        if not files_to_rename:
            QMessageBox.information(
                self,
                "Sin Archivos",
                "No se encontraron archivos con formato MD5.ext.txt para renombrar."
            )
            return
        
        # Ordenar por nombre para orden determinístico
        files_to_rename.sort()
        
        # Confirmar
        reply = QMessageBox.question(
            self,
            "Confirmar Renombrado",
            f"Se renombrarán {len(files_to_rename)} archivos.\n"
            "Se eliminará la extensión intermedia (ej: .png, .jpg) del nombre.\n"
            "¿Deseas continuar?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Renombrar archivos
        renamed_count = 0
        error_count = 0
        preview_examples = []
        collisions = []
        
        for file_path in files_to_rename:
            try:
                basename = os.path.basename(file_path)
                folder_dir = os.path.dirname(file_path)
                
                # Extraer MD5 del nombre
                match = md5_pattern.match(basename)
                if not match:
                    continue
                
                md5_hash = match.group(1)
                new_name = f"{md5_hash}.txt"
                new_path = os.path.join(folder_dir, new_name)
                
                # Verificar si el archivo destino ya existe
                if os.path.exists(new_path) and new_path != file_path:
                    collisions.append(f"{basename} -> {new_name} (ya existe)")
                    logger.warning(f"Colisión: {new_path} ya existe")
                    continue
                
                # Renombrar
                os.rename(file_path, new_path)
                renamed_count += 1
                
                # Guardar ejemplo para preview
                if len(preview_examples) < 5:
                    preview_examples.append(f"{basename} -> {new_name}")
                
                logger.info(f"Renombrado: {basename} -> {new_name}")
                
            except Exception as e:
                logger.error(f"Error renombrando {file_path}: {e}")
                error_count += 1
        
        # Mostrar resultado
        message = f"Renombrado completado.\n"
        message += f"Archivos renombrados: {renamed_count}\n"
        if error_count > 0:
            message += f"Errores: {error_count}\n"
        if collisions:
            message += f"Colisiones (archivos no renombrados): {len(collisions)}\n"
        if preview_examples:
            message += f"\nEjemplos:\n" + "\n".join(preview_examples[:5])
        if collisions and len(collisions) <= 5:
            message += f"\nColisiones:\n" + "\n".join(collisions[:5])
        
        QMessageBox.information(self, "Renombrado Completado", message)
