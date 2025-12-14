"""
Operaciones para extracción de keyframes de videos.
"""
import os
import subprocess
import logging
import imagehash
from PIL import Image, ImageSequence

logger = logging.getLogger(__name__)


def ensure_dir(directory):
    """
    Asegura que un directorio existe, creándolo si es necesario.
    
    Args:
        directory: Ruta del directorio
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.debug(f"Created directory: {directory}")


def extract_gif_frames(gif_path, output_dir, hash_size=8, cutoff=5):
    """
    Extrae frames únicos de un archivo GIF usando hash de imágenes.
    
    Args:
        gif_path: Ruta del archivo GIF
        output_dir: Directorio de salida para los frames
        hash_size: Tamaño del hash (default: 8)
        cutoff: Umbral de diferencia para considerar frames únicos (default: 5)
    """
    logger.info(f"Extracting frames from GIF: {gif_path}")
    hashes = []
    frame_count = 0

    try:
        with Image.open(gif_path) as img:
            frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
            for i, frame in enumerate(frames):
                h = imagehash.dhash(frame, hash_size)
                if not any((h - other) < cutoff for other in hashes):
                    output_path = os.path.join(
                        output_dir,
                        f"{os.path.splitext(os.path.basename(gif_path))[0]}_frame_{i}.png"
                    )
                    frame.save(output_path)
                    hashes.append(h)
                    frame_count += 1
                    logger.debug(f"Saved frame {i} to {output_path}")

        logger.info(f"Extracted {frame_count} unique frames from GIF")
    except Exception as e:
        logger.error(f"Error extracting GIF frames: {e}")
        raise


def extract_webm_key_frames(webm_path, output_dir, hash_size=8, cutoff=5):
    """
    Extrae keyframes únicos de un archivo WebM usando FFmpeg.
    
    Args:
        webm_path: Ruta del archivo WebM
        output_dir: Directorio de salida para los keyframes
        hash_size: Tamaño del hash (default: 8)
        cutoff: Umbral de diferencia para considerar frames únicos (default: 5)
    """
    logger.info(f"Extracting keyframes from WebM: {webm_path}")
    temp_pattern = os.path.join(output_dir, "temp_%04d.png")
    
    cmd = [
        'ffmpeg',
        '-i', webm_path,
        '-vf', "select='eq(pict_type\\,I)',scale=320:240,format=rgb24",
        '-vsync', 'vfr',
        '-frame_pts', 'true',
        temp_pattern
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.debug("FFmpeg extraction completed")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else 'Unknown error'}")
        raise
    except FileNotFoundError:
        logger.error("FFmpeg not found. Please install FFmpeg.")
        raise

    hashes = []
    i = 0
    keyframe_count = 0

    try:
        while True:
            temp_image_path = temp_pattern % i
            if not os.path.exists(temp_image_path):
                break
            
            with Image.open(temp_image_path) as img:
                h = imagehash.dhash(img, hash_size)
                if not any((h - other) < cutoff for other in hashes):
                    output_path = os.path.join(
                        output_dir,
                        f"{os.path.splitext(os.path.basename(webm_path))[0]}_key_frame_{len(hashes)}.png"
                    )
                    img.save(output_path)
                    hashes.append(h)
                    keyframe_count += 1
                    logger.debug(f"Saved keyframe {keyframe_count} to {output_path}")
            os.remove(temp_image_path)
            i += 1

        logger.info(f"Extracted {keyframe_count} unique keyframes from WebM")
    except Exception as e:
        logger.error(f"Error processing extracted frames: {e}")
        raise

