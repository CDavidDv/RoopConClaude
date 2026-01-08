# Guía de Optimización de Memoria para Roop Batch Processing

## Limitaciones Actuales

### TensorFlow GPU
- **Límite de VRAM**: 10.24 GB (configurado en `core.py:99`)
- **Proveedor**: CUDA/TensorRT
- **Consumo por video**: 2-3 GB según tamaño/complejidad

### RAM del Sistema
- **Límite configurable**: `--max-memory` (ahora 8GB en batch)
- **Consumo base**: ~1-2 GB por proceso
- **Riesgo con 65 videos**: Filtraciones de memoria acumulativas

## Parámetros Clave en `runbatch.py`

```bash
--max-memory 8                # 8GB límite de RAM
--execution-threads 4         # 4 threads CUDA (T4: máximo 4)
--temp-frame-format png       # PNG sin compresión (usa más espacio)
--temp-frame-quality 100      # 100% calidad
```

## Optimizaciones Implementadas

### 1. **Monitoreo de Memoria en Tiempo Real**
```python
current_mem = get_system_memory_usage()  # GB
mem_percent = (current_mem / total_mem) * 100
```
- Muestra uso actual antes y después de cada video
- Alerta si supera 85% de memoria

### 2. **Limpieza Automática de Frames Temporales**
```python
clean_temp_frames()  # Borra carpetas roop/temp*
```
- Se ejecuta después de cada video exitoso
- También en caso de error/interrupción
- Libera 500MB-2GB por video

### 3. **Pausa Inteligente**
```python
wait_for_memory(target_gb=total_mem * 0.5)  # Espera a 50%
```
- Si memoria > 85%, espera hasta bajar a 50%
- Timeout de 2 minutos (configurable)
- Registra advertencias

### 4. **Estadísticas Finales**
- Total de archivos generados
- Tamaño total en disco
- Tasa de éxito/fallo
- Warnings de memoria

## Recomendaciones por Escenario

### Escenario A: Máximo Rendimiento (T4 GPU con 16GB RAM)
```bash
python runbatch.py
# Ya optimizado en el código actual
```
**Resultado esperado**: ~7-10 min por video, 65 videos en 8-11 horas

### Escenario B: Máxima Estabilidad (Memory Leak Protection)
```bash
# Editar runbatch.py línea 85:
--max-memory 4                # Reducir a 4GB
--execution-threads 2         # Reducir threads
```
**Resultado**: Más lento pero muy estable, ideal para 65+ videos

### Escenario C: Mejor Calidad en Disco (Menos videos/batch)
```bash
python runbatch.py 1-30       # Procesar en lotes de 30
# Esperar entre lotes
python runbatch.py 31-60
```
**Resultado**: Menor riesgo de crash, mejor limpieza de memoria

## Causas Comunes de Memory Leaks

1. **Frames temporales no borrados** → Ocupan 50-100MB c/u
2. **Modelos ONNX sin descargar** → 200-500MB por modelo
3. **Variables de TensorFlow en GPU** → Acumulación gradual
4. **Subprocesos de ffmpeg** → Pueden dejar memoria reservada

## Monitoreo Manual

### En otra terminal mientras procesa:
```bash
# Linux/Mac
watch -n 1 'ps aux | grep python | grep roop'
free -h

# Windows
tasklist /FI "IMAGENAME eq python.exe"  # Cada 5 segundos
```

### Ver memoria de GPU:
```bash
nvidia-smi -l 1  # Cada 1 segundo
```

## Si se Queda Sin Memoria

### Acción Inmediata:
1. Cancelar procesamiento (Ctrl+C)
2. Limpiar temp: `rmdir /s roop\temp*` (Windows)
3. Esperar 30 segundos a liberación
4. Reintentar video anterior

### Análisis Post-Mortem:
```bash
# Ver cuánto espacio ocupan videos parciales
du -sh outputVideos/*
# Los incompletos pueden borrarse sin afectar completados
```

## Fórmula de Cálculo Seguro

```
Memoria segura = (RAM Total - 2GB) / (Consumo por video)
Máximo videos simultáneos = (RAM Total - 2GB) / 2.5GB

Ejemplo: 16GB RAM
Máximo = (16 - 2) / 2.5 = 5.6 videos simultáneos
```

## Parámetros Alternativos de Calidad

Si necesitas reducir carga:

```bash
# Menor calidad de frames (usa menos RAM)
--temp-frame-format jpg       # JPG con compresión
--temp-frame-quality 75       # Baja a 75%

# Encoder más rápido
--output-video-encoder libx264  # CPU fallback
--output-video-quality 25       # Baja a 25% (más comprimido)

# Frames processor más ligero
--frame-processor face_swapper  # Sin enhancer (ahorra 0.5GB)
```

## Logs Útiles

El script ahora muestra:
```
📊 Memoria antes: 2.3GB
📊 Memoria después: 2.1GB (diferencia: -0.2GB)
💾 Memoria actual: 8.5GB / 16.0GB (53.1%)
⚠️ Memoria alta (89.2%). Esperando antes de continuar...
```

## Próximas Mejoras Sugeridas

1. **Implementar garbage collection forzado**
   ```python
   import gc
   gc.collect()  # Entre videos
   ```

2. **Usar streaming en lugar de buffering completo**
   - Roop ya lo hace por frames, pero ffmpeg podría optimizarse

3. **Procesamiento por chunks de frames**
   - En lugar de toda la secuencia, procesar N frames a la vez

4. **Background cleanup thread**
   - Liberar memoria mientras se procesa siguiente video

## Soporte y Debugging

Si tienes issues:
1. Verifica `nvidia-smi` que VRAM esté disponible
2. Revisa si hay procesos Python legacy: `tasklist | find "python"`
3. Intenta con `--max-memory 4` para aislar el problema
4. Mira logs en stdout del procesamiento

---

**Última actualización**: 2026-01-08
**Script**: runbatch.py (versión mejorada con monitoreo)
