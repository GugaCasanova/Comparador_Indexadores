from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from functools import lru_cache
import yfinance as yf
import time
from bs4 import BeautifulSoup
from io import StringIO

app = Flask(__name__)

# Códigos das séries no BCB
codigos_bcb = {
    'selic': 432,      # Meta Selic definida pelo Copom
    'ipca': 433,       # IPCA - Var. % mensal
    'cdi': 4389,       # CDI
    'igpm': 189,       # IGP-M
    'dolar': 1,        # Dólar comercial
    'cesta': 27864,    # Cesta Básica - São Paulo
    'salario': 1619,   # Salário Mínimo
    'gasolina': 32848, # Preço médio gasolina - São Paulo
    'energia': 28752,  # Tarifa média energia residencial - São Paulo
    'aluguel': 28140,  # Índice FipeZap - Aluguel - São Paulo
}

def retry_request(func, retries=3, delay=1):
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            if attempt == retries - 1:
                raise e
            print(f"Tentativa {attempt + 1} falhou, tentando novamente em {delay} segundos...")
            time.sleep(delay)

@lru_cache(maxsize=128)
def obter_dados_bcb_cached(codigo_serie, data_inicial_str, data_final_str):
    def make_request():
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados"
        params = {
            'formato': 'json',
            'dataInicial': data_inicial_str,
            'dataFinal': data_final_str
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    try:
        return retry_request(make_request)
    except Exception as e:
        print(f"Erro ao buscar dados do BCB para série {codigo_serie}: {str(e)}")
        return []

def obter_dados_ibovespa(data_inicial, data_final):
    try:
        print(f"Buscando dados do Ibovespa de {data_inicial} até {data_final}")
        
        ibov = yf.download(
            '^BVSP',
            start=data_inicial.strftime('%Y-%m-%d'),
            end=data_final.strftime('%Y-%m-%d'),
            interval='1d',
            progress=False
        )
        
        if ibov.empty:
            print("Sem dados do Ibovespa")
            return []
        
        dados = []
        for index, row in ibov.iterrows():
            try:
                close_value = float(row['Close'])
                dados.append({
                    'data': index.strftime('%d/%m/%Y'),
                    'valor': str(close_value)
                })
            except Exception as e:
                print(f"Erro ao processar linha: {e}")
                continue
        
        return dados
    except Exception as e:
        print(f"Erro ao buscar dados do Ibovespa: {str(e)}")
        return []

def obter_dados_cesta_basica(data_inicial, data_final):
    try:
        print(f"Buscando dados da cesta básica...")
        
        url = "https://raw.githubusercontent.com/GugaCasanova/Comparador_Indexadores/main/data/cesta_basica.csv"
        
        # Lê o CSV
        df = pd.read_csv(url)
        df['data'] = pd.to_datetime(df['data'])
        df = df.sort_values('data')
        
        # Filtra pelo período
        mask = (df['data'] >= data_inicial) & (df['data'] <= data_final)
        df_filtrado = df.loc[mask]
        
        # Converte para o formato esperado
        dados = []
        for _, row in df_filtrado.iterrows():
            dados.append({
                'data': row['data'].strftime('%d/%m/%Y'),
                'valor': str(row['valor'])
            })
        
        return dados
        
    except Exception as e:
        print(f"Erro ao buscar dados da Cesta Básica: {str(e)}")
        return []

def obter_dados_bigmac(data_inicial, data_final):
    try:
        print(f"Buscando dados do Big Mac de {data_inicial.strftime('%d/%m/%Y')} até {data_final.strftime('%d/%m/%Y')}...")
        
        # URL do dataset oficial do The Economist no GitHub
        url = "https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/output-data/big-mac-full-index.csv"
        
        # Lê o CSV
        df = pd.read_csv(url)
        
        # Filtra apenas dados do Brasil
        df = df[df['iso_a3'] == 'BRA']
        
        # Converte data e valor
        df['data'] = pd.to_datetime(df['date'])
        df['valor'] = pd.to_numeric(df['local_price'], errors='coerce')
        
        # Remove linhas com valores nulos
        df = df.dropna(subset=['data', 'valor'])
        
        # Ordena por data
        df = df.sort_values('data')
        
        # Filtra pelo período
        mask = (df['data'] >= data_inicial) & (df['data'] <= data_final)
        df_filtrado = df.loc[mask]
        
        # Preenche os meses faltantes com o último valor disponível
        idx = pd.date_range(start=data_inicial, end=data_final, freq='MS')
        df_completo = df_filtrado.set_index('data').reindex(idx, method='ffill')
        df_completo = df_completo.reset_index()
        df_completo = df_completo.rename(columns={'index': 'data'})
        
        # Remove valores nulos após o preenchimento
        df_completo = df_completo.dropna(subset=['valor'])
        
        # Converte para o formato esperado
        dados = []
        for _, row in df_completo.iterrows():
            dados.append({
                'data': row['data'].strftime('%d/%m/%Y'),
                'valor': str(row['valor'])
            })
        
        print(f"Dados obtidos: {len(dados)} registros")
        if dados:
            print(f"Período: de {dados[0]['data']} até {dados[-1]['data']}")
            print(f"Valores: de R$ {float(dados[0]['valor']):.2f} até R$ {float(dados[-1]['valor']):.2f}")
        
        return dados
        
    except Exception as e:
        print(f"Erro ao buscar dados do Big Mac: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []

def obter_dados_fipezap(data_inicial, data_final):
    try:
        print(f"Buscando dados do FipeZap para período {data_inicial} até {data_final}...")
        
        url = "https://raw.githubusercontent.com/GugaCasanova/Comparador_Indexadores/main/data/fipezap.csv"
        
        # Faz a requisição com timeout e verifica o status
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        content = response.text
        if not content.strip():
            print("URL retornou conteúdo vazio")
            return []
            
        # Verifica se o conteúdo parece ser um CSV válido
        if ',' not in content and ';' not in content:
            print("Conteúdo não parece ser um CSV válido")
            print(f"Primeiros 100 caracteres: {content[:100]}")
            return []
        
        # Tenta diferentes separadores e encodings
        for sep in [',', ';']:
            try:
                df = pd.read_csv(StringIO(content), sep=sep)
                if not df.empty:
                    break
            except:
                continue
        
        if df.empty:
            print("Não foi possível carregar dados válidos do CSV")
            return []
        
        # Resto do processamento
        df['data'] = pd.to_datetime(df['data'])
        df = df.sort_values('data')
        
        mask = (df['data'] >= data_inicial) & (df['data'] <= data_final)
        df_filtrado = df.loc[mask]
        
        dados = []
        for _, row in df_filtrado.iterrows():
            dados.append({
                'data': row['data'].strftime('%d/%m/%Y'),
                'valor': str(row['valor'])
            })
        
        print(f"Processados {len(dados)} registros do FipeZap")
        return dados
        
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição HTTP: {e}")
        return []
    except Exception as e:
        print(f"Erro ao processar dados do FipeZap: {e}")
        import traceback
        print(traceback.format_exc())
        return []

def obter_dados_gasolina(data_inicial, data_final):
    try:
        print(f"Buscando dados da gasolina para período {data_inicial} até {data_final}...")
        
        # URL do arquivo CSV com dados da gasolina
        url = "https://raw.githubusercontent.com/GugaCasanova/Comparador_Indexadores/main/data/gasolina.csv"
        
        # Faz a requisição com timeout
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        content = response.text
        if not content.strip():
            print("URL retornou conteúdo vazio")
            return []
        
        # Lê o CSV
        df = pd.read_csv(StringIO(content))
        df['data'] = pd.to_datetime(df['data'])
        df = df.sort_values('data')
        
        # Filtra pelo período
        mask = (df['data'] >= data_inicial) & (df['data'] <= data_final)
        df_filtrado = df.loc[mask]
        
        if df_filtrado.empty:
            print("Nenhum dado encontrado para o período especificado")
            return []
        
        # Converte para o formato esperado
        dados = []
        for _, row in df_filtrado.iterrows():
            dados.append({
                'data': row['data'].strftime('%d/%m/%Y'),
                'valor': str(row['valor'])
            })
        
        print(f"Processados {len(dados)} registros da gasolina")
        return dados
        
    except Exception as e:
        print(f"Erro ao buscar dados da Gasolina: {str(e)}")
        return []

def obter_dados_energia(data_inicial, data_final):
    try:
        print(f"Buscando dados de energia para período {data_inicial} até {data_final}...")
        
        # URL do arquivo CSV com dados da energia
        url = "https://raw.githubusercontent.com/GugaCasanova/Comparador_Indexadores/main/data/energia.csv"
        
        # Faz a requisição com timeout
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        content = response.text
        if not content.strip():
            print("URL retornou conteúdo vazio")
            return []
        
        # Lê o CSV
        df = pd.read_csv(StringIO(content))
        df['data'] = pd.to_datetime(df['data'])
        df = df.sort_values('data')
        
        # Filtra pelo período
        mask = (df['data'] >= data_inicial) & (df['data'] <= data_final)
        df_filtrado = df.loc[mask]
        
        if df_filtrado.empty:
            print("Nenhum dado encontrado para o período especificado")
            return []
        
        # Converte para o formato esperado
        dados = []
        for _, row in df_filtrado.iterrows():
            dados.append({
                'data': row['data'].strftime('%d/%m/%Y'),
                'valor': str(row['valor'])
            })
        
        print(f"Processados {len(dados)} registros de energia")
        return dados
        
    except Exception as e:
        print(f"Erro ao buscar dados de Energia: {str(e)}")
        return []

def processar_dados_indicador(indicador, periodo_str):
    hoje = datetime.now()
    periodo = int(periodo_str)
    data_inicial = hoje - timedelta(days=periodo * 30)
    data_final = hoje
    
    try:
        if indicador == 'fipezap':
            print(f"Processando FipeZap para período de {data_inicial} até {data_final}")
            
            # Lê direto do CSV
            url = "https://raw.githubusercontent.com/GugaCasanova/Comparador_Indexadores/main/data/fipezap.csv"
            df = pd.read_csv(url)
            df['data'] = pd.to_datetime(df['data'])
            
            # Filtra pelo período
            mask = (df['data'] >= data_inicial) & (df['data'] <= data_final)
            df = df.loc[mask]
            
            if df.empty:
                print("Nenhum dado do FipeZap encontrado para o período")
                return [], []
            
            # Ordena por data
            df = df.sort_values('data')
            
            print(f"Encontrados {len(df)} registros do FipeZap")
            print(f"Primeiro registro: {df['data'].iloc[0]} - R$ {df['valor'].iloc[0]}")
            print(f"Último registro: {df['data'].iloc[-1]} - R$ {df['valor'].iloc[-1]}")
            
            # Converte para o formato esperado
            datas = df['data'].dt.strftime('%Y-%m-%d').tolist()
            valores = df['valor'].tolist()
            
            return datas, valores
            
        elif indicador == 'gasolina':
            dados = obter_dados_gasolina(data_inicial, data_final)
            if not dados:
                return [], []
                
            df = pd.DataFrame(dados)
            df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
            df = df.dropna()
            df = df.sort_values('data')
            
            datas = df['data'].dt.strftime('%Y-%m-%d').tolist()
            valores = df['valor'].tolist()
            return datas, valores
            
        elif indicador in ['energia', 'aluguel']:
            data_inicial_str = data_inicial.strftime('%d/%m/%Y')
            data_final_str = data_final.strftime('%d/%m/%Y')
            dados = obter_dados_bcb_cached(codigos_bcb[indicador], data_inicial_str, data_final_str)
            
            if not dados:
                print(f"Nenhum dado retornado para {indicador}")
                return [], []
            
            df = pd.DataFrame(dados)
            df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
            df['valor'] = pd.to_numeric(df['valor'].str.replace(',', '.'), errors='coerce')
            
            # Tratamentos específicos
            if indicador == 'aluguel':
                df['valor'] = df['valor'] * 10  # Converte para R$
            elif indicador == 'energia':
                df['valor'] = df['valor'] / 100  # Converte para R$/kWh
            elif indicador == 'gasolina':
                df['valor'] = df['valor']  # Já está em R$/litro
                
            df = df.dropna()
            df = df.sort_values('data')
            
            datas = df['data'].dt.strftime('%Y-%m-%d').tolist()
            valores = df['valor'].tolist()
            
            return datas, valores
            
        else:
            # Para IPCA e IGP-M, pega 12 meses a mais para calcular o acumulado
            if indicador in ['ipca', 'igpm']:
                data_inicial = data_inicial - timedelta(days=365)
                
            data_inicial_str = data_inicial.strftime('%d/%m/%Y')
            data_final_str = data_final.strftime('%d/%m/%Y')
            
            if indicador == 'bigmac':
                dados = obter_dados_bigmac(data_inicial, data_final)
            elif indicador == 'cesta':
                dados = obter_dados_cesta_basica(data_inicial, data_final)
            elif indicador == 'ibov':
                dados = obter_dados_ibovespa(data_inicial, data_final)
            else:
                dados = obter_dados_bcb_cached(codigos_bcb[indicador], data_inicial_str, data_final_str)
            
            if not dados:
                print(f"Nenhum dado retornado para {indicador}")
                return [], []
            
            df = pd.DataFrame(dados)
            df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
            df['valor'] = pd.to_numeric(df['valor'].str.replace(',', '.'), errors='coerce')
            df = df.dropna()
            df = df.set_index('data')
            
            # Tratamento especial para IPCA e IGP-M (acumulado 12 meses)
            if indicador in ['ipca', 'igpm']:
                df['valor_acum'] = (1 + df['valor']/100).rolling(window=12).apply(lambda x: np.prod(x) - 1) * 100
                df = df.dropna()
                df['valor'] = df['valor_acum']
            
            # Agrupa por mês pegando o último valor
            df = df.resample('ME').last()
            df = df.dropna()
            
            # Filtra pelo período solicitado
            df = df[df.index >= data_inicial]
            
            if df.empty:
                print(f"Sem dados para o período solicitado: {indicador}")
                return [], []
            
            datas = df.index.strftime('%Y-%m-%d').tolist()
            valores = df['valor'].tolist()
            
            return datas, valores
            
    except Exception as e:
        print(f"Erro ao processar dados de {indicador}: {str(e)}")
        return [], []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dados')
def dados():
    try:
        indicador1 = request.args.get('indicador1', 'selic')
        indicador2 = request.args.get('indicador2', 'ipca')
        periodo = request.args.get('periodo', '12')
        
        datas1, valores1 = processar_dados_indicador(indicador1, periodo)
        datas2, valores2 = processar_dados_indicador(indicador2, periodo)
        
        return jsonify({
            'datas': datas1,
            'valores1': valores1,
            'valores2': valores2,
            'indicador1': indicador1.upper(),
            'indicador2': indicador2.upper()
        })
    except Exception as e:
        print(f"Erro na rota /dados: {str(e)}")
        return jsonify({
            'datas': [],
            'valores1': [],
            'valores2': [],
            'indicador1': indicador1.upper() if 'indicador1' in locals() else '',
            'indicador2': indicador2.upper() if 'indicador2' in locals() else ''
        })

def testar_acesso_cesta():
    url = "https://raw.githubusercontent.com/GugaCasanova/Comparador_Indexadores/main/data/cesta_basica.csv"
    
    try:
        print("Testando acesso à URL...")
        response = requests.get(url)
        print(f"Status code: {response.status_code}")
        print("Conteúdo da resposta:", response.text[:200])
        
        if response.status_code == 404:
            print("Arquivo não encontrado. Verifique se o caminho está correto.")
            return
            
        print("\nTentando ler como DataFrame...")
        df = pd.read_csv(url)
        print("\nPrimeiras linhas:")
        print(df.head())
        
    except Exception as e:
        print(f"Erro: {str(e)}")

def testar_acesso_fipezap():
    url = "https://raw.githubusercontent.com/GugaCasanova/Comparador_Indexadores/main/data/fipezap.csv"
    
    try:
        print("Testando acesso à URL do FipeZap...")
        response = requests.get(url)
        print(f"Status code: {response.status_code}")
        print("Conteúdo da resposta:", response.text[:200])
        
        if response.status_code == 404:
            print("Arquivo não encontrado. Verifique se o caminho está correto.")
            return
            
        print("\nTentando ler como DataFrame...")
        df = pd.read_csv(url)
        print("\nPrimeiras linhas:")
        print(df.head())
        
    except Exception as e:
        print(f"Erro: {str(e)}")

testar_acesso_cesta()
testar_acesso_fipezap()

if __name__ == '__main__':
    app.run(debug=True) 