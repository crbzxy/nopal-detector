# 🌵 Detector de Nopal

Sistema de detección de nopal utilizando *computer vision* con OpenCV y algoritmos ORB + Homografía.

## 📁 Estructura del proyecto

```bash
nopal-detector/
├── nopal_all_in_one.py    # Script principal (auto-configura todo)
├── data/
│   └── ref/               # Coloca aquí la imagen de referencia
│       └── nopal_ref.jpg  # Imagen de referencia del nopal
├── examples/              # Imágenes/videos de ejemplo para probar
├── output/                # Archivos de salida generados
└── README.md              # Este archivo
```

👉 **Nota:** si no existen las carpetas `data/ref`, `examples` u `output`, el script las crea automáticamente al ejecutarse.

---

## 🚀 Uso rápido

El script es completamente auto-contenido. Se encarga de:
- ✅ Crear entorno virtual (`.venv`)
- ✅ Instalar OpenCV y NumPy
- ✅ Verificar dependencias del sistema
- ✅ Ejecutar el detector

### Comandos básicos

```bash
# 📷 Detección con cámara web (índice 0)
python nopal_all_in_one.py --source 0 --ref data/ref/nopal_ref.jpg

# 🖼️ Detección en imagen con guardado
python nopal_all_in_one.py --source examples/mi_foto.jpg --ref data/ref/nopal_ref.jpg --save output/resultado.png

# 🎥 Detección en video con guardado
python nopal_all_in_one.py --source examples/mi_video.mp4 --ref data/ref/nopal_ref.jpg --save output/resultado.mp4
```

---

## 🔧 Parámetros avanzados

```bash
python nopal_all_in_one.py   --source examples/test.jpg   --ref data/ref/nopal_ref.jpg   --save output/result.png   --min_matches 12   --ratio 0.8
```

- `--min_matches`: Mínimo de coincidencias para detección (default: 18)
- `--ratio`: Ratio test de Lowe para filtrar matches (default: 0.75)

---

## 📋 Requisitos previos

- **Python 3.7+** (recomendado: 3.10 o superior)
- **Imagen de referencia**: Coloca una foto clara del nopal en `data/ref/nopal_ref.jpg`
- En Linux/macOS puede requerirse instalar librerías del sistema:
  ```bash
  sudo apt update && sudo apt install -y libgl1 libglib2.0-0 libgtk-3-0 ffmpeg
  ```

---

## 📦 Instalación de dependencias (similar a `npm i`)

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip wheel
.\.venv\Scripts\python -m pip install opencv-python numpy
```

### macOS / Linux

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip wheel
./.venv/bin/python -m pip install opencv-python numpy
```

> En servidores sin entorno gráfico, usa `opencv-python-headless` en lugar de `opencv-python`.

---

## 🎯 Cómo preparar la imagen de referencia

1. Toma una foto clara del nopal que quieres detectar.  
2. Asegúrate de que tenga buena textura y contraste.  
3. Recorta solo la parte distintiva si es necesario.  
4. Guárdala como `data/ref/nopal_ref.jpg`.  

---

## 🐛 Solución de problemas

**"Referencia no encontrada"**  
```bash
ls -la data/ref/nopal_ref.jpg
```

**"Muy pocos puntos clave"**
- Usa una imagen con más textura/contraste.  
- Recorta al área más distintiva del nopal.  
- Prueba con mejor iluminación.  

**Error de cámara**
- Verifica permisos de cámara.  
- Asegúrate de que no esté en uso por otra aplicación.  
- Prueba con otro índice: `--source 1` o `--source 2`.  

**Problemas en Linux**
- Instala librerías de sistema:  
  ```bash
  sudo apt install -y libgl1 libglib2.0-0 libgtk-3-0
  ```

---

## 🧠 Cómo funciona

1. **Extracción de características**: Usa ORB para encontrar puntos clave únicos.  
2. **Matching**: Compara características entre la imagen de referencia y el input.  
3. **Homografía**: Calcula transformación geométrica para proyectar contornos.  
4. **Visualización**: Dibuja un polígono verde alrededor del nopal detectado.  

---

## 📊 Controles durante ejecución

- **Cámara/Video**: Presiona `q` para salir.  
- **Imagen**: Presiona cualquier tecla o cierra la ventana.  

---

## 💡 Tip extra: Configuración en VS Code

Selecciona el intérprete de tu venv:  
`Ctrl+Shift+P` → “Python: Select Interpreter” → `.venv/bin/python` (Linux/macOS) o `.venv\Scripts\python.exe` (Windows).

Opcional en `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.analysis.extraPaths": [".venv/lib/python3.x/site-packages"]
}
```
