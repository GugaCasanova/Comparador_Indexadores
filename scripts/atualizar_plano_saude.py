import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup

def atualizar_plano_saude():
    """Atualiza dados dos reajustes de planos de saúde"""
    try:
        # URL da tabela de reajustes da ANS
        url = "https://www.gov.br/ans/pt-br/assuntos/noticias/beneficiarios/ans-define-teto-de-reajuste-para-planos-de-saude-individuais-familiares-regulamentados"
        
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Busca a tabela com os reajustes históricos
        tabela = soup.find('table')
        
        if tabela:
            # Processa os dados da tabela
            dados = []
            for linha in tabela.find_all('tr')[1:]:  # Pula o cabeçalho
                colunas = linha.find_all('td')
                if len(colunas) >= 2:
                    ano = int(colunas[0].text.strip())
                    reajuste = float(colunas[1].text.strip().replace('%', '').replace(',', '.'))
                    dados.append({'data': f"{ano}-06-30", 'valor': reajuste})
            
            # Cria DataFrame e salva
            df = pd.DataFrame(dados)
            df.to_csv('data/plano_saude.csv', index=False)
            print("Dados do plano de saúde atualizados com sucesso!")
            
        else:
            print("Tabela de reajustes não encontrada na página da ANS")
            
    except Exception as e:
        print(f"Erro ao atualizar dados do plano de saúde: {e}") 