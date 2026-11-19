const apiKey = document.querySelector('#apiKey');
const message = document.querySelector('#message');
const classifyButton = document.querySelector('#classifyButton');
const healthBadge = document.querySelector('#healthBadge');
const versionBadge = document.querySelector('#versionBadge');
const resultLabel = document.querySelector('#resultLabel');
const latencyLabel = document.querySelector('#latencyLabel');
const probabilityBar = document.querySelector('#probabilityBar');
const probabilityValue = document.querySelector('#probabilityValue');
const servedBy = document.querySelector('#servedBy');
const messageBox = document.querySelector('#messageBox');

let requestCount = 0;
let errorCount = 0;
let latencies = [];

async function checkHealth() {
  try {
    const response = await fetch('/health');
    if (!response.ok) throw new Error('API indisponível');
    const data = await response.json();
    healthBadge.className = 'badge status-ok';
    healthBadge.innerHTML = '<span class="dot"></span> Serviço OK';
    versionBadge.textContent = `versão ${data.versao}`;
  } catch (error) {
    healthBadge.className = 'badge status-error';
    healthBadge.innerHTML = '<span class="dot"></span> Serviço fora do ar';
    versionBadge.textContent = 'versão —';
  }
}

function showMessage(text, type = 'error') {
  messageBox.textContent = text;
  messageBox.className = `message-box ${type}`;
}

function updateMetrics(latency, failed = false) {
  requestCount += 1;
  if (failed) errorCount += 1;
  if (Number.isFinite(latency)) latencies.push(latency);

  document.querySelector('#requestCount').textContent = requestCount;
  document.querySelector('#errorCount').textContent = errorCount;
  document.querySelector('#averageLatency').textContent = latencies.length
    ? `${Math.round(latencies.reduce((sum, value) => sum + value, 0) / latencies.length)} ms`
    : '— ms';
}

async function classify() {
  if (!message.value.trim()) {
    showMessage('Digite uma mensagem antes de classificar.', 'error');
    message.focus();
    return;
  }

  classifyButton.disabled = true;
  classifyButton.textContent = 'Classificando...';
  const started = performance.now();

  try {
    const headers = {'Content-Type': 'application/json'};
    if (apiKey.value) headers['X-API-Key'] = apiKey.value;

    const response = await fetch('/predict', {
      method: 'POST',
      headers,
      body: JSON.stringify({texto: message.value.trim()})
    });

    const data = await response.json().catch(() => ({}));
    const elapsed = Math.round(performance.now() - started);

    if (!response.ok) {
      if (response.status === 401) throw new Error('Chave de API incorreta. Informe a chave correta.');
      throw new Error(data.detail || 'Não foi possível consultar a API.');
    }

    const probability = Number(data.probabilidade);
    const isSpam = data.rotulo === 'spam';

    resultLabel.textContent = isSpam ? 'spam' : 'não spam';
    resultLabel.className = `result-label ${isSpam ? 'spam' : 'normal'}`;
    latencyLabel.textContent = `${elapsed} ms`;
    probabilityValue.textContent = probability.toLocaleString('pt-BR', {style: 'percent', minimumFractionDigits: 2});
    probabilityBar.style.width = `${probability * 100}%`;
    probabilityBar.style.background = isSpam ? '#c83f49' : '#18855b';
    servedBy.textContent = `respondido pela ${data.versao}`;
    showMessage('Predição realizada com sucesso.', 'success');
    updateMetrics(elapsed, false);
  } catch (error) {
    const elapsed = Math.round(performance.now() - started);
    showMessage(error.message || 'API fora do ar.', 'error');
    updateMetrics(elapsed, true);
  } finally {
    classifyButton.disabled = false;
    classifyButton.textContent = 'Classificar';
  }
}

async function sendLoad() {
  const button = document.querySelector('#loadButton');
  button.disabled = true;
  const originalText = button.textContent;

  for (let i = 0; i < 50; i += 1) {
    button.textContent = `Enviando ${i + 1}/50`;
    await fetch('/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(apiKey.value ? {'X-API-Key': apiKey.value} : {})
      },
      body: JSON.stringify({texto: i % 2 ? 'A reunião foi remarcada para amanhã' : 'Ganhe dinheiro rápido clicando neste link'})
    }).then(async response => {
      const elapsed = 10;
      updateMetrics(elapsed, !response.ok);
    }).catch(() => updateMetrics(0, true));
  }

  button.textContent = originalText;
  button.disabled = false;
}

document.querySelector('#toggleKey').addEventListener('click', event => {
  const showing = apiKey.type === 'text';
  apiKey.type = showing ? 'password' : 'text';
  event.currentTarget.textContent = showing ? 'Ver' : 'Ocultar';
});
document.querySelector('#spamExample').addEventListener('click', () => {
  message.value = 'Parabéns! Você ganhou um prêmio. Clique aqui para resgatar agora.';
  message.focus();
});
document.querySelector('#normalExample').addEventListener('click', () => {
  message.value = 'A reunião de amanhã foi remarcada para as 15h na sala 2.';
  message.focus();
});
classifyButton.addEventListener('click', classify);
document.querySelector('#loadButton').addEventListener('click', sendLoad);
message.addEventListener('keydown', event => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') classify();
});

checkHealth();
setInterval(checkHealth, 30000);
