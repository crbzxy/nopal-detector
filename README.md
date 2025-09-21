# 🌵 Detector de Nopal

Sistema avanzado de detección de nopal utilizando computer vision con OpenCV y algoritmos ORB + Homografía.

**🐍 100% Python - Sin dependencias externas**

## ✨ Características

- 🚀 **Un solo comando** para instalación completa
- 🐍 **Solo Python** - sin make, npm, o herramientas externas  
- 🔧 **Multiplataforma** - Windows, Linux, macOS
- 📦 **Virtual environment** automático
- 🎯 **Múltiples fuentes** - cámara, imagen, video
- 📊 **Diagnósticos inteligentes** con colores

## 📁 Estructura

```
nopal-detector/
├── 🐍 manage.py              # ← GESTOR PRINCIPAL (todo en uno)
├── 🐍 nopal_all_in_one.py    # Script detector (auto-setup incluido)
├── 📋 requirements.txt       # Dependencias: OpenCV + NumPy
├── 📄 README.md              # Esta documentación
├── 📁 data/ref/              # Imagen de referencia (¡REQUERIDA!)
├── 📁 examples/              # Imágenes/videos de prueba
└── 📁 output/                # Resultados generados
```

## 🚀 Inicio rápido (3 comandos)

```bash
# 1. Instalación completa automática
python manage.py install

# 2. Coloca tu imagen: data/ref/nopal_ref.jpg 

# 3. ¡Ejecutar!
python manage.py run
```

## 📋 Todos los comandos

### 📦 **CONFIGURACIÓN**
```bash
python manage.py install     # 🎯 Instalación completa automática
python manage.py setup       # 🔧 Solo venv + dependencias  
python manage.py folders     # 📁 Solo crear carpetas
```

### 🚀 **EJECUCIÓN** 
```bash
python manage.py run          # 📷 Cámara web (básico)
python manage.py run-camera   # 📷 Cámara + guardar video
python manage.py run-image    # 🖼️ Imagen (usar --source)
python manage.py run-video    # 🎥 Video (usar --source)
```

### 🔧 **UTILIDADES**
```bash
python manage.py status       # 📊 Ver estado completo
python manage.py check        # ✅ Verificar dependencias
python manage.py clean        # 🧹 Limpiar todo
```

## 💡 Ejemplos de uso

### **Instalación y primer uso:**
```bash
# Instalar desde cero
python manage.py install

# Ver qué falta
python manage.py status

# Ejecutar (necesita imagen de referencia)
python manage.py run
```

### **Detección con diferentes fuentes:**
```bash
# Cámara web con guardado
python manage.py run-camera

# Imagen específica
python manage.py run-image --source examples/mi_foto.jpg --save output/resultado.png

# Video específico  
python manage.py run-video --source examples/mi_video.mp4 --save output/resultado.mp4

# Cámara con parámetros ajustados
python manage.py run --source 0 --min_matches 12 --ratio 0.8
```

### **Mantenimiento:**
```bash
# Verificar todo funciona
python manage.py check

# Empezar completamente limpio
python manage.py clean
python manage.py install
```

## 📊 Diagnósticos automáticos

El comando `status` te muestra exactamente qué falta:

```bash
python manage.py status
```

**Ejemplo de salida:**
```
🌵 Estado del Proyecto
==================================================

🔍 Entorno Virtual:
  ✅ .venv existe
  ✅ Python 3.12.10

📁 Estructura de carpetas:
  ✅ data/
  ✅ data/ref/
  ✅ examples/
  ✅ output/

🖼️ Imagen de referencia:
  ❌ data/ref/nopal_ref.jpg falta - coloca tu imagen

📦 Dependencias:
  ✅ OpenCV 4.9.0
  ✅ NumPy 1.26.4
```

## 🎯 Imagen de referencia

**⚠️ OBLIGATORIO:** El proyecto necesita una imagen del nopal que quieres detectar.

### **Dónde colocarla:**
```
data/ref/nopal_ref.jpg
```

### **Consejos para mejor detección:**
- **Resolución:** Mínimo 640x480
- **Iluminación:** Uniforme y clara  
- **Enfoque:** Nítido y bien definido
- **Contenido:** Solo la parte distintiva del nopal
- **Fondo:** Simple, sin distracciones
- **Formatos:** JPG, PNG, BMP, TIFF

## 🛠️ Parámetros avanzados

```bash
python manage.py run \
  --source 0 \
  --save output/deteccion.mp4 \
  --min_matches 15 \
  --ratio 0.8
```

**Parámetros disponibles:**
- `--source`: Fuente de entrada
  - `0, 1, 2...` para cámaras
  - `ruta/imagen.jpg` para imágenes
  - `ruta/video.mp4` para videos
- `--save`: Archivo de salida (opcional)
- `--min_matches`: Mínimo coincidencias válidas (default: 18)
- `--ratio`: Filtro ratio test de Lowe (default: 0.75)

## 📋 Requisitos del sistema

**Mínimos:**
- **Python 3.7+** (recomendado 3.10+)
- **1GB RAM libre**
- **500MB espacio en disco**

**Para mejor rendimiento:**
- **Cámara web** (detección en tiempo real)
- **GPU** (acelera OpenCV si está disponible)
- **ffmpeg** (mejor soporte de video)

**Instalación de ffmpeg (opcional):**
```bash
# Windows (con chocolatey)
choco install ffmpeg

# macOS (con homebrew)  
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt update && sudo apt install ffmpeg
```

## 🐛 Solución de problemas

### **❌ "Python 3 no encontrado"**
```bash
# Instalar Python 3
# Windows: https://python.org/downloads/
# macOS: brew install python3  
# Linux: sudo apt install python3 python3-venv
```

### **❌ "Entorno virtual no existe"**
```bash
python manage.py setup
```

### **❌ "Imagen de referencia no encontrada"**
```bash
# 1. Verificar estructura
python manage.py folders

# 2. Colocar imagen en: data/ref/nopal_ref.jpg
# 3. Verificar
python manage.py status
```

### **❌ "Muy pocos puntos clave"**
- Mejora la calidad de la imagen de referencia
- Usa mejor iluminación y enfoque
- Recorta solo la parte distintiva
- Prueba con diferentes ángulos

### **❌ "No se puede abrir la cámara"**
```bash
# Probar diferentes índices
python manage.py run --source 1
python manage.py run --source 2

# Verificar permisos de cámara en tu sistema
```

### **❌ "Dependencias faltan"**
```bash
# Reinstalar todo
python manage.py clean
python manage.py install
```

### **❌ "Errores en Linux"**
```bash
# Instalar librerías del sistema
sudo apt update
sudo apt install -y python3-venv python3-dev
sudo apt install -y libgl1 libglib2.0-0 libgtk-3-0
```

## 🧠 Cómo funciona

### **Algoritmo de detección:**

1. **Extracción ORB** - Encuentra puntos únicos en la imagen de referencia
2. **Matching** - Compara características entre referencia y entrada  
3. **Homografía** - Calcula transformación geométrica con RANSAC
4. **Proyección** - Dibuja contorno del objeto detectado

### **Flujo de ejecución:**
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Imagen    │ -> │  Extracción  │ -> │  Matching   │
│ Referencia  │    │     ORB      │    │ Bilateral   │
└─────────────┘    └──────────────┘    └─────────────┘
                                              │
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ Detección   │ <- │ Proyección   │ <- │ Homografía  │
│   Final     │    │  Contorno    │    │   RANSAC    │
└─────────────┘    └──────────────┘    └─────────────┘
```

## 📊 Controles durante ejecución

**Modos de operación:**
- **Cámara/Video**: Presiona `q` para salir
- **Imagen**: Presiona cualquier tecla o cierra ventana
- **Batch**: Se guarda automáticamente si usas `--save`

**Información en pantalla:**
- **Matches: X**: Número de características coincidentes
- **Rectángulo verde**: Detección confirmada (≥18 matches)
- **"NOPAL ESPECIFICO"**: Etiqueta cuando detecta
- **"Sin homografía"**: Detección débil (<18 matches)

## 🔄 Modo desarrollo

Para desarrolladores que quieren modificar el código:

```bash
# Usar el script original (auto-setup incluido)
python nopal_all_in_one.py --help
python nopal_all_in_one.py --source 0 --ref data/ref/nopal_ref.jpg

# O usar el gestor para desarrollo  
python manage.py run --source examples/test.jpg
```

---
## 🎨 Referencia artística

Este proyecto toma **referencias cromáticas y compositivas** de la obra de  
**Gabriela Sandoval Hernández** — [gabrielasandoval.art](https://gabrielasandoval.art/).

> **Nota ética:** El objetivo es explorar el cruce entre arte y tecnología con
> inspiración visual (paletas, ritmo, repetición y contraste), **sin reproducir ni
> imitar directamente el “estilo de” una artista**. Las imágenes generadas por el
> sistema son originales y no intentan suplantar autoría.

### Pautas de inspiración responsable
- Usa **paletas vibrantes** y **repetición modular** (series de nopales) para un
  efecto gráfico contemporáneo.
- Evita prompts o descripciones del tipo *“al estilo de [artista]”*.  
- Cita la referencia cuando corresponda y enlaza a la página oficial.

### Paletas sugeridas (sin copiar obras)
- **Vibrante México**: `#1E8F3B` (verde nopal), `#82D736` (verde claro),
  `#F4EA2A` (amarillo lima), `#E21E79` (magenta), `#3FA9F5` (azul medio), `#FFFFFF` (fondo).
- **Alta saturación suave**: `#2AA14A`, `#9BE24B`, `#FFD93B`, `#E84590`, `#67B6FF`.

> Consejo visual: alterna nopales cromáticos con nopales naturales para crear
> capas de contraste (natural ↔ cromático) y mantener un **ritmo** visual sin
> replicar composiciones específicas.

### Créditos
- **Investigación y desarrollo**: Gabriela Sandoval Hernández - Carlos Armando Boyzo Oregon  
- **Referencia artística**: Gabriela Sandoval Hernández — [gabrielasandoval.art](https://gabrielasandoval.art/)

## 📞 Información

**Desarrollado por:** Carlos Armando Boyzo Oregon  
**Tecnologías:** Python, OpenCV, NumPy, ORB, Homografía  
**Licencia:** Proyecto de detección con computer vision

---  

**💡 Tip:** Siempre ejecuta `python manage.py status` para ver qué necesita el proyecto.



