"""
Utilidades para manejo y conversión de colores.
"""

from typing import Tuple


def rgb_to_bgr(rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Convierte color RGB a BGR (formato OpenCV)."""
    r, g, b = rgb
    return (b, g, r)


def parse_rgb_string(rgb_text: str) -> Tuple[int, int, int]:
    """
    Convierte string 'R,G,B' a tupla RGB.
    
    Args:
        rgb_text: String en formato "R,G,B" (ej. "0,255,0")
        
    Returns:
        Tupla (R, G, B) con valores 0-255
        
    Raises:
        ValueError: Si el formato es inválido o valores fuera de rango
    """
    parts = [p.strip() for p in rgb_text.split(",")]
    if len(parts) != 3:
        raise ValueError("Color inválido. Usa formato R,G,B (ej. 0,255,0).")
    
    try:
        r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        raise ValueError("Los componentes de color deben ser números enteros.")
    
    for component, name in [(r, 'R'), (g, 'G'), (b, 'B')]:
        if component < 0 or component > 255:
            raise ValueError(f"Componente {name} debe estar entre 0 y 255, recibido: {component}")
    
    return (r, g, b)


def parse_rgb_to_bgr(rgb_text: str) -> Tuple[int, int, int]:
    """Convierte string 'R,G,B' directamente a tupla BGR."""
    rgb = parse_rgb_string(rgb_text)
    return rgb_to_bgr(rgb)


def bgr_to_hsv_range(bgr_color: Tuple[int, int, int], 
                     h_tolerance: int = 10,
                     s_min: int = 50, 
                     v_min: int = 50) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """
    Convierte un color BGR a rango HSV para detección.
    
    Args:
        bgr_color: Color en formato BGR (0-255)
        h_tolerance: Tolerancia en Hue (±)
        s_min: Saturación mínima
        v_min: Valor (brillo) mínimo
        
    Returns:
        Tupla (lower_hsv, upper_hsv) para cv2.inRange
    """
    import cv2
    import numpy as np
    
    # Convertir BGR a HSV
    bgr_array = np.uint8([[bgr_color]])
    hsv_array = cv2.cvtColor(bgr_array, cv2.COLOR_BGR2HSV)
    h, s, v = hsv_array[0][0]
    
    # Crear rango con tolerancias
    h_lower = max(0, h - h_tolerance)
    h_upper = min(179, h + h_tolerance)  # H va de 0-179 en OpenCV
    s_lower = max(s_min, s - 50)
    s_upper = 255
    v_lower = max(v_min, v - 50)
    v_upper = 255
    
    return ((h_lower, s_lower, v_lower), (h_upper, s_upper, v_upper))


def validate_hsv_range(hsv_range: Tuple[Tuple[int, int, int], Tuple[int, int, int]]) -> bool:
    """
    Valida que un rango HSV sea correcto.
    
    Args:
        hsv_range: Tupla ((h_min, s_min, v_min), (h_max, s_max, v_max))
        
    Returns:
        True si el rango es válido
    """
    (h_min, s_min, v_min), (h_max, s_max, v_max) = hsv_range
    
    # Verificar rangos OpenCV: H=[0,179], S=[0,255], V=[0,255]
    if not (0 <= h_min <= 179 and 0 <= h_max <= 179):
        return False
    if not (0 <= s_min <= 255 and 0 <= s_max <= 255):
        return False
    if not (0 <= v_min <= 255 and 0 <= v_max <= 255):
        return False
    
    # Verificar que los máximos sean mayores o iguales que los mínimos
    if s_min > s_max or v_min > v_max:
        return False
    
    # Para Hue, puede haber wrap-around (ej. rojo: 170-10)
    # Por simplicidad, asumimos rangos normales aquí
    return True


def color_name_to_bgr(color_name: str) -> Tuple[int, int, int]:
    """
    Convierte nombres de colores comunes a BGR.
    
    Args:
        color_name: Nombre del color en español o inglés
        
    Returns:
        Color en formato BGR
        
    Raises:
        ValueError: Si el color no está definido
    """
    color_map = {
        # Español
        'rojo': (0, 0, 255),
        'verde': (0, 255, 0),
        'azul': (255, 0, 0),
        'amarillo': (0, 255, 255),
        'magenta': (255, 0, 255),
        'cian': (255, 255, 0),
        'blanco': (255, 255, 255),
        'negro': (0, 0, 0),
        'naranja': (0, 165, 255),
        'rosa': (203, 192, 255),
        'morado': (128, 0, 128),
        'lima': (0, 255, 191),
        # Inglés
        'red': (0, 0, 255),
        'green': (0, 255, 0),
        'blue': (255, 0, 0),
        'yellow': (0, 255, 255),
        'magenta': (255, 0, 255),
        'cyan': (255, 255, 0),
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'orange': (0, 165, 255),
        'pink': (203, 192, 255),
        'purple': (128, 0, 128),
        'lime': (0, 255, 191),
    }
    
    color_key = color_name.lower().strip()
    if color_key not in color_map:
        available = ', '.join(sorted(color_map.keys()))
        raise ValueError(f"Color '{color_name}' no reconocido. Disponibles: {available}")
    
    return color_map[color_key]
