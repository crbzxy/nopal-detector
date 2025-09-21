#!/usr/bin/env python3
"""
Punto de entrada principal para el detector de nopal refactorizado.

Este archivo sirve como punto de entrada unificado que utiliza la nueva
arquitectura basada en componentes.

Uso:
    python main.py --source examples/example.png --reference data/ref/nopal_ref.jpg
    python main.py --source 0 --reference data/ref/nopal_ref.jpg --output output/webcam.mp4
    python main.py --help
"""

import sys
from pathlib import Path

# Añadir el directorio del paquete al path para imports relativos
sys.path.insert(0, str(Path(__file__).parent))

from nopal_detector.cli.main import main

if __name__ == "__main__":
    main()