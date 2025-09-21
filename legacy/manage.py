#!/usr/bin/env python3
"""
🌵 Nopal Detector - Gestor Principal
Gestión completa del proyecto usando solo Python
"""

import os
import sys
import subprocess
import platform
import shutil
import argparse
from pathlib import Path

# Configuración del proyecto
PROJECT_NAME = "nopal-detector"
VENV_DIR = Path(".venv")
REQUIREMENTS = ["opencv-python>=4.9.0", "numpy>=1.26"]

# Detección del sistema operativo
IS_WIN = platform.system().lower().startswith("win")
IS_MAC = platform.system().lower().startswith("darwin")
IS_LINUX = platform.system().lower().startswith("linux")

# Colores para terminal
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

def print_colored(message, color=Colors.NC):
    """Imprime mensaje con color"""
    print(f"{color}{message}{Colors.NC}")

def print_header(title):
    """Imprime encabezado bonito"""
    print("\n" + "="*50)
    print_colored(f"🌵 {title}", Colors.BLUE)
    print("="*50)

def run_command(cmd, shell=False, check=True, capture_output=False):
    """Ejecuta comando y maneja errores"""
    try:
        print_colored(f"$ {' '.join(cmd) if isinstance(cmd, list) else cmd}", Colors.CYAN)
        result = subprocess.run(
            cmd, 
            shell=shell, 
            check=check, 
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Error ejecutando comando: {e}", Colors.RED)
        if capture_output and e.stderr:
            print_colored(f"Error: {e.stderr}", Colors.RED)
        return None
    except FileNotFoundError:
        print_colored(f"❌ Comando no encontrado: {cmd}", Colors.RED)
        return None

def get_python_executable():
    """Obtiene el ejecutable de Python correcto"""
    candidates = ["python3", "python", "py"]
    
    for cmd in candidates:
        result = run_command([cmd, "--version"], capture_output=True, check=False)
        if result and result.returncode == 0:
            # Verificar que es Python 3
            version_output = result.stdout + result.stderr
            if "Python 3" in version_output:
                return cmd
    
    raise RuntimeError("❌ No se encontró Python 3. Instálalo desde:\n"
                      "  - Windows: https://python.org/downloads/\n"
                      "  - macOS: brew install python3\n"
                      "  - Linux: sudo apt install python3 python3-venv")

def get_venv_python():
    """Obtiene la ruta al ejecutable de Python en el venv"""
    if IS_WIN:
        return str(VENV_DIR / "Scripts" / "python.exe")
    else:
        return str(VENV_DIR / "bin" / "python")

def get_venv_pip():
    """Obtiene la ruta al pip en el venv"""
    python_exe = get_venv_python()
    return [python_exe, "-m", "pip"]

def venv_exists():
    """Verifica si existe el virtual environment"""
    python_exe = get_venv_python()
    return VENV_DIR.exists() and Path(python_exe).exists()

def ref_image_exists():
    """Verifica si existe la imagen de referencia"""
    return Path("data/ref/nopal_ref.jpg").exists()

def create_folders():
    """Crea la estructura de carpetas del proyecto"""
    print_header("Creando estructura de carpetas")
    
    folders = [
        "data/ref",
        "examples", 
        "output",
        "temp"
    ]
    
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
        print_colored(f"✅ Creada: {folder}/", Colors.GREEN)
    
    print_colored("✅ Estructura de carpetas completada", Colors.GREEN)

def setup_venv():
    """Configura el virtual environment"""
    print_header("Configurando entorno virtual")
    
    # Obtener Python executable
    try:
        python_cmd = get_python_executable()
        print_colored(f"✅ Python encontrado: {python_cmd}", Colors.GREEN)
    except RuntimeError as e:
        print_colored(str(e), Colors.RED)
        return False
    
    # Crear venv si no existe
    if not venv_exists():
        print_colored("📦 Creando entorno virtual...", Colors.YELLOW)
        result = run_command([python_cmd, "-m", "venv", str(VENV_DIR)])
        if not result:
            return False
    else:
        print_colored("✅ Entorno virtual ya existe", Colors.GREEN)
    
    # Verificar que el venv funciona
    venv_python = get_venv_python()
    result = run_command([venv_python, "--version"], capture_output=True)
    if not result:
        print_colored("❌ Error: El entorno virtual no funciona correctamente", Colors.RED)
        return False
    
    version = result.stdout.strip()
    print_colored(f"✅ Entorno virtual funcionando: {version}", Colors.GREEN)
    
    # Actualizar pip
    print_colored("📦 Actualizando pip y wheel...", Colors.YELLOW)
    pip_cmd = get_venv_pip()
    result = run_command(pip_cmd + ["install", "--upgrade", "pip", "wheel"])
    if not result:
        return False
    
    # Instalar dependencias
    print_colored("📦 Instalando dependencias...", Colors.YELLOW)
    
    # Verificar si existe requirements.txt
    if Path("requirements.txt").exists():
        result = run_command(pip_cmd + ["install", "-r", "requirements.txt"])
    else:
        result = run_command(pip_cmd + ["install"] + REQUIREMENTS)
    
    if not result:
        return False
    
    print_colored("✅ Dependencias instaladas correctamente", Colors.GREEN)
    return True

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    if not venv_exists():
        print_colored("❌ Entorno virtual no existe", Colors.RED)
        return False
    
    venv_python = get_venv_python()
    
    # Verificar OpenCV
    result = run_command([
        venv_python, "-c", 
        "import cv2; print('OpenCV', cv2.__version__)"
    ], capture_output=True, check=False)
    
    if result and result.returncode == 0:
        print_colored(f"✅ {result.stdout.strip()}", Colors.GREEN)
    else:
        print_colored("❌ OpenCV no instalado", Colors.RED)
        return False
    
    # Verificar NumPy
    result = run_command([
        venv_python, "-c", 
        "import numpy; print('NumPy', numpy.__version__)"
    ], capture_output=True, check=False)
    
    if result and result.returncode == 0:
        print_colored(f"✅ {result.stdout.strip()}", Colors.GREEN)
    else:
        print_colored("❌ NumPy no instalado", Colors.RED)
        return False
    
    return True

def show_status():
    """Muestra el estado completo del proyecto"""
    print_header("Estado del Proyecto")
    
    print_colored("🔍 Entorno Virtual:", Colors.BLUE)
    if venv_exists():
        print_colored("  ✅ .venv existe", Colors.GREEN)
        venv_python = get_venv_python()
        result = run_command([venv_python, "--version"], capture_output=True, check=False)
        if result and result.returncode == 0:
            print_colored(f"  ✅ {result.stdout.strip()}", Colors.GREEN)
        else:
            print_colored("  ❌ Python no ejecutable", Colors.RED)
    else:
        print_colored("  ❌ .venv no existe - ejecuta 'python manage.py setup'", Colors.RED)
    
    print_colored("\n📁 Estructura de carpetas:", Colors.BLUE)
    folders = ["data", "data/ref", "examples", "output"]
    for folder in folders:
        if Path(folder).exists():
            print_colored(f"  ✅ {folder}/", Colors.GREEN)
        else:
            print_colored(f"  ❌ {folder}/", Colors.RED)
    
    print_colored("\n🖼️ Imagen de referencia:", Colors.BLUE)
    if ref_image_exists():
        print_colored("  ✅ data/ref/nopal_ref.jpg existe", Colors.GREEN)
    else:
        print_colored("  ❌ data/ref/nopal_ref.jpg falta - coloca tu imagen", Colors.RED)
    
    print_colored("\n📦 Dependencias:", Colors.BLUE)
    if venv_exists():
        check_dependencies()
    else:
        print_colored("  ❌ Entorno virtual no configurado", Colors.RED)

def run_detector(source="0", save=None, **kwargs):
    """Ejecuta el detector de nopal"""
    print_header("Ejecutando Detector de Nopal")
    
    # Verificaciones previas
    if not venv_exists():
        print_colored("❌ Entorno virtual no existe. Ejecuta 'python manage.py setup'", Colors.RED)
        return False
    
    if not ref_image_exists():
        print_colored("❌ Imagen de referencia no encontrada", Colors.RED)
        print_colored("💡 Coloca tu imagen en: data/ref/nopal_ref.jpg", Colors.YELLOW)
        return False
    
    if not check_dependencies():
        print_colored("❌ Dependencias faltantes. Ejecuta 'python manage.py setup'", Colors.RED)
        return False
    
    # Construir comando
    venv_python = get_venv_python()
    cmd = [
        venv_python, "nopal_all_in_one.py",
        "--source", str(source),
        "--ref", "data/ref/nopal_ref.jpg"
    ]
    
    if save:
        cmd.extend(["--save", save])
    
    # Agregar parámetros adicionales
    for key, value in kwargs.items():
        if key in ["min_matches", "ratio"] and value is not None:
            cmd.extend([f"--{key}", str(value)])
    
    print_colored("🚀 Iniciando detección...", Colors.GREEN)
    print_colored("💡 Presiona 'q' para salir (si es cámara/video)", Colors.YELLOW)
    
    # Ejecutar detector
    result = run_command(cmd, check=False)
    return result is not None and result.returncode == 0

def clean_project(deep=False, preserve_outputs=False):
    """Limpia archivos temporales del proyecto con opciones avanzadas"""
    if deep:
        print_header("Limpieza PROFUNDA del proyecto")
        print_colored("⚠️ ATENCIÓN: Limpieza profunda eliminará TODOS los archivos temporales", Colors.YELLOW)
    else:
        print_header("Limpieza estándar del proyecto")
    
    # Items básicos siempre se limpian
    basic_items = [
        ".venv",
        "__pycache__",
        "temp",
        ".pytest_cache",
        ".mypy_cache", 
        ".ruff_cache",
        "*.pyc",
        "*.pyo",
        "*.pyd"
    ]
    
    # Items adicionales para limpieza profunda
    deep_items = [
        "build",
        "dist",
        "*.egg-info",
        ".eggs",
        "htmlcov",
        ".coverage",
        ".tox",
        ".nox",
        "*.log",
        "*.tmp",
        "*.temp",
        "*.bak",
        "*.orig",
        "*.DS_Store",
        "Thumbs.db",
        "*.swp",
        "*.swo"
    ]
    
    # Outputs (solo en limpieza profunda y si no se preservan)
    output_items = [
        "output/*.mp4",
        "output/*.png",
        "output/*.jpg",
        "output/*.jpeg"
    ]
    
    items_to_clean = basic_items.copy()
    
    if deep:
        items_to_clean.extend(deep_items)
        if not preserve_outputs:
            items_to_clean.extend(output_items)
            print_colored("🗑️ Incluyendo archivos de salida (output)", Colors.YELLOW)
        else:
            print_colored("💾 Preservando archivos de salida (output)", Colors.GREEN)
    
    cleaned_count = 0
    cleaned_size = 0
    
    for item in items_to_clean:
        if "*" in item:
            # Usar glob para patrones
            from glob import glob
            import os
            
            # Buscar en directorio actual y subdirectorios
            pattern_files = glob(item, recursive=True)
            # También buscar en subdirectorios específicos
            for subdir in ["", "**"]:
                pattern_files.extend(glob(f"{subdir}/{item}", recursive=True))
            
            # Eliminar duplicados
            pattern_files = list(set(pattern_files))
            
            for file in pattern_files:
                try:
                    if os.path.isfile(file):
                        size = os.path.getsize(file)
                        os.remove(file)
                        print_colored(f"🗑️ Archivo: {file} ({_format_size(size)})", Colors.YELLOW)
                        cleaned_count += 1
                        cleaned_size += size
                except Exception as e:
                    print_colored(f"⚠️ No se pudo eliminar {file}: {e}", Colors.YELLOW)
        else:
            path = Path(item)
            if path.exists():
                try:
                    if path.is_dir():
                        size = _get_dir_size(path)
                        shutil.rmtree(path)
                        print_colored(f"🗑️ Directorio: {item}/ ({_format_size(size)})", Colors.YELLOW)
                        cleaned_count += 1
                        cleaned_size += size
                    else:
                        size = path.stat().st_size
                        path.unlink()
                        print_colored(f"🗑️ Archivo: {item} ({_format_size(size)})", Colors.YELLOW)
                        cleaned_count += 1
                        cleaned_size += size
                except Exception as e:
                    print_colored(f"⚠️ No se pudo eliminar {item}: {e}", Colors.YELLOW)
    
    # Limpiar carpetas vacías
    if deep:
        _clean_empty_dirs(['temp', 'build', 'dist'])
    
    # Resumen de limpieza
    print("\n" + "="*50)
    print_colored(f"✅ Limpieza completada", Colors.GREEN)
    print_colored(f"📊 {cleaned_count} elementos eliminados", Colors.CYAN)
    print_colored(f"💾 {_format_size(cleaned_size)} liberados", Colors.CYAN)
    print("="*50)
    
    # Sugerencia post-limpieza
    if cleaned_count > 0:
        print_colored("💡 Sugerencia: Ejecuta 'python manage.py status' para ver el estado actual", Colors.BLUE)

def _format_size(size_bytes):
    """Formatea tamaño en bytes a formato legible"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def _get_dir_size(path):
    """Calcula el tamaño total de un directorio"""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except (OSError, FileNotFoundError):
                    pass
    except (OSError, FileNotFoundError):
        pass
    return total

def _clean_empty_dirs(dirs_to_check):
    """Elimina directorios vacíos"""
    for dir_name in dirs_to_check:
        dir_path = Path(dir_name)
        if dir_path.exists() and dir_path.is_dir():
            try:
                # Verificar si está vacío
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    print_colored(f"🗑️ Directorio vacío eliminado: {dir_name}/", Colors.YELLOW)
            except Exception:
                pass

def install_project():
    """Instalación completa del proyecto"""
    print_header("Instalación Completa del Proyecto")
    
    # 1. Limpiar proyecto
    clean_project()
    
    # 2. Crear carpetas
    create_folders()
    
    # 3. Configurar venv
    if not setup_venv():
        print_colored("❌ Error en la configuración", Colors.RED)
        return False
    
    # 4. Verificar instalación
    print_header("Verificando instalación")
    if check_dependencies():
        print_colored("✅ ¡Instalación completada exitosamente!", Colors.GREEN)
        print_colored("💡 Ahora coloca tu imagen de referencia en: data/ref/nopal_ref.jpg", Colors.YELLOW)
        print_colored("🚀 Luego ejecuta: python manage.py run", Colors.BLUE)
        return True
    else:
        print_colored("❌ Error en la verificación", Colors.RED)
        return False

def main():
    """Función principal con menú de comandos"""
    parser = argparse.ArgumentParser(
        description="🌵 Nopal Detector - Gestor del Proyecto",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Comandos disponibles:

📦 CONFIGURACIÓN:
  install     - Instalación completa automática
  setup       - Configurar venv e instalar dependencias  
  folders     - Crear estructura de carpetas

🚀 EJECUCIÓN:
  run         - Ejecutar detector con cámara
  run-camera  - Ejecutar con cámara y guardar video
  run-image   - Ejecutar con imagen (especifica --source)
  run-video   - Ejecutar con video (especifica --source)

🔧 UTILIDADES:
  status      - Mostrar estado del proyecto
  check       - Verificar dependencias
  clean       - Limpieza estándar (venv, cache, temporales)
  deep-clean  - Limpieza profunda (incluye logs, builds, etc.)

Ejemplos:
  python manage.py install
  python manage.py run
  python manage.py run-image --source examples/test.jpg --save output/result.png
  python manage.py run --source 0 --min_matches 12 --ratio 0.8
  python manage.py clean --deep --preserve-outputs
        """)
    
    parser.add_argument('command', nargs='?', default='help',
                       choices=['help', 'install', 'setup', 'folders', 'status', 'check',
                               'run', 'run-camera', 'run-image', 'run-video', 'clean', 'deep-clean'],
                       help='Comando a ejecutar')
    
    # Parámetros para detector
    parser.add_argument('--source', default='0', help='Fuente: cámara (0,1,2...), imagen o video')
    parser.add_argument('--save', help='Archivo de salida')
    parser.add_argument('--min_matches', type=int, help='Mínimo coincidencias (default: 18)')
    parser.add_argument('--ratio', type=float, help='Ratio test Lowe (default: 0.75)')
    
    # Parámetros para limpieza
    parser.add_argument('--deep', action='store_true', help='Limpieza profunda (incluye más archivos)')
    parser.add_argument('--preserve-outputs', action='store_true', help='Preservar archivos de salida en limpieza profunda')
    
    args = parser.parse_args()
    
    # Banner del proyecto
    print_colored("🌵 NOPAL DETECTOR - Gestor Principal", Colors.PURPLE)
    print_colored("Sistema de detección con computer vision\n", Colors.CYAN)
    
    # Ejecutar comandos
    if args.command == 'help' or args.command is None:
        parser.print_help()
    
    elif args.command == 'install':
        install_project()
    
    elif args.command == 'setup':
        create_folders()
        setup_venv()
    
    elif args.command == 'folders':
        create_folders()
    
    elif args.command == 'status':
        show_status()
    
    elif args.command == 'check':
        if venv_exists():
            check_dependencies()
        else:
            print_colored("❌ Entorno virtual no configurado", Colors.RED)
    
    elif args.command == 'clean':
        clean_project(deep=args.deep, preserve_outputs=args.preserve_outputs)
    
    elif args.command == 'deep-clean':
        clean_project(deep=True, preserve_outputs=args.preserve_outputs)
    
    elif args.command.startswith('run'):
        # Configurar parámetros según el tipo de run
        source = args.source
        save = args.save
        
        if args.command == 'run-camera':
            source = '0'
            save = save or 'output/camera_detection.mp4'
        
        run_detector(
            source=source,
            save=save,
            min_matches=args.min_matches,
            ratio=args.ratio
        )
    
    else:
        print_colored(f"❌ Comando no reconocido: {args.command}", Colors.RED)
        parser.print_help()

if __name__ == "__main__":
    main()