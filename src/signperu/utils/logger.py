# utils/logger.py
# Configuración simple y reutilizable del logger para todo el proyecto.
# Crea un logger con manejo de fichero rotativo y salida por consola.
import logging
import logging.handlers
import os

DEFAULT_LOG_FOLDER = "logs"
DEFAULT_LOG_FILE = "signperu.log"
DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
DEFAULT_BACKUP_COUNT = 3

def get_logger(name: str, log_folder: str = DEFAULT_LOG_FOLDER, log_file: str = DEFAULT_LOG_FILE,
               level=logging.INFO):
    """
    Devuelve un logger configurado. Llamar desde otros módulos:
        logger = get_logger(__name__)
    """
    if not os.path.exists(log_folder):
        os.makedirs(log_folder, exist_ok=True)

    logger = logging.getLogger(name)
    # evitar añadir handlers múltiples si ya fue configurado
    if logger.handlers:
        logger.setLevel(level)
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    # Handler rotativo a fichero
    fh = logging.handlers.RotatingFileHandler(os.path.join(log_folder, log_file),
                                              maxBytes=DEFAULT_MAX_BYTES,
                                              backupCount=DEFAULT_BACKUP_COUNT,
                                              encoding='utf-8')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Handler a consola
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
