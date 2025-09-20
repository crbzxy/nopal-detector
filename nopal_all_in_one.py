#!/usr/bin/env python3
"""
nopal_all_in_one.py
- Un solo archivo que:
  1) Crea/activa venv (.venv)
  2) Instala dependencias (opencv-python, numpy)
  3) Verifica librerías del sistema y da soluciones
  4) Ejecuta detector ORB+Homography agnóstico (imagen / video / cámara)
  5) Manejo de errores con pistas de solución

Uso:
  python nopal_all_in_one.py --source 0 --ref data/ref/nopal_ref.jpg
  python nopal_all_in_one.py --source ./foto.jpg --ref ./data/ref/nopal_ref.jpg --save ./out.png
  python nopal_all_in_one.py --source ./video.mp4 --ref ./data/ref/nopal_ref.jpg --save ./out.mp4
"""

import os, sys, subprocess, platform, shutil, argparse, textwrap, json, time
from pathlib import Path

REQS = ["opencv-python>=4.9.0", "numpy>=1.26"]
VENV_DIR = Path(".venv")
IS_WIN = platform.system().lower().startswith("win")
IS_MAC = platform.system().lower().startswith("darwin")
IS_LINUX = platform.system().lower().startswith("linux")

def info(msg):  print(f"[INFO] {msg}")
def warn(msg):  print(f"[WARN] {msg}")
def err(msg):   print(f"[ERROR] {msg}")

def run(cmd, check=True, env=None):
    info(f"$ {' '.join(map(str, cmd))}")
    return subprocess.run(cmd, check=check, env=env)

def python_exe_in_venv():
    return str(VENV_DIR / ("Scripts/python.exe" if IS_WIN else "bin/python"))

def ensure_python3_available():
    # Verifica que exista python3/py/python
    cand = ["python3", "py", "python"]
    for c in cand:
        try:
            out = subprocess.run([c, "--version"], capture_output=True, text=True)
            if out.returncode == 0 and "Python 3" in out.stdout + out.stderr:
                return c
        except Exception:
            pass
    raise RuntimeError("No se encontró Python 3 en PATH. Instálalo:\n"
                       " - Windows: https://www.python.org/downloads/windows/\n"
                       " - macOS:   brew install python (o desde python.org)\n"
                       " - Linux:   sudo apt install -y python3 python3-venv (Debian/Ubuntu)")

def create_venv(py_cmd):
    if VENV_DIR.exists():
        info("Venv ya existe, continuo.")
        return
    info("Creando entorno virtual .venv ...")
    run([py_cmd, "-m", "venv", str(VENV_DIR)])

def pip_install(pkgs):
    py = python_exe_in_venv()
    # Actualiza pip/wheel
    run([py, "-m", "pip", "install", "--upgrade", "pip", "wheel"])
    # Instala dependencias
    run([py, "-m", "pip", "install", *pkgs])

def check_system_libs(save_path: str|None):
    # ffmpeg (recomendado si --save a video/mp4)
    if save_path and Path(save_path).suffix.lower() in {".mp4", ".mov", ".m4v"}:
        if shutil.which("ffmpeg") is None:
            warn("ffmpeg no encontrado. Para mejor soporte de video:")
            if IS_MAC:
                print("  macOS: brew install ffmpeg")
            elif IS_LINUX:
                print("  Debian/Ubuntu: sudo apt update && sudo apt install -y ffmpeg")
            elif IS_WIN:
                print("  Windows: choco install ffmpeg -y  (o scoop install ffmpeg)")
    # GUI libs en Linux (a veces faltan)
    if IS_LINUX:
        # Solo mostramos sugerencias: no instalamos automáticamente
        # porque puede requerir sudo y confirmar prompts.
        missing_suggestions = []
        for lib in ("libgl1", "libglib2.0-0", "libgtk-3-0"):
            # No hay una forma directa de "ver si está instalado" sin dpkg-query;
            # damos sugerencias preventivas.
            missing_suggestions.append(lib)
        print("Si ves errores como 'libGL.so.1' o GTK, ejecuta:")
        print("  sudo apt update && sudo apt install -y libgl1 libglib2.0-0 libgtk-3-0")
        print("  (en otras distros, instala equivalentes)")

def relaunch_inside_venv(argv):
    py = python_exe_in_venv()
    env = os.environ.copy()
    # Señalizamos que ya hicimos bootstrap
    env["NOPAL_BOOTSTRAPPED"] = "1"
    cmd = [py, __file__, "--stage", "run", *argv]
    result = subprocess.run(cmd, env=env)
    sys.exit(result.returncode)

# ======= Detector (solo se importa en stage run) =======

def open_source(src: str):
    import cv2
    # ¿Cámara?
    if src.isdigit():
        cap = cv2.VideoCapture(int(src))
        if not cap.isOpened():
            raise RuntimeError(f"No pude abrir la cámara '{src}'.")
        return cap, True, None

    p = Path(src)
    if not p.exists():
        raise FileNotFoundError(f"No existe la fuente: {src}")

    ext = p.suffix.lower()
    img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    if ext in img_exts:
        img = cv2.imread(str(p))
        if img is None:
            raise RuntimeError(f"No pude leer la imagen: {src}")
        return None, False, img

    cap = cv2.VideoCapture(str(p))
    if not cap.isOpened():
        raise RuntimeError(f"No pude abrir el video: {src}")
    return cap, True, None

def load_reference(ref_path: str):
    import cv2
    ref_img = cv2.imread(ref_path)
    if ref_img is None:
        raise FileNotFoundError(f"No pude abrir la referencia: {ref_path}")
    ref_gray = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
    return ref_img, ref_gray

def prepare_orb(ref_gray, nfeatures=2000):
    import cv2
    orb = cv2.ORB_create(nfeatures=nfeatures, scaleFactor=1.2, nlevels=8)
    kp_ref, des_ref = orb.detectAndCompute(ref_gray, None)
    if des_ref is None or len(kp_ref) < 8:
        raise RuntimeError("Muy pocos puntos clave en la referencia. Usa una foto con más textura/detalle.")
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    return orb, bf, kp_ref, des_ref

def detect_and_draw(frame, orb, bf, kp_ref, des_ref,
                    ref_size, min_matches=18, ratio=0.75):
    import cv2, numpy as np
    out = frame.copy()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    kp_frm, des_frm = orb.detectAndCompute(gray, None)
    good = []
    if des_frm is not None and len(kp_frm) >= 8:
        matches = bf.knnMatch(des_ref, des_frm, k=2)
        for m, n in matches:
            if m.distance < ratio * n.distance:
                good.append(m)

        cv2.putText(out, f"Matches: {len(good)}", (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        if len(good) >= min_matches:
            src_pts = np.float32([kp_ref[m.queryIdx].pt for m in good]).reshape(-1,1,2)
            dst_pts = np.float32([kp_frm[m.trainIdx].pt for m in good]).reshape(-1,1,2)
            H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            if H is not None:
                h, w = ref_size
                corners = np.float32([[0,0],[w,0],[w,h],[0,h]]).reshape(-1,1,2)
                proj = cv2.perspectiveTransform(corners, H)
                out = cv2.polylines(out, [np.int32(proj)], True, (0,255,0), 3, cv2.LINE_AA)
                cv2.putText(out, "NOPAL ESPECIFICO",
                            (int(proj[0,0,0]), max(20, int(proj[0,0,1]) - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            else:
                cv2.putText(out, "Sin homografia", (10, 58),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
    else:
        cv2.putText(out, "Pocos puntos en frame", (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
    return out

def run_detector(args):
    import cv2, numpy as np
    ref_img, ref_gray = load_reference(args.ref)
    orb, bf, kp_ref, des_ref = prepare_orb(ref_gray)
    h_ref, w_ref = ref_gray.shape

    cap, is_stream, first_frame = open_source(args.source)

    writer = None
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps_guess = 25

    try:
        if is_stream:
            if args.save:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)
                fps = cap.get(cv2.CAP_PROP_FPS)
                if not fps or np.isnan(fps) or fps <= 1:
                    fps = fps_guess
                writer = cv2.VideoWriter(args.save, fourcc, fps, (width, height))

            while True:
                ok, frame = cap.read()
                if not ok:
                    warn("Fin del stream o frame inválido.")
                    break
                out = detect_and_draw(frame, orb, bf, kp_ref, des_ref,
                                      (h_ref, w_ref),
                                      min_matches=args.min_matches,
                                      ratio=args.ratio)
                if writer is not None:
                    writer.write(out)
                cv2.imshow("Nopal detector (q para salir)", out)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        else:
            out = detect_and_draw(first_frame, orb, bf, kp_ref, des_ref,
                                  (h_ref, w_ref),
                                  min_matches=args.min_matches,
                                  ratio=args.ratio)
            if args.save:
                cv2.imwrite(args.save, out)
                info(f"Salida guardada en: {args.save}")
            cv2.imshow("Nopal detector (cierra ventana o presiona cualquier tecla)", out)
            cv2.waitKey(0)
    finally:
        if is_stream and cap is not None:
            cap.release()
        if writer is not None:
            writer.release()
        cv2.destroyAllWindows()

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="All-in-one: prepara venv, instala deps y ejecuta detector one-shot de nopal.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    p.add_argument("--source", required=False, default="0",
                   help="Ruta a imagen/video o índice de cámara (ej. 0).")
    p.add_argument("--ref", required=False, default="data/ref/nopal_ref.jpg",
                   help="Imagen de referencia del nopal.")
    p.add_argument("--save", default=None,
                   help="Ruta para guardar salida (PNG/JPG para imagen; MP4 para video/cámara).")
    p.add_argument("--min_matches", type=int, default=18,
                   help="Mínimo de coincidencias buenas para aceptar detección.")
    p.add_argument("--ratio", type=float, default=0.75,
                   help="Ratio test de Lowe.")
    p.add_argument("--stage", choices=["bootstrap","run"], default="bootstrap",
                   help=argparse.SUPPRESS)  # interno
    return p.parse_args(argv)

def main():
    args = parse_args()

    if args.stage == "run":
        # Ya estamos dentro del venv
        try:
            import cv2, numpy as np  # noqa
        except Exception as e:
            err(f"No se pudo importar OpenCV/Numpy dentro del venv: {e}")
            print("\nPosibles soluciones:")
            print("  - Reinstala dependencias: .venv/bin/python -m pip install -U pip wheel && "
                  "pip install --force-reinstall " + " ".join(REQS))
            print("  - Si estás en Linux y ves 'libGL.so.1': sudo apt install -y libgl1 libglib2.0-0 libgtk-3-0")
            sys.exit(1)

        # Validaciones de insumos
        if not args.ref or not Path(args.ref).exists():
            err(f"Referencia no encontrada: {args.ref}")
            print("Solución: proporciona una imagen existente con --ref path/a/tu_nopal.jpg")
            sys.exit(1)

        try:
            run_detector(args)
        except FileNotFoundError as e:
            err(str(e))
            sys.exit(1)
        except RuntimeError as e:
            err(str(e))
            print("\nSugerencias:")
            print(" - Si es cámara: verifica permisos y que no esté en uso por otra app.")
            print(" - Si es imagen: que el archivo exista y sea legible.")
            print(" - Si es video: instala ffmpeg y prueba con otro contenedor (mp4).")
            print(" - Si dice 'Muy pocos puntos clave': usa una referencia con más textura/contraste "
                  "o recorta al área más distintiva del nopal.")
            sys.exit(2)
        except Exception as e:
            err(f"Fallo inesperado en ejecución: {e}")
            sys.exit(3)
        sys.exit(0)

    # stage: bootstrap
    try:
        py_cmd = ensure_python3_available()
    except Exception as e:
        err(str(e)); sys.exit(1)

    # Crea venv si no existe
    try:
        create_venv(py_cmd)
    except Exception as e:
        err(f"No pude crear venv: {e}")
        print("Soluciones:")
        print(" - Windows: asegúrate de instalar Python con opción 'Add to PATH'.")
        print(" - Linux (Debian/Ubuntu): sudo apt install -y python3-venv")
        print(" - Verifica permisos de escritura en el directorio actual.")
        sys.exit(1)

    # Instala dependencias
    try:
        pip_install(REQS)
    except subprocess.CalledProcessError as e:
        err("Falló la instalación de dependencias.")
        print("Salida de pip arriba. Posibles soluciones:")
        print(" - Actualiza pip: .venv/bin/python -m pip install -U pip wheel")
        print(" - Si error de compilación: usa 'opencv-python-headless' en servidores sin GUI.")
        print(" - Verifica conexión a Internet / proxy.")
        sys.exit(e.returncode)

    # Checks de sistema útiles
    try:
        check_system_libs(args.save)
    except Exception:
        pass

    # Re-ejecuta dentro del venv para correr el detector
    relaunch_inside_venv(sys.argv[1:])

if __name__ == "__main__":
    main()