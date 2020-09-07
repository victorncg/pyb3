
import pandas as pd

from urllib.request import Request, urlopen  # Python 3

def projecoes():
    url = 'https://www.itau.com.br/_arquivosestaticos/itauBBA/contents/common/docs/Projecoes_de_Longo_Prazo_Itau_BRASIL_ago20_.xlsx?raw=true'
    req = Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0')
    content = urlopen(req)
    df = pd.read_excel(content)
    df = pd.DataFrame(df.values[:,2:][df.values[:,2:][:,1]==df.values[:,2:][:,1]][2:], columns=['ind']+df.values[:,2:][0].tolist()[1:])
    df = df.replace({'-':'0'})
    for i in df.replace({'-':0}).columns[1:]: df[i]=df[i].astype(float)
    return df





