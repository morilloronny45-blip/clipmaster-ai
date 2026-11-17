# ClipMaster AI — MVP

Esta primera versión permite:
- Subir un video local o pegar un enlace público compatible con `yt-dlp`.
- Crear segmentos consecutivos de 30, 60 o 90 segundos.
- Descargar cada segmento en MP4.

**Importante:** esta versión todavía no detecta automáticamente los momentos más interesantes con IA. Divide el video en segmentos consecutivos. La compatibilidad con enlaces de YouTube, Facebook y TikTok depende de que `yt-dlp` pueda acceder al contenido y de las condiciones de cada plataforma. No evade videos privados, DRM ni restricciones de acceso.

## Requisitos
- Python 3.10+
- FFmpeg y FFprobe instalados y disponibles en PATH.

## Ejecutar
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Abre http://127.0.0.1:5000

Para usarlo públicamente hace falta desplegar el servidor en un hosting que permita FFmpeg, almacenamiento temporal y trabajos de video largos. No publiques el servidor sin añadir autenticación, límites de uso y limpieza automática de archivos.
