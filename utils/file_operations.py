"""
Operaciones de archivos y búsqueda.
"""
import os
import logging

logger = logging.getLogger(__name__)


def find_files_with_phrase(folder_path, search_terms, search_in_subfolders):
    """
    Busca archivos .txt que contengan las frases especificadas.
    
    Args:
        folder_path: Ruta de la carpeta donde buscar
        search_terms: Términos de búsqueda separados por comas (pueden tener prefijo - para negación)
        search_in_subfolders: Si True, busca en subcarpetas
    
    Returns:
        Lista de rutas de archivos que coinciden
    """
    matching_files = []
    tags = [tag.strip() for tag in search_terms.split(',') if tag.strip()]
    
    positive_tags = [tag for tag in tags if not tag.startswith('-')]
    negative_tags = [tag[1:] for tag in tags if tag.startswith('-')]

    def search_in_directory(directory):
        try:
            for file in os.listdir(directory):
                full_path = os.path.join(directory, file)
                if os.path.isdir(full_path) and search_in_subfolders:
                    search_in_directory(full_path)
                elif file.endswith(".txt"):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                            if all(tag.lower() in content for tag in positive_tags) and \
                               all(tag.lower() not in content for tag in negative_tags):
                                matching_files.append(full_path)
                    except Exception as e:
                        logger.warning(f"Error reading file {full_path}: {e}")
        except PermissionError as e:
            logger.error(f"Permission denied accessing {directory}: {e}")
        except Exception as e:
            logger.error(f"Error searching in {directory}: {e}")

    logger.info(f"Searching in {folder_path} with terms: {search_terms}")
    search_in_directory(folder_path)
    logger.info(f"Found {len(matching_files)} matching files")
    return matching_files

