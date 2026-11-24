# Relatório do Sistema — Classificador de Spam

## Visão geral da solução

Este projeto disponibiliza um classificador de mensagens em português por meio de uma API FastAPI e de uma página web integrada. O modelo TF-IDF + Regressão Logística está armazenado em `model/modelo.joblib` e recebe uma mensagem, devolvendo o rótulo `spam` ou `nao_spam`, a probabilidade da previsão e a versão do modelo.

Fluxo completo:

```text
Navegador → página HTML/JavaScript → GET /health ou POST /predict
                                                   ↓
                                     FastAPI (app/main.py)
                                                   ↓
                                Modelo scikit-learn (.joblib)
                                                   ↓
                                      Resposta JSON à página
```

## Funcionalidades implementadas

- Página inicial servida em `/`.
- Consulta periódica a `/health` para indicar se o serviço está disponível.
- Campo protegido para chave de API, sem chave fixa no frontend.
- Campo para mensagem com limite máximo de 2.000 caracteres.
- Exemplos prontos de mensagem suspeita e mensagem comum.
- Resultado com rótulo, probabilidade, latência e versão que respondeu.
- Mensagens claras para texto vazio, chave inválida e API indisponível.
- Painel local com quantidade de requisições, erros e latência média.
- Geração de 50 requisições de carga pela página.
- Documentação interativa em `/docs`.

## Tecnologias

| Tecnologia | Uso |
|---|---|
| Python 3.14 no ambiente atual | Execução da aplicação |
| FastAPI | API HTTP e documentação OpenAPI |
| Uvicorn | Servidor ASGI local |
| scikit-learn 1.8.0 | Modelo carregado pelo joblib |
| joblib | Serialização e carregamento do modelo |
| Pydantic | Validação do corpo da requisição |
| python-dotenv | Carregamento das variáveis de `.env` |
| HTML, CSS e JavaScript | Interface web |
| pytest e TestClient | Testes automatizados dos endpoints |

A separação entre FastAPI, modelo e frontend permite testar a inferência pela documentação ou pela página, sem duplicar a lógica de classificação no navegador.

## Arquitetura dos arquivos

- `app/main.py`: configuração da API, middleware CORS, arquivos estáticos, validação, autenticação e inferência.
- `static/index.html`: estrutura da interface.
- `static/app.js`: chamadas à API, estado de saúde, resultados e métricas do navegador.
- `static/styles.css`: apresentação visual.
- `model/modelo.joblib`: modelo treinado.
- `model/exemplo_uso.py`: exemplo direto de uso do modelo em Python.
- `tests/test_api.py`: testes dos endpoints e regras de autenticação.
- `.env.example`: modelo das variáveis de ambiente.

## Contrato da API

### `GET /health`

Não exige chave e retorna:

```json
{
  "status": "ok",
  "versao": "v1",
  "ambiente": "dev"
}
```

Observado durante o teste local: status HTTP `200`, com `versao: v1` e `ambiente: dev`.

### `POST /predict`

Corpo válido:

```json
{
  "texto": "Parabéns! Você ganhou um prêmio, clique no link"
}
```

Resposta esperada:

```json
{
  "rotulo": "spam",
  "probabilidade": 0.67,
  "versao": "v1"
}
```

O rótulo possível é `spam` ou `nao_spam`. O valor de probabilidade representa a confiança da classe escolhida.

### Regras

- Texto contendo somente espaços é rejeitado.
- Texto vazio não é permitido pelo contrato.
- Quando `API_KEY` está definida, `/predict` exige o cabeçalho `X-API-Key`.
- Sem a chave correta, o endpoint retorna `401`.
- `/health` não exige chave.
- `MODEL_VERSION` define a versão exibida pela API.
- `APP_ENV` identifica o ambiente exibido pela API.
- `MODEL_PATH` permite indicar outro arquivo de modelo.

## Configuração local

Execute os comandos na pasta que contém `app`, `static`, `model` e `requirements.txt`:

```powershell
cd .\cetam-disciplina-mlops-e-deploy-main
.\..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Se o ambiente virtual já estiver configurado na raiz do workspace, pode-se usar:

```powershell
C:\Users\Administrador\Videos\cetam-disciplina-mlops-e-deploy-main\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

URLs locais:

- Página: http://127.0.0.1:8000/
- Documentação: http://127.0.0.1:8000/docs
- Saúde: http://127.0.0.1:8000/health

Não execute o servidor a partir da pasta externa que contém apenas outra pasta do projeto. A execução precisa ocorrer na raiz interna do repositório.

## Variáveis de ambiente

| Variável | Obrigatória | Padrão | Função |
|---|---:|---|---|
| `MODEL_VERSION` | Não | `v1` | Versão apresentada pela API |
| `APP_ENV` | Não | `dev` | Ambiente apresentado por `/health` |
| `API_KEY` | Não | Sem valor | Protege `/predict` quando definida |
| `MODEL_PATH` | Não | `model/modelo.joblib` | Caminho do modelo |

Exemplo baseado em `.env.example`:

```dotenv
APP_ENV=dev
MODEL_VERSION=v1
API_KEY=chave-ficticia-123
```

O arquivo `.env` não deve ser enviado ao Git. A chave usada no exercício é fictícia.

## Testes automatizados

Na raiz interna do projeto:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_api.py -vv
```

Resultado obtido na validação:

```text
4 passed, 15 warnings
```

Cobertura dos testes:

- `/health` retorna os valores esperados.
- `/predict` sem chave retorna `401` quando `API_KEY` está definida.
- `/predict` aceita uma chave válida e retorna um rótulo permitido.
- Texto contendo apenas espaços gera erro HTTP 4xx.

Os avisos registrados são avisos de compatibilidade e de uso de APIs internas do AnyIO/FastAPI; não são falhas dos testes.

## Uso pela interface

1. Abra http://127.0.0.1:8000/.
2. O sistema consulta `/health` ao abrir e a cada 30 segundos.
3. Informe a chave fictícia configurada em `API_KEY`, se ela estiver ativa.
4. Digite uma mensagem ou use um exemplo pronto.
5. Selecione **Classificar** ou use `Ctrl+Enter`.
6. Consulte o rótulo, a probabilidade, a latência e a versão na coluna de resultado.
7. Use **Enviar 50 requisições** para gerar carga local e observar contadores e latência média.

## Limitações conhecidas

- O conjunto de treino é pequeno e a precisão não é o objetivo principal da atividade.
- Probabilidades podem ser baixas ou variar conforme o texto.
- O modelo exige `scikit-learn==1.8.0` para evitar incompatibilidade ao carregar o arquivo.
- Em produção, a chave deve ser configurada na plataforma e não no código ou no navegador.
- O painel de carga atual conta requisições no navegador; ele não substitui métricas técnicas do servidor.

## Situação atual do projeto

- API iniciada com sucesso em http://127.0.0.1:8000.
- Endpoint `/health` validado com resposta HTTP `200`.
- Página, documentação e endpoints configurados.
- Quatro testes automatizados validados com sucesso.
- Sistema empacotado com Docker e executado pelo Docker Desktop usando WSL.
- Container ativo: `cetam-api-1`.
- Imagem versionada: `cetam-api:v1`.
- Metadado da imagem: `org.opencontainers.image.version=v1`.
- Container confirmado com estado `healthy`.
- `/health` validado dentro do container com `versao: v1` e `ambiente: dev`.
- `/predict` validado dentro do container com resposta de classificação `spam`.
- Repositório GitHub sincronizado na branch `main`.
- Aplicação publicada no Render com HTTPS: https://kenedy-emerson.onrender.com.
- Endpoint online `/health` validado com resposta HTTP `200`; página e classificação também verificadas no navegador.
- O serviço está no plano gratuito do Render e pode levar alguns segundos para responder após ficar inativo.

## Empacotamento Docker atualizado

O Compose gera e usa a imagem:

```text
cetam-api:v1
```

A imagem contém metadados do Open Containers Initiative, incluindo título e versão. A versão `v1` também é configurada em `MODEL_VERSION` dentro do container.

Comandos atuais:

```powershell
docker compose up --build -d
docker ps
docker inspect cetam-api:v1
```

Para recriar a imagem e o container com a versão atual:

```powershell
docker compose -p cetam build --build-arg IMAGE_VERSION=v1
docker compose -p cetam up -d --force-recreate
```

URLs locais do container:

- Página: http://localhost:8000/
- Documentação: http://localhost:8000/docs
- Saúde: http://localhost:8000/health

## Pendências de entrega

- [ ] Informar a URL pública após o deploy.
- [ ] Registrar `APP_ENV=test` na plataforma online.
- [ ] Configurar `MODEL_VERSION=v1` e `API_KEY` na plataforma online.
- [ ] Executar os testes da aplicação após o deploy.
- [ ] Testar chave ausente, chave incorreta e texto vazio pela interface.
- [ ] Registrar integrantes da dupla e responsabilidades.
- [ ] Criar e publicar a tag `v1`.

---

# Classificador de spam: repositório-base da atividade "Do notebook à produção"

Componente curricular **MLOps e Deploy** · Atividade em **dupla**

## 1. A história

Vocês são a "squad de MLOps" de uma startup. Uma cientista de dados criou um **classificador de
mensagens spam** que funciona no notebook dela. A empresa precisa dele **rodando de forma
confiável, versionada e monitorada**, com uma página web para testar, e acessível pela internet.

Seu trabalho **não** é melhorar o modelo. É colocá-lo em produção sem cair no "funciona só na
minha máquina". Nesta etapa vocês constroem a API, a página web e publicam a primeira versão.

## 2. O modelo

| | |
|---|---|
| **O que faz** | Lê uma mensagem de texto e diz se é `spam` ou `nao_spam`, com a probabilidade |
| **Para que serve** | Filtrar mensagens indesejadas (golpes, promoções falsas, links suspeitos) |
| **Tipo** | TF-IDF + Regressão Logística (scikit-learn) |
| **Arquivo** | `model/modelo.joblib` (poucos KB) |
| **Dados de treino** | `data/mensagens.csv`: 66 mensagens em português, rotuladas pelo professor |
| **Entrada** | Um texto |
| **Saída** | Um rótulo (`spam` ou `nao_spam`) e a probabilidade de cada classe |

**Limitações (importante):**
- O conjunto de treino é **pequeno**; o modelo erra com facilidade e as probabilidades são baixas
  (algo como 0,6 a 0,7). Isso é esperado: a atividade é sobre **entrega e operação**, não sobre acurácia.
- Para carregar o `.joblib`, é necessário **Python com `scikit-learn==1.8.0`**. Outra versão pode
  dar erro ou resultados diferentes.
- Se quiserem retreinar: `pip install -r requirements-treino.txt` e `python model/train.py`.

### Como usar o modelo em Python

Veja o arquivo `model/exemplo_uso.py`. Resumo:

    import joblib
    modelo = joblib.load("model/modelo.joblib")
    probabilidades = modelo.predict_proba(["Você ganhou um prêmio! Clique aqui"])[0]
    rotulo = modelo.classes_[probabilidades.argmax()]      # "spam" ou "nao_spam"

## 3. O que vocês vão construir

    [ Página web ]  --->  [ API de inferência ]  --->  [ Modelo (.joblib) ]
     (navegador)            /health  /predict

- **API:** completem o esqueleto em `app/main.py`.
- **Página web:** sigam o modelo de site em `docs/modelo_de_pagina.md`.
- **Tecnologias:** **vocês decidem.** A API precisa carregar o modelo `.joblib`, então precisa
  rodar em **Python** (o esqueleto usa FastAPI, mas Flask também serve). A página pode ser HTML +
  JavaScript simples ou um framework, e pode ficar junto da API ou em outro serviço.
  **Anotem e justifiquem** as escolhas no README de vocês.

## 4. Contrato da API (não mudem, a página e as próximas etapas dependem dele)

**`GET /health`** devolve status 200 e:

    {"status": "ok", "versao": "v1", "ambiente": "dev"}

**`POST /predict`** recebe:

    {"texto": "Parabéns! Você ganhou um prêmio, clique no link"}

e devolve:

    {"rotulo": "spam", "probabilidade": 0.67, "versao": "v1"}

Regras:
- Texto vazio deve ser rejeitado (erro 4xx).
- Se a variável `API_KEY` estiver definida, o `/predict` exige o cabeçalho `X-API-Key` com o
  mesmo valor; sem ele, responda **401**. O `/health` nunca exige chave.
- A `versao` vem da variável de ambiente `MODEL_VERSION`.

## 5. Etapa 1: passo a passo

### 5.1 Preparação
Este repositório-base é entregue em **pendrive**. Vocês vão criar o repositório da dupla **do zero**
no GitHub.

1. Cada pessoa usa sua conta no **GitHub**.
2. Copiem a pasta do pendrive para o computador de vocês.
3. Uma pessoa cria um repositório **vazio** no GitHub (sugestão de nome: `mlops-spam-nome1-nome2`).
   Adicionem a outra pessoa da dupla e **o professor** como colaboradores
   (*Settings > Collaborators*). O professor informará o usuário dele em sala.
4. Na pasta copiada, iniciem o Git e enviem o primeiro commit:

       git init -b main
       git add .
       git commit -m "chore: importa repositório-base"
       git remote add origin <url-do-repositorio>
       git push -u origin main

5. A outra pessoa clona o repositório: `git clone <url>`.
6. Instalem o ambiente:

       python -m venv .venv
       source .venv/bin/activate        # no Windows: .venv\Scripts\activate
       pip install -r requirements.txt

### 5.2 API
1. Completem `GET /health` e `POST /predict` em `app/main.py`.
2. Rodem: `uvicorn app.main:app --reload` e abram `http://localhost:8000/docs` para testar.
3. Testem com `curl` ou pela página `/docs` (exemplos prontos: veja `model/exemplo_uso.py`).

### 5.3 Configuração e segredos
- **Nada de configuração fixa no código.** Leiam tudo de variáveis de ambiente
  (`MODEL_VERSION`, `APP_ENV`, `API_KEY`).
- Copiem `.env.example` para `.env` (o `.gitignore` já impede o envio ao Git).
- A chave de API deste exercício é **fictícia**. Mesmo assim, tratem como segredo: nunca no
  código nem no repositório. Em produção, ela é configurada na plataforma de hospedagem.
- `APP_ENV=dev` (na sua máquina) e `APP_ENV=test` (online): o que muda entre os dois?
  Definam e documentem.

### 5.4 Página web
- Sigam `docs/modelo_de_pagina.md`.
- A página **não deve ter a chave embutida**: o usuário digita a chave em um campo.
- Testem os casos de erro: chave errada (401), API fora do ar, texto vazio.

### 5.5 Git (os dois fazem commits)
- **Commits pequenos e frequentes**, com mensagens claras. Exemplos:
  `feat: implementa endpoint /health` · `fix: trata texto vazio no /predict` · `docs: explica como rodar`.
- Os **dois** integrantes devem ter commits no histórico. Usem **pareamento**: uma pessoa digita
  (piloto) e a outra revisa e orienta (copiloto), e troquem a cada tarefa.
- Antes de começar a trabalhar: `git pull`. Depois de terminar uma tarefa: `git add`, `git commit`, `git push`.
- Sugestão: uma branch por tarefa e *pull request* no GitHub para a outra pessoa revisar.

### 5.6 Publicar online
Com internet, vocês vão testar **localmente e online**. O professor sugere o **Render**, mas a escolha é de vocês: escolham uma plataforma de hospedagem
gratuita para publicar a API e a página. Algumas opções (confiram as condições atuais, pois
planos gratuitos mudam):

| Opção | Observação |
|---|---|
| **Render** (sugestão do professor) | Serviços web e sites estáticos gratuitos, publicando direto do GitHub; o serviço gratuito "hiberna" após alguns minutos sem uso, então a primeira requisição pode demorar |
| **GitHub Pages** | Só para páginas estáticas (a API precisa ficar em outro lugar) |
| Outras | Pesquisem e justifiquem a escolha |

Configurem as variáveis de ambiente **na plataforma** (não no código) e anotem a URL.
Depois, repitam os testes na versão online.

### 5.7 Documentação
Escrevam um `README` da dupla (substituam este ou criem `README_DUPLA.md`) com: o que foi
construído, tecnologias escolhidas e por quê, como rodar localmente, variáveis de ambiente
necessárias, a URL online e quem fez o quê.

## 6. Entrega e critérios de aceite da Etapa 1

- [ ] API com `/health` e `/predict` funcionando **localmente**, conforme o contrato
- [ ] `/predict` devolve 401 sem a chave correta (quando `API_KEY` está definida) e erro 4xx para texto vazio
- [ ] Página web funcionando localmente, com os itens obrigatórios do modelo de site
- [ ] Configuração por variáveis de ambiente e `.env.example` presente
- [ ] Nenhum segredo no repositório (conferir o histórico, não só os arquivos atuais)
- [ ] Repositório no GitHub com histórico de commits **dos dois integrantes** e o **professor adicionado como colaborador**
- [ ] Tag **`v1`** criada no commit entregue (`git tag v1 && git push origin v1`)
- [ ] Primeira versão **publicada online**, testada pela URL pública
- [ ] README da dupla com instruções, escolhas de tecnologia e URL. **O professor vai clonar o repositório e rodar seguindo só o README**, então ele precisa estar completo (versão do Python, comandos, variáveis de ambiente)

## 7. O que vem depois

Nas próximas etapas vocês vão **empacotar** o serviço (Docker), **implantar** em um cluster local,
montar um **pipeline de CI/CD**, adicionar **logs e métricas** e, por fim, enfrentar um **incidente
simulado** com rollback. Por isso, o que vocês construírem agora precisa ser organizado, com
configuração fora do código e testes fáceis de rodar.

## 8. Erros comuns

- **`InconsistentVersionWarning` ou erro ao abrir o modelo:** a versão do scikit-learn não é a 1.8.0.
- **A página não consegue chamar a API estando em outro endereço:** pesquisem sobre **CORS**.
- **Serviço online demora muito na primeira requisição:** plano gratuito hibernando; é esperado.
- **Subiram uma chave por engano:** apaguem do código, troquem a chave e avisem o professor.
  Apagar o arquivo depois do commit não remove a chave do histórico.

## Implementação da Etapa 1

### Executar localmente

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Acesse:

- Página: `http://localhost:8000/`
- Documentação: `http://localhost:8000/docs`
- Saúde: `http://localhost:8000/health`

### Variáveis de ambiente

- `MODEL_VERSION`: versão apresentada pela API. Padrão: `v1`.
- `APP_ENV`: ambiente apresentado pela API. Padrão: `dev`.
- `API_KEY`: chave opcional exigida no cabeçalho `X-API-Key`.
- `MODEL_PATH`: caminho opcional do modelo `.joblib`.

Quando `API_KEY` não estiver definida, o `/predict` fica público. Quando estiver definida, a chave da página é enviada apenas no cabeçalho da requisição.

### Testes

```powershell
pytest -q
```

Os testes cobrem `/health`, autenticação, predição e texto vazio.

## Empacotamento com Docker

Arquivos disponíveis:

- `Dockerfile`: imagem da aplicação.
- `.dockerignore`: exclui arquivos locais desnecessários da imagem.
- `docker-compose.yml`: execução local com API na porta 8000.

Com Docker Desktop instalado e em execução:

```powershell
docker compose up --build
```

Para iniciar em segundo plano:

```powershell
docker compose up --build -d
```

Para parar:

```powershell
docker compose down
```

A página, documentação e saúde ficam disponíveis em:

- http://localhost:8000/
- http://localhost:8000/docs
- http://localhost:8000/health

O Compose configura `APP_ENV=dev`, `MODEL_VERSION=v1` e uma chave fictícia de API.

## Limitações conhecidas

- O conjunto de treino é pequeno e a precisão não é o objetivo principal da atividade.
- Probabilidades podem ser baixas ou variar conforme o texto.
- O modelo exige `scikit-learn==1.8.0` para evitar incompatibilidade ao carregar o arquivo.
- Em produção, a chave deve ser configurada na plataforma e não no código ou no navegador.
- O painel de carga atual conta requisições no navegador; ele não substitui métricas técnicas do servidor.

## Situação atual do projeto

- API iniciada com sucesso em http://127.0.0.1:8000.
- Endpoint `/health` validado com resposta HTTP `200`.
- Página, documentação e endpoints configurados.
- Quatro testes automatizados validados com sucesso.
- Sistema empacotado com Docker e executado pelo Docker Desktop usando WSL.
- Container ativo: `cetam-api-1`.
- Imagem versionada: `cetam-api:v1`.
- Metadado da imagem: `org.opencontainers.image.version=v1`.
- Container confirmado com estado `healthy`.
- `/health` validado dentro do container com `versao: v1` e `ambiente: dev`.
- `/predict` validado dentro do container com resposta de classificação `spam`.
- Repositório GitHub sincronizado na branch `main`.
- Aplicação publicada no Render com HTTPS: https://kenedy-emerson.onrender.com.
- Endpoint online `/health` validado com resposta HTTP `200`; página e classificação também verificadas no navegador.
- O serviço está no plano gratuito do Render e pode levar alguns segundos para responder após ficar inativo.

## Empacotamento Docker atualizado

O Compose gera e usa a imagem:

```text
cetam-api:v1
```

A imagem contém metadados do Open Containers Initiative, incluindo título e versão. A versão `v1` também é configurada em `MODEL_VERSION` dentro do container.

Comandos atuais:

```powershell
docker compose up --build -d
docker ps
docker inspect cetam-api:v1
```

Para recriar a imagem e o container com a versão atual:

```powershell
docker compose -p cetam build --build-arg IMAGE_VERSION=v1
docker compose -p cetam up -d --force-recreate
```

URLs locais do container:

- Página: http://localhost:8000/
- Documentação: http://localhost:8000/docs
- Saúde: http://localhost:8000/health

## Pendências de entrega

- [ ] Informar a URL pública após o deploy.
- [ ] Registrar `APP_ENV=test` na plataforma online.
- [ ] Configurar `MODEL_VERSION=v1` e `API_KEY` na plataforma online.
- [ ] Executar os testes da aplicação após o deploy.
- [ ] Testar chave ausente, chave incorreta e texto vazio pela interface.
- [ ] Registrar integrantes da dupla e responsabilidades.
- [ ] Criar e publicar a tag `v1`.