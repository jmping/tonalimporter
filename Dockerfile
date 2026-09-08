FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY sync_workouts.py tonal_service.py ./

ENV PYTHONUNBUFFERED=1 \
    TONAL_SERVICE_HOST=0.0.0.0 \
    TONAL_SERVICE_PORT=8787 \
    TONAL_SYNC_INTERVAL_MINUTES=180

EXPOSE 8787

CMD ["python", "tonal_service.py"]
