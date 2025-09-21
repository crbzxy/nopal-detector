"""
CLI principal para el detector de nopal.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from ..config.settings import ApplicationConfig
from ..core.detector import NopalDetector
from ..services.environment import EnvironmentService
from ..utils.logging import setup_logger
from ..utils.colors import parse_rgb_string


def create_parser() -> argparse.ArgumentParser:
    """Crea y configura el parser de argumentos."""
    parser = argparse.ArgumentParser(
        prog="nopal-detector",
        description="Detector de nopal usando OpenCV y algoritmos ORB",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Argumentos principales
    parser.add_argument(
        "--source", "-s",
        default="0",
        help="Fuente de entrada: ruta a imagen/video o índice de cámara (ej. 0)"
    )
    
    parser.add_argument(
        "--reference", "--ref", "-r",
        default="data/ref/nopal_ref.jpg",
        help="Imagen de referencia del nopal"
    )
    
    parser.add_argument(
        "--output", "--save", "-o",
        default=None,
        help="Ruta para guardar resultado (PNG/JPG para imagen; MP4 para video/cámara)"
    )
    
    parser.add_argument(
        "--mask",
        default=None,
        help="Ruta para guardar máscara binaria (solo en modo imagen)"
    )
    
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="No mostrar ventana de visualización"
    )
    
    # Parámetro de detector principal
    parser.add_argument(
        "--detector", "-d",
        choices=["orb", "color", "auto"],
        default="auto",
        help="Método de detección: ORB (textura), COLOR (HSV), AUTO (ORB + color fallback)"
    )

    # Parámetros ORB
    orb_group = parser.add_argument_group("Parámetros ORB")
    orb_group.add_argument(
        "--min-matches",
        type=int,
        default=18,
        help="Mínimo de coincidencias buenas para aceptar detección"
    )
    
    orb_group.add_argument(
        "--ratio",
        type=float,
        default=0.75,
        help="Ratio test de Lowe para filtrar matches"
    )
    
    orb_group.add_argument(
        "--orb-features",
        type=int,
        default=2000,
        help="Número máximo de características ORB a extraer"
    )
    
    # Parámetros de visualización
    visual_group = parser.add_argument_group("Parámetros de visualización")
    visual_group.add_argument(
        "--border-color",
        default="0,255,0",
        help="Color del borde en RGB (ej. 0,255,0 para verde)"
    )
    
    visual_group.add_argument(
        "--fill-color",
        default="0,255,0",
        help="Color de relleno en RGB (ej. 0,255,0 para verde)"
    )
    
    visual_group.add_argument(
        "--fill-alpha",
        type=float,
        default=0.25,
        help="Opacidad del relleno [0-1]"
    )
    
    # Argumentos internos (ocultos)
    parser.add_argument(
        "--stage",
        choices=["bootstrap", "run"],
        default="bootstrap",
        help=argparse.SUPPRESS
    )
    
    # Parámetros de detección por color
    color_group = parser.add_argument_group("Parámetros de detección por color")
    color_group.add_argument(
        "--min-area",
        type=int,
        default=800,
        help="Área mínima de contornos para detección por color"
    )
    
    color_group.add_argument(
        "--max-area",
        type=int,
        default=1000000,
        help="Área máxima de contornos para detección por color"
    )
    
    color_group.add_argument(
        "--draw-bbox",
        action="store_true",
        help="Dibujar bounding boxes en detección por color"
    )
    
    color_group.add_argument(
        "--solidity-min",
        type=float,
        default=0.85,
        help="Solidez mínima para filtrar contornos (0-1)"
    )

    # Argumentos de desarrollo/debug
    debug_group = parser.add_argument_group("Debug")
    debug_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar información detallada"
    )
    
    return parser


def validate_args(args: argparse.Namespace) -> None:
    """
    Valida los argumentos de línea de comandos.
    
    Raises:
        argparse.ArgumentError: Si algún argumento es inválido
    """
    logger = setup_logger(__name__)
    
    # Validar colores
    try:
        parse_rgb_string(args.border_color)
    except ValueError as e:
        logger.error(f"Color de borde inválido: {e}")
        sys.exit(1)
    
    try:
        parse_rgb_string(args.fill_color)
    except ValueError as e:
        logger.error(f"Color de relleno inválido: {e}")
        sys.exit(1)
    
    # Validar alpha
    if not 0 <= args.fill_alpha <= 1:
        logger.error(f"fill-alpha debe estar entre 0 y 1, recibido: {args.fill_alpha}")
        sys.exit(1)
    
    # Validar ratio
    if not 0 < args.ratio < 1:
        logger.error(f"ratio debe estar entre 0 y 1, recibido: {args.ratio}")
        sys.exit(1)
    
    # Validar min_matches
    if args.min_matches < 4:
        logger.error(f"min-matches debe ser al menos 4, recibido: {args.min_matches}")
        sys.exit(1)
    
    # Validar orb_features
    if args.orb_features < 100:
        logger.error(f"orb-features debe ser al menos 100, recibido: {args.orb_features}")
        sys.exit(1)
    
    # Validar parámetros de color
    if args.min_area < 10:
        logger.error(f"min-area debe ser al menos 10, recibido: {args.min_area}")
        sys.exit(1)
    
    if args.max_area < args.min_area:
        logger.error(f"max-area ({args.max_area}) debe ser mayor que min-area ({args.min_area})")
        sys.exit(1)
    
    if not 0 <= args.solidity_min <= 1:
        logger.error(f"solidity-min debe estar entre 0 y 1, recibido: {args.solidity_min}")
        sys.exit(1)


def bootstrap_stage(args: argparse.Namespace) -> None:
    """
    Etapa de bootstrap: configura entorno y relanza en venv.
    
    Args:
        args: Argumentos parseados
    """
    logger = setup_logger(__name__)
    
    try:
        # Crear configuración y asegurar directorios
        config = ApplicationConfig.create_default()
        config.ensure_directories()
        
        # Configurar servicio de entorno
        env_service = EnvironmentService(config.environment)
        
        # Verificar dependencias del sistema
        env_service.check_system_dependencies(args.output)
        
        # Bootstrap del entorno
        env_service.bootstrap_environment()
        
        # Relanzar en venv con stage="run"
        script_path = str(Path(__file__).parent.parent.parent / "main.py")
        relaunch_args = sys.argv[1:] + ["--stage", "run"]
        env_service.relaunch_in_venv(script_path, relaunch_args)
        
    except Exception as e:
        logger.error(f"Error en bootstrap: {e}")
        sys.exit(1)


def run_stage(args: argparse.Namespace) -> None:
    """
    Etapa de ejecución: ejecuta el detector.
    
    Args:
        args: Argumentos parseados
    """
    logger = setup_logger(__name__)
    
    # Verificar imports de OpenCV
    try:
        import cv2  # noqa: F401
        import numpy  # noqa: F401
    except ModuleNotFoundError as e:
        logger.error(f"Dependencia faltante en venv: {e}")
        print("\\nSolución: reinstala dependencias ejecutando:")
        print("  .venv/Scripts/python -m pip install --force-reinstall opencv-python numpy")
        sys.exit(1)
    
    # Validar argumentos
    validate_args(args)
    
    # Crear configuración
    config = ApplicationConfig.create_default()
    config.ensure_directories()
    
    # Aplicar parámetros desde CLI a la configuración
    custom_orb_params = {
        'min_matches': args.min_matches,
        'ratio_threshold': args.ratio,
        'n_features': args.orb_features
    }
    
    custom_drawing_params = {
        'border_color': parse_rgb_string(args.border_color),
        'fill_color': parse_rgb_string(args.fill_color),
        'fill_alpha': args.fill_alpha
    }
    
    custom_color_params = {
        'min_area': args.min_area,
        'max_area': args.max_area,
        'draw_bbox': args.draw_bbox,
        'solidity_min': args.solidity_min
    }
    
    # Verificar imagen de referencia
    if not Path(args.reference).exists():
        logger.error(f"Imagen de referencia no encontrada: {args.reference}")
        print("Solución: proporciona una imagen válida con --reference path/a/tu_nopal.jpg")
        sys.exit(1)
    
    # Crear detector y ejecutar
    detector = NopalDetector(config)
    
    try:
        success = detector.detect_from_source(
            source_path=args.source,
            reference_path=args.reference,
            output_path=args.output,
            mask_path=args.mask,
            show_display=not args.no_display,
            detector_mode=args.detector,
            custom_orb_params=custom_orb_params,
            custom_drawing_params=custom_drawing_params,
            custom_color_params=custom_color_params
        )
        
        if success:
            logger.info("Detección completada exitosamente")
            
            # Mostrar estadísticas si está en modo verbose
            if args.verbose:
                stats = detector.get_detection_stats()
                logger.info(f"Estadísticas: {stats}")
        else:
            logger.error("La detección falló")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Detección interrumpida por el usuario")
    except Exception as e:
        logger.error(f"Error durante la detección: {e}")
        
        # Sugerencias específicas según el tipo de error
        if "No pude abrir" in str(e):
            print("\\nSugerencias:")
            print(" - Si es cámara: verifica permisos y que no esté en uso")
            print(" - Si es archivo: verifica que exista y sea legible")
            print(" - Si es video: instala ffmpeg y prueba otro formato")
        elif "Muy pocos puntos clave" in str(e):
            print("\\nSugerencia:")
            print(" - Usa una imagen de referencia con más textura/contraste")
            print(" - O recorta al área más distintiva del nopal")
        
        sys.exit(1)


def main(argv: Optional[List[str]] = None) -> None:
    """
    Función principal del CLI.
    
    Args:
        argv: Lista de argumentos (por defecto usa sys.argv)
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Configurar nivel de logging
    if hasattr(args, 'verbose') and args.verbose:
        import logging
        setup_logger(__name__, logging.DEBUG)
    
    # Ejecutar según la etapa
    if args.stage == "bootstrap":
        bootstrap_stage(args)
    elif args.stage == "run":
        run_stage(args)
    else:
        parser.error(f"Etapa desconocida: {args.stage}")


if __name__ == "__main__":
    main()