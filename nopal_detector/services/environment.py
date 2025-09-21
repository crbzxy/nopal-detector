"""
Servicio para gestión del entorno y dependencias.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from ..config.settings import EnvironmentConfig
from ..utils.logging import setup_logger


class EnvironmentService:
    """Servicio para gestión del entorno de ejecución."""
    
    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.logger = setup_logger(__name__)
        self.is_windows = platform.system().lower().startswith("win")
        self.is_mac = platform.system().lower().startswith("darwin")
        self.is_linux = platform.system().lower().startswith("linux")
    
    @property
    def python_exe_in_venv(self) -> str:
        """Devuelve la ruta del ejecutable Python en el venv."""
        if self.is_windows:
            return str(self.config.venv_dir / "Scripts/python.exe")
        return str(self.config.venv_dir / "bin/python")
    
    def find_python_executable(self) -> str:
        """
        Encuentra un ejecutable Python 3 válido.
        
        Returns:
            Comando Python ejecutable
            
        Raises:
            RuntimeError: Si no se encuentra Python 3
        """
        for candidate in self.config.python_candidates:
            try:
                result = subprocess.run(
                    [candidate, "--version"], 
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                combined_output = (result.stdout or "") + (result.stderr or "")
                if result.returncode == 0 and "Python 3" in combined_output:
                    self.logger.info(f"Encontrado Python: {candidate}")
                    return candidate
            except OSError:
                continue
        
        error_msg = (
            "No se encontró Python 3 en PATH.\n"
            "Instala Python 3:\n"
            " - Windows: https://www.python.org/downloads/windows/\n"
            " - macOS: brew install python\n"
            " - Linux: sudo apt install -y python3 python3-venv"
        )
        raise RuntimeError(error_msg)
    
    def create_venv(self, python_cmd: str) -> None:
        """
        Crea el entorno virtual si no existe.
        
        Args:
            python_cmd: Comando Python a usar
        """
        if self.config.venv_dir.exists():
            self.logger.info("Entorno virtual ya existe")
            return
        
        self.logger.info(f"Creando entorno virtual en {self.config.venv_dir}")
        try:
            subprocess.run(
                [python_cmd, "-m", "venv", str(self.config.venv_dir)], 
                check=True
            )
            self.logger.info("Entorno virtual creado exitosamente")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error creando entorno virtual: {e}")
    
    def install_requirements(self) -> None:
        """
        Instala las dependencias requeridas en el venv.
        
        Raises:
            RuntimeError: Si falla la instalación
        """
        python_exe = self.python_exe_in_venv
        
        # Actualizar pip y wheel
        self.logger.info("Actualizando pip y wheel")
        try:
            subprocess.run(
                [python_exe, "-m", "pip", "install", "--upgrade", "pip", "wheel"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error actualizando pip: {e}")
        
        # Instalar dependencias
        self.logger.info(f"Instalando dependencias: {self.config.requirements}")
        try:
            subprocess.run(
                [python_exe, "-m", "pip", "install"] + self.config.requirements,
                check=True
            )
            self.logger.info("Dependencias instaladas exitosamente")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error instalando dependencias: {e}")
    
    def check_system_dependencies(self, output_path: Optional[str] = None) -> None:
        """
        Verifica dependencias del sistema y muestra sugerencias.
        
        Args:
            output_path: Ruta de salida (para verificar si necesita ffmpeg)
        """
        suggestions = []
        
        # Verificar ffmpeg para video
        if output_path and Path(output_path).suffix.lower() in {".mp4", ".mov", ".m4v"}:
            if shutil.which("ffmpeg") is None:
                suggestions.append(self._get_ffmpeg_suggestion())
        
        # Verificar librerías gráficas en Linux
        if self.is_linux:
            suggestions.append(
                "Si ves errores como 'libGL.so.1' o GTK, ejecuta:\n"
                "  sudo apt update && sudo apt install -y libgl1 libglib2.0-0 libgtk-3-0\n"
                "  (en otras distros, instala equivalentes)"
            )
        
        if suggestions:
            self.logger.info("Sugerencias para el sistema:")
            for suggestion in suggestions:
                print(suggestion)
    
    def _get_ffmpeg_suggestion(self) -> str:
        """Devuelve sugerencia de instalación de ffmpeg según el OS."""
        if self.is_mac:
            return "ffmpeg no encontrado. Para mejor soporte de video:\n  macOS: brew install ffmpeg"
        elif self.is_linux:
            return "ffmpeg no encontrado. Para mejor soporte de video:\n  Debian/Ubuntu: sudo apt update && sudo apt install -y ffmpeg"
        elif self.is_windows:
            return "ffmpeg no encontrado. Para mejor soporte de video:\n  Windows: choco install ffmpeg -y (o scoop install ffmpeg)"
        return "ffmpeg no encontrado. Instala ffmpeg para mejor soporte de video."
    
    def bootstrap_environment(self) -> str:
        """
        Configura completamente el entorno de ejecución.
        
        Returns:
            Ruta del ejecutable Python en el venv
            
        Raises:
            RuntimeError: Si falla algún paso del bootstrap
        """
        # Encontrar Python
        python_cmd = self.find_python_executable()
        
        # Crear venv
        self.create_venv(python_cmd)
        
        # Instalar dependencias
        self.install_requirements()
        
        return self.python_exe_in_venv
    
    def relaunch_in_venv(self, script_path: str, args: List[str]) -> None:
        """
        Relanza el script dentro del venv.
        
        Args:
            script_path: Ruta del script a ejecutar
            args: Argumentos para el script
        """
        python_exe = self.python_exe_in_venv
        env = os.environ.copy()
        env["NOPAL_BOOTSTRAPPED"] = "1"
        
        cmd = [python_exe, script_path] + args
        self.logger.info(f"Relanzando en venv: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, env=env, check=False)
        sys.exit(result.returncode)