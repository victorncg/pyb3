

import requests
import pandas as pd
import numpy as np

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}


# lib usada para buscar os dados de series ações


# classe para manipular uma serie de uma tivo
class Serie(pd.DataFrame):
 
    @property
    def _constructor(self):
        return Serie

    @property
    def _constructor_sliced(self):
        return pd.Series

    # Gera a coluna de retornos dia a  tipo = 0 gera o retorno por ln
    def gera_retornos(self, tipo=0):
        df = self.copy()
        df['retornos'] = np.log(df.price/df.price.shift(-1)) if not tipo else df.price/df.price.shift(-1)-1
        return self._constructor(df.values.tolist(), columns = df.columns)

    # Gera coluna com as médias moveis
    def media_movel(self, n):
        df = self.copy()
        
        df['media_movel'] = df.price.iloc[::-1].rolling(window=n).mean()    
        return self._constructor(df.values.tolist(), columns = df.columns)
    
    
    # calcula o coeficiente beta. O tipo é o tipo de retornos.
    def coefbeta(self, tipo=0):
        if 'retornos' not in self: self = self.gera_retornos()
        d = 1 if len(str(min(self.date))) > 8 else 0
        t = [min(self.date), max(self.date)]
        ibov = Carteira('IBOV', intraday=d, periodo=t)['IBOV']
        ibov = ibov.gera_retornos()
      #  return ibov, self
        df = self[['date', 'retornos']].merge(ibov[['date', 'retornos']], on='date')
        df[['retornos_x', 'retornos_y']].cov().values[0][1]
        beta = df[['retornos_x', 'retornos_y']].cov().values[0][1]/ibov.retornos.var()
        return beta
    
    # desvio padrão dos retornos
    def std(self, ddof=0):
        if 'retornos' not in self: self = self.gera_retornos()
        return self.retornos.std(ddof = ddof)
    
    

# Busca as séries de preços dos ativos no site da uol
class UolSeries:
    def __init__(self):
        self.__id = self.__lista_ids()
        
    # gera a lista de ids dos ativos no site da uol
    def __lista_ids(self):
        url = f"""http://cotacoes.economia.uol.com.br/ws/asset/stock/list?size=10000"""
        response = requests.get(url, headers=headers).json()
        return response
    
    # retorna as informações dos ativos
    def __acao(self, papel):
        papel = [i+'.SA' for i in papel]
        ids = [i for i in self.__id['data'] if i['code'] in papel]
        if 'IBOV.SA' in papel:
            ids+=[{'idt':'1', 'code':'IBOV.SA'}]
        return ids
    
    # pesquisa a serie de preços de um ativo
    def __pesquisar(self, id, tipo):
        tipo = 'intraday/list' if tipo == 'intraday' else 'interday/list/years'
        id = id['idt']
        url = f"""https://api.cotacoes.uol.com/asset/{tipo}/?format=JSON&fields=date,price,high,low,open,volume,close,bid,ask&item={id}&"""
        response = requests.get(url, headers=headers).json()
        return response
    
    # dados históricos
    def historico(self, papel, periodo, dataini):
        ids = self.__acao(papel)
        series = [(self.__pesquisar(i, 'interday'), i['code'].replace('.SA','') ) for i in ids]


        # tratando o periodo
        if len(str(min(periodo))) != len(str(max(periodo))):
            print('ERRO: O período inicial e final tem que ter o mesmo formato!!')
            return
        if dataini:
            dini, dfin = dataini, 99999999
            lendt = len(str(dataini))
        else:
            dini, dfin = min(periodo), max(periodo)
            lendt = len(str(min(periodo)))
     #   return [i for i in series[0][0]['docs'] if dini<=int(i['date'][:lendt])<=dfin]
        dfs = [(Serie([i for i in series[n][0]['docs'] if dini<=int(i['date'][:lendt])<=dfin]), series[n][1]) for n, _ in enumerate(ids)]
        
        for i, p in dfs:
            if len(i)>0:
                i['dataref'] = (i.date.astype(float)/1000000).astype(int)
                i['ativo'] = p
        
        cols = ['ativo','dataref','price','high','low','open','volume','close','bid','ask']
        rename = {'price':'preco', 'high':'maximo', 'low':'minimo', 'open':'abertura', 'close':'fech'}

        return [[df[0][cols].rename(columns=rename), df[1]] for df in dfs if len(df[0])]
    
    # intraday do último dia
    def intraday(self, papel):
        ids = self.__acao(papel)
        series = [(self.__pesquisar(i, 'intraday'), i['code'].replace('.SA','') ) for i in ids]
        
        dfs = [(Serie([i for i in series[n][0]['docs']]), series[n][1]) for n, _ in enumerate(ids)]
        for i, p in dfs:
            if len(i)>0:
                i['asset'] = p
        cols = ['ativo','dataref','price','high','low','open','volume','close','bid','ask']
        rename = {'price':'preco', 'high':'maximo', 'low':'minimo', 'open':'abertura', 'close':'fech'}
        return [[df[0][cols].rename(columns=rename), df[1]] for df in dfs if len(df[0])]
        
    def get(self, ativos, intraday=0, periodo=[2010, 2030], dataini=0):
        l = self.historico(ativos, periodo, dataini) if not intraday else self.intraday(ativos)
        for i in l:
            i[0]['dataref'] = pd.to_datetime(i[0].dataref.astype(str), format='%Y%m%d')
        return l









