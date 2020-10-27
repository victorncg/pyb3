
import pandas as pd 
from pyb3.crawler import balancos_investsite as inv
from pyb3.crawler import balancos_cvm as bcvm
from datetime import datetime
import copy


# Lib para tratar os balançoes obtidos da internet

mes_trimestre = {
3:1, 6:2, 9:3, 12:4}
indice_ind = inv.indice_ind


def todate(data): 
    return datetime.strptime(data, "%d/%m/%Y").date() if type(data) == str else data

class Balancos:

    def __init__(self, papel, wdriver='', cvm=0):
        self.papel=papel
        self.balanco = bcvm.Raw(self.papel, wdriver=wdriver) if cvm and wdriver else inv.Raw(self.papel)
        self.datarefs = {}

    # Transforma os valores em float
    def __trata_valores(self, df):
        if not df.iloc[:,2].dtype==float:
            df.iloc[:,2] = df.iloc[:,2].str.replace('.','').str.replace(',','.').astype(float)*1000
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
    def get(self, ind, ano, tri, ajustado=False, n=0):
        self.ind,self.ano,self.tri, self.ajustado, self.n = ind, ano, tri, ajustado, n
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
        b.b=copy.copy(self)
        return b

    def analise_fundamentalista(self, ano, tri):
        return AnaliseFundamentalista(self, ano, tri)



# classe para analise fundamentalista
class Balanco(pd.DataFrame):

    @property
    def _constructor(self):
        return Balanco

    @property
    def _constructor_sliced(self):
        return pd.Series


    # calcula a análise vertical
    def __av(self, df):
        df['av'] = df.valor/df.valor.tolist()[0]
       # df['av']=df['valor']/ df.assign(conta1=df.conta.str[:df.conta.str.len().min()])\
       #     .merge(df[['conta','valor']].rename(columns={'conta':'conta1'}), on='conta1')['valor_y']      
        return df

    # gera a coluna de análise vertical no dataframe
    def analise_vertical(self):
        df = self.copy()
        df = self.__av(df)
        return self._constructor(data=df.values.tolist(), columns = df.columns)

   # gera a tabela com a nálise horizontal comparando com outro mês de outro ano 
    def analise_horizontal(self, ano=0, tri=0):
        ano1, tri1 = self.b.ano, self.b.tri
        ano = self.b.ano-1 if not ano else ano
        tri = self.b.tri if not tri else tri
        b1 = self.copy()
        b2 = self.b.get(self.b.ind, ano, tri, self.b.ajustado, n=self.b.n)
        for b in [b1, b2]:
            trimestre = [i for i in b if 'trimestre' in i]
            dataref = [i for i in b if 'data' in i]
            b = self.__av(b)
            anotri = str(b.ano.tolist()[0]) +'/'+ str(b[trimestre[-1]].tolist()[0])       
            b.rename(columns = {'valor':'valor ' + anotri, 'av':'av '+anotri}, inplace=True)
            b.drop(dataref+trimestre+['ano'], axis=1, inplace=True)
        self.b.ano, self.b.tri = ano1, tri1
        bc = b1.merge(b2, how='outer')
        v1, v2 = [i for i in bc if 'valor' in i]
        bc['ah'] = bc[v1]/bc[v2]-1   
        
        return self._constructor(data=bc.values.tolist(), columns = bc.columns)


    # retorna o float da conta
    def get_conta(self, conta, t=1):
        if t:
            df = self.copy()
            df = self.__av(df) if not [i for i in df if 'av' in i] else df
        else:
            df = self.analise_horizontal()

        campo_valor = [i for i in df if 'valor' in i]
        c = df[df['conta']==conta]
        conta = Conta(c[campo_valor[t-1]].sum())
        conta.conta = c['conta'].tolist()[0]
        conta.dsc = c['descricao'].tolist()[0]
        conta.margem = c[[i for i in df if 'av' in i][t-1]].tolist()[0]

        return conta

    # retorna a soma
    def get_conta_dsc(self, dsc, t=1):
        if t:
            df = self.copy()
            df = self.__av(df) if not [i for i in df if 'av' in i] else df
        else:
            df = self.analise_horizontal()
        campo_valor = [i for i in df if 'valor' in i]
        c = pd.concat([df[df['descricao'].str.lower().str.contains(i)] for i in dsc]).drop_duplicates()
        conta = Conta(c[campo_valor[t-1]].sum())
        conta.conta = ' + '.join([i for i in c['conta']])
        conta.dsc = ' + '.join([i for i in c['descricao']])
        conta.margem=c[[i for i in df if 'av' in i][t-1]].sum()
        return conta


    # resume pela conta
    def n(self, n):
        df = self.copy()
        df = df[df.conta.str.count('\.')<=n] if n else df
        df = self._constructor(data=df.values.tolist(), columns = df.columns)
        df.b = copy.copy(self.b)
        df.b.n=n
        return df


# cria uma classe int para mostrar o tipo de conta
class Conta(float):
    def __repr__(self):
        return f"conta: {self.conta}\ndescrição: {self.dsc}\nvalor: " + '{:>,.2f}'.format(self.real) + f"\nmargem: " + '{:>,.2f}'.format(self.margem*100)+"%"


class AnaliseFundamentalista:
    def __init__(self, balanco, ano, tri):
        self.b=balanco
        self.ano = ano
        self.tri = tri
        
    def calcular(self, calc):
        formula, formula_contas = calc,calc
        inds = [i for i, _ in enumerate(calc) if calc.startswith('ind',i)]
        inds = [calc[i+4: len(calc[:i+4]) + calc[i+4:].find(')')] for i in inds]
        for i in inds: calc=calc.replace(f'ind({i})', f'({str(self.indicador(i).real)})')
        for i in inds: formula=formula.replace(f'ind({i})', f'({str(self.indicador(i).formula)})')
        for i in inds: formula_contas=formula_contas.replace(f'ind({i})', f'({str(self.indicador(i).formula_contas)})')
            
        dscs = [i for i, _ in enumerate(calc) if calc.startswith('dsc',i)]
        d = [calc[i+4: len(calc[:i+4]) + calc[i+4:].find(')')] for i in dscs]
        dscs = [i.split(',') for i in d]
        dscs = [[i.split()[0] for i in j] for j in dscs]
        for i in dscs: i.append('1') if i[-1] not in ('0','1') else 0
        dscs = dict(zip(d,[self.b.get(int(i[0]), self.ano, self.tri, 0).get_conta_dsc(i[1:-1], int(i[-1])) for i in dscs]))
    
        contas = [i for i, _ in enumerate(calc) if calc.startswith('conta',i)]
        c = [calc[i+6: len(calc[:i+6]) + calc[i+6:].find(')')] for i in contas]
        contas = [i.split(',') for i in c]
        for i in contas: i.append(1) if len(i)==1 else 0
        contas = dict(zip(c,[self.b.get(int(i[0]), self.ano, self.tri, 0).get_conta(i, int(t)) for i,t in contas]))
        
        for i in contas: formula = formula.replace(f'conta({i})', f'({str(contas[i].dsc)})')
        for i in dscs: formula = formula.replace(f'dsc({i})', f'({str(dscs[i].dsc)})')
        for i in contas: formula_contas = formula_contas.replace(f'conta({i})', f'({str(contas[i].conta)})')
        for i in dscs: formula_contas = formula_contas.replace(f'dsc({i})', f'({str(dscs[i].conta)})')
            
        for i in contas: calc=calc.replace(f'conta({i})', f'({str(contas[i].real)})')
        for i in dscs: calc = calc.replace(f'dsc({i})',f'({str(dscs[i].real)})')

        valor = eval(calc)
        valor = Indicador(valor)
        valor.formula=formula
        valor.formula_contas = formula_contas
        return valor
        
    def indicador(self, ind):
        return self.calcular(dictind[ind])
    
    def principais_indicadores(self):
        return pd.DataFrame([[i,self.calcular(f'ind({i})')] for i in dictind], columns=['Indicador', 'Valor'])
    
    
# cria uma classe int para mostrar o tipo de conta
class Indicador(float):
    def __repr__(self):
        return f"valor: " + '{:>,.2f}'.format(self.real) +f"\nformula: {self.formula}\nformula contas: {self.formula_contas}"


dictind = {# Balanço Patrimonial
    'margem ativo circulante' : 'conta(1.01)/conta(1)',
    'margem ativo não circulante' : 'conta(1.02)/conta(1)',
    'capital terceiros' : '(conta(2.01) + conta(2.02))/conta(2)',
    'capital socios' : 'conta(2.03)/conta(2)',
    'passivo oneroso' : '(conta(2.01.04)+conta(2.02.01))/conta(2)',

    # Demonstração de resultado e margens
    'margem bruta' : 'conta(3.03)/conta(3.01)',
    'margem ebit' : 'conta(3.05)/conta(3.01)',
    'margem liquida' : 'conta(3.09)/conta(3.01)',
    'ebitda' : 'conta(3.05) + dsc(6,amortiza ,deprecia)',
    'margem ebitda' : 'ind(ebitda)/conta(3.01)',

    # Demonstração dos fluxos de caixa
    'fco receita' : 'conta(6.01)/conta(3.01)',
    'fci dep' : 'abs(conta(6.02))/dsc(6,amortiza ,deprecia)',
    'fcl' : 'conta(6.01) + conta(6.02)',

    # capital de giro
    'liquidez corrente' : 'conta(1.01)/conta(2.01)',
    'ncg' : '(conta(1.01)-conta(1.01.01)-conta(1.01.02))-(conta(2.01)-conta(2.01.04))',
    'ncg receita' : 'ind(ncg)/conta(3.01)',
    'pmr' : 'conta(1.01.03)/conta(3.01)*360',
    'pme' : 'conta(1.01.04)/abs(conta(3.02))*360',
    'compras' : 'conta(1.01.04)-conta(1.01.04,0) +abs(conta(3.02))',
    'pmp' : 'conta(2.01.02)/ind(compras)*360',
    'ciclo financeiro' : 'ind(pmr)+ind(pme)-ind(pmp)',

    # endividamento
    'endividamento geral' : 'ind(capital terceiros)',
    'endividamento oneroso' : 'ind(passivo oneroso)',
    'icj' : 'conta(3.05)/abs(conta(3.06))',
    'divida liquida' : '(conta(2.01.04)+conta(2.02.01))-(conta(1.01.01)-conta(1.01.02))',
    #'ebitda' = 'conta(3.05) + conta(6.01.01.03)'
    'alavancamento ebitda' : 'ind(divida liquida)/ind(ebitda)',

    # Analise integrada
    #'margem liquida' = ind
    'giro ativo' : 'conta(3.01)/conta(1)',
    'roa' : 'ind(margem liquida)*ind(giro ativo)',
    'alavancagem pl' : 'conta(1)/conta(2.03)',
    'roe' : 'ind(roa) * ind(alavancagem pl)',
    'roi' : 'conta(3.05)/conta(1)',
    'custo medio divida' : 'abs(conta(3.06))/(conta(2.01)+conta(2.02))'
}






