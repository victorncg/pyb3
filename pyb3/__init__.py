
from pyb3 import portfolio as pt
from pyb3 import opcoes as opc
from pyb3 import balancos
from pyb3.crawler import proventos as pr

Serie = pt.Serie

proventos = pr.proventos

class Carteira(pt.Carteira):
    pass

class Opcoes(opc.Opcoes):
    pass

class Balancos(balancos.Balancos):
    pass




