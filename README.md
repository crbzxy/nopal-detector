# 🌵 Detector de Nopal

Sistema de detección de nopal utilizando computer vision con OpenCV y algoritmos ORB + Homografía.

## 📁 Estructura del proyecto

```
nopal-detector/
├── nopal_all_in_one.py    # Script principal (auto-configura todo)
├── data/
│   └── ref/               # Coloca aquí la imagen de referencia
│       └── nopal_ref.jpg  # Imagen de referencia del nopal
├── examples/              # Imágenes/videos de ejemplo para probar
├── output/                # Archivos de salida generados
└── README.md              # Este archivo
```

## 🚀 Uso rápido

El script es completamente auto-contenido. Se encarga de:
- ✅ Crear entorno virtual (.venv)
- ✅ Instalar OpenCV y NumPy
- ✅ Verificar dependencias del sistema
- ✅ Ejecutar el detector

### Comandos básicos:

```bash
# 📷 Detección con cámara web (índice 0)
python nopal_all_in_one.py --source 0 --ref data/ref/nopal_ref.jpg

# 🖼️ Detección en imagen con guardado
python nopal_all_in_one.py --source examples/mi_foto.jpg --ref data/ref/nopal_ref.jpg --save output/resultado.png

# 🎥 Detección en video con guardado
python nopal_all_in_one.py --source examples/mi_video.mp4 --ref data/ref/nopal_ref.jpg --save output/resultado.mp4
```

## 🔧 Parámetros avanzados

```bash
python nopal_all_in_one.py \
  --source examples/test.jpg \
  --ref data/ref/nopal_ref.jpg \
  --save output/result.png \
  --min_matches 12 \
  --ratio 0.8
```

- `--min_matches`: Mínimo de coincidencias para detección (default: 18)
- `--ratio`: Ratio test de Lowe para filtrar matches (default: 0.75)

## 📋 Requisitos previos

- **Python 3.7+** (tienes Python 3.12.10 ✅)
- **Imagen de referencia**: Coloca una foto clara del nopal en `data/ref/nopal_ref.jpg`

## 🎯 Cómo preparar la imagen de referencia

1. Toma una foto clara del nopal que quieres detectar
2. Asegúrate de que tenga buena textura y contraste
3. Recorta solo la parte distintiva si es necesario
4. Guárdala como `data/ref/nopal_ref.jpg`

## 🐛 Solución de problemas

### "Referencia no encontrada"
```bash
# Verifica que existe la imagen
ls -la data/ref/nopal_ref.jpg
```

### "Muy pocos puntos clave"
- Usa una imagen con más textura/contraste
- Recorta al área más distintiva del nopal
- Prueba con mejor iluminación

### Error de cámara
- Verifica permisos de cámara
- Asegúrate de que no esté en uso por otra aplicación
- Prueba con otro índice: `--source 1` o `--source 2`

## 🧠 Cómo funciona

1. **Extracción de características**: Usa ORB para encontrar puntos clave únicos
2. **Matching**: Compara características entre imagen de referencia e input
3. **Homografía**: Calcula transformación geométrica para proyectar contornos
4. **Visualización**: Dibuja rectángulo verde alrededor del nopal detectado

## 📊 Controles durante ejecución

- **Cámara/Video**: Presiona `q` para salir
- **Imagen**: Presiona cualquier tecla o cierra la ventana# nopal-detector
