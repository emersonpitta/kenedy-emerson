FROM python:3.14-slim

ARG IMAGE_VERSION=v1

LABEL org.opencontainers.image.title="Classificador de Spam" \
      org.opencontainers.image.version="${IMAGE_VERSION}" \
      org.opencontainers.image.description="API e pagina web para classificacao de mensagens spam"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=prod

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY model ./model
COPY static ./static

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
