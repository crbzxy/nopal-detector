# 🚀 Quick Start - Nopal Detector

## 3 Comandos para empezar

```bash
# 1. Instalar todo desde cero
python manage.py install

# 2. Ver estado
python manage.py status

# 3. Ejecutar (necesita imagen en data/ref/nopal_ref.jpg)
python manage.py run
```

## 🎯 Comandos más usados

```bash
python manage.py install        # 🎯 TODO en uno
python manage.py status         # 📊 Ver qué falta
python manage.py run            # 🚀 Ejecutar detector
python manage.py run-camera     # 📷 Cámara + guardar
python manage.py clean          # 🧹 Limpieza estándar
python manage.py deep-clean     # 🧹 Limpieza profunda
```

## 📂 Archivos importantes

- `data/ref/nopal_ref.jpg` ← **¡OBLIGATORIO!**
- `examples/` ← Tus imágenes/videos de prueba
- `output/` ← Resultados generados

## ⚡ Solución rápida de problemas

```bash
# ❌ "Entorno virtual no existe"
python manage.py setup

# ❌ "Dependencias faltan"  
python manage.py clean
python manage.py install

# ❌ "Imagen de referencia falta"
# → Colocar imagen en: data/ref/nopal_ref.jpg

# 🧹 Limpieza estándar (venv, cache, temporales)
python manage.py clean

# 🧹 Limpieza profunda (incluye logs, builds, outputs)
python manage.py deep-clean

# 💾 Limpieza profunda pero preservando resultados
python manage.py deep-clean --preserve-outputs

# 🧹 Empezar completamente limpio
python manage.py deep-clean
python manage.py install
```

---
💡 **Tip:** `python manage.py status` te dice exactamente qué necesitas