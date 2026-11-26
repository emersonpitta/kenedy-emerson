import os

import pytest

os.environ.setdefault("API_KEY", "teste-ficticio")
os.environ.setdefault("MODEL_VERSION", "v1")
os.environ.setdefault("APP_ENV", "test")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "versao": "v1",
        "ambiente": "test",
    }


@pytest.mark.parametrize("path", ["/", "/static/app.js"])
def test_pagina_e_recursos_estaticos_nao_sao_cacheados(path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"


def test_predict_sem_chave_retorna_401():
    response = client.post("/predict", json={"texto": "Você ganhou um prêmio!"})
    assert response.status_code == 401


def test_predict_sem_chave_configurada_retorna_503(monkeypatch):
    monkeypatch.setattr("app.main.API_KEY", None)
    response = client.post(
        "/predict",
        json={"texto": "Você ganhou um prêmio!"},
        headers={"X-API-Key": "teste-ficticio"},
    )
    assert response.status_code == 503


def test_predict_com_chave():
    response = client.post(
        "/predict",
        json={"texto": "Você ganhou um prêmio! Clique aqui"},
        headers={"X-API-Key": "teste-ficticio"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["rotulo"] in {"spam", "nao_spam"}
    assert 0 <= body["probabilidade"] <= 1
    assert body["versao"] == "v1"


def test_texto_vazio_retorna_erro():
    response = client.post(
        "/predict",
        json={"texto": "   "},
        headers={"X-API-Key": "teste-ficticio"},
    )
    assert 400 <= response.status_code < 500
