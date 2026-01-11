# Guía de Deployment en Runpod

## Arquitectura

```
Tu Cliente (web/app)
        ↓ HTTP POST
   Runpod API
        ↓
   Runpod Endpoint (handler.py)
        ↓
   Roop Core (face swapping)
        ↓
   Output Video → S3/Cloudinary/tu storage
```

**NO necesitas hacer una API extra.** El `handler.py` YA es tu endpoint.

## ¿Qué es lo que tienes?

| Archivo | Propósito |
|---------|-----------|
| `handler.py` | Endpoint Runpod que recibe requests JSON |
| `Dockerfile` | Empaqueta todo para Runpod |
| `requirements.txt` | Dependencias Python |

## Flujo de Comunicación

### 1️⃣ Tú envías un JSON a Runpod:
```json
{
  "source_image_url": "https://ejemplo.com/cara.jpg",
  "target_video_url": "https://ejemplo.com/video.mp4",
  "output_filename": "resultado.mp4",
  "frame_processors": ["face_swapper", "face_enhancer"],
  "keep_fps": true,
  "execution_provider": "cuda"
}
```

### 2️⃣ Runpod ejecuta `handler(job)` en `handler.py`

### 3️⃣ handler.py retorna:
```json
{
  "status": "success",
  "output_path": "/tmp/xxxxx/resultado.mp4",
  "file_size": 52428800,
  "message": "Face swap completed successfully. Output size: 50.00 MB"
}
```

## Pasos de Deployment

### Opción A: Usar el Dockerfile existente

**Paso 1: Verificar Dockerfile**
```bash
# Ya existe, revisar que todo esté bien
cat Dockerfile
```

**Paso 2: Crear en Runpod**

En https://www.runpod.io/console:
1. Click en "Create New" → "Serverless Endpoint"
2. Selecciona GPU (RTX 3090, A100, etc)
3. En "Container Image" pega:
   ```
   ghcr.io/tu-usuario/roop:latest
   ```
   O sube el Dockerfile directamente

4. En "Input" Template, agrega este JSON de ejemplo:
   ```json
   {
     "source_image_url": "https://example.com/face.jpg",
     "target_video_url": "https://example.com/video.mp4",
     "output_filename": "output.mp4",
     "frame_processors": ["face_swapper"],
     "keep_fps": true,
     "execution_provider": "cuda"
   }
   ```

5. Click "Deploy"

### Opción B: Build y Push a Docker Hub

```bash
# 1. Login a Docker
docker login

# 2. Build image
docker build -t tu-usuario/roop:latest .

# 3. Push
docker push tu-usuario/roop:latest

# 4. En Runpod, usa: tu-usuario/roop:latest
```

## Cómo Hacer una Request (Cliente)

### Con Python:
```python
import requests
import json

# Tu endpoint de Runpod
RUNPOD_ENDPOINT = "https://api.runpod.io/v2/YOUR_ENDPOINT_ID/run"
RUNPOD_API_KEY = "tu_runpod_api_key"

payload = {
    "source_image_url": "https://ejemplo.com/cara.jpg",
    "target_video_url": "https://ejemplo.com/video.mp4",
    "output_filename": "resultado.mp4",
    "frame_processors": ["face_swapper", "face_enhancer"],
    "keep_fps": True,
    "execution_provider": "cuda"
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {RUNPOD_API_KEY}"
}

# Ejecutar
response = requests.post(RUNPOD_ENDPOINT, json=payload, headers=headers)
job_id = response.json()["id"]
print(f"Job started: {job_id}")

# Esperar resultado
import time
while True:
    status_response = requests.get(
        f"{RUNPOD_ENDPOINT}/{job_id}/status",
        headers=headers
    )
    status = status_response.json()

    if status["status"] == "COMPLETED":
        output = status["output"]
        print(f"✅ Completado!")
        print(f"Salida: {output['output_path']}")
        print(f"Tamaño: {output['file_size']} bytes")
        break
    elif status["status"] == "FAILED":
        print(f"❌ Error: {status['error']}")
        break
    else:
        print(f"⏳ Estado: {status['status']}")

    time.sleep(5)
```

### Con cURL:
```bash
# Ejecutar job
curl -X POST \
  https://api.runpod.io/v2/YOUR_ENDPOINT_ID/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "source_image_url": "https://ejemplo.com/cara.jpg",
    "target_video_url": "https://ejemplo.com/video.mp4",
    "output_filename": "resultado.mp4",
    "frame_processors": ["face_swapper", "face_enhancer"]
  }'

# Obtener resultado (con JOB_ID del response anterior)
curl https://api.runpod.io/v2/YOUR_ENDPOINT_ID/status/JOB_ID \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Errores Comunes y Soluciones

### Error 1: `ImportError: No module named 'roop'`
**Causa**: PYTHONPATH no incluye /app
**Solución**: Ya está configurado en handler.py línea 16:
```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

Si sigue fallando, agregar al Dockerfile:
```dockerfile
ENV PYTHONPATH=/app:$PYTHONPATH
```

### Error 2: `No module named 'runpod'`
**Causa**: runpod no instalado
**Solución**: Dockerfile línea 36 ya lo instala:
```dockerfile
RUN pip install --no-cache-dir runpod
```

Si necesitas otra versión:
```dockerfile
RUN pip install --no-cache-dir runpod==0.10.0
```

### Error 3: `ModuleNotFoundError: No module named 'onnx'`
**Causa**: requirements.txt incompleto
**Solución**: Asegurar que requirements.txt tenga todas las deps:
```
onnxruntime>=1.14.0
tensorflow>=2.10.0
insightface>=0.7.3
opencv-python>=4.7.0
```

### Error 4: `CUDA out of memory`
**Causa**: GPU sin suficiente memoria
**Solución**: En la request, bajar parámetros:
```json
{
  "max_memory": 8,
  "execution_threads": 2,
  "temp_frame_format": "jpg",
  "frame_processors": ["face_swapper"]
}
```

### Error 5: `handler.py: line X: not found` (en logs)
**Causa**: El handler no se ejecuta como Python
**Solución**: En Dockerfile, CMD debe ser:
```dockerfile
CMD ["python", "-u", "handler.py"]
```
NO:
```dockerfile
CMD ["./handler.py"]
```

### Error 6: `Runpod timeout (60 segundos)`
**Causa**: Procesamiento muy lento
**Solución**: Aumentar timeout en handler.py:
```python
response = requests.get(url, stream=True, timeout=600)  # 10 minutos
```

## Variables de Ambiente para Runpod

Agregar en Dockerfile o en Runpod UI:

```dockerfile
ENV CUDA_VISIBLE_DEVICES=0
ENV OMP_NUM_THREADS=1
ENV TF_CPP_MIN_LOG_LEVEL=2
```

## Monitoreo en Runpod

En el dashboard de Runpod puedes ver:
- Logs en tiempo real
- GPU/CPU usage
- Requests exitosos/fallidos
- Tiempo promedio de respuesta

Acciona a: https://www.runpod.io/console/endpoints

## Optimización para Runpod

### Para velocidad máxima (A100/RTX 3090):
```json
{
  "max_memory": 20,
  "execution_threads": 8,
  "output_video_quality": 18,
  "frame_processors": ["face_swapper", "face_enhancer"]
}
```

### Para estabilidad (RTX 3080/A40):
```json
{
  "max_memory": 12,
  "execution_threads": 4,
  "output_video_quality": 20,
  "frame_processors": ["face_swapper"]
}
```

### Para GPU pequeña (RTX 2080/V100):
```json
{
  "max_memory": 8,
  "execution_threads": 2,
  "output_video_quality": 25,
  "temp_frame_format": "jpg",
  "frame_processors": ["face_swapper"]
}
```

## Almacenamiento de Output

Opciones para guardar la salida:

### Opción 1: Retornar URL presignada (S3/GCS)
```python
# En handler.py, después de procesar:
import boto3
s3 = boto3.client('s3')
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'mi-bucket', 'Key': output_path},
    ExpiresIn=3600
)
return {"status": "success", "download_url": url}
```

### Opción 2: Usar Runpod Volume
```json
{
  "output_directory": "/runpod/output",
  "output_filename": "resultado.mp4"
}
```

### Opción 3: Upload a Cloudinary
```python
# En handler.py:
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name="tu_cloud",
    api_key="key",
    api_secret="secret"
)

result = cloudinary.uploader.upload_video(output_path)
return {"status": "success", "cloudinary_url": result['url']}
```

## Testing Local

Prueba el handler localmente antes de hacer deploy:

```bash
# 1. Instalar runpod localmente
pip install runpod

# 2. Ejecutar handler
python handler.py

# 3. En otra terminal, hacer request
python test_request.py
```

Contenido de `test_request.py`:
```python
import requests

job = {
    "input": {
        "source_image_path": "./source/face.jpg",
        "target_video_path": "./input/video.mp4",
        "output_filename": "test_output.mp4",
        "frame_processors": ["face_swapper"],
        "execution_provider": "cuda"
    }
}

# Llamar handler directamente (local testing)
from handler import handler
result = handler(job)
print(result)
```

## Checklist de Deployment

- [ ] `requirements.txt` tiene todas las deps
- [ ] `handler.py` importa correctamente `roop.core`
- [ ] `Dockerfile` instala `runpod`
- [ ] `Dockerfile` CMD es: `["python", "-u", "handler.py"]`
- [ ] PYTHONPATH incluye `/app`
- [ ] Variables de env configuradas (CUDA_VISIBLE_DEVICES, etc)
- [ ] GPU disponible en Runpod (verificar tipo de máquina)
- [ ] Test local funciona
- [ ] Endpoint creado en Runpod
- [ ] API key guardada segura

## Links Útiles

- Docs Runpod Serverless: https://docs.runpod.io/serverless/overview
- Runpod Console: https://www.runpod.io/console
- Docker Hub: https://hub.docker.com/
- Roop: https://github.com/s0md3v/roop

---

**Actualizado**: 2026-01-08
**Para**: Roop en Runpod Serverless
