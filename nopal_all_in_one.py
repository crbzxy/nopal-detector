#!/usr/bin/env python3
"""
nopal_all_in_one.py

Script “todo en uno” para:
1) Crear/activar venv (.venv)
2) Instalar dependencias (opencv-python, numpy)
3) Verificar librerías del sistema y sugerir soluciones
4) Ejecutar detector ORB + Homography (imagen / video / cámara)
5) Manejo de errores con pistas de solución

Uso rápido:
  python nopal_all_in_one.py --source 0 --ref data/ref/nopal_ref.jpg
  python nopal_all_in_one.py --source ./foto.jpg --ref ./data/ref/nopal_ref.jpg --save ./out.png
  python nopal_all_in_one.py --source ./video.mp4 --ref ./data/ref/nopal_ref.jpg --save ./out.mp4
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Tuple, List, TYPE_CHECKING

# Importes solo para type-checking (no se ejecutan en runtime).
# Evita E0401 (import-error) y “invalid type form” en Pylance.
if TYPE_CHECKING:  # pragma: no cover
    import cv2 as _cv2_type  # type: ignore
    import numpy as _np_type  # type: ignore

REQS: List[str] = ["opencv-python>=4.9.0", "numpy>=1.26"]
VENV_DIR = Path(".venv")

IS_WIN = platform.system().lower().startswith("win")
IS_MAC = platform.system().lower().startswith("darwin")
IS_LINUX = platform.system().lower().startswith("linux")


def info(msg: str) -> None:
    """Log informativo."""
    print(f"[INFO] {msg}")


def warn(msg: str) -> None:
    """Log de advertencia."""
    print(f"[WARN] {msg}")


def err(msg: str) -> None:
    """Log de error."""
    print(f"[ERROR] {msg}")


def run_cmd(
    cmd: List[str],
    *,
    check: bool = True,
    env: Optional[dict] = None,
) -> subprocess.CompletedProcess:
    """
    Ejecuta un comando de shell mostrando el comando.
    Define 'check' explícitamente para satisfacer linters.
    """
    info(f"$ {' '.join(map(str, cmd))}")
    return subprocess.run(cmd, check=check, env=env)  # noqa: S603


def python_exe_in_venv() -> str:
    """Devuelve la ruta del ejecutable de Python dentro del venv."""
    return str(VENV_DIR / ("Scripts/python.exe" if IS_WIN else "bin/python"))


def ensure_python3_available() -> str:
    """
    Verifica que exista un intérprete Python 3 en PATH.
    Devuelve el comando invocable ('python3'/'py'/'python').
    """
    candidates = ["python3", "py", "python"]
    for cand in candidates:
        try:
            out = subprocess.run(  # noqa: S603
                [cand, "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
            combined = (out.stdout or "") + (out.stderr or "")
            if out.returncode == 0 and "Python 3" in combined:
                return cand
        except OSError:
            continue

    raise RuntimeError(
        "No se encontró Python 3 en PATH.\n"
        "Instala Python 3:\n"
        " - Windows: https://www.python.org/downloads/windows/\n"
        " - macOS:   brew install python (o descargando de python.org)\n"
        " - Linux:   sudo apt install -y python3 python3-venv (Debian/Ubuntu)"
    )


def create_venv(py_cmd: str) -> None:
    """Crea el entorno virtual .venv si no existe."""
    if VENV_DIR.exists():
        info("Venv ya existe, continúo.")
        return
    info("Creando entorno virtual .venv ...")
    run_cmd([py_cmd, "-m", "venv", str(VENV_DIR)], check=True)


def pip_install(packages: List[str]) -> None:
    """Actualiza pip/wheel e instala las dependencias requeridas en el venv."""
    py = python_exe_in_venv()
    run_cmd([py, "-m", "pip", "install", "--upgrade", "pip", "wheel"], check=True)
    run_cmd([py, "-m", "pip", "install", *packages], check=True)


def check_system_libs(save_path: Optional[str]) -> None:
    """
    Muestra sugerencias de instalación de librerías del sistema
    (ffmpeg para video/MP4, librerías de GUI en Linux).
    """
    if save_path and Path(save_path).suffix.lower() in {".mp4", ".mov", ".m4v"}:
        if shutil.which("ffmpeg") is None:
            warn("ffmpeg no encontrado. Para mejor soporte de video:")
            if IS_MAC:
                print("  macOS: brew install ffmpeg")
            elif IS_LINUX:
                print("  Debian/Ubuntu: sudo apt update && sudo apt install -y ffmpeg")
            elif IS_WIN:
                print("  Windows: choco install ffmpeg -y  (o scoop install ffmpeg)")

    if IS_LINUX:
        print("Si ves errores como 'libGL.so.1' o GTK, ejecuta:")
        print("  sudo apt update && sudo apt install -y libgl1 libglib2.0-0 libgtk-3-0")
        print("  (en otras distros, instala equivalentes)")


def relaunch_inside_venv(argv: List[str]) -> None:
    """Reejecuta este script dentro del venv ya creado para la fase de ejecución."""
    py = python_exe_in_venv()
    env = os.environ.copy()
    env["NOPAL_BOOTSTRAPPED"] = "1"
    script_path = str(Path(__file__).resolve())
    cmd = [py, script_path, "--stage", "run", *argv]
    result = subprocess.run(cmd, env=env, check=False)  # noqa: S603
    sys.exit(result.returncode)


# ==================== BLOQUE DETECTOR ====================

@dataclass
class OrbContext:
    """Contexto de detección ORB y parámetros de matching."""
    orb: Any
    bf: Any
    kp_ref: List[Any]
    des_ref: Any
    ref_h: int
    ref_w: int
    min_matches: int
    ratio: float


def open_source(src: str) -> Tuple[Optional[Any], bool, Optional[Any]]:
    """
    Abre una fuente (cámara/video/imagen) y devuelve:
    (captura, is_stream, first_frame_si_imagen)
    """
    import cv2 as _cv2  # pylint: disable=import-outside-toplevel
    import numpy as _np  # pylint: disable=import-outside-toplevel, unused-import

    if src.isdigit():
        cap = _cv2.VideoCapture(int(src))
        if not cap.isOpened():
            raise RuntimeError(f"No pude abrir la cámara '{src}'.")
        return cap, True, None

    path = Path(src)
    if not path.exists():
        raise FileNotFoundError(f"No existe la fuente: {src}")

    ext = path.suffix.lower()
    img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    if ext in img_exts:
        img = _cv2.imread(str(path))
        if img is None:
            raise RuntimeError(f"No pude leer la imagen: {src}")
        return None, False, img

    cap = _cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"No pude abrir el video: {src}")
    return cap, True, None


def load_reference(ref_path: str) -> Tuple[Any, Any]:
    """Carga la imagen de referencia y su versión en escala de grises."""
    import cv2 as _cv2  # pylint: disable=import-outside-toplevel

    ref_img = _cv2.imread(ref_path)
    if ref_img is None:
        raise FileNotFoundError(f"No pude abrir la referencia: {ref_path}")
    ref_gray = _cv2.cvtColor(ref_img, _cv2.COLOR_BGR2GRAY)
    return ref_img, ref_gray


def prepare_orb(ref_gray: Any, nfeatures: int = 2000) -> Tuple[Any, Any, List[Any], Any]:
    """Crea ORB y BFMatcher, y computa keypoints/descriptores de la referencia."""
    import cv2 as _cv2  # pylint: disable=import-outside-toplevel

    orb = _cv2.ORB_create(nfeatures=nfeatures, scaleFactor=1.2, nlevels=8)
    kp_ref, des_ref = orb.detectAndCompute(ref_gray, None)
    if des_ref is None or len(kp_ref) < 8:
        raise RuntimeError(
            "Muy pocos puntos clave en la referencia. Usa una foto con más textura/detalle."
        )
    bf = _cv2.BFMatcher(_cv2.NORM_HAMMING, crossCheck=False)
    return orb, bf, kp_ref, des_ref


def build_context(ref_gray: Any, min_matches: int, ratio: float) -> OrbContext:
    """Construye el contexto ORB/BF con metadatos de referencia y umbrales."""
    orb, bf, kp_ref, des_ref = prepare_orb(ref_gray)
    h_ref, w_ref = ref_gray.shape
    return OrbContext(
        orb=orb,
        bf=bf,
        kp_ref=kp_ref,
        des_ref=des_ref,
        ref_h=h_ref,
        ref_w=w_ref,
        min_matches=min_matches,
        ratio=ratio,
    )


def detect_and_draw(frame: Any, ctx: OrbContext) -> Any:
    """
    Detecta el nopal específico en 'frame' usando ORB+Homography
    y dibuja el polígono de proyección si la homografía es válida.
    """
    import cv2 as _cv2  # pylint: disable=import-outside-toplevel
    import numpy as _np  # pylint: disable=import-outside-toplevel

    output = frame.copy()
    gray = _cv2.cvtColor(frame, _cv2.COLOR_BGR2GRAY)

    kp_frm, des_frm = ctx.orb.detectAndCompute(gray, None)
    good = []
    if des_frm is not None and kp_frm and len(kp_frm) >= 8:
        matches = ctx.bf.knnMatch(ctx.des_ref, des_frm, k=2)
        for m, n in matches:
            if m.distance < ctx.ratio * n.distance:
                good.append(m)

        _cv2.putText(
            output,
            f"Matches: {len(good)}",
            (10, 28),
            _cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

        if len(good) >= ctx.min_matches:
            src_pts = _np.float32([ctx.kp_ref[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = _np.float32([kp_frm[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
            homography, _mask = _cv2.findHomography(src_pts, dst_pts, _cv2.RANSAC, 5.0)

            if homography is not None:
                corners = _np.float32(
                    [[0, 0], [ctx.ref_w, 0], [ctx.ref_w, ctx.ref_h], [0, ctx.ref_h]]
                ).reshape(-1, 1, 2)
                proj = _cv2.perspectiveTransform(corners, homography)

                output = _cv2.polylines(
                    output,
                    [_np.int32(proj)],
                    True,
                    (0, 255, 0),
                    3,
                    _cv2.LINE_AA,
                )
                x0, y0 = int(proj[0, 0, 0]), int(proj[0, 0, 1])
                _cv2.putText(
                    output,
                    "NOPAL ESPECIFICO",
                    (x0, max(20, y0 - 10)),
                    _cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )
            else:
                _cv2.putText(
                    output,
                    "Sin homografia",
                    (10, 58),
                    _cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                )
    else:
        _cv2.putText(
            output,
            "Pocos puntos en frame",
            (10, 28),
            _cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
        )

    return output


def run_detector(args: argparse.Namespace) -> None:
    """Ejecuta el pipeline de detección para imagen/cámara/video."""
    import cv2 as _cv2  # pylint: disable=import-outside-toplevel
    import numpy as _np  # pylint: disable=import-outside-toplevel, unused-import

    _ref_img, ref_gray = load_reference(args.ref)
    ctx = build_context(ref_gray, args.min_matches, args.ratio)

    cap, is_stream, first_frame = open_source(args.source)

    writer = None
    fourcc = _cv2.VideoWriter_fourcc(*"mp4v")
    fps_guess = 25

    try:
        if is_stream:
            if args.save:
                width = int(cap.get(_cv2.CAP_PROP_FRAME_WIDTH) or 1280)  # type: ignore
                height = int(cap.get(_cv2.CAP_PROP_FRAME_HEIGHT) or 720)  # type: ignore
                fps = cap.get(_cv2.CAP_PROP_FPS)  # type: ignore
                if not fps or fps <= 1:
                    fps = fps_guess
                writer = _cv2.VideoWriter(args.save, fourcc, fps, (width, height))

            while True:
                ok, frame = cap.read()  # type: ignore
                if not ok:
                    warn("Fin del stream o frame inválido.")
                    break
                out = detect_and_draw(frame, ctx)
                if writer is not None:
                    writer.write(out)
                _cv2.imshow("Nopal detector (q para salir)", out)
                if _cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        else:
            out = detect_and_draw(first_frame, ctx)  # type: ignore[arg-type]
            if args.save:
                Path(args.save).parent.mkdir(parents=True, exist_ok=True)
                _cv2.imwrite(args.save, out)
                info(f"Salida guardada en: {args.save}")
            _cv2.imshow(
                "Nopal detector (cierra ventana o presiona cualquier tecla)",
                out,
            )
            _cv2.waitKey(0)
    finally:
        if is_stream and cap is not None:
            cap.release()
        if writer is not None:
            writer.release()
        _cv2.destroyAllWindows()


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Define y parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description=(
            "All-in-one: prepara venv, instala deps y ejecuta detector one-shot de nopal."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--source",
        required=False,
        default="0",
        help="Ruta a imagen/video o índice de cámara (ej. 0).",
    )
    parser.add_argument(
        "--ref",
        required=False,
        default="data/ref/nopal_ref.jpg",
        help="Imagen de referencia del nopal.",
    )
    parser.add_argument(
        "--save",
        default=None,
        help="Ruta para guardar salida (PNG/JPG para imagen; MP4 para video/cámara).",
    )
    parser.add_argument(
        "--min_matches",
        type=int,
        default=18,
        help="Mínimo de coincidencias buenas para aceptar detección.",
    )
    parser.add_argument(
        "--ratio",
        type=float,
        default=0.75,
        help="Ratio test de Lowe.",
    )
    parser.add_argument(
        "--stage",
        choices=["bootstrap", "run"],
        default="bootstrap",
        help=argparse.SUPPRESS,  # solo uso interno
    )
    return parser.parse_args(argv)


def main() -> None:
    """Punto de entrada principal (bootstrap o ejecución)."""
    # Asegura estructura base independientemente del flujo.
    for folder in ["data/ref", "examples", "output"]:
        Path(folder).mkdir(parents=True, exist_ok=True)

    args = parse_args()

    if args.stage == "run":
        # En esta etapa, ya deberíamos tener las deps instaladas.
        try:
            import cv2 as _cv2  # pylint: disable=import-outside-toplevel, unused-import
            import numpy as _np  # pylint: disable=import-outside-toplevel, unused-import
        except ModuleNotFoundError as exc:
            err(f"No se pudo importar una dependencia dentro del venv: {exc}")
            print("\nPosibles soluciones:")
            print(
                "  - Reinstala dependencias:\n"
                "    .venv/bin/python -m pip install -U pip wheel && "
                "pip install --force-reinstall " + " ".join(REQS)
            )
            if IS_LINUX:
                print(
                    "  - Si ves 'libGL.so.1': "
                    "sudo apt install -y libgl1 libglib2.0-0 libgtk-3-0"
                )
            sys.exit(1)

        if not args.ref or not Path(args.ref).exists():
            err(f"Referencia no encontrada: {args.ref}")
            print("Solución: proporciona una imagen válida con --ref path/a/tu_nopal.jpg")
            sys.exit(1)

        try:
            run_detector(args)
        except FileNotFoundError as exc:
            err(str(exc))
            sys.exit(1)
        except RuntimeError as exc:
            err(str(exc))
            print("\nSugerencias:")
            print(" - Si es cámara: verifica permisos y que no esté en uso por otra app.")
            print(" - Si es imagen: que el archivo exista y sea legible.")
            print(" - Si es video: instala ffmpeg y prueba con otro contenedor (mp4).")
            print(
                " - Si dice 'Muy pocos puntos clave': usa una referencia con más textura/contraste "
                "o recorta al área más distintiva del nopal."
            )
            sys.exit(2)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            # Red de seguridad final para loguear fallos inesperados.
            err(f"Fallo inesperado en ejecución: {exc}")
            sys.exit(3)
        sys.exit(0)

    # ========= Etapa bootstrap =========
    try:
        py_cmd = ensure_python3_available()
    except RuntimeError as exc:
        err(str(exc))
        sys.exit(1)

    try:
        create_venv(py_cmd)
    except subprocess.CalledProcessError as exc:
        err(f"No pude crear venv: {exc}")
        print("Soluciones:")
        print(" - Windows: instala Python con 'Add to PATH'.")
        print(" - Linux (Debian/Ubuntu): sudo apt install -y python3-venv")
        print(" - Verifica permisos de escritura en el directorio actual.")
        sys.exit(1)

    try:
        pip_install(REQS)
    except subprocess.CalledProcessError as exc:
        err("Falló la instalación de dependencias.")
        info(
            "Salida de pip arriba. Posibles soluciones:\n"
            " - Actualiza pip: .venv/bin/python -m pip install -U pip wheel\n"
            " - En servidores sin GUI: usa 'opencv-python-headless'.\n"
            " - Verifica conexión a Internet / proxy."
        )
        sys.exit(exc.returncode)

    try:
        check_system_libs(args.save)
    except Exception:
        # Sugerencias no críticas; ignoramos errores aquí.
        pass

    relaunch_inside_venv(sys.argv[1:])


if __name__ == "__main__":
    main()
