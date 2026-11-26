"""Verifica a saúde e reinicia o Deployment após falhas consecutivas."""

import os
import subprocess
import time
import urllib.request


URL = os.getenv("HEALTH_URL", "http://localhost:8000/health")
DEPLOYMENT = os.getenv("DEPLOYMENT_NAME", "spam-service")
INTERVALO_SEGUNDOS = int(os.getenv("HEALTH_INTERVAL_SECONDS", "10"))
TIMEOUT_SEGUNDOS = int(os.getenv("HEALTH_TIMEOUT_SECONDS", "3"))
MAX_FALHAS = int(os.getenv("HEALTH_MAX_FAILURES", "3"))


def verificar_saude() -> bool:
    try:
        with urllib.request.urlopen(URL, timeout=TIMEOUT_SEGUNDOS) as resposta:
            return resposta.status == 200
    except Exception as exc:
        print(f"Erro ao consultar {URL}: {exc}")
        return False


def reiniciar_deployment() -> None:
    subprocess.run(
        ["kubectl", "rollout", "restart", f"deployment/{DEPLOYMENT}"],
        check=True,
    )
    print(f"rollout restart iniciado para deployment/{DEPLOYMENT}")


def main() -> None:
    falhas = 0
    while True:
        if verificar_saude():
            falhas = 0
            print("OK: serviço saudável")
        else:
            falhas += 1
            print(f"ALERTA: falha consecutiva {falhas}/{MAX_FALHAS}")

            if falhas >= MAX_FALHAS:
                reiniciar_deployment()
                falhas = 0

        time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    main()
