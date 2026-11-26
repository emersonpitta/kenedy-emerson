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
const characterCount = document.querySelector('#characterCount');
const resultEmpty = document.querySelector('#resultEmpty');
const resultContent = document.querySelector('#resultContent');
const copyButton = document.querySelector('#copyButton');
const historyList = document.querySelector('#historyList');

let currentResult = null;

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem('spamguard-history') || '[]');
  } catch {
    return [];
  }
}

function saveHistory(entries) {
  localStorage.setItem('spamguard-history', JSON.stringify(entries.slice(0, 8)));
}

function renderHistory() {
  const entries = loadHistory().filter(entry =>
    entry && typeof entry.text === 'string' && typeof entry.label === 'string'
      && typeof entry.time === 'string'
  );
  if (!entries.length) {
    historyList.innerHTML = '<p class="history-empty">Nenhuma análise realizada nesta sessão.</p>';
    return;
  }

  historyList.replaceChildren();
  entries.forEach(entry => {
    const item = document.createElement('div');
    item.className = 'history-item';

    const label = document.createElement('strong');
    label.className = entry.label === 'spam' ? 'history-spam' : 'history-normal';
    label.textContent = entry.label === 'spam' ? 'SPAM' : 'NÃO SPAM';

    const text = document.createElement('p');
    text.textContent = entry.text;
    text.title = entry.text;

    const time = document.createElement('time');
    time.textContent = entry.time;

    item.append(label, text, time);
    historyList.append(item);
  });
}

function addHistory(text, label) {
  const entries = loadHistory();
  entries.unshift({
    text,
    label,
    time: new Intl.DateTimeFormat('pt-BR', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date())
  });
  saveHistory(entries);
  renderHistory();
}

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

async function refreshMetrics() {
  try {
    const response = await fetch('/metrics');
    if (!response.ok) throw new Error('Métricas indisponíveis');
    const data = await response.json();
    document.querySelector('#requestCount').textContent = data.requisicoes;
    document.querySelector('#errorCount').textContent = data.erros_5xx;
    document.querySelector('#averageLatency').textContent =
      `${Number(data.latencia_media_ms).toFixed(1)} ms`;
  } catch (error) {
    showMessage(error.message || 'Não foi possível consultar as métricas.', 'error');
  }
}

async function classify() {
  if (!apiKey.value.trim()) {
    showMessage('Informe a chave de API para classificar.', 'error');
    apiKey.focus();
    return;
  }

  if (!message.value.trim()) {
    showMessage('Digite uma mensagem antes de classificar.', 'error');
    message.focus();
    return;
  }

  classifyButton.disabled = true;
  classifyButton.textContent = 'Classificando...';
  const started = performance.now();

  try {
    const headers = {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey.value
    };

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

    currentResult = {
      label: isSpam ? 'Spam' : 'Não spam',
      probability,
      version: data.versao,
      text: message.value.trim()
    };
    resultEmpty.classList.add('hidden');
    resultContent.classList.remove('hidden');
    copyButton.disabled = false;
    resultLabel.textContent = isSpam ? 'spam' : 'não spam';
    resultLabel.className = `result-label ${isSpam ? 'spam' : 'normal'}`;
    latencyLabel.textContent = `${elapsed} ms`;
    probabilityValue.textContent = probability.toLocaleString('pt-BR', {style: 'percent', minimumFractionDigits: 2});
    probabilityBar.style.width = `${probability * 100}%`;
    probabilityBar.style.background = isSpam ? '#c83f49' : '#18855b';
    servedBy.textContent = `respondido pela ${data.versao}`;
    addHistory(message.value.trim(), data.rotulo);
    showMessage('Predição realizada com sucesso.', 'success');
  } catch (error) {
    showMessage(error.message || 'API fora do ar.', 'error');
  } finally {
    await refreshMetrics();
    classifyButton.disabled = false;
    classifyButton.textContent = 'Classificar';
  }
}

async function sendLoad() {
  const button = document.querySelector('#loadButton');
  if (!apiKey.value.trim()) {
    showMessage('Informe a chave de API antes de enviar requisições.', 'error');
    apiKey.focus();
    return;
  }

  button.disabled = true;
  const originalText = button.textContent;

  for (let i = 0; i < 50; i += 1) {
    button.textContent = `Enviando ${i + 1}/50`;
    await fetch('/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey.value
      },
      body: JSON.stringify({texto: i % 2 ? 'A reunião foi remarcada para amanhã' : 'Ganhe dinheiro rápido clicando neste link'})
    }).catch(() => {});
  }

  await refreshMetrics();
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
  characterCount.textContent = `${message.value.length.toLocaleString('pt-BR')} / 2.000`;
  message.focus();
});
document.querySelector('#normalExample').addEventListener('click', () => {
  message.value = 'A reunião de amanhã foi remarcada para as 15h na sala 2.';
  characterCount.textContent = `${message.value.length.toLocaleString('pt-BR')} / 2.000`;
  message.focus();
});
message.addEventListener('input', () => {
  characterCount.textContent = `${message.value.length.toLocaleString('pt-BR')} / 2.000`;
});
document.querySelector('#clearButton').addEventListener('click', () => {
  message.value = '';
  characterCount.textContent = '0 / 2.000';
  currentResult = null;
  resultEmpty.classList.remove('hidden');
  resultContent.classList.add('hidden');
  copyButton.disabled = true;
  messageBox.className = 'message-box hidden';
  message.focus();
});
copyButton.addEventListener('click', async () => {
  if (!currentResult) return;
  const text = `Resultado: ${currentResult.label}\nConfiança: ${(currentResult.probability * 100).toFixed(2)}%\nModelo: ${currentResult.version}`;
  try {
    await navigator.clipboard.writeText(text);
    showMessage('Resultado copiado para a área de transferência.', 'success');
  } catch {
    showMessage('Não foi possível copiar o resultado.', 'error');
  }
});
document.querySelector('#clearHistory').addEventListener('click', () => {
  localStorage.removeItem('spamguard-history');
  renderHistory();
});
document.querySelector('#themeToggle').addEventListener('click', () => {
  const dark = document.body.classList.toggle('dark');
  localStorage.setItem('spamguard-theme', dark ? 'dark' : 'light');
});
if (localStorage.getItem('spamguard-theme') === 'dark') {
  document.body.classList.add('dark');
}
classifyButton.addEventListener('click', classify);
document.querySelector('#loadButton').addEventListener('click', sendLoad);
message.addEventListener('keydown', event => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') classify();
});

renderHistory();
checkHealth();
refreshMetrics();
setInterval(checkHealth, 30000);
setInterval(refreshMetrics, 5000);
