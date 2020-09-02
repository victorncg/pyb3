
import requests
from bs4 import BeautifulSoup
import pandas as pd


def ipea(cod, anual=0):

    r = requests.get(f'http://www.ipeadata.gov.br/ExibeSerie.aspx?serid={str(cod)}')
    dados = BeautifulSoup(r.content, 'html.parser')
    tabela = dados.find('table', id='grd_DXMainTable')

    tabela = [[n.text.replace('\n','') for n in j] for j in [i.find_all('td') for i in tabela.findAll('tr')]]
    head=[tabela[1][0], tabela[2][0]]
    columns = tabela[3:]
    df = pd.DataFrame(columns, columns=head)
    df.iloc[:,1] = df.iloc[:,1].str.replace('.','').str.replace(',','.')#.astype(float)
    df.iloc[:,1] = df.iloc[:,1].str.strip().apply(lambda x: '0' if x=='' else x)
    
    if anual and df.iloc[:,0][0].__len__()>4:       
        if 'T' in df.iloc[:,0][0][-2:]:
            df = df[df.iloc[:,0].str[-1:]=='4']
        else:
            df = df[df.iloc[:,0].str[-2:]=='12']
        df[s.columns[0]] = df.iloc[:,0].str[:4].astype(int)

    return df



def pesquisar(nome):
    nome = nome.replace(' ','+')
    r = requests.get(f'http://www.ipeadata.gov.br/ListaSeries.aspx?Text={nome}&NoCache=1599012665349')
    soup = BeautifulSoup(r.content, 'html.parser')
    t = [[''.join([j for j in i['href'] if j.isdigit()]), i.text] for i in soup.findAll('a', class_='dxeHyperlink')]
    
    print(f"Cod {' '*(20-len('Cod'))} Nome")
    print('')
    [print(i[0] + ' '+'-'*(20-len(i[0]))+' ' + i[1]) for i in t]







