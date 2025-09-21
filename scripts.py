#!/usr/bin/env python3
"""
Scripts de utilidad para el proyecto nopal-detector.

Uso:
    python scripts.py clean       # Limpiar archivos temporales
    python scripts.py test        # Ejecutar tests
    python scripts.py format      # Formatear código
    python scripts.py install     # Instalar en modo desarrollo
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def clean():
    """Limpia archivos temporales y caché."""
    print("🧹 Limpiando archivos temporales...")
    
    patterns_to_remove = [
        "__pycache__",
        "*.pyc",
        "*.pyo", 
        "*.pyd",
        ".pytest_cache",
        ".mypy_cache",
        "*.egg-info",
        "build",
        "dist",
        ".coverage"
    ]
    
    removed_count = 0
    
    for pattern in patterns_to_remove:
        if "*" in pattern:
            # Para archivos con wildcard
            for path in Path(".").rglob(pattern):
                # Evitar tocar .venv
                if ".venv" in str(path):
                    continue
                if path.is_file():
                    path.unlink()
                    removed_count += 1
                    print(f"  ✓ Eliminado: {path}")
        else:
            # Para directorios
            for path in Path(".").rglob(pattern):
                # Evitar tocar .venv
                if ".venv" in str(path):
                    continue
                if path.is_dir():
                    shutil.rmtree(path)
                    removed_count += 1
                    print(f"  ✓ Eliminado directorio: {path}")
    
    # Limpiar archivos de output temporales
    output_dir = Path("output")
    if output_dir.exists():
        for temp_file in output_dir.glob("test_*"):
            temp_file.unlink()
            removed_count += 1
            print(f"  ✓ Eliminado: {temp_file}")
    
    print(f"✅ Limpieza completada. {removed_count} elementos eliminados.")


def test():
    """Ejecuta los tests del proyecto."""
    print("🧪 Ejecutando tests...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "nopal_detector/tests/", "-v"],
            check=True
        )
        print("✅ Tests completados exitosamente.")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests fallaron con código {e.returncode}")
        return False
    except FileNotFoundError:
        print("⚠️ pytest no está instalado. Instala con: pip install pytest")
        return False


def format_code():
    """Formatea el código usando black e isort."""
    print("🎨 Formateando código...")
    
    formatters = [
        (["black", "nopal_detector/", "main.py", "setup.py"], "black"),
        (["isort", "nopal_detector/", "main.py", "setup.py"], "isort")
    ]
    
    all_success = True
    
    for cmd, name in formatters:
        try:
            subprocess.run(cmd, check=True)
            print(f"  ✓ {name} ejecutado correctamente")
        except subprocess.CalledProcessError:
            print(f"  ❌ Error ejecutando {name}")
            all_success = False
        except FileNotFoundError:
            print(f"  ⚠️ {name} no está instalado")
            all_success = False
    
    if all_success:
        print("✅ Formateo completado.")
    else:
        print("⚠️ Algunos formatters fallaron. Instala con: pip install black isort")


def install_dev():
    """Instala el proyecto en modo desarrollo."""
    print("📦 Instalando proyecto en modo desarrollo...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".[dev]"], check=True)
        print("✅ Instalación completada.")
    except subprocess.CalledProcessError:
        print("❌ Error en la instalación.")


def lint():
    """Ejecuta linting del código."""
    print("🔍 Ejecutando linting...")
    
    linters = [
        (["flake8", "nopal_detector/"], "flake8"),
        (["mypy", "nopal_detector/"], "mypy")
    ]
    
    for cmd, name in linters:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✓ {name}: Sin problemas encontrados")
            else:
                print(f"  ⚠️ {name}: Problemas encontrados")
                print(result.stdout)
        except FileNotFoundError:
            print(f"  ⚠️ {name} no está instalado")


def demo():
    """Ejecuta una demostración del detector."""
    print("🎯 Ejecutando demostración...")
    
    cmd = [
        sys.executable, "main.py",
        "--source", "examples/example.png",
        "--output", "output/demo_result.png",
        "--no-display",
        "--verbose"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Demostración completada. Ver output/demo_result.png")
    except subprocess.CalledProcessError:
        print("❌ Error en la demostración.")


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(description="Scripts de utilidad para nopal-detector")
    parser.add_argument(
        "command",
        choices=["clean", "test", "format", "install", "lint", "demo"],
        help="Comando a ejecutar"
    )
    
    args = parser.parse_args()
    
    print(f"🚀 Nopal Detector - {args.command.upper()}")
    print("-" * 40)
    
    if args.command == "clean":
        clean()
    elif args.command == "test":
        test()
    elif args.command == "format":
        format_code()
    elif args.command == "install":
        install_dev()
    elif args.command == "lint":
        lint()
    elif args.command == "demo":
        demo()


if __name__ == "__main__":
    main()