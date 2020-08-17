
import pandas as pd 
from pyb3.crawler import balancos_investsite as inv
from datetime import datetime


# Lib para tratar os balançoes obtidos da internet

mes_trimestre = {
3:1, 6:2, 9:3, 12:4}
indice_ind = inv.indice_ind


def todate(data): 
    return datetime.strptime(data, "%d/%m/%Y").date() if type(data) == str else data

class Balancos:

    def __init__(self, papel, site=True):
        self.papel=papel
        self.site = site
        self.balanco = inv.Raw(self.papel) if site else None
        self.datarefs = {}

    # Transforma os valores em float
    def __trata_valores(self, df):
        if not df.iloc[:,2].dtype==float:
            df.iloc[:,2] = df.iloc[:,2].str.replace('.','').str.replace(',','.').astype(float)
        return df
        
    # Verifica os trimestres que o valor está consolidando
    def __tri_cons(self, df):
        datas = list(df)[2].split('a')
        meses = [int(i.split('/')[1]) for i in datas]
        tri = [mes_trimestre[i] for i in range(min(meses),max(meses)) if i in mes_trimestre]
        return tri

    # Subtrai aos trimestre anteriores para obter o valor específico do trimestre
    def __subtrai_mes_ant(self, df1, df2):
        s = df1.merge(df2, how='left')
        s.iloc[:,2] = s.iloc[:,2].replace({pd.np.nan:0}) - s.iloc[:,3].replace({pd.np.nan:0})
        s.drop(s.columns[3], axis=1, inplace=True)
        return s
        
    # puxa os dados e trata os campos
    def __raw(self):
        raw = self.balanco.get(self.ind,self.ano,self.tri)
    #    if not raw:
    #        return
        relatorio = self.__trata_valores(raw)
      #  return relatorio
        if not self.ajustado:
            return relatorio
        
        listtri = self.__tri_cons(relatorio)
        
        # obtem os banços dos meses anteriores para desconsolidar
        while len(listtri)>0:
            b = self.balanco.get(self.ind,self.ano,listtri[-1:][0])
     #       if not b:
     #           return
            triant = self.__trata_valores(b)
            relatorio = self.__subtrai_mes_ant(relatorio, triant)
            listtri = [i for i in listtri[:-1] if i not in self.__tri_cons(triant)]
            
   #     relatorio[0][2] = relatorio[0][2].split('a')[-1:][0]

        return relatorio

    # Monta o layout da tabela
    def get(self, ind, ano, tri, ajustado=True, n=0):
        self.ind,self.ano,self.tri, self.ajustado = ind, ano, tri, ajustado
        # encontra o trimestre inicial e final
        df = self.__raw()
        df = df.copy()
        datas = df.columns[2].split('a')

        datas = [todate(i) for i in datas]
        datas = [min(datas), max(datas)]
        meses = [i.month for i in datas]
        trimestre = [int(i/3)+1 if i%3 else int(i/3) for i in meses]

        campos_data = ['dataref'] if self.ajustado else ['dataini', 'datafin']
        campos_tri = ['trimestre'] if self.ajustado else ['trimestreini', 'trimestrefin']
        datas = datas[-1:] if self.ajustado else datas
        trimestre = trimestre[-1:] if self.ajustado else trimestre
        for c, t in zip(campos_data, datas):
            df[c] = t
            df[c] = pd.to_datetime(df[c])
        for c, t in zip(campos_tri, trimestre):
            df[c] = t  

        df['ano'] = self.ano
        df['ativo'] = self.papel
        df['demonstrativo'] = indice_ind[self.ind]

        df.rename(columns={df.columns[2]:'valor', 'Conta':'conta', 'Descrição':'descricao'}, inplace=True)
        colunas = ['ativo', 'demonstrativo', 'conta', 'descricao', 'dataref', 'dataini', 'datafin', 'trimestre', 'trimestreini', 'trimestrefin', 'ano', 'valor']
        df = df[[c for c in colunas if c in df]]
        if n: df = df[df.conta.str.count('\.')<=n]
        b = Balanco(data = df.values.tolist(), columns = df.columns)
        b.b=self
        return b



# classe para analise fundamentalista
class Balanco(pd.DataFrame):

    @property
    def _constructor(self):
        return Balanco

    @property
    def _constructor_sliced(self):
        return pd.Series

    # gera a coluna de análise vertical
    def analise_vertical(self):
        df = self.copy()
        df['av'] = df.valor/df.valor.tolist()[0]
        return self._constructor(data=df.values.tolist(), columns = df.columns)

   # gera a tabela com a nálise horizontal comparando com outro mês de outro ano 
    def analise_horizontal(self, ano=0, tri=0):
        ano = self.b.ano-1 if not ano else ano
        tri = self.b.tri if not tri else tri
        b1 = self.copy()
        print(self.b.ind, ano, tri, self.b.ajustado)
        b2 = self.b.get(self.params[0], ano, tri, self.params[3], n=2)
        for b in [b1, b2]:
            trimestre = [i for i in b if 'trimestre' in i]
            dataref = [i for i in b if 'data' in i]
            b['av'] = b.valor/b.valor.tolist()[0]
            anotri = str(b.ano.tolist()[0]) +'/'+ str(b[trimestre[1]].tolist()[0])       
            b.rename(columns = {'valor':'valor ' + anotri, 'av':'av '+anotri}, inplace=True)
            b.drop(dataref+trimestre+['ano'], axis=1, inplace=True)
        bc = b1.merge(b2, how='outer')
        v1, v2 = [i for i in s if 'valor' in i]
        bc['ah'] = bc[v1]/bc[v2]-1    
        return self._constructor(data=bc.values.tolist(), columns = bc.columns)





