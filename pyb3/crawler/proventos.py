

import requests
import pandas as pd

def proventos(papel):
    url=f'https://statusinvest.com.br/acao/companytickerprovents?ticker={papel}&chartProventsType=2'
    dados = requests.get(url).json()
    dados = pd.DataFrame(dados['assetEarningsModels'])[['ed', 'pd', 'et', 'etd', 'sv']]
    dados.columns = ['data_neg', 'data_pgto', 'tipo', 'descricao', 'valor']
    return dados







