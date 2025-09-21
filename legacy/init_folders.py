#!/usr/bin/env python3
"""
init_folders.py
Crea la estructura básica de carpetas para nopal-detector
y deja un README.txt en cada carpeta para explicar su uso.
"""

import os
from pathlib import Path

# Carpetas requeridas
folders = {
    "data/ref": "Coloca aquí la imagen de referencia del nopal (ej: nopal_ref.jpg)",
    "examples": "Guarda aquí imágenes o videos de prueba para experimentar con el detector",
    "output": "Aquí se guardarán las salidas generadas por el detector (imágenes/videos procesados)"
}

def main():
    base = Path(__file__).parent.resolve()
    print(f"[INFO] Inicializando estructura en {base}")
    
    for folder, desc in folders.items():
        fpath = base / folder
        fpath.mkdir(parents=True, exist_ok=True)
        
        # Agrega un README.txt dentro de cada carpeta
        readme_path = fpath / "README.txt"
        if not readme_path.exists():
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(desc + "\n")
        
        print(f"✅ {fpath} creado")

    print("\nEstructura lista. Ahora coloca tu referencia en: data/ref/nopal_ref.jpg")

if __name__ == "__main__":
    main()
