"""API de classificação de mensagens como spam ou não spam."""
import hashlib
import hmac
import json
import os
import time
import uuid
from pathlib import Path
from threading import Lock

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

import joblib
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from starlette.requests import Request

MODEL_VERSION = os.getenv("MODEL_VERSION", "v1")
APP_ENV = os.getenv("APP_ENV", "dev")
API_KEY_HASH = os.getenv("API_KEY_HASH", "").strip().lower()
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(RAIZ / "model" / "modelo.joblib")))

try:
    modelo = joblib.load(MODEL_PATH)
except Exception as exc:
    raise RuntimeError(f"Não foi possível carregar o modelo em {MODEL_PATH}: {exc}") from exc

app = FastAPI(title="API de classificação de spam", version=MODEL_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

STATIC_DIR = RAIZ / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


metricas = {"requisicoes": 0, "erros_5xx": 0, "ms_total": 0.0}
metricas_lock = Lock()


def log_evento(nivel: str, mensagem: str, **campos) -> None:
    registro = {
        "hora": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "nivel": nivel,
        "mensagem": mensagem,
        **campos,
    }
    print(json.dumps(registro, ensure_ascii=False), flush=True)


@app.middleware("http")
async def observar_requisicao(request: Request, call_next):
    id_req = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    inicio = time.perf_counter()

    log_evento(
        "INFO",
        "inicio da requisicao",
        id=id_req,
        rota=request.url.path,
        metodo=request.method,
    )

    with metricas_lock:
        metricas["requisicoes"] += 1

    try:
        resposta = await call_next(request)
    except Exception:
        duracao_ms = (time.perf_counter() - inicio) * 1000
        with metricas_lock:
            metricas["erros_5xx"] += 1
            metricas["ms_total"] += duracao_ms
        log_evento(
            "ERROR",
            "requisicao falhou",
            id=id_req,
            rota=request.url.path,
            status=500,
            ms=round(duracao_ms, 1),
        )
        raise

    duracao_ms = (time.perf_counter() - inicio) * 1000
    with metricas_lock:
        metricas["ms_total"] += duracao_ms
        if resposta.status_code >= 500:
            metricas["erros_5xx"] += 1

    nivel = "ERROR" if resposta.status_code >= 500 else "WARNING" if resposta.status_code >= 400 else "INFO"
    log_evento(
        nivel,
        "requisicao atendida" if resposta.status_code < 400 else "requisicao com erro",
        id=id_req,
        rota=request.url.path,
        metodo=request.method,
        status=resposta.status_code,
        ms=round(duracao_ms, 1),
    )
    if request.method == "GET" and (
        request.url.path == "/" or request.url.path.startswith("/static/")
    ):
        resposta.headers["Cache-Control"] = "no-store"
        resposta.headers["Pragma"] = "no-cache"
    resposta.headers["X-Request-ID"] = id_req
    return resposta


class Mensagem(BaseModel):
    texto: str = Field(min_length=1, max_length=2000)

    @field_validator("texto")
    @classmethod
    def validar_texto(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("O texto não pode estar vazio")
        return valor


@app.get("/", include_in_schema=False)
def pagina():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "versao": MODEL_VERSION, "ambiente": APP_ENV}


@app.get("/ready")
def ready():
    if modelo is None:
        raise HTTPException(status_code=503, detail="Modelo não está pronto")
    return {"status": "pronto", "versao": MODEL_VERSION}


@app.get("/metrics")
def ver_metricas():
    with metricas_lock:
        requisicoes = metricas["requisicoes"]
        erros_5xx = metricas["erros_5xx"]
        ms_total = metricas["ms_total"]
    media = ms_total / requisicoes if requisicoes else 0
    return {
        "requisicoes": requisicoes,
        "erros_5xx": erros_5xx,
        "latencia_media_ms": round(media, 1),
    }


@app.post("/predict")
def predict(msg: Mensagem, x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    try:
        hash_configurado = bytes.fromhex(API_KEY_HASH)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Configuração de autenticação inválida") from exc

    if len(hash_configurado) != hashlib.sha256().digest_size:
        detail = "Autenticação não configurada" if not API_KEY_HASH else "Configuração de autenticação inválida"
        raise HTTPException(status_code=503, detail=detail)

    if x_api_key is None or not hmac.compare_digest(
        hashlib.sha256(x_api_key.encode("utf-8")).digest(),
        hash_configurado,
    ):
        raise HTTPException(status_code=401, detail="Chave de API inválida")

    probabilidades = modelo.predict_proba([msg.texto])[0]
    indice = int(probabilidades.argmax())

    return {
        "rotulo": str(modelo.classes_[indice]),
        "probabilidade": round(float(probabilidades[indice]), 2),
        "versao": MODEL_VERSION,
    }
