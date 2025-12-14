# Dataset Maker App

Aplicación profesional y modular para gestión de datasets de imágenes con múltiples herramientas integradas.

## Estructura del Proyecto

```
DatasetMakerApp/
├── main.py                 # Punto de entrada principal
├── config/                 # Configuración
│   ├── __init__.py
│   └── logging_config.py  # Configuración del sistema de logging
├── core/                   # Núcleo de la aplicación
│   ├── __init__.py
│   └── main_window.py     # Ventana principal
├── tabs/                   # Módulos de pestañas
│   ├── __init__.py
│   ├── search_tags/       # Búsqueda de tags
│   │   ├── __init__.py
│   │   └── search_tags_tab.py
│   ├── upscale_image/     # Redimensionado de imágenes
│   │   ├── __init__.py
│   │   └── upscale_image_tab.py
│   ├── fuse_characters/   # Fusión de caracteres
│   │   ├── __init__.py
│   │   └── fuse_characters_tab.py
│   ├── keyframes/         # Extracción de keyframes
│   │   ├── __init__.py
│   │   └── keyframes_tab.py
│   └── tag_images/        # Etiquetado de imágenes
│       ├── __init__.py
│       └── tag_images_tab.py
├── utils/                  # Utilidades
│   ├── __init__.py
│   ├── file_operations.py # Operaciones con archivos
│   ├── image_operations.py # Operaciones con imágenes
│   └── keyframes.py        # Funciones de keyframes
└── logs/                   # Logs de la aplicación (generado automáticamente)
```

## Características

### 1. Search Tags
- Búsqueda de archivos por tags en archivos de texto
- Soporte para tags positivos y negativos (prefijo `-`)
- Búsqueda recursiva en subcarpetas
- Visualización de imágenes y contenido de texto
- Operaciones: eliminar, mover, copiar archivos
- Conversión de WebP/WebM a PNG

### 2. Upscale Image
- Redimensionado de imágenes manteniendo relación de aspecto
- Añadir fondo blanco a imágenes PNG con transparencia
- Configuración de resolución personalizada

### 3. Fuse Characters
- Fusión de imágenes de dos directorios
- Combinación de textos usando templates
- Opción de añadir fondo blanco

### 4. KeyFrames
- Extracción de keyframes únicos de archivos GIF
- Extracción de keyframes de archivos WebM usando FFmpeg
- Eliminación de frames duplicados usando hash de imágenes

### 5. Tag Images
- Etiquetado automático de imágenes usando modelos de IA
- Integración con sd-scripts
- Configuración de extensión y separador de captions
- Modo recursivo

## Requisitos

- Python 3.8+
- PySide6
- PIL (Pillow)
- imagehash
- FFmpeg (para extracción de keyframes de WebM)
- accelerate (para etiquetado de imágenes)

## Instalación

```bash
pip install PySide6 Pillow imagehash
```

Para funcionalidad completa:
- Instalar FFmpeg para extracción de keyframes WebM
- Instalar accelerate para etiquetado de imágenes

## Uso

Ejecutar la aplicación:

```bash
python main.py
```

## Sistema de Logging

La aplicación incluye un sistema de logging completo:
- Logs guardados en el directorio `logs/`
- Rotación automática de archivos (máximo 5 archivos de 10MB cada uno)
- Logs con fecha en el nombre del archivo
- Niveles de logging configurables

## Desarrollo

Cada pestaña es un módulo independiente con su propio directorio y recursos. Esto facilita:
- Mantenimiento del código
- Escalabilidad
- Reutilización de componentes
- Testing individual

## Notas

- El archivo `T1.py` es la versión antigua y puede ser eliminado después de verificar que la nueva estructura funciona correctamente.
- Los logs se generan automáticamente en el directorio `logs/`.

