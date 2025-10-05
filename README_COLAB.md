# 🎭 Roop Batch Processor - Google Colab

Procesamiento por lotes optimizado para face swap en Google Colab con Tesla T4.

## 🚀 Inicio Rápido (3 Pasos)

### Opción 1: Usando el Notebook Optimizado (RECOMENDADO)

1. **Abre el notebook en Colab**:
   - [RoopConClaude_Optimized.ipynb](https://colab.research.google.com/github/CDavidDv/RoopConClaude/blob/main/RoopConClaude_Optimized.ipynb)

2. **Ejecuta las celdas en orden**:
   - ✅ Setup (solo una vez)
   - 📤 Subir imagen de referencia
   - 📤 Subir videos a procesar
   - 🎯 Ejecutar procesamiento
   - 💾 Descargar resultados

3. **¡Listo!** Descarga tus videos procesados

---

### Opción 2: Manual (Comandos Directos)

```python
# 1. Clonar repositorio
!git clone https://github.com/CDavidDv/RoopConClaude.git
%cd RoopConClaude

# 2. Setup optimizado (solo una vez)
!bash setup_optimized.sh

# 3. Subir archivos (usar el panel de archivos de Colab)
# - Imagen de referencia → source/
# - Videos a procesar → inputVideos/

# 4. Procesar
!python runbatch.py

# 5. Descargar resultados
from google.colab import files
import glob
for video in glob.glob('outputVideos/*.mp4'):
    files.download(video)
```

## 📋 Estructura del Proyecto

```
RoopConClaude/
├── source/              # Tu imagen de referencia (la cara fuente)
├── inputVideos/         # Videos a procesar
├── outputVideos/        # Videos procesados (resultados)
├── runbatch.py          # Script de procesamiento por lotes
├── check_videos.py      # Verificador de videos
├── debug_single.py      # Diagnóstico de problemas
└── setup_optimized.sh   # Setup automatizado
```

## ⚙️ Configuración por Defecto

El procesamiento está optimizado para Tesla T4 con estos parámetros:

- **Procesador**: `face_swapper` (cambio de caras)
- **Aceleración**: CUDA (si está disponible)
- **Memoria máxima**: 12 GB
- **Threads**: 4 (óptimo para T4)
- **FPS**: Mantiene el FPS original
- **Calidad de frames**: 95%
- **Calidad de video**: 85%
- **Detección**: `--many-faces` activado

## 🎯 Nombrado de Archivos

Los videos procesados se nombran automáticamente:

```
Entrada:  source/DanielaAS.jpg + inputVideos/24.mp4
Salida:   outputVideos/DanielaAS_24.mp4
```

## 🔧 Herramientas de Diagnóstico

### Verificar Videos Antes de Procesar

```python
!python check_videos.py
```

Esto verifica:
- ✅ Videos válidos y procesables
- ❌ Videos corruptos o demasiado pequeños
- 📊 Duración, resolución y tamaño

### Diagnosticar Problemas

```python
!python debug_single.py
```

Ejecuta tests para identificar problemas con:
- Formato de video
- Memoria disponible
- Configuración de CUDA
- Codecs de video

## 📝 Requisitos de Videos

Para mejores resultados, tus videos deben:

- ✅ Ser archivos válidos (MP4, AVI, MOV, MKV)
- ✅ Tener al menos 1 segundo de duración
- ✅ Tamaño mayor a 100 KB
- ✅ Resolución mínima: 100x100 px
- ✅ Contener al menos 10 frames
- ✅ Tener una cara visible y clara

## 🚨 Solución de Problemas

### Videos no se procesan

```python
# 1. Verifica los videos
!python check_videos.py

# 2. Verifica CUDA
!python -c "import onnxruntime as ort; print(ort.get_available_providers())"

# 3. Ejecuta diagnóstico completo
!python debug_single.py
```

### Videos muy pequeños (< 1 MB)

Probablemente están corruptos. Re-súbelos o verifica el formato.

### Sin archivos en outputVideos/

```python
# Busca archivos en otras ubicaciones
!find . -name "*DanielaAS*" -type f

# Verifica espacio en disco
!df -h
```

### Procesamiento muy lento

- Verifica que CUDA esté habilitado
- Asegúrate de usar GPU T4 en Colab (Runtime → Change runtime type → GPU)
- Reduce la calidad temporalmente: edita `runbatch.py` líneas 87-89

## 🔄 Actualizar el Repositorio

```python
%cd RoopConClaude
!git pull
```

## 📊 Rendimiento Esperado

En Tesla T4 (Google Colab):

- Video 720p, 10 segundos: ~30-60 segundos
- Video 1080p, 30 segundos: ~2-4 minutos
- Video 1080p, 60 segundos: ~4-8 minutos

*Tiempos aproximados, varían según complejidad de la escena*

## 🆘 Soporte

Si encuentras problemas:

1. Ejecuta `!python debug_single.py`
2. Ejecuta `!python check_videos.py`
3. Verifica que tus videos sean válidos
4. Asegúrate de estar usando GPU en Colab

## 📄 Licencia

Este proyecto usa modelos y bibliotecas de terceros. Consulta sus licencias individuales.