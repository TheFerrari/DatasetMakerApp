"""
Configuración del sistema de logging para la aplicación.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(log_dir="logs", log_level=logging.INFO):
    """
    Configura el sistema de logging con rotación de archivos.
    
    Args:
        log_dir: Directorio donde se guardarán los logs
        log_level: Nivel de logging (default: INFO)
    """
    # Crear directorio de logs si no existe
    os.makedirs(log_dir, exist_ok=True)
    
    # Nombre del archivo de log con fecha
    log_filename = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Configurar formato
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Configurar handler con rotación (máximo 5 archivos de 10MB cada uno)
    file_handler = RotatingFileHandler(
        log_filename,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger


def get_logger(name):
    """
    Obtiene un logger con el nombre especificado.
    
    Args:
        name: Nombre del logger (típicamente __name__)
    
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)

