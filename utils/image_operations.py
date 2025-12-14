"""
Operaciones con imágenes.
"""
import os
import logging
from PIL import Image

logger = logging.getLogger(__name__)


def resize_images(directory, resolution=(1216, 1216), add_white_bg=False):
    """
    Redimensiona imágenes en un directorio.
    
    Args:
        directory: Directorio con las imágenes
        resolution: Tupla (ancho, alto) para la resolución objetivo
        add_white_bg: Si True, añade fondo blanco a PNGs con transparencia
    """
    if not isinstance(resolution, tuple) or len(resolution) != 2:
        raise ValueError("La resolución debe ser una tupla de dos valores, por ejemplo, (1024, 1024)")

    logger.info(f"Resizing images in {directory} to {resolution}")
    processed_count = 0

    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            file_path = os.path.join(directory, filename)
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    max_res = max(resolution)

                    resized_img = img
                    resized = False

                    if width < max_res or height < max_res:
                        # Mantener la relación de aspecto
                        aspect_ratio = width / height
                        if width < height:
                            new_width = int(max_res * aspect_ratio)
                            new_height = max_res
                        else:
                            new_width = max_res
                            new_height = int(max_res / aspect_ratio)

                        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
                        resized = True
                        logger.debug(f"Imagen {filename} redimensionada a {new_width}x{new_height}")

                    # Check if need to add white background
                    if add_white_bg and filename.lower().endswith('.png') and 'A' in resized_img.getbands():
                        background = Image.new('RGB', resized_img.size, (255, 255, 255))
                        background.paste(resized_img, mask=resized_img.split()[3])  # 3 is the alpha channel
                        resized_img = background
                        logger.debug(f"Fondo blanco añadido a {filename}")

                    # Save the image
                    resized_img.save(file_path)
                    processed_count += 1
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")

    logger.info(f"Processed {processed_count} images")


def add_white_background_to_images(directory):
    """
    Añade fondo blanco a imágenes PNG con transparencia.
    
    Args:
        directory: Directorio con las imágenes PNG
    """
    logger.info(f"Adding white background to PNG images in {directory}")
    processed_count = 0

    for filename in os.listdir(directory):
        if filename.lower().endswith('.png'):
            file_path = os.path.join(directory, filename)
            try:
                with Image.open(file_path) as img:
                    if 'A' in img.getbands():
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
                        background.save(file_path)
                        logger.debug(f"Fondo blanco añadido a {filename}")
                        processed_count += 1
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")

    logger.info(f"Processed {processed_count} PNG images with transparency")


def convert_webp_to_png(directory):
    """
    Convierte archivos WebP y WebM a PNG.
    
    Args:
        directory: Directorio con los archivos a convertir
    """
    logger.info(f"Converting WebP/WebM files to PNG in {directory}")
    converted_count = 0

    for file in os.listdir(directory):
        if file.endswith((".webp", ".webm")):
            webp_path = os.path.join(directory, file)
            png_path = os.path.splitext(webp_path)[0] + ".png"

            try:
                with Image.open(webp_path) as img:
                    img.save(png_path, "PNG")
                    logger.info(f"Converted: {file} to PNG")
                    converted_count += 1
            except Exception as e:
                logger.error(f"Error converting {file}: {e}")

    logger.info(f"Converted {converted_count} files")

