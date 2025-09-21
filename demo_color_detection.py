#!/usr/bin/env python3
"""
Demostración de las capacidades de detección del nopal detector v2.0
con detección por color y modo AUTO.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd_list):
    """Ejecuta un comando y muestra el resultado."""
    print(f"🚀 Ejecutando: {' '.join(cmd_list)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd_list, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(e.stderr if e.stderr else "")
        return False

def main():
    """Función principal de demostración."""
    print("🎯 Nopal Detector v2.0 - Demostración de Detección por Color")
    print("=" * 70)
    print()
    
    # Verificar que existan los archivos necesarios
    example_image = Path("examples/example.png")
    if not example_image.exists():
        print(f"❌ No se encontró la imagen de ejemplo: {example_image}")
        return False
    
    # Crear directorio output si no existe
    Path("output").mkdir(exist_ok=True)
    
    demos = [
        {
            "name": "1. Detección Solo por ORB (modo tradicional)",
            "cmd": [
                "python", "main.py",
                "--detector", "orb",
                "--source", "examples/example.png",
                "--output", "output/demo_orb_only.png",
                "--min-matches", "5",
                "--ratio", "0.9",
                "--no-display", "--verbose"
            ],
            "description": "Usa solo algoritmo ORB (detección por textura/keypoints)"
        },
        {
            "name": "2. Detección Solo por Color",
            "cmd": [
                "python", "main.py", 
                "--detector", "color",
                "--source", "examples/example.png",
                "--output", "output/demo_color_only.png",
                "--mask", "output/demo_color_mask.png",
                "--min-area", "500",
                "--draw-bbox",
                "--no-display", "--verbose"
            ],
            "description": "Usa solo segmentación HSV (ideal para objetos planos de colores)"
        },
        {
            "name": "3. Detección Modo AUTO (ORB + Color fallback)",
            "cmd": [
                "python", "main.py",
                "--detector", "auto", 
                "--source", "examples/example.png",
                "--output", "output/demo_auto_mode.png",
                "--mask", "output/demo_auto_mask.png",
                "--min-matches", "15",  # ORB más estricto
                "--min-area", "600",
                "--draw-bbox",
                "--no-display", "--verbose"
            ],
            "description": "Intenta ORB primero, si falla usa Color automáticamente"
        }
    ]
    
    successful_demos = 0
    
    for demo in demos:
        print(f"\n{demo['name']}")
        print(f"📝 {demo['description']}")
        print()
        
        success = run_command(demo['cmd'])
        if success:
            successful_demos += 1
            print("✅ Demo completado exitosamente")
        else:
            print("❌ Demo falló")
        
        print("\n" + "="*70 + "\n")
    
    # Resumen final
    print(f"📊 Resumen: {successful_demos}/{len(demos)} demos exitosos")
    print("\n📁 Archivos generados en output/:")
    
    output_files = list(Path("output").glob("demo_*.png"))
    for file in sorted(output_files):
        print(f"   • {file.name}")
    
    print(f"\n🎨 Colores detectables configurados:")
    colors = ["verde_lima", "verde", "amarillo", "magenta", "azul", "naranja", "cian"]
    for color in colors:
        print(f"   • {color}")
    
    print(f"\n🚀 Para usar en tus propias imágenes:")
    print(f"   python main.py --detector color --source tu_imagen.png --output resultado.png")
    print(f"   python main.py --detector auto --source tu_imagen.png --output resultado.png")
    
    return successful_demos == len(demos)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)