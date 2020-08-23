## Esse pacote busca os dados na CVM usando o Selenium, é necessário fazer o download do Chromewebdriver

from bs4 import BeautifulSoup
import requests
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
import numpy as np
import time
from datetime import datetime
from pyb3.crawler import dados_ativos
#import dados_ativos
import pandas as pd

options = webdriver.ChromeOptions()
options.add_argument("--headless")
#options.add_argument("--start-maximized")

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}


# links cvm

link_ind = {
'Resultado' : 'https://www.rad.cvm.gov.br/ENETCONSULTA/frmDemonstracaoFinanceiraITR.aspx?Informacao=2&Demonstracao=4&Periodo=0&Grupo=DFs+Consolidadas&Quadro=Demonstra%c3%a7%c3%a3o+do+Resultado&NomeTipoDocumento=ITR&Empresa=MAGAZ%20LUIZA&DataReferencia=2014-09-30&Versao=1&CodTipoDocumento=3&NumeroSequencialDocumento=',
'Balanço Ativo' : 'https://www.rad.cvm.gov.br/ENETCONSULTA/frmDemonstracaoFinanceiraITR.aspx?Informacao=2&Demonstracao=2&Periodo=0&Grupo=DFs+Consolidadas&Quadro=Balan%C3%A7o+Patrimonial+Ativo&NomeTipoDocumento=&DataReferencia=&Versao=1&CodTipoDocumento=3&NumeroSequencialDocumento=',
'Balanço Passivo': 'https://www.rad.cvm.gov.br/ENETCONSULTA/frmDemonstracaoFinanceiraITR.aspx?Informacao=2&Demonstracao=3&Periodo=0&Grupo=DFs+Consolidadas&Quadro=Balan%c3%a7o+Patrimonial+Passivo&NomeTipoDocumento=ITR&Empresa=MOVIDA&DataReferencia=&Versao=3&CodTipoDocumento=3&NumeroSequencialDocumento=',
'Resultado Abrangente' : 'https://www.rad.cvm.gov.br/ENETCONSULTA/frmDemonstracaoFinanceiraITR.aspx?Informacao=2&Demonstracao=5&Periodo=0&Grupo=DFs+Consolidadas&Quadro=Demonstra%c3%a7%c3%a3o+do+Resultado+Abrangente&NomeTipoDocumento=ITR&Empresa=&DataReferencia=&Versao=1&CodTipoDocumento=3&NumeroSequencialDocumento=',
'Fluxo de Caixa' : 'https://www.rad.cvm.gov.br/ENETCONSULTA/frmDemonstracaoFinanceiraITR.aspx?Informacao=2&Demonstracao=99&Periodo=0&Grupo=DFs+Consolidadas&Quadro=Demonstra%C3%A7%C3%A3o+do+Fluxo+de+Caixa&NomeTipoDocumento=&Empresa=&DataReferencia=&Versao=1&CodTipoDocumento=3&NumeroSequencialDocumento=',
'Valor Adicionado' : 'https://www.rad.cvm.gov.br/ENETCONSULTA/frmDemonstracaoFinanceiraITR.aspx?Informacao=2&Demonstracao=9&Periodo=0&Grupo=DFs+Consolidadas&Quadro=Demonstra%c3%a7%c3%a3o+de+Valor+Adicionado&NomeTipoDocumento=&Empresa=&DataReferencia=&Versao=1&CodTipoDocumento=3&NumeroSequencialDocumento=',
'Mutações do PL' : 'https://www.rad.cvm.gov.br/ENETCONSULTA/frmDemonstracaoFinanceiraITR.aspx?Informacao=200&Demonstracao=8&Periodo=4|6&Grupo=DFs+Consolidadas&Quadro=Demonstra%c3%a7%c3%a3o+das+Muta%c3%a7%c3%b5es+do+Patrim%c3%b4nio+L%c3%adquido&NomeTipoDocumento=&Empresa=&DataReferencia=&Versao=1&CodTipoDocumento=3&NumeroSequencialDocumento='

}

indice_ind = {
1:'Balanço Ativo',  2:'Balanço Passivo', 3:'Resultado',  4:'Resultado Abrangente', 6:'Fluxo de Caixa', 
7:'Valor Adicionado' #, 7:'Mutações do PL'
}


def todate(data): 
    return datetime.strptime(data, "%d/%m/%Y").date() if type(data) == str else data

class Raw:

    def __init__(self, papel, wdriver = 'chromedriver.exe'):
        self.papel = papel
        self.dados = dados_ativos.Dados(self.papel)
        self.wdriver = wdriver
        self.relatorios = {}
        self.series = {}
        
    # Extrai o número do relatório do script da B3
    def __num_doc(self, href):  
        strn = 'NumeroSequencialDocumento='
        href = href[href.find(strn)+len(strn):]
        return int(href[:href.find('&')])

    # Extrai a data de referência e data de publicação do relatório do script da B3
    def __datas(self, relat):
        dats = relat['onmouseover']
        strm = 'MontaHint'
        tp = eval(dats[dats.find(strm)+len(strm):][:-2])
        return [todate(tp[0]), todate(tp[3][:10])]

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
        
    # busca no site da B3 as datas e números dos relatórios de um ano para um papel
    def relatorios_cvm_b3(self, ano):
        # Verifica se o ano já foi pesquisado antes para esse objeto
        if ano in self.relatorios:
            return self.relatorios[ano]
        self.cd_cvm_ = self.dados.cd_cvm()
        url = f'http://bvmf.bmfbovespa.com.br/cias-listadas/empresas-listadas/ResumoDemonstrativosFinanceiros.aspx?codigoCvm={self.cd_cvm_}&idioma=pt-br'
        
        for i in range(20):
            print(1)
            soup = self.bstimeout(url, 10)
  
            viewstate = soup.find('input', id='__VIEWSTATE')
            eventval = soup.find('input', id='__EVENTVALIDATION')
            
            if viewstate and eventval:
                break
            elif i==19:
                print('Número de tentativas excedidads para o site da B3!!')

        anos = soup.find(id='ctl00_contentPlaceHolderConteudo_cmbAno').find_all('option')
        if str(ano) not in [i.text for i in anos]:
            return False

        viewstate = viewstate['value']
        eventval = eventval['value']
        data = {
            '__EVENTTARGET': 'ctl00$contentPlaceHolderConteudo$cmbAno',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': viewstate,
            '__VIEWSTATEGENERATOR': '72E426D7',
            '__EVENTVALIDATION': eventval,
            'ctl00$contentPlaceHolderConteudo$MenuEmpresasListadas1$tabMenuEmpresa':' {"State":{},"TabState":{"ctl00_contentPlaceHolderConteudo_MenuEmpresasListadas1_tabMenuEmpresa_tabRelatoriosFinanceiros":{"Selected":true}}}',
            'ctl00$contentPlaceHolderConteudo$cmbAno': str(ano)
            }
            
        # as vezes a página da bolsa precisa de mais de uma tentativa para retornar os dados
        for i in range(20):
            soup = self.bstimeout(url, 10, data=data)
            relatorios = [i for i in soup.find_all('a') if "Informações Trimestrais" in i.text or 'Demonstrações Financeiras Padronizadas' in i.text]
            
            if len(relatorios) > 0:
                break
            elif i==19:
                print('Número de tentativas excedidads para o site da B3!!')
                
        
        d = np.array([[int(self.__datas(i)[0].month/3)]+self.__datas(i)+[self.__num_doc(i['href'])] for i in relatorios], dtype='object')
        # retorna os números dos relatórios do ano
        dic = dict(zip(d[:,0], d[:,[1,2,3]]))
        self.relatorios.update({ano:dic})
        return dic
        
    def relatorios_cvm(self, ano=False):
        # Verifica se o ano já foi pesquisado antes para esse objeto
        if ano and ano in self.relatorios:
            return self.relatorios[ano]
        elif len(self.relatorios):
            return

        self.cd_cvm_ = self.dados.cd_cvm()
        driver = webdriver.Chrome(self.wdriver, chrome_options=options)
        url = 'https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx?tipoconsulta=CVM&codigoCVM='+str(self.cd_cvm_)

        driver.get(url)
        time.sleep(3)

        driver.find_element_by_id('rdPeriodo').click()
        time.sleep(3)

        dataini = driver.find_element_by_id('txtDataIni')
        dataini.clear()
        dataini.send_keys('01012011')
        #datafim = driver.find_element_by_id('txtDataFim')
        #datafim.clear()
        #datafim.send_keys('3112'+str(ano+1))

        d=[]
        for s in ['ITR', 'DFP']:
            driver.find_element_by_id('cboCategoria_chosen_input').send_keys(s)
            driver.find_element_by_id('cboCategoria_chosen_input').send_keys(Keys.RETURN)
            driver.find_element_by_id('btnConsulta').click()
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            relat = soup.find(id='grdDocumentos').find('tbody')
            relat = [[i.text for i in j.find_all('td')[:-1]]+[self.__num_doc(j.find_all('td')[-1:][0].find('i')['onclick'])] for j in relat.find_all('tr')]
            
       #     relat = [i for i in relat if i[7]=='Ativo' and todate(i[5].split()[1]).year==ano]
            relat = [i for i in relat if i[7]=='Ativo']
            if len(relat)>0:
                relat = np.array(relat, dtype=object)[:,[5,6,10]]
                for c in [0,1]:
                    relat[:,c]=[todate(i.split()[1]) for i in relat[:,c]]

                d.append(np.column_stack([[int(i[0].month/3) for i in relat], relat]))

            driver.find_element_by_id('textoDivPesquisa').click()
            time.sleep(2)

        d=np.concatenate(d)
        driver.close()
        if len(d)>0:
            dic = {}
            for y in list(set([i.year for i in d[:,1]])):
                a = np.array([i for i in d if i[1].year==y])
                dic.update({y:dict(zip(a[:,0], a[:,[1,2,3]]))})
            self.relatorios.update(dic)
            if ano:
                return dic[ano]


    def get(self, ind, ano, tri):
    
        link = link_ind[indice_ind[ind]] if type(ind)==int else link_ind[ind]
        if (ind, ano, tri) in self.series:
            return self.series[(ind, ano, tri)] 
            
        dados = self.relatorios_cvm(ano)
        num = dados[tri][2]

        driver = webdriver.Chrome(self.wdriver, chrome_options=options)
        # instanciar
        #driver.set_page_load_timeout(8)
        
        url = f'http://www.rad.cvm.gov.br/ENETCONSULTA/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={num}&CodigoTipoInstituicao=2'
 #       print(url)
 #       print(link+str(num))
        driver.get(url)
        
        url=link+str(num)
        driver.get(url)
        response = driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
        soup = BeautifulSoup(response)
        tabela = soup.find('tbody').findAll('tr')        
        driver.close()
        tabela = [[i.text.replace('\xa0','') if i.text.replace('\xa0','') not in ('','0') else None for i in j.find_all('td')[:3]] for j in tabela]
        self.series.update({(ind, ano, tri):pd.DataFrame(tabela[1:], columns=tabela[0])})   
    
        return pd.DataFrame(tabela[1:], columns=tabela[0])


#print(Raw('PETR4', wdriver=r'C:\Users\11111\Desktop\Python\chromedriver.exe').get(1,2020,2))








