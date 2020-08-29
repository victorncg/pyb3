
import pandas as pd 
import requests 
from bs4 import BeautifulSoup
from pyb3.crawler import dados_ativos

# Busca os demonstrativos no investsite.com.br

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
codigos = {
    'Resultado' : [4, 'dre_empresa'],
    'Balanço Ativo' : [2, 'balanco_empresa'],
    'Balanço Passivo': [3, 'balanco_empresa'],
    'Fluxo de Caixa' : [7, 'dfc_empresa'],
    'Valor Adicionado' : [9, 'dva_empresa']
}
trimestre = {
    1 : ['0331', 'ITR'],
    2 : ['0630', 'ITR'],
    3 : ['0930', 'ITR'],
    4 : ['1231', 'DFP']    
}
indice_ind = {
1:'Balanço Ativo',  2:'Balanço Passivo', 3:'Resultado', 6:'Fluxo de Caixa', 
7:'Valor Adicionado',  8:'Resultado Abrangente' #, 7:'Mutações do PL'
}

Dados = dados_ativos.Dados

# Busca os demonstrativos no investsite.com.br
class Raw:
    def __init__(self, papel):
        self.papel = papel
        self.dados = Dados(self.papel)
        self.series = {}
        
    # tenta acessar 20x o request
    def post(self, url, data, headers):
        for i in range(20):
            try:
                response = requests.post(url, data=data, headers=headers)
                return response
            except:
                pass
        print('Número de tentativas excedidas no investsite.com.br')
        return 'erro'

    # obtem os dados 
    def get(self, ind, ano, tri):
    
        tpind = codigos[indice_ind[ind]] if type(ind)==int else codigos[ind]

        # se já foi rodado uma vez, fica salvo na memória
        if (ind, ano, tri) in self.series:
            return self.series[(ind, ano, tri)] 
        url = 'https://www.investsite.com.br/includes/demonstrativo_tabela_ajax.php'

        self.isin = self.dados.isin()
        
        # parâmetros passados para o request
        data = {
            'tipo_dem': trimestre[tri][1],
            'tipo_fonte': 'XML',
            'ano_dem': str(ano),
            'mes_dia_dem': trimestre[tri][0],
            'consolid': '2',
            'tipocontabil': '2',
            'codigodem': str(tpind[0]),
            'ISIN': self.isin
          }
      #  print(url, data, headers)
        response = self.post(url, data, headers)
        if response == 'erro': return
            
        soup = BeautifulSoup(response.content, 'html.parser')
        idd = tpind[1] if tri == 4 else tpind[1]+'_itr'
       # if not soup.find('table', id=idd):
       #     return
        soup = soup.find('table', id=idd).findAll('tr')
        if not len(soup[2:]):
            self.series.update({(ind, ano, tri):None})
            return
        
        th = [i.text.replace('(R$)', '').replace('(R$ mil)', '').replace(' ','') for i in soup[0].findAll('th')[:3]]
        td = [[i.text if i.text !='0' else None for i in j.findAll('td')[:3]] for j in soup[2:]]
        
        self.series.update({(ind, ano, tri):pd.DataFrame(td, columns=th)})
        return pd.DataFrame(td, columns=th)
        

        



