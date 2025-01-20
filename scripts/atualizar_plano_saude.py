import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

def atualizar_plano_saude():
    """Atualiza dados dos reajustes de planos de saúde"""
    try:
        # URL da página de notícias da ANS sobre reajustes
        url = "https://www.gov.br/ans/pt-br/assuntos/noticias/beneficiarios"
        
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Busca notícias sobre reajuste
        noticias = soup.find_all('article', class_='tileItem')
        for noticia in noticias:
            titulo = noticia.find('h2').text.lower()
            if 'reajuste' in titulo and 'plano' in titulo and 'individual' in titulo:
                data_noticia = noticia.find('span', class_='summary-view-icon').text
                link = noticia.find('a')['href']
                
                # Se encontrar notícia nova sobre reajuste, processa
                print(f"Nova notícia sobre reajuste encontrada: {titulo}")
                print(f"Data: {data_noticia}")
                print(f"Link: {link}")
                
                # Busca o valor do reajuste na página da notícia
                response_noticia = requests.get(link)
                soup_noticia = BeautifulSoup(response_noticia.content, 'html.parser')
                
                # Procura o valor do reajuste no texto
                texto = soup_noticia.find('div', class_='content').text.lower()
                # Implementar lógica para extrair o valor do reajuste
                
                # Atualiza o CSV com o novo reajuste
                # Implementar lógica de atualização
                
    except Exception as e:
        print(f"Erro ao verificar reajustes: {e}") 