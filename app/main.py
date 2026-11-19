"""API de classificação de mensagens como spam ou não spam."""
import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

import joblib
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

MODEL_VERSION = os.getenv("MODEL_VERSION", "v1")
APP_ENV = os.getenv("APP_ENV", "dev")
API_KEY = os.getenv("API_KEY")
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


@app.post("/predict")
def predict(msg: Mensagem, x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Chave de API inválida")

    probabilidades = modelo.predict_proba([msg.texto])[0]
    indice = int(probabilidades.argmax())

    return {
        "rotulo": str(modelo.classes_[indice]),
        "probabilidade": round(float(probabilidades[indice]), 2),
        "versao": MODEL_VERSION,
    }
