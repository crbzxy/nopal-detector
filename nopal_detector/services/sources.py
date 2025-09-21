"""
Factory pattern y clases para manejo de fuentes de entrada (imagen, video, cámara).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, Tuple, TYPE_CHECKING

from ..utils.logging import setup_logger

if TYPE_CHECKING:
    import cv2 as _cv2_type
    import numpy as _np_type


class BaseSource(ABC):
    """Clase base abstracta para fuentes de entrada."""
    
    def __init__(self, source_path: str):
        self.source_path = source_path
        self.logger = setup_logger(__name__)
    
    @abstractmethod
    def open(self) -> Tuple[Optional[Any], bool, Optional[Any]]:
        """
        Abre la fuente.
        
        Returns:
            Tupla (captura, is_stream, frame_inicial_si_imagen)
        """
        pass
    
    @abstractmethod
    def is_valid(self) -> bool:
        """Verifica si la fuente es válida."""
        pass
    
    @abstractmethod
    def get_type(self) -> str:
        """Devuelve el tipo de fuente."""
        pass


class CameraSource(BaseSource):
    """Fuente de cámara."""
    
    def is_valid(self) -> bool:
        """Verifica si el índice de cámara es válido."""
        return self.source_path.isdigit()
    
    def get_type(self) -> str:
        return "camera"
    
    def open(self) -> Tuple[Optional[Any], bool, Optional[Any]]:
        """Abre la cámara."""
        import cv2 as _cv2
        
        camera_index = int(self.source_path)
        cap = _cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            raise RuntimeError(f"No se pudo abrir la cámara {camera_index}")
        
        self.logger.info(f"Cámara {camera_index} abierta exitosamente")
        return cap, True, None


class ImageSource(BaseSource):
    """Fuente de imagen."""
    
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    
    def is_valid(self) -> bool:
        """Verifica si el archivo es una imagen válida."""
        path = Path(self.source_path)
        return (path.exists() and 
                path.suffix.lower() in self.IMAGE_EXTENSIONS)
    
    def get_type(self) -> str:
        return "image"
    
    def open(self) -> Tuple[Optional[Any], bool, Optional[Any]]:
        """Carga la imagen."""
        import cv2 as _cv2
        
        img = _cv2.imread(self.source_path)
        if img is None:
            raise RuntimeError(f"No se pudo leer la imagen: {self.source_path}")
        
        self.logger.info(f"Imagen cargada: {self.source_path}")
        return None, False, img


class VideoSource(BaseSource):
    """Fuente de video."""
    
    VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".m4v", ".mkv", ".webm"}
    
    def is_valid(self) -> bool:
        """Verifica si el archivo es un video válido."""
        path = Path(self.source_path)
        return (path.exists() and 
                path.suffix.lower() in self.VIDEO_EXTENSIONS)
    
    def get_type(self) -> str:
        return "video"
    
    def open(self) -> Tuple[Optional[Any], bool, Optional[Any]]:
        """Abre el video."""
        import cv2 as _cv2
        
        cap = _cv2.VideoCapture(self.source_path)
        if not cap.isOpened():
            raise RuntimeError(f"No se pudo abrir el video: {self.source_path}")
        
        self.logger.info(f"Video abierto: {self.source_path}")
        return cap, True, None


class SourceFactory:
    """Factory para crear fuentes según el tipo de entrada."""
    
    @staticmethod
    def create_source(source_path: str) -> BaseSource:
        """
        Crea una fuente según el tipo de entrada.
        
        Args:
            source_path: Ruta o índice de la fuente
            
        Returns:
            Instancia de la fuente apropiada
            
        Raises:
            ValueError: Si no se puede determinar el tipo de fuente
            FileNotFoundError: Si el archivo no existe
        """
        logger = setup_logger(__name__)
        
        # Verificar si es cámara (número)
        if source_path.isdigit():
            source = CameraSource(source_path)
            if source.is_valid():
                return source
            raise ValueError(f"Índice de cámara inválido: {source_path}")
        
        # Verificar si el archivo existe
        if not Path(source_path).exists():
            raise FileNotFoundError(f"No existe la fuente: {source_path}")
        
        # Intentar imagen
        source = ImageSource(source_path)
        if source.is_valid():
            return source
        
        # Intentar video
        source = VideoSource(source_path)
        if source.is_valid():
            return source
        
        # Si ninguno funciona
        path = Path(source_path)
        logger.error(f"Tipo de archivo no soportado: {path.suffix}")
        raise ValueError(
            f"Tipo de archivo no soportado: {path.suffix}. "
            f"Soportados: {ImageSource.IMAGE_EXTENSIONS | VideoSource.VIDEO_EXTENSIONS}"
        )


class SourceManager:
    """Manager para manejar fuentes de manera uniforme."""
    
    def __init__(self, source_path: str):
        self.source = SourceFactory.create_source(source_path)
        self.cap: Optional[Any] = None
        self.is_stream: bool = False
        self.current_frame: Optional[Any] = None
        self.logger = setup_logger(__name__)
    
    def __enter__(self):
        """Context manager entry."""
        self.cap, self.is_stream, self.current_frame = self.source.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
    
    def release(self) -> None:
        """Libera recursos."""
        if self.cap is not None:
            self.cap.release()
            self.logger.info("Fuente liberada")
    
    def get_source_type(self) -> str:
        """Devuelve el tipo de fuente."""
        return self.source.get_type()
    
    def get_video_properties(self) -> Tuple[int, int, float]:
        """
        Obtiene propiedades del video (ancho, alto, fps).
        Solo válido para streams.
        """
        if not self.is_stream or self.cap is None:
            raise ValueError("No es un stream válido")
        
        import cv2 as _cv2
        
        width = int(self.cap.get(_cv2.CAP_PROP_FRAME_WIDTH) or 1280)
        height = int(self.cap.get(_cv2.CAP_PROP_FRAME_HEIGHT) or 720)
        fps = self.cap.get(_cv2.CAP_PROP_FPS) or 25.0
        
        return width, height, fps
    
    def read_frame(self) -> Optional[Any]:
        """
        Lee el siguiente frame (solo para streams).
        
        Returns:
            Frame si está disponible, None si terminó el stream
        """
        if not self.is_stream or self.cap is None:
            return self.current_frame
        
        ok, frame = self.cap.read()
        return frame if ok else None