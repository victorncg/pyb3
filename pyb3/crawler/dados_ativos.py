import pandas as pd
from bs4 import BeautifulSoup

# Busca o codigo cvm, cnpj e isin usando o site da B3, 
class Dados_B3:

    def __init__(self, papel):
        self.papel = papel

    # Obtem o cnpj e isin
    def cnpj(self):
    
        if 'cnpj_' in self.__dict__:
            return self.__dict__['cnpj_']

        cd = self.cd_cvm()

        url='http://bvmf.bmfbovespa.com.br/pt-br/mercados/acoes/empresas/ExecutaAcaoConsultaInfoEmp.asp?CodCVM='+str(cd)
        
        soup = self.bstimeout(url, 3)
        soup = soup.find('ul', class_='accordion').findAll('tr')
        
        tipo_papel = 'ACNOR' if int(self.papel[-1:]) == 3 else 'ACNPR'
        isin = [i.replace(',','') for i in list(set(soup[1].text.split())) if i[6:11] == tipo_papel][0]
        cnpj_ = soup[2].text.split()[1]

        setattr(self, '__isin', isin)
        setattr(self, 'cnpj_', cnpj_)

        return cnpj_


    def isin(self):
        if '__isin' in self.__dict__:
            return self.__dict__['__isin']
        self.cnpj()
        isin = self.__dict__['__isin']
        return isin
    
    # Busca o nome da empresa listada na cvm e o código
    def cd_cvm(self):

        if 'cd_cvm' in self.__dict__:
            return self.__dict__['cd_cvm']

        url = f'http://bvmf.bmfbovespa.com.br/cias-listadas/empresas-listadas/BuscaEmpresaListada.aspx?Nome={self.papel}&idioma=pt-br'
        soup = self.bstimeout(url, 3)
        codigo = soup.find('tr', class_='GridRow_SiteBmfBovespa GridBovespaItemStyle')
        codigo = codigo.find('td').find('a')['href']
        codigo[codigo.find('codigoCvm=')+len('codigoCvm='):]
        cd_cvm_ = int(codigo[codigo.find('codigoCvm=')+len('codigoCvm='):])
        setattr(self, 'cd_cvm', cd_cvm_)
        return cd_cvm_

    # Função para fazer obter o html do site da b3,
    # muitas vezes a página fica carregando muito tempo, é necessário recarregar algumas vezes até funcionar
    def bstimeout(self, url, time, data=''):
        for i in range(20):
            try:
                response = requests.post(url, data=data, headers=headers, timeout=time)
                soup = BeautifulSoup(response.content,'html.parser')
                return soup
            except:
                print('Tentativas excedidas no site da B3')
                pass



# Obtem dados de outros sites
class Dados:

    def __init__(self, papel):
        self.papel = papel
        self.dados = {}

    # Obtem o nome e cnpj da ação no site status invest
    def cnpj(self):
        if 'cnpj_' in self.__dict__:
            return self.__dict__['cnpj_']
        url = f"""https://statusinvest.com.br/acoes/"""+self.papel.lower()
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        try:
            cnpj_ = soup.find('small', class_ = 'd-block fs-4 fw-100 lh-4').text
            setattr(self, 'cnpj_', cnpj_)
            return cnpj_
        except:
            pass
            #print('CNPJ não encontrado')   

    # Obtem o isin no site adfvn
    def isin(self):
        if '__isin' in self.__dict__:
            return self.__dict__['__isin']
        url='https://br.advfn.com/p.php?pid=qkquote&symbol='+self.papel.lower()
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        isin = soup.find(id = 'quoteElementPiece6').text 
        setattr(self, '__isin', isin)
        return isin
        
    # Busca o código cvm no site da cvm
    def cd_cvm(self):
        if 'cd_cvm_' in self.__dict__:
            return self.__dict__['cd_cvm_']
        url=f'https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/CiaAb/ResultBuscaParticCiaAb.aspx?CNPJNome={self.cnpj()}&TipoConsult=C'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        cd_cvm_ = soup.find(id = 'dlCiasCdCVM__ctl1_Linkbutton5').text  
        setattr(self, 'cd_cvm_', int(cd_cvm_))   
        return int(cd_cvm_)









