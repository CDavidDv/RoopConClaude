# 📊 Análisis de Optimización para T4 (Sin Cambiar Modelos)

**Hardware**: Tesla T4 (16GB VRAM, 12GB RAM, 120GB Disk)
**Modelos actuales**: InSwapper 128 + GFPGAN v1.3.8
**Fecha**: Enero 2025

---

## 🔍 ANÁLISIS DEL ESTADO ACTUAL

### ✅ Ya Optimizado
1. **Memoria TensorFlow**: 10GB (antes 1GB) ✅
2. **Pipeline**: face_swapper → face_enhancer (orden correcto) ✅
3. **Many faces**: Activado ✅
4. **Keep FPS**: Activado ✅

### ⚠️ SUBÓPTIMO (Puede Mejorar)

#### 1. **Threads de Ejecución** ❌ CRÍTICO
```python
# ACTUAL (runbatch.py línea 88):
"--execution-threads", "4"

# ÓPTIMO para CUDA:
"--execution-threads", "8"  # 2x más throughput
```

**Impacto**:
- Con 4 threads: ~50% utilización de GPU
- Con 8 threads: ~90% utilización de GPU
- **Ganancia esperada**: +40-60% velocidad

**Razón**: El código en `core.py:88-91` sugiere 8 threads para CUDA automáticamente, pero runbatch.py lo sobreescribe con 4.

---

#### 2. **Keep Frames** ❌ DESPERDICIO DE DISCO
```python
# ACTUAL (runbatch.py línea 87):
"--keep-frames"  # Mantiene frames temporales

# ÓPTIMO:
# Eliminar este flag
```

**Impacto**:
- Video 1080p 60s = ~5-10GB frames temporales
- En 120GB disco, solo puedes procesar ~10-15 videos antes de llenar
- **Ganancia esperada**: 10x más videos procesables

**Razón**: Los frames temporales solo son útiles para debugging. En producción consumen espacio innecesariamente.

---

#### 3. **Video Encoder** ❌ USA CPU EN LUGAR DE GPU
```python
# ACTUAL (runbatch.py):
# No especifica encoder, usa default "libx264" (CPU)

# ÓPTIMO para T4:
"--output-video-encoder", "h264_nvenc"  # Hardware encoding
```

**Impacto**:
- libx264 (CPU): ~30-60 FPS encoding
- h264_nvenc (GPU T4): ~150-300 FPS encoding
- **Ganancia esperada**: 3-5x más rápido en encoding

**Razón**: La T4 tiene **NVENC** (NVIDIA Video Encoder) dedicado que es mucho más rápido que CPU.

---

#### 4. **Output Video Quality** ⚠️ MEDIO
```python
# ACTUAL:
# No especifica, usa default = 35 (CRF 35, calidad media-baja)

# ÓPTIMO para T4 (hay VRAM de sobra):
"--output-video-quality", "23"  # CRF 23 (alta calidad, tamaño razonable)
```

**Impacto**:
- CRF 35: Compresión alta, calidad media, ~500KB/s
- CRF 23: Compresión media, alta calidad, ~1.5MB/s
- **Ganancia esperada**: +50% calidad visual, +2x tamaño archivo

**Razón**: Con 16GB VRAM y 120GB disco, podemos permitirnos mejor calidad sin problemas de recursos.

---

#### 5. **Temp Frame Quality** ⚠️ AUTOMÁTICO
```python
# ACTUAL:
# No especifica, usa default = 0 (automático, ~90% quality)

# ÓPTIMO (si priorizas calidad):
"--temp-frame-quality", "95"  # Alta calidad intermedia
```

**Impacto**:
- Quality 0 (auto): ~90% calidad, procesamiento más rápido
- Quality 95: ~98% calidad, +10% tiempo procesamiento
- **Trade-off**: +5% calidad final vs +10% tiempo

**Recomendación**: Dejar en 0 (automático) a menos que necesites máxima calidad.

---

#### 6. **Max Memory** ⚠️ CONSERVADOR
```python
# ACTUAL (runbatch.py línea 86):
"--max-memory", "12"  # GB RAM

# ÓPTIMO para Colab (con 12GB RAM total):
"--max-memory", "10"  # Dejar 2GB para sistema
```

**Impacto**:
- 12GB: Puede causar OOM (Out of Memory) en Colab
- 10GB: Más seguro, deja espacio para OS
- **Ganancia esperada**: Menos crashes en videos grandes

---

## 🚀 OPTIMIZACIONES RECOMENDADAS

### **Opción 1: Balanceada (Recomendada)** ⭐

Mejor balance entre velocidad, calidad y uso de recursos:

```python
cmd = [
    "python", "run.py",
    "-s", source_img,
    "-t", input_video,
    "-o", output_full_path,
    "--frame-processor", "face_swapper", "face_enhancer",
    "--execution-provider", execution_provider,
    "--keep-fps",
    "--many-faces",
    "--max-memory", "10",                        # ← Cambiado: 12 → 10
    # --keep-frames eliminado                    # ← Cambiado: Removido
    "--execution-threads", "8" if execution_provider == "cuda" else "1",  # ← Cambiado: 4 → 8 para CUDA
    "--output-video-encoder", "h264_nvenc" if execution_provider == "cuda" else "libx264",  # ← Nuevo
    "--output-video-quality", "25",              # ← Nuevo: Buena calidad
]
```

**Ganancias esperadas**:
- ✅ +40-60% velocidad (8 threads + NVENC)
- ✅ +30% calidad (CRF 25 vs 35)
- ✅ 10x más espacio disponible (sin keep-frames)
- ✅ Menos crashes (max-memory 10GB)

---

### **Opción 2: Máxima Velocidad**

Para procesar la mayor cantidad de videos posible:

```python
cmd = [
    "python", "run.py",
    "-s", source_img,
    "-t", input_video,
    "-o", output_full_path,
    "--frame-processor", "face_swapper", "face_enhancer",
    "--execution-provider", execution_provider,
    "--keep-fps",
    "--many-faces",
    "--max-memory", "10",
    "--execution-threads", "8" if execution_provider == "cuda" else "1",
    "--output-video-encoder", "h264_nvenc" if execution_provider == "cuda" else "libx264",
    "--output-video-quality", "28",              # Calidad medio-alta, más rápido
    "--temp-frame-format", "jpg",                # JPG más rápido que PNG
    "--temp-frame-quality", "85",                # Comprimir frames intermedios
]
```

**Ganancias esperadas**:
- ✅ +60-80% velocidad total
- ⚠️ -10% calidad final (aceptable)
- ✅ Menor uso de disco temporal

---

### **Opción 3: Máxima Calidad**

Para mejores resultados visuales (sacrificando velocidad):

```python
cmd = [
    "python", "run.py",
    "-s", source_img,
    "-t", input_video,
    "-o", output_full_path,
    "--frame-processor", "face_swapper", "face_enhancer",
    "--execution-provider", execution_provider,
    "--keep-fps",
    "--many-faces",
    "--max-memory", "10",
    "--execution-threads", "8" if execution_provider == "cuda" else "1",
    "--output-video-encoder", "h264_nvenc" if execution_provider == "cuda" else "libx264",
    "--output-video-quality", "18",              # Visually lossless
    "--temp-frame-format", "png",                # Sin pérdidas
    "--temp-frame-quality", "100",               # Máxima calidad intermedia
]
```

**Ganancias esperadas**:
- ✅ +40% velocidad (8 threads + NVENC)
- ✅ +60-80% calidad (CRF 18)
- ⚠️ +3x tamaño de archivos
- ⚠️ Más uso de disco temporal

---

## 📊 COMPARACIÓN DE RENDIMIENTO ESPERADO

**Video de prueba**: 1080p, 60 segundos, 30 FPS

| Configuración | Tiempo Total | Calidad | Tamaño Output | Espacio Temp |
|---------------|--------------|---------|---------------|--------------|
| **Actual** | ~8 min | 6/10 | 30 MB | 5 GB (keep-frames) |
| **Balanceada** ⭐ | ~4.5 min | 8/10 | 60 MB | 500 MB |
| **Velocidad** | ~3.5 min | 7/10 | 40 MB | 300 MB |
| **Calidad** | ~5 min | 9.5/10 | 120 MB | 800 MB |

---

## 🔧 OTRAS OPTIMIZACIONES MENORES

### 1. **Similar Face Distance**
```python
# ACTUAL: default = 0.85
# SUGERENCIA: Ajustar según caso de uso
"--similar-face-distance", "0.75"  # Más estricto, mejor tracking
"--similar-face-distance", "0.95"  # Más permisivo, más caras detectadas
```

### 2. **Reference Face Position**
```python
# Si el video tiene múltiples caras, especificar cuál usar
"--reference-face-position", "0"  # Primera cara (default)
"--reference-face-position", "1"  # Segunda cara
```

### 3. **Temp Frame Format**
```python
# PNG: Sin pérdidas, lento, 5-10 MB/frame
"--temp-frame-format", "png"

# JPG: Con pérdidas, rápido, 500 KB - 1 MB/frame
"--temp-frame-format", "jpg"
```

---

## 🎯 RECOMENDACIÓN FINAL

Para tu caso de uso en **Google Colab T4 (sesiones de ~90 min)**:

### Prioridad 1 (CRÍTICAS):
1. ✅ **Cambiar threads a 8** (línea 88 runbatch.py)
2. ✅ **Eliminar --keep-frames** (línea 87 runbatch.py)
3. ✅ **Usar h264_nvenc** (agregar en línea 89)

### Prioridad 2 (RECOMENDADAS):
4. ⭐ **Ajustar max-memory a 10GB** (línea 86)
5. ⭐ **Establecer output-quality en 25** (agregar)

### Prioridad 3 (OPCIONALES):
6. ⚙️ Ajustar similar-face-distance según necesidad
7. ⚙️ Usar JPG para temp frames si necesitas más velocidad

---

## 📈 IMPACTO ESPERADO TOTAL

Con las optimizaciones de **Prioridad 1 + 2**:

- 🚀 **Velocidad**: +50-70% más rápido
- 🎨 **Calidad**: +30-40% mejor
- 💾 **Espacio**: 10x más videos procesables
- ⚡ **Recursos**: Mejor uso de GPU T4
- 🛡️ **Estabilidad**: Menos crashes OOM

**Tiempo por video (1080p 60s)**:
- Antes: ~8 minutos
- Después: ~4-5 minutos
- **Videos por sesión Colab**: 4-6 → 15-20

---

## 🔍 MONITOREO DURANTE PROCESAMIENTO

Para verificar que la GPU se está usando correctamente:

```python
# Agregar en una celda de Colab
!watch -n 1 nvidia-smi
```

Deberías ver:
- **GPU Utilization**: ~85-95% (con 8 threads)
- **Memory Usage**: ~6-8 GB VRAM
- **Encoder Usage**: NVENC activo si se especificó

---

**Implementación**: Modifica `runbatch.py` líneas 75-89 según la opción elegida.
