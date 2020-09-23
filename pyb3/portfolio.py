
import pandas as pd
from pyb3.crawler import acoes
from scipy.stats import norm

def Serie(ativo, volumes=[], intraday=0, periodo=[2010, 2030], dataini=0):
    ativo=[ativo]
    return acoes.UolSeries().get(ativo, intraday, periodo, dataini)[0][0] if intraday else acoes.YahooSeries(ativo,periodo,dataini)[0][0]

# trabalha com um conjunto de series de ativos
class Carteira:
    def __init__(self, ativos, volumes=[], intraday=0, periodo=[2010, 2030], dataini=0):
        ativos = ativos if type(ativos)==list else [ativos]
        periodo = periodo if type(periodo)==list else [periodo]
        volumes = volumes if type(volumes)==list else [volumes]
        series = acoes.UolSeries().get(ativos, intraday, periodo, dataini) if intraday else acoes.YahooSeries(ativos,periodo,dataini)
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
        m = [[self[j][['dataref', 'retornos']].merge(self[i][['dataref', 'retornos']], on='dataref') for j in self.ativos] for i in self.ativos]
        m = [[i[['retornos_x','retornos_y']].corr().values[0][1] for i in s] for s in m]
        return pd.DataFrame(m, columns=self.ativos, index = self.ativos)
    
    # Gera a porcentagem que cada ativo ocupa no portfolio que são os pesos
    def ponderar(self):
        total = sum(self.volumes)
        if total:
            return [v/total for v in self.volumes]

    # Gera o retorno médio dos ativos
    def retorno_ativos(self):
        return [self[a].gera_retornos().retornos.mean() for a in self.ativos]

    # soma os retornos médios ponderados para obter o retorno médio da carteira
    def retorno_carteira(self):
        return sum([m[0]*m[1] for m in zip(self.retorno_ativos(), self.ponderar())])
                  
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
        l = [sorted([n1,n2]) for n1, _ in enumerate(self.ativos) for n2,_ in enumerate(self.ativos) if n1!=n2]
        l = list(map(list, set(map(frozenset, l))))
        # calculo
        vol = sum([2*stds[n1]*stds[n2]*pesos[n1]*pesos[n2]*matriz[n1][n2] for n1, n2 in l]+[p**2*o**2 for p, o in zip(pesos, stds)])**(1/2)
        return vol                      

    # calcula o value at risk da carteira para determinado nível de confiança
    def risco(self, nc):
        return self.vol_carteira()*norm.ppf(nc)*sum(self.volumes)                              






