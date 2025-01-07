// Função para determinar se o indicador usa valor nominal
const isValorNominal = (indicador) => [
    'DOLAR',
    'IBOV',
    'CESTA',
    'SALARIO',
    'BIGMAC',
    'FIPEZAP',
    'GASOLINA',
    'ENERGIA',
    'ALUGUEL'
].includes(indicador);

// Função para mostrar mensagens de erro
function mostrarErro(mensagem) {
    const grafico = document.getElementById('grafico');
    grafico.style.opacity = '1';

    // Remove loading se existir
    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        loadingEl.remove();
    }

    // Mostra mensagem de erro
    const errorMsg = document.createElement('div');
    errorMsg.id = 'error-message';
    errorMsg.innerHTML = mensagem;
    errorMsg.style.position = 'absolute';
    errorMsg.style.top = '50%';
    errorMsg.style.left = '50%';
    errorMsg.style.transform = 'translate(-50%, -50%)';
    errorMsg.style.color = '#ff0000';
    errorMsg.style.fontSize = '20px';
    grafico.appendChild(errorMsg);

    // Limpa o erro após 3 segundos
    setTimeout(() => {
        const errorMsg = document.getElementById('error-message');
        if (errorMsg) {
            errorMsg.remove();
        }
    }, 3000);
}

function atualizarGrafico() {
    const indicador1 = document.getElementById('indicador1').value;
    const indicador2 = document.getElementById('indicador2').value;
    const periodo = document.getElementById('periodo').value;
    const check1 = document.getElementById('check1').checked;
    const check2 = document.getElementById('check2').checked;

    // Remove mensagens de erro anteriores
    const errorMsg = document.getElementById('error-message');
    if (errorMsg) {
        errorMsg.remove();
    }

    // Mostra loading
    const grafico = document.getElementById('grafico');
    grafico.style.opacity = '0.5';
    grafico.style.position = 'relative';

    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        loadingEl.remove();
    }

    const loading = document.createElement('div');
    loading.id = 'loading';
    loading.innerHTML = 'Carregando...';
    loading.style.position = 'absolute';
    loading.style.top = '50%';
    loading.style.left = '50%';
    loading.style.transform = 'translate(-50%, -50%)';
    loading.style.color = '#fff';
    loading.style.fontSize = '20px';
    grafico.appendChild(loading);

    fetch(`/dados?indicador1=${indicador1}&indicador2=${indicador2}&periodo=${periodo}`)
        .then(response => response.json())
        .then(data => {
            // Remove loading
            grafico.style.opacity = '1';
            const loadingEl = document.getElementById('loading');
            if (loadingEl) loadingEl.remove();

            // Verifica se há dados válidos
            if (!data.datas || !data.datas.length ||
                (!data.valores1.length && !data.valores2.length)) {
                throw new Error('Dados não disponíveis');
            }

            // Configuração do primeiro indicador (azul)
            const trace1 = {
                x: data.datas,
                y: data.valores1,
                name: data.indicador1,
                type: 'scatter',
                visible: check1 ? true : 'legendonly',
                yaxis: 'y',
                line: {
                    color: '#4da6ff',
                    width: 2,
                    shape: 'linear'
                }
            };

            // Adiciona a sombra como uma segunda linha logo abaixo
            const shadow1 = {
                x: data.datas,
                y: data.valores1.map(v => v * 0.995),
                name: data.indicador1 + '_shadow',
                type: 'scatter',
                visible: check1 ? true : 'legendonly',
                yaxis: 'y',
                mode: 'lines',
                line: {
                    color: 'rgba(77, 166, 255, 0.05)',
                    width: 8,
                    shape: 'linear'
                },
                showlegend: false,
                hoverinfo: 'skip'
            };

            // Configuração do segundo indicador (verde)
            const trace2 = {
                x: data.datas,
                y: data.valores2,
                name: data.indicador2,
                type: 'scatter',
                visible: check2 ? true : 'legendonly',
                yaxis: 'y2',
                line: {
                    color: '#50fa7b',
                    width: 2,
                    shape: 'linear'
                }
            };

            // Adiciona a sombra como uma segunda linha logo abaixo
            const shadow2 = {
                x: data.datas,
                y: data.valores2.map(v => v * 0.995),
                name: data.indicador2 + '_shadow',
                type: 'scatter',
                visible: check2 ? true : 'legendonly',
                yaxis: 'y2',
                mode: 'lines',
                line: {
                    color: 'rgba(80, 250, 123, 0.05)',
                    width: 8,
                    shape: 'linear'
                },
                showlegend: false,
                hoverinfo: 'skip'
            };

            const layout = {
                title: {
                    text: 'Comparação de Indicadores',
                    font: {
                        color: '#ffffff',
                        size: 24
                    }
                },
                showlegend: false,
                height: 700,
                xaxis: {
                    title: 'Data',
                    gridcolor: '#333333',
                    linecolor: '#333333',
                    tickfont: {
                        color: '#ffffff'
                    }
                },
                yaxis: {
                    title: data.indicador1,
                    titlefont: { color: '#4da6ff' },
                    tickfont: { color: '#ffffff' },
                    gridcolor: '#333333',
                    linecolor: '#333333',
                    side: 'left'
                },
                yaxis2: {
                    title: data.indicador2,
                    titlefont: { color: '#50fa7b' },
                    tickfont: { color: '#ffffff' },
                    overlaying: 'y',
                    side: 'right',
                    gridcolor: '#333333',
                    linecolor: '#333333',
                    showgrid: false
                },
                plot_bgcolor: 'transparent',
                paper_bgcolor: 'transparent',
                font: {
                    color: '#ffffff'
                },
                margin: {
                    l: 60,
                    r: 60,
                    t: 80,
                    b: 50
                }
            };

            // Configurações do hover com efeito neon
            [trace1, trace2].forEach(trace => {
                trace.hoverlabel = {
                    bgcolor: 'rgba(42, 47, 66, 0.9)',
                    bordercolor: 'rgba(42, 47, 66, 0.9)',
                    font: {
                        color: '#ffffff',
                        size: 12
                    }
                };
                trace.hoverinfo = 'x+y';
                trace.mode = 'lines';  // Apenas linhas para efeito mais limpo
            });

            Plotly.newPlot('grafico', [shadow1, trace1, shadow2, trace2], layout, {
                responsive: true,
                displayModeBar: false,
                scrollZoom: true,
                modeBarButtonsToRemove: ['autoScale2d'],
                toImageButtonOptions: {
                    format: 'png',
                    filename: 'comparador_indicadores',
                    height: 700,
                    width: 1200,
                    scale: 2
                }
            });
        })
        .catch(error => {
            console.error('Erro:', error);
            mostrarErro('Erro ao carregar os dados');
        });
}

// Adiciona debounce para evitar múltiplas chamadas
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Usa debounce nas chamadas de atualização
const atualizarGraficoDebounced = debounce(atualizarGrafico, 300);

document.addEventListener('DOMContentLoaded', function () {
    atualizarGrafico();

    document.getElementById('indicador1').addEventListener('change', atualizarGraficoDebounced);
    document.getElementById('indicador2').addEventListener('change', atualizarGraficoDebounced);
    document.getElementById('periodo').addEventListener('change', atualizarGraficoDebounced);
    document.getElementById('check1').addEventListener('change', atualizarGraficoDebounced);
    document.getElementById('check2').addEventListener('change', atualizarGraficoDebounced);
});

// No objeto de formatação de valores
const formatadores = {
    // ... outros formatadores ...
    'energia': (valor) => `R$ ${parseFloat(valor).toFixed(2)}/kWh`,
    // ... resto dos formatadores ...
};

// No objeto de cores (se existir)
const cores = {
    // ... outras cores ...
    'energia': '#4CAF50',  // Verde para energia
    // ... resto das cores ...
};