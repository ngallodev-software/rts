FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libgl1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY rts_export ./rts_export
COPY version-manifest.json ./

EXPOSE 8791

CMD ["python", "-m", "rts_export.server", "--host", "0.0.0.0", "--port", "8791"]
