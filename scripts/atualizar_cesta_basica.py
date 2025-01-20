import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re

def atualizar_cesta_basica():
    """Atualiza dados da cesta básica de São Paulo"""
    try:
        # URL da página principal de pesquisa da cesta básica
        url = "https://www.dieese.org.br/analisecestabasica"
        
        print(f"Acessando página principal: {url}")
        response = requests.get(url)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Procura o link mais recente da pesquisa
            links = []
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if '/analisecestabasica/' in href and 'cestabasica.html' in href:
                    links.append(href)
            
            if links:
                # Pega o link mais recente (primeiro da lista)
                ultimo_link = links[0]
                url_pesquisa = f"https://www.dieese.org.br{ultimo_link}"
                print(f"Acessando última pesquisa: {url_pesquisa}")
                
                response_pesquisa = requests.get(url_pesquisa)
                if response_pesquisa.status_code == 200:
                    soup_pesquisa = BeautifulSoup(response_pesquisa.content, 'html.parser')
                    
                    # Procura a primeira tabela (que contém os dados das capitais)
                    tabela = soup_pesquisa.find('table')
                    if tabela:
                        print("\nConteúdo da tabela:")
                        linhas = tabela.find_all('tr')
                        for linha in linhas:
                            print(f"Linha: {linha.get_text().strip()}")
                            
                        # Procura linha de São Paulo
                        for linha in linhas:
                            texto_linha = linha.get_text().strip()
                            if 'São Paulo' in texto_linha:
                                # Extrai o valor usando regex para encontrar o padrão "R$ XXX,XX"
                                valor_match = re.search(r'R\$\s*(\d+[,.]\d+)', texto_linha)
                                if valor_match:
                                    valor_texto = valor_match.group(1)
                                    valor = float(valor_texto.replace('.', '').replace(',', '.'))
                                    
                                    # Extrai data do URL (formato: AAAAMM)
                                    data_str = re.search(r'/(\d{6})cestabasica', url_pesquisa).group(1)
                                    ano = data_str[:4]
                                    mes = data_str[4:]
                                    data = f"{ano}-{mes}-30"
                                    
                                    # Atualiza CSV
                                    try:
                                        df = pd.read_csv('data/cesta_basica.csv')
                                    except:
                                        df = pd.DataFrame(columns=['data', 'valor'])
                                    
                                    nova_linha = pd.DataFrame([{'data': data, 'valor': valor}])
                                    df = pd.concat([df, nova_linha], ignore_index=True)
                                    df = df.drop_duplicates(subset=['data'])
                                    df = df.sort_values('data')
                                    
                                    df.to_csv('data/cesta_basica.csv', index=False)
                                    print(f"Dados atualizados: {data} - R$ {valor:.2f}")
                                    return
                        
                        print("Linha de São Paulo não encontrada na tabela")
                    else:
                        print("Tabela principal não encontrada")
            else:
                print("Nenhum link de pesquisa encontrado")
                
    except Exception as e:
        print(f"Erro ao atualizar dados da cesta básica: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    atualizar_cesta_basica() 