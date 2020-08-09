

import requests

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}


# lib usada para buscar os dados

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
                i['date'] = (i.date.astype(float)/1000000).astype(int)
                i['asset'] = p
        
        cols = ['asset','date','price','high','low','open','volume','close','bid','ask']

        return [[df[0][cols], df[1]] for df in dfs if len(df[0])]
    
    # intraday do último dia
    def intraday(self, papel):
        ids = self.__acao(papel)
        series = [(self.__pesquisar(i, 'intraday'), i['code'].replace('.SA','') ) for i in ids]
        
        dfs = [(Serie([i for i in series[n][0]['docs']]), series[n][1]) for n, _ in enumerate(ids)]
        for i, p in dfs:
            if len(i)>0:
                i['asset'] = p
        cols = ['asset','date','price','high','low','open','volume','close','bid','ask']
        return [[df[0][cols], df[1]] for df in dfs if len(df[0])]
        
    def get(self, ativos, intraday=0, periodo=[2010, 2030], dataini=0):
        return self.historico(ativos, periodo, dataini) if not intraday else self.intraday(ativos)






