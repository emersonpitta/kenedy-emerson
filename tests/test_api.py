import hashlib
import os

import pytest

CHAVE_TESTE = "teste-ficticio"
os.environ["API_KEY_HASH"] = hashlib.sha256(CHAVE_TESTE.encode("utf-8")).hexdigest()
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


def test_predict_com_chave_incorreta_retorna_401():
    response = client.post(
        "/predict",
        json={"texto": "Você ganhou um prêmio!"},
        headers={"X-API-Key": "chave-incorreta"},
    )
    assert response.status_code == 401


@pytest.mark.parametrize("hash_configurado", ["", "hash-invalido", "00" * 31])
def test_predict_sem_hash_valido_retorna_503(monkeypatch, hash_configurado):
    monkeypatch.setattr("app.main.API_KEY_HASH", hash_configurado)
    response = client.post(
        "/predict",
        json={"texto": "Você ganhou um prêmio!"},
        headers={"X-API-Key": CHAVE_TESTE},
    )
    assert response.status_code == 503


def test_predict_com_chave():
    response = client.post(
        "/predict",
        json={"texto": "Você ganhou um prêmio! Clique aqui"},
        headers={"X-API-Key": CHAVE_TESTE},
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
        headers={"X-API-Key": CHAVE_TESTE},
    )
    assert 400 <= response.status_code < 500


def test_ready_retorna_status_ok():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "pronto"


def test_metrics_retorna_contadores():
    response = client.get("/metrics")
    assert response.status_code == 200
    metricas = response.json()
    assert "requisicoes" in metricas
    assert "erros_5xx" in metricas
    assert "latencia_media_ms" in metricas


def test_request_id_e_retorna_no_header():
    response = client.post(
        "/predict",
        json={"texto": "Teste de identificação da requisição"},
        headers={"X-API-Key": CHAVE_TESTE, "X-Request-ID": "req-teste-123"},
    )
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-teste-123"
