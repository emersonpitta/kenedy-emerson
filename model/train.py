"""Treina o classificador de spam e salva em model/modelo.joblib.

Uso:
    python model/train.py
    python model/train.py --csv outro.csv --saida model/modelo_novo.joblib
"""
import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

RAIZ = Path(__file__).resolve().parent.parent
ROTULOS_PERMITIDOS = {"spam", "nao_spam"}


def carregar_dados(caminho_csv: Path) -> pd.DataFrame:
    if not caminho_csv.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {caminho_csv}")

    dados = pd.read_csv(caminho_csv)
    if not {"texto", "rotulo"}.issubset(dados.columns):
        raise ValueError("O CSV precisa conter exatamente as colunas 'texto' e 'rotulo'")

    dados = dados[["texto", "rotulo"]].copy()
    dados["texto"] = dados["texto"].astype("string").str.strip()
    dados["rotulo"] = dados["rotulo"].astype("string").str.strip().str.lower()
    dados = dados.dropna(subset=["texto", "rotulo"])

    if dados.empty:
        raise ValueError("O arquivo CSV não contém mensagens válidas")

    rotulos_invalidos = set(dados["rotulo"].unique()) - ROTULOS_PERMITIDOS
    if rotulos_invalidos:
        raise ValueError(
            "Rótulos inválidos encontrados: " + ", ".join(sorted(rotulos_invalidos))
        )

    return dados


def criar_modelo() -> Pipeline:
    return Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                strip_accents="unicode",
                sublinear_tf=True,
            ),
        ),
        ("clf", LogisticRegression(max_iter=1000, random_state=42)),
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description="Treina o classificador de spam")
    parser.add_argument("--csv", default=str(RAIZ / "data" / "mensagens.csv"))
    parser.add_argument("--saida", default=str(RAIZ / "model" / "modelo.joblib"))
    args = parser.parse_args()

    dados = carregar_dados(Path(args.csv))
    contagens = dados["rotulo"].value_counts()
    menor_classe = int(contagens.min())

    if menor_classe < 2:
        raise ValueError("Cada rótulo precisa ter pelo menos duas mensagens")

    proporcao_teste = 0.25
    if len(dados) * proporcao_teste < len(ROTULOS_PERMITIDOS):
        proporcao_teste = len(ROTULOS_PERMITIDOS) / len(dados)

    x_treino, x_teste, y_treino, y_teste = train_test_split(
        dados["texto"],
        dados["rotulo"],
        test_size=proporcao_teste,
        random_state=42,
        stratify=dados["rotulo"],
    )

    modelo = criar_modelo()
    modelo.fit(x_treino, y_treino)

    y_previsto = modelo.predict(x_teste)
    print("Avaliação no conjunto de teste:")
    print(classification_report(y_teste, y_previsto, digits=3, zero_division=0))

    modelo.fit(dados["texto"], dados["rotulo"])

    caminho_saida = Path(args.saida)
    if not caminho_saida.is_absolute():
        caminho_saida = RAIZ / caminho_saida
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    caminho_temporario = caminho_saida.with_suffix(caminho_saida.suffix + ".tmp")
    joblib.dump(modelo, caminho_temporario)
    caminho_temporario.replace(caminho_saida)

    print(f"Modelo treinado com {len(dados)} mensagens")
    print(f"Modelo salvo em {caminho_saida}")


if __name__ == "__main__":
    main()
