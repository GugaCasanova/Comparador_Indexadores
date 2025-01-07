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

            // Converte as datas para objetos Date e ajusta para meio-dia UTC
            const dates = data.datas.map(d => {
                const date = new Date(d);
                date.setUTCHours(12);  // Define para meio-dia UTC para evitar problemas de timezone
                return date;
            });

            // Configuração do primeiro indicador (azul)
            const trace1 = {
                x: dates,
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
                x: dates,
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
                x: dates,
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
                x: dates,
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
                    },
                    tickformat: '%b %Y',  // Formato dos ticks do eixo X
                    hoverformat: '%B/%Y'  // Formato do hover
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
                },
                hovermode: 'x unified',
                hoverlabel: {
                    bgcolor: '#282a36',
                    bordercolor: '#282a36',
                    font: {
                        color: '#f8f8f2'
                    }
                }
            };

            // Configurações do hover com efeito neon
            [trace1, trace2].forEach(trace => {
                trace.hovertemplate =
                    '<b>%{x|%d/%m/%Y}</b><br>' +  // Formato brasileiro de data
                    '%{y:.2f}<br>' +
                    '<extra></extra>';
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

// Formatadores para cada tipo de indicador
const formatadores = {
    'energia': (valor) => `R$ ${parseFloat(valor).toFixed(2)}/kWh`,
    'cesta': (valor) => `R$ ${parseFloat(valor).toFixed(2)}`,
    'gasolina': (valor) => `R$ ${parseFloat(valor).toFixed(2)}/L`,
    'aluguel': (valor) => `R$ ${parseFloat(valor).toFixed(2)}/m²`,
    'default': (valor) => `${parseFloat(valor).toFixed(2)}%`
};

// Cores para cada indicador
const cores = {
    'energia': '#4CAF50',    // Verde
    'cesta': '#FF9800',      // Laranja
    'gasolina': '#E91E63',   // Rosa
    'aluguel': '#9C27B0',    // Roxo
    'default': '#2196F3'     // Azul
};

// Função para formatar o valor
function formatarValor(indicador, valor) {
    const formatador = formatadores[indicador] || formatadores.default;
    return formatador(valor);
}

// Função para formatar a data corretamente
function formatarData(data) {
    const dataObj = new Date(data);
    const mes = dataObj.toLocaleString('pt-BR', { month: 'long' });
    const ano = dataObj.getFullYear();
    return `${mes}/${ano}`;
}