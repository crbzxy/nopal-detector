"""
Servicio de detección por segmentación de color HSV.
Especializado para detectar objetos planos de colores brillantes como nopales de colores.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from ..utils.logging import setup_logger

if TYPE_CHECKING:
    import cv2 as _cv2_type
    import numpy as _np_type


# Tipos de ayuda
BGR = Tuple[int, int, int]
HSVRange = Tuple[Tuple[int, int, int], Tuple[int, int, int]]  # (lower), (upper)


@dataclass
class ColorDetectionResult:
    """Resultado de detección por color."""
    frame_with_overlay: Any  # Frame procesado
    mask: Optional[Any]      # Máscara binaria global
    detections: List[Tuple[str, Any]]  # Lista de (color_name, contorno)
    total_detections: int
    colors_found: List[str]


@dataclass
class ColorDetectionConfig:
    """Configuración para detección por color."""
    # Rangos HSV por color (H=[0..179], S=[0..255], V=[0..255] en OpenCV)
    hsv_ranges: Dict[str, HSVRange]
    min_area: int = 800            # Área mínima del contorno
    max_area: int = 10_000_000     # Área máxima del contorno  
    aspect_min: float = 0.5        # Relación ancho/alto mínima
    aspect_max: float = 2.2        # Relación ancho/alto máxima
    solidity_min: float = 0.85     # Solidez mínima (área/área_convex_hull)
    blur_kernel_size: int = 3      # Tamaño del kernel para suavizado
    morph_kernel_size: int = 5     # Kernel para operaciones morfológicas
    draw_border: BGR = (0, 0, 0)   # Color del borde
    draw_fill: BGR = (0, 255, 0)   # Color de relleno
    fill_alpha: float = 0.35       # Transparencia del relleno
    border_thickness: int = 0      # Grosor del borde (0 = automático)
    draw_bbox: bool = False        # Dibujar bounding box
    draw_labels: bool = True       # Dibujar etiquetas de color


# Rangos HSV por defecto para colores típicos de nopales
DEFAULT_COLOR_RANGES: Dict[str, HSVRange] = {
    "verde_lima":  ((38,  80,  80), (75, 255, 255)),  # Verde limón brillante
    "verde":       ((30,  60,  60), (85, 255, 255)),  # Verde estándar
    "amarillo":    ((20, 120, 120), (35, 255, 255)),  # Amarillo
    "magenta":     ((140, 80,  80), (175, 255, 255)), # Magenta/rosa
    "azul":        ((95,  80,  80), (130, 255, 255)), # Azul
    "naranja":     ((5,  120, 120), (20, 255, 255)),  # Naranja
    "cian":        ((80,  80,  80), (100, 255, 255)), # Cian
}


class ColorDetectionService:
    """Servicio para detección de objetos por segmentación de color."""
    
    def __init__(self, config: ColorDetectionConfig):
        self.config = config
        self.logger = setup_logger(__name__)
    
    def detect_in_frame(self, frame: Any) -> ColorDetectionResult:
        """
        Detecta objetos de colores en un frame usando segmentación HSV.
        
        Args:
            frame: Frame de entrada en formato BGR
            
        Returns:
            ColorDetectionResult con los resultados
        """
        import cv2 as _cv2
        import numpy as _np
        
        # Crear copia del frame para dibujar
        output_frame = frame.copy()
        mask_global = _np.zeros(frame.shape[:2], dtype=_np.uint8)
        all_detections: List[Tuple[str, Any]] = []
        colors_found: List[str] = []
        
        # Convertir a HSV
        hsv = _cv2.cvtColor(frame, _cv2.COLOR_BGR2HSV)
        
        # Aplicar suavizado si está configurado
        if self.config.blur_kernel_size > 1:
            ksize = self.config.blur_kernel_size | 1  # Asegurar que sea impar
            hsv = _cv2.GaussianBlur(hsv, (ksize, ksize), 0)
        
        # Procesar cada color
        for color_name, (lower, upper) in self.config.hsv_ranges.items():
            detections = self._detect_color(
                hsv, output_frame, mask_global, 
                color_name, lower, upper
            )
            
            if detections:
                all_detections.extend(detections)
                colors_found.append(color_name)
                self.logger.debug(f"Detectado color '{color_name}': {len(detections)} objetos")
        
        # Si no se detectó nada, mask_global será None
        final_mask = mask_global if mask_global.any() else None
        
        # Log del resultado
        total = len(all_detections)
        if total > 0:
            self.logger.info(f"Detección por color: {total} objetos encontrados en colores: {colors_found}")
        else:
            self.logger.info("Detección por color: No se encontraron objetos")
        
        return ColorDetectionResult(
            frame_with_overlay=output_frame,
            mask=final_mask,
            detections=all_detections,
            total_detections=total,
            colors_found=colors_found
        )
    
    def _detect_color(self, hsv: Any, output_frame: Any, mask_global: Any, 
                     color_name: str, lower: Tuple[int, int, int], 
                     upper: Tuple[int, int, int]) -> List[Tuple[str, Any]]:
        """Detecta objetos de un color específico."""
        import cv2 as _cv2
        import numpy as _np
        
        detections: List[Tuple[str, Any]] = []
        
        # Crear máscara para este color
        lower_np = _np.array(lower, dtype=_np.uint8)
        upper_np = _np.array(upper, dtype=_np.uint8)
        color_mask = _cv2.inRange(hsv, lower_np, upper_np)
        
        # Aplicar operaciones morfológicas para limpiar la máscara
        if self.config.morph_kernel_size > 0:
            kernel = _np.ones((self.config.morph_kernel_size, self.config.morph_kernel_size), _np.uint8)
            # Cerrar huecos
            color_mask = _cv2.morphologyEx(color_mask, _cv2.MORPH_CLOSE, kernel, iterations=2)
            # Eliminar ruido
            color_mask = _cv2.morphologyEx(color_mask, _cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Encontrar contornos
        contours, _ = _cv2.findContours(color_mask, _cv2.RETR_EXTERNAL, _cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Filtrar por área
            area = _cv2.contourArea(contour)
            if area < self.config.min_area or area > self.config.max_area:
                continue
            
            # Filtrar por relación de aspecto
            x, y, w, h = _cv2.boundingRect(contour)
            aspect_ratio = w / max(1, h)
            if not (self.config.aspect_min <= aspect_ratio <= self.config.aspect_max):
                continue
            
            # Filtrar por solidez (compacidad)
            hull = _cv2.convexHull(contour)
            hull_area = _cv2.contourArea(hull)
            solidity = area / max(1.0, hull_area)
            if solidity < self.config.solidity_min:
                continue
            
            # Suavizar contorno
            epsilon = 0.01 * _cv2.arcLength(contour, True)
            smooth_contour = _cv2.approxPolyDP(contour, epsilon, True)
            
            # Dibujar en el frame de salida
            self._draw_detection(output_frame, smooth_contour, color_name, x, y, w, h)
            
            # Añadir a la máscara global
            _cv2.drawContours(mask_global, [smooth_contour], -1, 255, thickness=_cv2.FILLED)
            
            # Guardar detección
            detections.append((color_name, smooth_contour))
        
        return detections
    
    def _draw_detection(self, output_frame: Any, contour: Any, color_name: str, 
                       x: int, y: int, w: int, h: int) -> None:
        """Dibuja una detección en el frame de salida."""
        import cv2 as _cv2
        
        # Dibujar relleno semitransparente
        overlay = output_frame.copy()
        _cv2.fillPoly(overlay, [contour], self.config.draw_fill)
        _cv2.addWeighted(
            overlay, self.config.fill_alpha,
            output_frame, 1.0 - self.config.fill_alpha,
            0, output_frame
        )
        
        # Calcular grosor del borde
        thickness = self.config.border_thickness
        if thickness == 0:  # Automático
            h_frame, w_frame = output_frame.shape[:2]
            thickness = max(2, int(0.003 * max(h_frame, w_frame)))
        
        # Dibujar borde del contorno
        _cv2.polylines(
            output_frame, [contour], True, 
            self.config.draw_border, thickness, _cv2.LINE_AA
        )
        
        # Dibujar bounding box si está habilitado
        if self.config.draw_bbox:
            _cv2.rectangle(
                output_frame, (x, y), (x + w, y + h), 
                self.config.draw_border, thickness, _cv2.LINE_AA
            )
        
        # Dibujar etiqueta con el nombre del color
        if self.config.draw_labels:
            label_y = max(20, y - 8)
            _cv2.putText(
                output_frame, color_name.upper(), (x, label_y),
                _cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                self.config.draw_border, 2
            )
    
    def get_detection_stats(self) -> dict:
        """Obtiene estadísticas de configuración."""
        return {
            'colors_configured': list(self.config.hsv_ranges.keys()),
            'min_area': self.config.min_area,
            'max_area': self.config.max_area,
            'aspect_range': (self.config.aspect_min, self.config.aspect_max),
            'solidity_min': self.config.solidity_min,
        }


def create_default_color_config() -> ColorDetectionConfig:
    """Crea una configuración por defecto para detección de color."""
    return ColorDetectionConfig(
        hsv_ranges=DEFAULT_COLOR_RANGES,
        min_area=800,
        max_area=1_000_000,
        aspect_min=0.5,
        aspect_max=2.2,
        solidity_min=0.85,
        blur_kernel_size=3,
        morph_kernel_size=5,
        draw_border=(0, 0, 0),
        draw_fill=(0, 255, 0),
        fill_alpha=0.35,
        border_thickness=0,
        draw_bbox=False,
        draw_labels=True
    )