"""
Sistema de observers para manejo de outputs y resultados.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, List, TYPE_CHECKING

from ..utils.logging import setup_logger

if TYPE_CHECKING:
    import cv2 as _cv2_type
    import numpy as _np_type


class OutputObserver(ABC):
    """Observer abstracto para manejo de outputs."""
    
    @abstractmethod
    def on_result(self, frame: Any, mask: Optional[Any], metadata: dict) -> None:
        """
        Maneja un resultado de detección.
        
        Args:
            frame: Frame procesado con overlay
            mask: Máscara binaria (si está disponible)
            metadata: Metadata del resultado (matches, source_type, etc.)
        """
        pass


class DisplayObserver(OutputObserver):
    """Observer para mostrar resultados en pantalla."""
    
    def __init__(self, window_name: str = "Nopal Detector"):
        self.window_name = window_name
        self.logger = setup_logger(__name__)
    
    def on_result(self, frame: Any, mask: Optional[Any], metadata: dict) -> None:
        """Muestra el frame en una ventana."""
        import cv2 as _cv2
        
        _cv2.imshow(self.window_name, frame)
        
        # Para streams, permitir salir con 'q'
        if metadata.get('is_stream', False):
            if _cv2.waitKey(1) & 0xFF == ord('q'):
                metadata['should_exit'] = True
        else:
            # Para imágenes, esperar cualquier tecla
            _cv2.waitKey(0)
    
    def cleanup(self) -> None:
        """Limpia recursos de display."""
        import cv2 as _cv2
        _cv2.destroyAllWindows()


class SaveImageObserver(OutputObserver):
    """Observer para guardar imágenes."""
    
    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.logger = setup_logger(__name__)
        # Asegurar que el directorio padre existe
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    def on_result(self, frame: Any, mask: Optional[Any], metadata: dict) -> None:
        """Guarda el frame como imagen."""
        import cv2 as _cv2
        
        success = _cv2.imwrite(str(self.output_path), frame)
        if success:
            self.logger.info(f"Imagen guardada en: {self.output_path}")
        else:
            self.logger.error(f"Error guardando imagen en: {self.output_path}")


class SaveMaskObserver(OutputObserver):
    """Observer para guardar máscaras binarias."""
    
    def __init__(self, mask_path: str):
        self.mask_path = Path(mask_path)
        self.logger = setup_logger(__name__)
        # Asegurar que el directorio padre existe
        self.mask_path.parent.mkdir(parents=True, exist_ok=True)
    
    def on_result(self, frame: Any, mask: Optional[Any], metadata: dict) -> None:
        """Guarda la máscara como imagen."""
        import cv2 as _cv2
        
        if mask is None:
            self.logger.warning("No hay máscara para guardar")
            return
        
        success = _cv2.imwrite(str(self.mask_path), mask)
        if success:
            self.logger.info(f"Máscara guardada en: {self.mask_path}")
        else:
            self.logger.error(f"Error guardando máscara en: {self.mask_path}")


class SaveVideoObserver(OutputObserver):
    """Observer para guardar videos."""
    
    def __init__(self, output_path: str, fourcc: str = "mp4v", fps: float = 25.0):
        self.output_path = Path(output_path)
        self.fourcc = fourcc
        self.fps = fps
        self.writer: Optional[Any] = None
        self.logger = setup_logger(__name__)
        # Asegurar que el directorio padre existe
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    def initialize_writer(self, frame: Any) -> None:
        """Inicializa el writer de video con las dimensiones del primer frame."""
        import cv2 as _cv2
        
        if self.writer is not None:
            return
        
        height, width = frame.shape[:2]
        fourcc_code = _cv2.VideoWriter_fourcc(*self.fourcc)
        self.writer = _cv2.VideoWriter(
            str(self.output_path), 
            fourcc_code, 
            self.fps, 
            (width, height)
        )
        self.logger.info(f"Writer de video inicializado: {self.output_path}")
    
    def on_result(self, frame: Any, mask: Optional[Any], metadata: dict) -> None:
        """Escribe el frame al video."""
        self.initialize_writer(frame)
        
        if self.writer is not None:
            self.writer.write(frame)
    
    def cleanup(self) -> None:
        """Libera el writer de video."""
        if self.writer is not None:
            self.writer.release()
            self.logger.info(f"Video guardado en: {self.output_path}")


class OutputManager:
    """Manager que coordina múltiples observers."""
    
    def __init__(self):
        self.observers: List[OutputObserver] = []
        self.logger = setup_logger(__name__)
    
    def add_observer(self, observer: OutputObserver) -> None:
        """Añade un observer."""
        self.observers.append(observer)
        self.logger.info(f"Observer añadido: {type(observer).__name__}")
    
    def remove_observer(self, observer: OutputObserver) -> None:
        """Remueve un observer."""
        if observer in self.observers:
            self.observers.remove(observer)
            self.logger.info(f"Observer removido: {type(observer).__name__}")
    
    def notify_result(self, frame: Any, mask: Optional[Any], metadata: dict) -> None:
        """Notifica a todos los observers de un nuevo resultado."""
        for observer in self.observers:
            try:
                observer.on_result(frame, mask, metadata)
            except Exception as e:
                self.logger.error(f"Error en observer {type(observer).__name__}: {e}")
    
    def cleanup(self) -> None:
        """Limpia recursos de todos los observers que tengan cleanup."""
        for observer in self.observers:
            if hasattr(observer, 'cleanup'):
                try:
                    observer.cleanup()  # type: ignore
                except Exception as e:
                    self.logger.error(f"Error limpiando observer {type(observer).__name__}: {e}")


class OutputFactory:
    """Factory para crear observers según configuración."""
    
    @staticmethod
    def create_display_observer(window_name: str = "Nopal Detector") -> DisplayObserver:
        """Crea observer de display."""
        return DisplayObserver(window_name)
    
    @staticmethod
    def create_save_observer(output_path: str, source_type: str, 
                           video_config: Optional[dict] = None) -> OutputObserver:
        """
        Crea observer de guardado según el tipo de fuente y ruta.
        
        Args:
            output_path: Ruta donde guardar
            source_type: Tipo de fuente (image, video, camera)
            video_config: Configuración para video (fourcc, fps)
        """
        path = Path(output_path)
        
        # Para imágenes estáticas, siempre guardar como imagen
        if source_type == "image":
            return SaveImageObserver(output_path)
        
        # Para streams, decidir por la extensión del output
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}:
            return SaveImageObserver(output_path)
        elif path.suffix.lower() in {".mp4", ".avi", ".mov", ".m4v", ".mkv"}:
            config = video_config or {}
            return SaveVideoObserver(
                output_path,
                fourcc=config.get('fourcc', 'mp4v'),
                fps=config.get('fps', 25.0)
            )
        else:
            # Default para streams: MP4
            output_path_with_ext = str(path.with_suffix('.mp4'))
            config = video_config or {}
            return SaveVideoObserver(
                output_path_with_ext,
                fourcc=config.get('fourcc', 'mp4v'),
                fps=config.get('fps', 25.0)
            )
    
    @staticmethod
    def create_mask_observer(mask_path: str) -> SaveMaskObserver:
        """Crea observer para guardar máscara."""
        return SaveMaskObserver(mask_path)