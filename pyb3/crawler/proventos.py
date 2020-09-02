

import requests
import pandas as pd
from datetime import datetime

def todate(data): 
    return datetime.strptime(data, "%d/%m/%Y").date() if type(data) == str else data

def proventos(papel):
    url=f'https://statusinvest.com.br/acao/companytickerprovents?ticker={papel}&chartProventsType=2'
    dados = requests.get(url).json()
    dados = pd.DataFrame(dados['assetEarningsModels'])[['ed', 'pd', 'et', 'etd', 'sv']]
    dados.columns = ['data_neg', 'data_pgto', 'tipo', 'descricao', 'valor']
    dados['valor'] = dados.valor.str.replace(',','.').astype(float)
    dados['data_neg'] = pd.to_datetime([todate(i) for i in dados['data_neg']])
    dados['data_pgto'] = pd.to_datetime([todate(i) for i in dados['data_pgto']])
    return dados







