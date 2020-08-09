
import pandas as pd
import numpy as np
from pyb3 import crawler

# trabalha com um ativo
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
    
    

# trabalha com um conjunto de series de ativos
class Carteira:
    def __init__(self, ativos, volumes=[], intraday=0, periodo=[2010, 2030], dataini=0):
        ativos = ativos if type(ativos)==list else [ativos]
        series = crawler.UolSeries().get(ativos, intraday, periodo, dataini)
        for i in series:
            setattr(self, i[1], i[0])
        setattr(self, 'ativos', ativos)
        self.add_volumes(volumes)
        
    def __getitem__(self, ativos):
        return getattr(self, ativos)
    
    def __repr__(self):
        if sum(self.volumes)>0:
            return '\n'.join([f'{a}: R$ {"%.2f" % v}' for a, v in zip(self.ativos, self.volumes)]) + f'\n\nTotal: R$ {"%.2f" % sum(self.volumes)}'
        else:
            return str(self.ativos)

    # Gera a coluna de retornos dia a  tipo = 0 gera o retorno por ln
    def gera_retornos(self, tipo=0):
        for i in self.ativos:
            self.__dict__[i] = self[i].gera_retornos(tipo)
        
    # Gera a coluna com médias móveis
    def medias_moveis(self, n):
        for i in self.ativos:
            self.__dict__[i] = self[i].media_movel(n)
            
    # insere volumes dos ativos da carteira
    def add_volumes(self, volumes):
        self.volumes=[0 for i in self.ativos] if not volumes else volumes
            
    # matriz de correlação
    def matriz_correl(self):
        self.gera_retornos()
        m = [[self[j][['date', 'retornos']].merge(self[i][['date', 'retornos']], on='date') for j in self.ativos] for i in self.ativos]
        m = [[i[['retornos_x','retornos_y']].corr().values[0][1] for i in s] for s in m]
        return pd.DataFrame(m, columns=self.ativos, index = self.ativos)
    
    # Gera a porcentagem que cada ativo ocupa no portfolio que são os pesos
    def ponderar(self):
        total = sum(self.volumes)
        if total:
            return [v/total for v in self.volumes]
                  
    # Gera a volatilidade de cada ativo
    def std(self):
        return [self[i].std() for i in self.ativos]
                              
    # Gera a volatilidade da carteira
    # fonte: http://ferramentasdoinvestidor.com.br/financas-quantitativas/matematica-de-portfolio/
    def vol_carteira(self):
        # obtem a matriz de correlação
        matriz = self.matriz_correl().values.tolist()
        # vetor de pesos de cada ativo
        pesos = self.ponderar()    
        # vetor de desvios
        stds = self.std()
        # matriz de ativos       
        l = [sorted([n1,n2]) for n1, _ in enumerate(self.ativos) for n2,_ in enumerate(s.ativos) if n1!=n2]
        l = list(map(list, set(map(frozenset, l))))
        # calculo
        vol = sum([2*stds[n1]*stds[n2]*pesos[n1]*pesos[n2]*matriz[n1][n2] for n1, n2 in l]+[p**2*o**2 for p, o in zip(pesos, stds)])**(1/2)
        return vol                      
                              
                              


