# Detector de Nopal v2.0 - Arquitectura Basada en Componentes

Una refactorización completa del detector de nopal utilizando OpenCV y algoritmos ORB, ahora con una arquitectura modular y escalable basada en componentes.

## 🆕 Novedades en v2.0

- **Arquitectura modular**: Separación clara de responsabilidades
- **Patrón Factory**: Para manejo de diferentes fuentes de entrada
- **Patrón Observer**: Para salidas flexibles (display, guardado, máscaras)
- **Configuración centralizada**: Usando dataclasses
- **Mejor manejo de errores**: Con logging estructurado
- **CLI mejorado**: Con validación de argumentos y ayuda detallada
- **Código testeable**: Estructura que facilita unit testing
- **Type hints**: Para mejor documentación y debugging

## 📁 Estructura del Proyecto

```
nopal-detector/
├── nopal_detector/                 # Paquete principal
│   ├── __init__.py
│   ├── config/                     # Configuración
│   │   ├── __init__.py
│   │   └── settings.py            # Configuración centralizada
│   ├── core/                      # Lógica principal
│   │   ├── __init__.py
│   │   └── detector.py            # Detector principal
│   ├── services/                  # Servicios especializados
│   │   ├── __init__.py
│   │   ├── detection.py           # Servicio OpenCV
│   │   ├── environment.py         # Gestión del entorno
│   │   ├── output.py              # Observers de salida
│   │   └── sources.py             # Factory de fuentes
│   ├── utils/                     # Utilidades
│   │   ├── __init__.py
│   │   ├── colors.py              # Manejo de colores
│   │   └── logging.py             # Sistema de logging
│   ├── cli/                       # Interfaz de línea de comandos
│   │   ├── __init__.py
│   │   └── main.py                # CLI principal
│   └── tests/                     # Tests (futuro)
│       └── __init__.py
├── main.py                        # Punto de entrada
├── setup.py                       # Configuración del paquete
├── requirements.txt               # Dependencias
├── data/                          # Datos de referencia
│   └── ref/
│       ├── nopal_ref.jpg
│       └── nopal_ref2.jpg
├── examples/                      # Ejemplos de entrada
│   ├── example.png
│   └── example2.png
└── output/                        # Salidas generadas
```

## 🚀 Instalación y Uso

### Uso Básico

```bash
# Detector con cámara
python main.py --source 0

# Detector con imagen
python main.py --source examples/example.png --output output/result.png

# Detector con video
python main.py --source video.mp4 --output output/result.mp4

# Detector con máscara (solo imágenes)
python main.py --source examples/example.png --mask output/mask.png
```

### Parámetros Avanzados

```bash
# Personalizar parámetros ORB
python main.py --source examples/example.png \
    --min-matches 15 \
    --ratio 0.8 \
    --orb-features 3000

# Personalizar visualización
python main.py --source 0 \
    --border-color "255,0,0" \
    --fill-color "0,0,255" \
    --fill-alpha 0.3

# Modo sin display (útil for scripts)
python main.py --source examples/example.png \
    --no-display \
    --output output/result.png

# Modo verbose para debugging
python main.py --source examples/example.png --verbose
```

### Ayuda Completa

```bash
python main.py --help
```

## 🏗️ Arquitectura

### Componentes Principales

1. **ApplicationConfig**: Configuración centralizada usando dataclasses
2. **NopalDetector**: Orquestador principal que coordina todos los servicios
3. **OpenCVService**: Lógica de detección ORB pura
4. **SourceManager**: Gestión uniforme de fuentes (imagen/video/cámara)
5. **OutputManager**: Sistema de observers para múltiples salidas
6. **EnvironmentService**: Gestión del entorno y dependencias

### Patrones de Diseño Utilizados

- **Factory Pattern**: `SourceFactory`, `OutputFactory`
- **Observer Pattern**: `OutputObserver` y subclases
- **Strategy Pattern**: Diferentes estrategias de fuente (imagen, video, cámara)
- **Dependency Injection**: Configuración inyectada en servicios
- **Single Responsibility**: Cada clase tiene una responsabilidad específica

### Ventajas de la Nueva Arquitectura

1. **Modularidad**: Cada componente es independiente y reutilizable
2. **Testabilidad**: Fácil de mockear componentes para testing
3. **Extensibilidad**: Agregar nuevas fuentes o salidas es sencillo
4. **Mantenibilidad**: Código organizado y documentado
5. **Flexibilidad**: Configuración externa sin modificar código

## 🔧 Desarrollo

### Ejecutar Tests (Future)

```bash
python -m pytest nopal_detector/tests/
```

### Formateo de Código

```bash
# Instalar herramientas de desarrollo
pip install -e ".[dev]"

# Formatear código
black nopal_detector/
isort nopal_detector/

# Linting
flake8 nopal_detector/
mypy nopal_detector/
```

## 🆚 Comparación con v1.0

| Característica | v1.0 (Monolítico) | v2.0 (Componentes) |
|----------------|--------------------|--------------------|
| Líneas de código | ~600 en 1 archivo | ~1500 en múltiples archivos |
| Testabilidad | Difícil | Fácil |
| Mantenimiento | Complicado | Sencillo |
| Extensibilidad | Limitada | Alta |
| Separación de responsabilidades | No | Sí |
| Reutilización | Baja | Alta |
| Configuración | Hardcodeada | Centralizada |
| Logging | Básico | Estructurado |
| Error handling | Limitado | Robusto |

## 📚 Ejemplos de Uso Programático

```python
from nopal_detector.config.settings import ApplicationConfig
from nopal_detector.core.detector import NopalDetector

# Crear detector con configuración por defecto
config = ApplicationConfig.create_default()
detector = NopalDetector(config)

# Detectar desde imagen
success = detector.detect_from_source(
    source_path="examples/example.png",
    reference_path="data/ref/nopal_ref.jpg",
    output_path="output/result.png",
    show_display=False
)

# Personalizar parámetros ORB
custom_orb = {
    'min_matches': 20,
    'ratio_threshold': 0.8
}

custom_drawing = {
    'border_color': (255, 0, 0),  # Rojo
    'fill_alpha': 0.4
}

success = detector.detect_from_source(
    source_path="0",  # Cámara
    reference_path="data/ref/nopal_ref.jpg",
    custom_orb_params=custom_orb,
    custom_drawing_params=custom_drawing
)
```

## 🤝 Contribuir

1. Fork del repositorio
2. Crear rama para feature (`git checkout -b feature/nueva-feature`)
3. Commit cambios (`git commit -am 'Agregar nueva feature'`)
4. Push a la rama (`git push origin feature/nueva-feature`)
5. Crear Pull Request

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

## 👨‍💻 Autor

**Carlos Armando Boyzo Oregon**  
---

## 🚀 Migración desde v1.0

Si estás usando la versión monolítica (v1.0), la migración es transparente:

```bash
# v1.0
python nopal_all_in_one.py --source examples/example.png --ref data/ref/nopal_ref.jpg

# v2.0 (equivalente)
python main.py --source examples/example.png --reference data/ref/nopal_ref.jpg
```

Los parámetros principales son compatibles, con mejoras en nombres más descriptivos y validación de entrada.