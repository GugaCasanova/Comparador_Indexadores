import requests
from datetime import datetime, timedelta
import pandas as pd
from bs4 import BeautifulSoup

class B3Client:
    def __init__(self):
        self.base_url = "https://www2.bmf.com.br/pages/portal/bmfbovespa/lumis/lum-taxas-referenciais-bmf-ptBR.asp"
    
    def get_di_futures(self, vencimento):
        """
        Busca taxas do DI Futuro para um determinado vencimento
        vencimento: 'F30' para Janeiro 2030
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(self.base_url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.find('table', {'id': 'tb_principal'})
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            venc = cols[0].text.strip()
                            if 'JAN/30' in venc:  # Procura por Janeiro 2030
                                taxa = cols[2].text.strip().replace(',', '.')  # Taxa de ajuste
                                taxa_float = float(taxa)
                                print(f"Taxa DI 2030 encontrada: {taxa_float}")
                                return taxa_float
                    print("Vencimento JAN/30 não encontrado na tabela")
                else:
                    print("Tabela não encontrada na página")
            return None
        except Exception as e:
            print(f"Erro ao buscar DI Futuro: {str(e)}")
            return None