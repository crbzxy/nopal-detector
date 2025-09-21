"""
Sistema de configuración centralizada para el detector de nopal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple, List, Optional, Dict


@dataclass
class EnvironmentConfig:
    """Configuración del entorno de ejecución."""
    venv_dir: Path = field(default_factory=lambda: Path(".venv"))
    requirements: List[str] = field(
        default_factory=lambda: ["opencv-python>=4.9.0", "numpy>=1.26"]
    )
    python_candidates: List[str] = field(
        default_factory=lambda: ["python3", "py", "python"]
    )


@dataclass
class ORBConfig:
    """Configuración para el detector ORB."""
    n_features: int = 2000
    scale_factor: float = 1.2
    n_levels: int = 8
    min_matches: int = 18
    ratio_threshold: float = 0.75
    ransac_threshold: float = 5.0


@dataclass
class DrawingConfig:
    """Configuración para el dibujo de resultados."""
    border_color: Tuple[int, int, int] = (0, 255, 0)  # RGB
    fill_color: Tuple[int, int, int] = (0, 255, 0)    # RGB
    fill_alpha: float = 0.25
    border_thickness: int = 3
    font_scale: float = 0.8
    font_thickness: int = 2


@dataclass
class VideoConfig:
    """Configuración para procesamiento de video."""
    fourcc: str = "mp4v"
    default_fps: int = 25
    default_width: int = 1280
    default_height: int = 720


@dataclass
class ColorDetectionConfig:
    """Configuración para detección por color HSV."""
    # Rangos HSV por defecto para colores de nopales
    hsv_ranges: Dict[str, Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = field(
        default_factory=lambda: {
            "verde_lima": ((38, 80, 80), (75, 255, 255)),
            "verde": ((30, 60, 60), (85, 255, 255)),
            "amarillo": ((20, 120, 120), (35, 255, 255)),
            "magenta": ((140, 80, 80), (175, 255, 255)),
            "azul": ((95, 80, 80), (130, 255, 255)),
            "naranja": ((5, 120, 120), (20, 255, 255)),
            "cian": ((80, 80, 80), (100, 255, 255)),
        }
    )
    min_area: int = 800
    max_area: int = 1_000_000
    aspect_min: float = 0.5
    aspect_max: float = 2.2
    solidity_min: float = 0.85
    blur_kernel_size: int = 3
    morph_kernel_size: int = 5
    draw_bbox: bool = False
    draw_labels: bool = True


@dataclass
class ApplicationConfig:
    """Configuración principal de la aplicación."""
    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    orb: ORBConfig = field(default_factory=ORBConfig)
    drawing: DrawingConfig = field(default_factory=DrawingConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    color_detection: ColorDetectionConfig = field(default_factory=ColorDetectionConfig)
    
    # Rutas por defecto
    default_ref_path: str = "data/ref/nopal_ref.jpg"
    default_output_dir: Path = field(default_factory=lambda: Path("output"))
    
    @classmethod
    def create_default(cls) -> ApplicationConfig:
        """Crea una configuración por defecto."""
        return cls()
    
    @classmethod  
    def from_dict(cls, config_dict: dict) -> ApplicationConfig:
        """Crea configuración desde diccionario (para futuro soporte de archivos config)."""
        # Implementación básica - se puede extender para cargar desde YAML/JSON
        return cls()
    
    def ensure_directories(self) -> None:
        """Asegura que los directorios necesarios existan."""
        directories = [
            "data/ref",
            "examples", 
            str(self.default_output_dir),
            "temp"
        ]
        for dir_path in directories:
            Path(dir_path).mkdir(parents=True, exist_ok=True)