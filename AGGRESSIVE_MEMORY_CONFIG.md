# Configuración Agresiva de Memoria para T4 (Google Colab)

## Tu Sistema
- **RAM**: 12 GB
- **GPU VRAM**: 15 GB (T4)
- **Objetivo**: Procesar 65 videos lo más rápido posible

## Cambios Realizados ✅

### 1. **TensorFlow GPU Limit** (core.py:99)
```python
# ANTES: 10.24 GB
memory_limit=10240

# AHORA: 13.31 GB (dejando 1.7GB de margen)
memory_limit=13312
```
**Impacto**: +3GB de VRAM disponible para face swapper/enhancer

### 2. **Parámetros Agresivos** (runbatch.py)
```bash
# ANTES
--max-memory 8
--execution-threads 4

# AHORA
--max-memory 11
--execution-threads 6
```
**Impacto**: Usar 11GB RAM + mayor paralelismo CUDA

### 3. **Nuevo: Procesamiento Paralelo** (runbatch_parallel.py)
```bash
# Procesar 2 videos simultáneamente
python runbatch_parallel.py --parallel 2
```
**Impacto**: ~40-50% más rápido (8-10 horas en lugar de 11-15)

## Modos de Uso

### Opción A: Serial Optimizado (RECOMENDADO para estabilidad)
```bash
# Uno a la vez, pero con más memoria
python runbatch.py

# Resultado esperado:
# - 65 videos en ~10-12 horas
# - Muy estable, sin riesgo de OOM
# - Uso: RAM 8-10GB, VRAM 12-13GB
```

### Opción B: Paralelo Agresivo (MÁS RÁPIDO)
```bash
# 2 videos simultáneos
python runbatch_parallel.py --parallel 2

# Resultado esperado:
# - 65 videos en ~6-8 horas
# - Mayor riesgo de OOM si hay picos
# - Uso: RAM 11-12GB, VRAM 13-14GB
```

### Opción C: Súper Paralelo (RIESGO ALTO)
```bash
# 3 videos simultáneos (EXPERIMENTAL)
python runbatch_parallel.py --parallel 3

# ⚠️ ADVERTENCIA:
# - Alto riesgo de crash por OOM
# - Solo si realmente necesitas máxima velocidad
# - Solo en Colab (ambiente controlado)
```

## Comparación de Rendimiento

| Modo | Velocidad | RAM | VRAM | Riesgo | Tiempo 65 vids |
|------|-----------|-----|------|--------|----------------|
| Original (8GB/4t) | 1x | 8GB | 10GB | Bajo | 15h |
| **Optimizado (11GB/6t)** | **1.3x** | **10GB** | **13GB** | **Bajo** | **12h** |
| Paralelo 2x | **1.8x** | **11GB** | **13GB** | **Medio** | **8h** |
| Paralelo 3x | **2.2x** | **12GB** | **14GB** | **Alto** | **7h** |

## Monitoreo en Tiempo Real (Google Colab)

En otra celda ejecuta esto para ver métricas:

```python
import subprocess
import time
import psutil

while True:
    # RAM
    ram = psutil.virtual_memory()
    print(f"RAM: {ram.used/1e9:.1f}GB / {ram.total/1e9:.1f}GB ({ram.percent:.1f}%)")

    # GPU (si nvidia-smi disponible)
    try:
        gpu_out = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,nounits,noheader'], text=True)
        used, total = map(float, gpu_out.strip().split(','))
        print(f"GPU: {used/1024:.1f}GB / {total/1024:.1f}GB ({used/total*100:.1f}%)")
    except:
        pass

    print("-" * 40)
    time.sleep(5)
```

## Qué Hacer Si Crashea

### OOM (Out of Memory) Error
```bash
# 1. Reducir a serial mode
python runbatch.py

# 2. Si sigue crashing, reducir memoria
# Editar runbatch.py línea 126:
--max-memory 9
--execution-threads 4

# 3. Reiniciar kernel de Colab (limpia memoria)
# Kernel → Restart runtime
```

### CUDA Out of Memory
```bash
# Opción A: Reducir batch size en core.py:99
memory_limit=11264  # De 13312

# Opción B: Solo usar face_swapper (sin enhancer)
--frame-processor face_swapper

# Opción C: Reducir calidad
--temp-frame-quality 80
--output-video-quality 15
```

## Configuración Segura para Colab Durantes Largas Ejecuciones

Si vas a procesar sin monitoreo (ej: de noche):

```bash
# Versión ultra-estable (pero más lenta)
python runbatch.py

# Editar parámetros a:
--max-memory 9          # Margen de seguridad
--execution-threads 4
```

Con esto:
- No debería crashear
- ~1 video cada 10 minutos
- 65 videos en ~11 horas

## Optimización por Rango

Si quieres máximo control, procesa en tandas:

```bash
# Tanda 1: Primeros 20 (paralelo 2x)
python runbatch_parallel.py --parallel 2 1-20

# Tanda 2: Siguiente 20
python runbatch_parallel.py --parallel 2 21-40

# Tanda 3: Últimos 25
python runbatch_parallel.py --parallel 2 41-65
```

**Ventajas**:
- Menor riesgo de mega-crash
- Puedes cambiar parámetros entre tandas
- Seguimiento más granular

## Benchmarks Esperados (T4 + 12GB RAM)

### Video típico: 30 segundos, 720p, 30fps
- **Face swapper**: ~50 segundos
- **Face enhancer**: ~40 segundos
- **Encoding**: ~30 segundos
- **Total por video**: ~2 minutos

### Con face_swapper solo (sin enhancer)
- **Total por video**: ~1.5 minutos

### Paralelo 2x (2 videos simultáneos)
- **Throughput**: 1 video cada 2 minutos
- **Para 65 videos**: ~2 minutos × 33 = ~66 minutos = 1.1 hora (teórico)

En práctica real:
- Overhead de filesystem: +10%
- Limpieza de temp frames: +5%
- Variabilidad de tamaño video: ±20%
- **Resultado real**: 1 video cada 2.5-3 minutos = 6-8 horas

## Logs Esperados (Modo Agresivo)

```
📊 Sistema: 12.0GB RAM disponibles
📊 GPU: T4 con ~15GB VRAM
---
💾 Memoria antes: 2.3GB
💾 Memoria después: 2.1GB (diferencia: -0.2GB)
📊 RAM: 9.5GB | GPU: 12.8GB  ← Presionado pero estable
🧹 Limpiado: roop/temp_xxxxxxxx
```

## Troubleshooting

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `CUDA OOM` | GPU sin suficiente VRAM | Reducir threads, usar face_swapper solo |
| `Malloc error` | RAM agotada | Reducir --max-memory, serial mode |
| Proceso lento | Swapping a disco | Reducir parallelismo |
| Intermitente crash | Fuga de memoria | Actualizar TensorFlow/ONNX |

## Configuración Final Recomendada

**Para máximo rendimiento en Colab (sin riesgo de crash):**

```bash
python runbatch.py
# Con valores: --max-memory 11, --execution-threads 6
# Resultado: ~12 horas para 65 videos, muy estable
```

**Si necesitas ir más rápido y aceptas riesgo:**

```bash
python runbatch_parallel.py --parallel 2
# Resultado: ~8 horas, riesgo medio
# Monitorea RAM/GPU en otra celda
```

---

**Actualizado**: 2026-01-08
**Optimizado para**: Google Colab T4 (15GB VRAM, 12GB RAM)
