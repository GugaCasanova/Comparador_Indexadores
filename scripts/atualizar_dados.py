import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import json

def atualizar_gasolina():
    """
    Atualiza dados da gasolina da ANP usando os relatórios semanais
    """
    try:
        print("Atualizando dados da gasolina...")
        
        # Lê arquivo atual
        df_atual = pd.read_csv('data/gasolina.csv')
        ultima_data = pd.to_datetime(df_atual['data'].max())
        
        # URL base dos arquivos da ANP
        base_url = "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/shpc/dsan"
        
        # Headers para simular navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Lista para armazenar dados novos
        novos_dados = []
        
        # Para cada ano que queremos buscar (atual e anterior)
        for ano in [datetime.now().year, datetime.now().year - 1]:
            url = f"{base_url}/{ano}"
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Encontra links para arquivos Excel
            for link in soup.find_all('a', href=True):
                if 'semanal' in link['href'].lower() and '.xlsx' in link['href'].lower():
                    try:
                        # Baixa o arquivo Excel
                        excel_url = link['href']
                        df = pd.read_excel(excel_url)
                        
                        # Filtra apenas dados de São Paulo capital e gasolina comum
                        df = df[
                            (df['Município'] == 'SAO PAULO') & 
                            (df['Produto'] == 'GASOLINA COMUM')
                        ]
                        
                        # Calcula média mensal
                        df['Data'] = pd.to_datetime(df['Data da Coleta'])
                        df_mensal = df.groupby(df['Data'].dt.strftime('%Y-%m-01')).agg({
                            'Preço Médio Revenda': 'mean'
                        }).reset_index()
                        
                        # Adiciona aos novos dados se for mais recente que o último registro
                        for _, row in df_mensal.iterrows():
                            data = pd.to_datetime(row['Data'])
                            if data > ultima_data:
                                novos_dados.append({
                                    'data': data.strftime('%Y-%m-%d'),
                                    'valor': round(row['Preço Médio Revenda'], 2)
                                })
                                
                    except Exception as e:
                        print(f"Erro ao processar arquivo {excel_url}: {e}")
                        continue
        
        # Atualiza CSV se tiver dados novos
        if novos_dados:
            df_novo = pd.DataFrame(novos_dados)
            df_final = pd.concat([df_atual, df_novo]).drop_duplicates(subset=['data'])
            df_final = df_final.sort_values('data')
            df_final.to_csv('data/gasolina.csv', index=False)
            print(f"Dados da gasolina atualizados: {len(novos_dados)} novos registros")
        else:
            print("Nenhum dado novo da gasolina encontrado")
            
    except Exception as e:
        print(f"Erro ao atualizar gasolina: {e}")

def atualizar_fipezap():
    """
    Atualiza dados do FipeZap
    """
    try:
        print("Atualizando dados do FipeZap...")
        
        # Lê arquivo atual
        df_atual = pd.read_csv('data/fipezap.csv')
        ultima_data = pd.to_datetime(df_atual['data'].max())
        
        # URL da API do FipeZap
        url = "https://fipezap.zapimoveis.com.br/api/v1/indicators"
        
        # Headers necessários
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Faz request
        response = requests.get(url, headers=headers)
        data = response.json()
        
        # Processa dados novos
        novos_dados = []
        # ... código de processamento específico do FipeZap ...
        
        # Atualiza CSV se tiver dados novos
        if novos_dados:
            df_novo = pd.DataFrame(novos_dados)
            df_final = pd.concat([df_atual, df_novo]).drop_duplicates()
            df_final.to_csv('data/fipezap.csv', index=False)
            print(f"Dados do FipeZap atualizados: {len(novos_dados)} novos registros")
        else:
            print("Nenhum dado novo do FipeZap encontrado")
            
    except Exception as e:
        print(f"Erro ao atualizar FipeZap: {e}")

def atualizar_dados_energia():
    """
    Atualiza dados de energia da ANEEL
    """
    try:
        print("Atualizando dados da energia...")
        
        # Lê o arquivo atual
        df_atual = pd.read_csv('data/energia.csv')
        df_atual['data'] = pd.to_datetime(df_atual['data'])
        
        # Obtém a última data no arquivo
        ultima_data = df_atual['data'].max()
        
        # URL correta do dataset da ANEEL
        url = "https://www.aneel.gov.br/dados/tarifas-residenciais/download"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            # Tenta baixar diretamente o arquivo mais recente
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Salva temporariamente o arquivo
            with open('temp_energia.csv', 'wb') as f:
                f.write(response.content)
            
            # Lê o arquivo CSV
            df_novo = pd.read_csv('temp_energia.csv', sep=';', decimal=',')
            
            # Remove o arquivo temporário
            import os
            os.remove('temp_energia.csv')
            
            # Processa as colunas
            df_novo['data'] = pd.to_datetime(df_novo['Data Início Vigência'], format='%d/%m/%Y')
            df_novo['valor'] = pd.to_numeric(df_novo['Tarifa Convencional B1'], errors='coerce')
            
            # Filtra apenas registros mais recentes
            df_novo = df_novo[df_novo['data'] > ultima_data]
            
            if not df_novo.empty:
                # Prepara os novos registros
                novos_registros = df_novo[['data', 'valor']].copy()
                
                # Concatena com dados existentes
                df_completo = pd.concat([df_atual, novos_registros])
                
                # Ordena e remove duplicatas
                df_completo = df_completo.sort_values('data')
                df_completo = df_completo.drop_duplicates(subset=['data'])
                
                # Salva o arquivo atualizado
                df_completo.to_csv('data/energia.csv', index=False)
                print(f"Adicionados {len(df_novo)} novos registros de energia")
            else:
                print("Nenhum dado novo de energia encontrado")
                
        except Exception as e:
            print(f"Erro ao baixar arquivo da ANEEL: {e}")
            print("Tentando método alternativo...")
            
            # Método alternativo usando a API
            api_url = "https://dadosabertos.aneel.gov.br/api/3/action/datastore_search"
            params = {
                'resource_id': '5e9f0d17-0245-4c93-8c0c-2c5b0bdc5014',
                'limit': 5000,
                'sort': 'PeriodoReferencia desc'
            }
            
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            dados = response.json()['result']['records']
            
            novos_registros = []
            for registro in dados:
                data = pd.to_datetime(registro['PeriodoReferencia'])
                if data > ultima_data:
                    valor = float(registro['ValorTarifaResidencial'].replace(',', '.'))
                    novos_registros.append({
                        'data': data,
                        'valor': valor
                    })
            
            if novos_registros:
                df_novos = pd.DataFrame(novos_registros)
                df_completo = pd.concat([df_atual, df_novos])
                df_completo = df_completo.sort_values('data')
                df_completo = df_completo.drop_duplicates(subset=['data'])
                df_completo.to_csv('data/energia.csv', index=False)
                print(f"Adicionados {len(novos_registros)} novos registros de energia (método alternativo)")
            else:
                print("Nenhum dado novo de energia encontrado (método alternativo)")
            
    except Exception as e:
        print(f"Erro ao atualizar dados da energia: {e}")
        import traceback
        print(traceback.format_exc())

def main():
    print(f"Iniciando atualização de dados: {datetime.now()}")
    atualizar_gasolina()
    atualizar_fipezap()
    atualizar_dados_energia()
    print("Atualização concluída!")

if __name__ == "__main__":
    main() 