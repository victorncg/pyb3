

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
        df['retornos'] = np.log(df.preco/df.preco.shift(-1)) if not tipo else df.preco/df.preco.shift(-1)-1
        return self._constructor(df.values.tolist(), columns = df.columns)

    # Gera coluna com as médias moveis
    def media_movel(self, n):
        df = self.copy()
        
        df['media_movel'] = df.preco.iloc[::-1].rolling(window=n).mean()    
        return self._constructor(df.values.tolist(), columns = df.columns)
    
    # calcula o coeficiente beta. O tipo é o tipo de retornos.
    def coefbeta(self, tipo=0):
        if '__beta' in self.__dict__: return self.__beta
        if 'retornos' not in self: self = self.gera_retornos()
        d = 1 if min(self.dataref).hour > 0 else 0
        tmin, tmax = min(self.dataref), max(self.dataref)
        tmin = tmin.year*10000+tmin.month*100+tmin.day
        tmax = tmax.year*10000+tmax.month*100+tmax.day
        t = [tmin, tmax]
        ibov = UolSeries().get(['IBOV'], intraday=d, periodo=t)[0][0] if d else YahooSeries(['IBOV'],periodo=t)[0][0]
        ibov = ibov.gera_retornos()
      #  return ibov, self
        df = self[['dataref', 'retornos']].merge(ibov[['dataref', 'retornos']], on='dataref')
        df[['retornos_x', 'retornos_y']].cov().values[0][1]
        self.__beta = df[['retornos_x', 'retornos_y']].cov().values[0][1]/ibov.retornos.var()
        return self.__beta
    
    # desvio padrão dos retornos
    def std(self, ddof=0):
        if 'retornos' not in self: self = self.gera_retornos()
        return self.retornos.std(ddof = ddof)

    # obtem o risco país do Brasil
    def risco_pais(self):
        return

    # obtem a inflação no brasil ou eua:
    def inflacao(self, pais):
        return

    # obtem a taxa livre de risco
    def tx_livre_risco(self):
        if '__rf' in self.__dict__: return self.__rf
        return

    # calcula o ke do ativo (rm=retorno esperado)
    def ke(self, rm):
        return self.tx_livre_risco()+self.coefbeta()*(rm-self.tx_livre_risco())
    

    

    
# Busca as séries de preços dos ativos no yahoo através do pandas_dataheader
def YahooSeries(ativos, periodo=[], dataini=[]):
    from pandas_datareader import data as web
    from calendar import monthrange
    ativos=ativos if type(ativos)==list else [ativos]
    atvs = [i+'.SA' if i!='IBOV' else '^BVSP' for i in ativos]
    periodo=periodo if type(periodo)==list else [periodo]
    p=[dataini, 20300101] if dataini else periodo
    ps=[[x for x in j] for j in  [[str(i)[:4], str(i)[4:6],str(i)[6:8]] for i in p]]

    dini=[[str(i[0])+str(i[1] if i[1] else '%02d' % 1)+str(i[2] if i[2] else '%02d' % 1)] for i in [min(ps)]]
    if periodo:
        dfin=[[str(i[0])+str(i[1] if i[1] else 12)+str(i[2] if i[2] else monthrange(int(i[0]), int(i[1]))[1] if i[1] else 31)] for i in [max(ps)]]
     #   periodo=[dini[0][0],dfin[0][0]]   
        s=web.get_data_yahoo(atvs,dini[0][0], dfin[0][0])
    else: 
        s= web.get_data_yahoo(atvs,dini[0][0])
    s=[s[[i for i in s if i[0]=='Date' or i[1]==ativo]].reset_index().dropna() for ativo in atvs]
   # ativos = [i.replace('.SA','') for i in ativos]
    for df, ativo in zip(s, ativos): 
        df.columns=[i[0] for i in df]
        df.rename(columns={'Date':'dataref', 'Adj Close':'preco'}, inplace=True)
        df['ativo']=ativo
    
        
    return [list(i) for i in zip([Serie(i.values.tolist(), columns = i.columns)[['ativo', 'dataref', 'preco']].sort_values(by='dataref', ascending=False) for i in s],[i.replace('.SA','') for i in ativos]) if len(i[0])]





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
                i['dataref'] = i.date
                i['ativo'] = p
        cols = ['ativo','dataref','price','high','low','open','volume','close','bid','ask']
        rename = {'price':'preco', 'high':'maximo', 'low':'minimo', 'open':'abertura', 'close':'fech'}
        return [[df[0][cols].rename(columns=rename), df[1]] for df in dfs if len(df[0])]
        
    def get(self, ativos, intraday=0, periodo=[2010, 2030], dataini=0):
        l = self.historico(ativos, periodo, dataini) if not intraday else self.intraday(ativos)
        form = '%Y%m%d' if not intraday else '%Y%m%d%H%M%S'
        for i in l:
            i[0]['dataref'] = pd.to_datetime(i[0].dataref.astype(str), format=form)
        return l







