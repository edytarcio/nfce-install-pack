#!/usr/bin/python2.7
#-*- coding: utf-8 -*-

#__all__ = ('NFCE',)
__author__= ('Edytarcio',)
__version__ = '0.0.2'
__data__ = '20141014'

import os
import sys
import subprocess
import collections
import argparse
import traceback
import xml.etree.ElementTree as xml
import re
from functools import wraps
from ctypes import *
from ConfigParser import ConfigParser

def build_chunks(l, n):
    """ (recipe) Funcao geradora que retorna uma sequencia de numeros (n) 
    conforme cadeia informada (l). O resultado e um 'generator object' (ou 
    'iterator' que pode ser utilizado em um loop.
    Ex: 
    >> list(chunks(range(1,11),5))
    >> [[1,2,3,4,5],[6,7,8,9,10]]
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

class NFCE():
    """NFCE e um wrapper da biblioteca DarumaFramework. Possui metodos para
    emissao de NFCE bem como outros processos para inutilizacao e consulta de 
    dados. Em resumo o DarumaFramework faz uma integracao com a Sefaz 
    via Migrate webserver.
    """
    def __init__(self):
        pass 

    #def carrega_dll(self):
    #    """Carrega biblioteca do Daruma Framework.
    #    """
    #    if "linux" in sys.platform:
    #        self.dll = cdll.LoadLibrary("/usr/local/lib/libDarumaFramework.so")
    #    else:
    #        self.dll = WinDLL("DarumaFrameWork.dll")
    def carrega_dll(f_executa_metodo):
        """Decorator para tratamento das Exceptions.
        """
        @wraps(f_executa_metodo) # recupera informacoes sobre o metodo
        def executa_metodo(*arguments):
            instancia = arguments[0]
            if "linux" in sys.platform:
                instancia.dll = cdll.LoadLibrary("/usr/local/lib/libDarumaFramework.so")
            else:
                instancia.dll = WinDLL("DarumaFrameWork.dll")
            f_executa_metodo(*arguments) # deve retornar apenas um dicionario 
        return executa_metodo 

    def template_nfce(self):
        """Inicia um ciclo basico para impressao de um Danfe NFCe.
           1. Abertura.
           2. Impressao dos Itens.
           3. Totalizacao.
           4. Pagamento.
           5. Encerramento.
        """
        #self.verifica_comunicacao() # particionando
        self.cancela_nfce_andamento() # Verifica comunicacao 1
        self.abre_nfce_com_xml()
        self.item_nfce_com_xml()
        self.totaliza_nfce_com_xml()
        self.pagamento_nfce_com_xml()
        #self.informar_valor_imposto()
        #self.informar_mensagem_do_imposto()
        return self.finaliza_nfce_com_xml()

    def cancela_nfce_andamento(self):
        """Cancela NFCe em andamento"""
        resposta = self.consulta_status_nfce()
	# Status irregulares [1, 2, 3, 4]
        # Ignorado status '1' porque a lib consegue refazer a abertura; mas 
	# nao consegue cancelar status '1' caso emitido a mais de 30 minutos
	if resposta['status'] in ( 2, 3, 4):
            self.cancela_ultimo_nfce()

    def consulta_status_nfce(self):
        """Consulta o status corrente da impressao do Danfe.
        Codigo  Status
        --------------
        0       - Cupom Fechado.
        1       - NFC-e em registro de item.
        2       - NFC-e em totalização.
        3       - NFC-e em pagamento.
        4       - NFC-e em finalização.
        5       - NFC-e finalizado.
        6       - NFC-e cancelado.
        """
        status_nfce =["Cupom Fechado.",
                      "NFC-e em registro de item.",
                      "NFC-e em totalização.",
                      "NFC-e em pagamento.",
                      "NFC-e em finalização.",
                      "NFC-e finalizado.",
                      "NFC-e cancelado."]
        status = self.dll.rCFVerificarStatus_NFCe_Daruma()
	if status not in (0, 1, 2, 3, 4, 5, 6):
            raise Exception("Erro ao executar o metodo Verifica Status.")
	return {"status": status, "descricao": status_nfce[status]}

    def verifica_comunicacao(self): # metodo em desuso
        # chacar se o gne_framework existe e se esta configurado...

        stts = self.status_impressora_dual()
        if not stts['resposta']:
            stts_inicial = stts
            # Atencao: Impressora esta inoperante...setar permissao e 
	    # velocidade automaticamente.

            # Implementar: Identificar a porta atraves do arquivo tty1.conf
            stts = self.permissao_porta("usb","115200")
            if not stts['resposta']:
                ## Impressora esta off-line e nao foi possivel dar
		## permissao na porta.
		return self.verifica_status({"status": 717})

            stts = self.velocidade_porta("usb","115200")
            if not stts['resposta']:
                ## Erro ao setar velocidade.
                return stts_inicial
        return stts
    
    def status_web(self): 
        """Informa status de comunicacao do Web Servidor.

        Status Descricao
        ----------------
        1      - Comunicacao Ok.
        """
        status = self.dll.rStatusWS_NFCe_Daruma()
	if status !=1:
	    if status == -1:
		raise Exception("-1: Falha de comunicacao.")
            elif status == -2:
		raise Exception("-2: Chave do desenvolvedor invalida.")
	    elif status == -5:
		raise Exception("-5: Erro generico.")
	    elif status == -8:
		raise Exception("-8: Usuario nao autorizado.")
	    elif status == -9:
		raise Exception("-9: Usuario nao licenciado.")
            else:
                raise Exception("0: Erro ao consultar status do Web Service.")
	return {'status':status}

    def status_impressora_dual(self):
        """Checa se impressora esta OFF-Line. 
        Util principalmente quando utilizado antes de processos cruciais 
        como inicializacao de Danfes e cancelamentos para evitar envio 
        de comandos com a impresssora OFF-Line.
        """
        # Verificar permissao porta, velocidade impressora.
        status = self.dll.rStatusImpressora_DUAL_DarumaFramework()
	if status !=1:
	    if status == -1:
		raise Exception("-1: Erro de atualizacao de Chave.")
            elif status == -2:
		raise Exception("-2: Linhas e colunas invalidas.")
	    elif status == -27:
		raise Exception("-27: Erro generico.")
	    elif status == -50:
		raise Exception("-50: Impressora OFF-LINE.")
	    elif status == -51:
		raise Exception("-51: Impressora sem papel.")
	    elif status == -52:
		raise Exception("-52: Impressora inicializando.")
            else:
                raise Exception("0: Erro! Nao foi possivel enviar o metodo.")
	return {'status':status}

    def permissao_porta(self):  # Testar este metodo.
        porta, velocidade = args

	# Implementar: Verifica se a porta eh com ou usb
        if "usb" in porta:
           status = subprocess.call(
              "su imprime -c 'chmod -R 777 /dev/ttyUSB0'".format(
              velocidade),shell=True)
        else:
           pass

        if status == 1:
            return {"status": 1}
        else:
            return {"status": 0}

    def velocidade_porta(self):  # Testar este metodo.
        """Configura velocidade da porta.
        Este metodo configura a velocidade da porta de comunicacao da
        impressora DUAL.

        porta   "saida"  "velocidade"
        ---------------------------------
        porta    usb      115200
        porta    com      9600

        """
        porta, velocidade = args
        if "usb" in porta:
           if velocidade:
               ## Retorna "0" se executado com sucesso
               status = subprocess.call(
                "stty -F /dev/ttyUSB0 speed {0}".format(velocidade),shell=True)
           else:
               status = subprocess.call(
                   "stty -a < /dev/ttyUSB0",shell=True)
        else:
            pass

        if status == 0:
            # comando executado com sucesso
            return {"status": 1}
        else:
            return {"status": 0}

    def reload_gne_framework(self, cfile, loja, serie, nnf):
        """Carrega o GNE_Framework com a configuracao do gne.ini"""
        section = loja
        tags = self.get_section_config_ini(cfile, section, dict_format=True)
        configs = [] 
        for key, value in tags.iteritems():
            if serie and key == 'serie':
                value = serie
                # Atualiza serie no gne.ini   
                self.set_param_section_config_ini(cfile, loja, key, value)
            elif nnf and key == 'nnf':
                value = nnf
                # Atualiza nnf no gne.ini 
                self.set_param_section_config_ini(cfile, loja, key, value)

            config = self.alterar_gne_framework(key, value)
            configs.append([key, config[key]])
        return configs 

    def reload_daruma_framework(self, cfile):
        """Carrega o DarumaFramework com a configuracao do daruma.ini"""
        section = 'DARUMA'
        cfile = '/usr/local/lib/daruma.ini'
        tags = self.get_section_config_ini(cfile, section, dict_format=True)
        configs = [] 
        for key, value in tags.iteritems():
            config = self.alterar_daruma_framework(key, value)
            configs.append([key, config[key]])
        return configs 


    def alterar_gne_framework(self, tag, value):
        """Alterar os valores do GNE_Framework.xml"""
        value = str(value)
        if not value:
            raise Exception("709 - Parametros insuficientes!")

        key_tag = self.carrega_endereco_tag_gne(tag.upper())
        self.dll.regAlterarValor_NFCe_Daruma.argstypes = [
            c_char_p, c_char_p]
        self.dll.regAlterarValor_NFCe_Daruma.restype = c_int
        status = self.dll.regAlterarValor_NFCe_Daruma(key_tag, value)

	if status !=1:
	    if status == -40:
		raise Exception("-40: Tag XML GNE_Framework nao encontrada.")
        return {tag: value}

    def alterar_daruma_framework(self, tag, value):
        """Alterar os valores do GNE_Framework.xml"""
        value = str(value)
        if not value:
            raise Exception("709 - Parametros insuficientes!")

        key_tag = self.carrega_endereco_tag_daruma(tag.upper()) # return 2 items list
        #self.dll.regAlterarValor_NFCe_Daruma.argstypes = [c_char_p, c_char_p]
        #self.dll.regAlterarValor_NFCe_Daruma.restype = c_int
        status = self.dll.regAlterarValor_Daruma((key_tag[0]+'\\'+key_tag[1]), value)

	if status !=1:
	    if status == -40:
		raise Exception("-40: Tag XML DarumaFramework nao encontrada.")
        return {tag: value}

    def carrega_endereco_tag_gne(self, tag):
        """Carrega endereco de tag para consulta e alteracao do arquivo
        GNE_Framework.xml.
        """
        gne_dict = {"EMPPK":"CONFIGURACAO\EmpPK",
                   "EMPCK":"CONFIGURACAO\EmpCK",
                   "MODELO":"CONFIGURACAO\Modelo",
                   "TIPONF":"CONFIGURACAO\TipoNF",
                   "TIPOAMBIENTE":"CONFIGURACAO\TipoAmbiente",
                   "TOKENSEFAZ":"CONFIGURACAO\TokenSefaz",
                   "IMPRESSAOCOMPLETA":"CONFIGURACAO\ImpressaoCompleta",
                   "CUF":"IDE\cUF",
                   "NNF":"IDE\\nNF",
                   "SERIE":"IDE\Serie",
                   "CMUNFG":"IDE\cMunFG",
                   "INDPRES":"IDE\indPres",
                   "CNPJ":"EMIT\CNPJ",
                   "XNOME":"EMIT\\xNome",
                   "XLGR":"EMIT\ENDEREMIT\\xLgr",
                   "NRO":"EMIT\ENDEREMIT\Nro",
                   "XBAIRRO":"EMIT\ENDEREMIT\\xBairro",
                   "CMUN":"EMIT\ENDEREMIT\cMun",
                   "XMUN":"EMIT\ENDEREMIT\\xMun",
                   "UF":"EMIT\ENDEREMIT\UF",
                   "CEP":"EMIT\ENDEREMIT\CEP",
                   "IE":"EMIT\IE",
                   "IMPRIMIR":"NFCE\MSGPROMOCIONAL\Imprimir",
                   "TITULO":"NFCE\MSGPROMOCIONAL\Titulo",
                   "MSGIMPOSTO":"NFCE\MsgLeiDoImposto"
                   }

        if tag not in gne_dict:
            raise Exception("-40: Tag XML GNE_Framework nao encontrada.")
        return gne_dict[tag]

    def carrega_endereco_tag_daruma(self, tag):
        """Carrega endereco de tag para consulta e alteracao do arquivo
        DarumaFramework.xml.
        """
        daruma_dict = {"LOCALARQUIVOS":['START','LocalArquivos'],
                       "LOCALARQUIVOSRELATORIOS":['START','LocalArquivosRelatorios'],
                       "LOGTAMMAXMB":['START','LogTamMaxMB'],
		       "MODOOBSERVER":['START','ModoObserver'],
                       "PATHBIBLIOTECASAUXILIARES":['START','PathBibliotecasAuxiliares'],
                       "PRODUTO":['START','Produto'],
                       "THREADAOINICIAR":['START','ThreadAoIniciar'],
                       "TIPOREGISTRO":['START','TipoRegistro'],
                       "TERMICA":['DUAL','Termica'],
                       "DUALTAMANHOBOBINA":['DUAL','TamanhoBobina'],
                       "DUALPORTACOMUNICACAO":['DUAL','PortaComunicacao'],
                       "DUALVELOCIDADE":['DUAL','Velocidade'],
                       "ROTA1":['DUAL','Rota1'],
                       "ROTA2":['DUAL','Rota2'],
                       "ROTA3":['DUAL','Rota3'],
                       "ROTA4":['DUAL','Rota4'],
                       "ROTA5":['DUAL','Rota5'],
                       "ATIVAROTA":['DUAL','AtivaRota'],
                       "AJUSTARDATAHORA":['NFCE','AjustarDataHora'],
                       "AVISOCONTINGENCIA":['NFCE','AvisoContingencia'],
                       "AUDITORIA":['NFCE','Auditoria'],
                       "ENCONTRARIMPRESSORA":['NFCE','EncontrarImpressora'],
		       "PATHARQUIVOSCTGOFFLINE":['NFCE','PathArquivosCtgOffline'],
                       "MARCAIMPRESSORA":['NFCE','IMPRESSORA\MarcaImpressora'],
                       "NFCETAMANHOBOBINA":['NFCE','IMPRESSORA\TamanhoBobina'],  
                       "NFCEPORTACOMUNICACAO":['NFCE','IMPRESSORA\PortaComunicacao'], 
                       "NFCEVELOCIDADE":['NFCE','IMPRESSORA\Velocidade']
                      }
        #"ENDERECOSERVIDOR":['NFCE','EnderecoServidor'],

        #if tag.upper() not in [x.upper() for x in daruma_dict.keys()]:
        if tag.upper() not in daruma_dict:
            raise Exception("-40: Tag XML DarumaFramework nao encontrada.")
        return daruma_dict[tag.upper()]

    def carrega_mensagem(self, codigo):
        """Retorna descricao da mensagem de erros. 
        Os codigos de erros estao na faixa de 700 a 799.
        """
        if not codigo:
            raise Exception("709 - Parametros insuficientes!")
           
        ## Futuramente salvar as mensagens em um arquivo.
        mensagem = {700:"Duplicidade de NFCe com diferrenca" + 
                    " na chave de acesso.",
                    701:"Danfe Autorizado mas houve erro na impressao!" + \
                    " Foi cancelado!",
                    702:"Impressora esta OFF-LINE!",
                    703:"Impressora sem papel!",
                    704:"Impressora nao esta operacional!",
                    705:"XML de envio fora do padrao!",
                    706:"Rejeicao: Duplicidade de Evento!",
                    707:"Falha ao dar permissao no arquivo!",
                    708:"Tag nao encontrada!",
                    709:"Parametros insuficientes!",
                    710:"Codigo nao catalogado!",
                    711:"Parametro nao encontrado!",
                    712:"Sem comunicacao com Web Service!",
                    713:"Rejeicao: NFC-e autorizada a mais de 24 horas",
                    714:"Nao foi possivel dar permissao na porta de impressao!",
                    715:"Falha ao configurar velocidade da porta de impressao!",
		    716:"ATENCAO: Danfe Autorizado mas houve um erro" +
                        " na impressao!",
		    717:"Impressora esta OFF-Line e nao foi possivel dar " +
		    "permissao na porta",
		    718:"Erro ao tentar invocar servico web!",
		    719:"Documento NFCe anterior pendente!",
		    720:"Falha na estrutura do evento enviado!",
		    721:"NFCe nao em fase de encerramento ou " + 
		        "Erro ao tentar invocar o servico!",
                    722:"Documento possui uma serie diferente da utilizada no PDV",
                    723:"Chave de comunicao invalida",
                    798:"Rejeicao: NFC-e com Data-Hora de emissao atrasada." + \
                    "|ou Duplicidade na chave de acesso.",
                    799:"ERRO nao catalogado!",
                   }
        if codigo not in mensagem.keys():
            raise Exception("710 - Codigo nao catalogado!")
        return {"codigo": codigo, "mensagem": mensagem[codigo]}

    def ler_gne_framework(self, tag):
        """Metodo para leitura de configuracoes do GNE_Framework.xml. 
        As informacoes retornadas sao:

        Param       Tipo de Configuracao
        --------------------------------
        "impressao" - Informa tipo de impressao, se reduzida("0") ou
                      e("1").
        "emppk"     - Informa chave EMPPK da empresa.
        "empck"     - Informa chave EMPCK da empresa.
        "empresa"   - Informa nome da empresa.
        "endereco"  - Informa endereco da empresa.
        "numero"    - Informa numero da empresa.
        "nnf"       - Informa NNF.
        "entrega"   - Informa tipo de entrega, se presencial("1") ou a
                      domicilio ("4").
        """
        if not tag:
            raise Exception("709 - Parametros insuficientes!")

        value = " "*40
        key_tag = self.carrega_endereco_tag_gne(tag.upper())
        if not key_tag:
            raise Exception("-40: Tag XML nao encontrada.")

        status = self.dll.regRetornarValor_NFCe_Daruma(key_tag, value)

	if status !=1:
            if status == -40:
                raise Exception("-40: Tag XML nao encontrada.")
        return {tag: value}

    def ler_daruma_framework(self, tag):
        """Metodo para leitura de configuracoes do DarumaFramework.xml. 
        """
        if not tag:
            raise Exception("709 - Parametros insuficientes!")

        #key_tag = self.carrega_endereco_tag_daruma(tag.upper())
        key_tag = self.carrega_endereco_tag_daruma(tag)
        if not key_tag:
            raise Exception("-40: Tag XML DarumaFramework nao encontrada.")

        # status = self.dll.regRetornarValor_Daruma(key_tag, value)
        value = " "*100
        status = self.dll.regRetornaValorChave_DarumaFramework(key_tag[0],key_tag[1], value)
        #status = self.dll.regRetornaValorChave_DarumaFramework('NFCE','Auditoria', value)
        #status = self.dll.regRetornaValorChave_DarumaFramework('DUAL','Rota1', value)

	if status !=1:
            raise Exception("-40: Tag XML DarumaFramework nao encontrada.")
        return {tag: value}

    def abre_nfce_com_xml(self):
        diretorio = '/u1/caixa/dev/tty1/dcret.xml'
        xml_string = self.ler_arquivo_xml(diretorio)
        header = self.xml_para_dicionario(xml_string, multi=False)

        cpf = header["nr_cpfcgc"]
        nome = header["no_cliente"]
        logradouro = header["tx_endereco"]
        numero = header["nr_numero"]
        bairro = header["no_bairro"]
        municipio = header["cd_municipio"]
        cidade = header["no_cidade"]
        uf = header["sg_uf"]
        cep = header["nr_cep"]
        email = header["cl_email"]

        # Verifica tipo de ambiente.
        tag = self.ler_gne_framework("tipoambiente")
	if int(tag["tipoambiente"]) == 2:
            nome = "NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL"

        self.abre_nfce(cpf, nome, logradouro, numero, bairro, municipio,
                      cidade, uf, cep, email)

    def abre_nfce(self, cpf, nome, logradouro, numero, bairro, municipio,
                 cidade, uf, cep, email):

        #self.dll.aCFAbrir_NFCe_Daruma.argstypes = [c_char_p * 9]
        #self.dll.aCFIdentificarConsumidor_NFCe_Daruma.argstypes = [c_char_p * 9]
        #self.dll.aCFAbrir_NFCe_Daruma.restype = c_int
        #self.dll.aCFAbrirNumSerie_NFCe_Daruma.argtypes = [c_char_p * 11]
        #self.dll.aCFAbrirNumSerie_NFCe_Daruma.argtypes = [c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p]
        #self.dll.aCFAbrirNumSerie_NFCe_Daruma.restype = c_int

        info_consumidor = [cpf, nome, logradouro, numero, bairro, municipio,
			  cidade, uf, cep]
        email = "nfce.metidieri@armazemparaiba.com.br"

        id_consumidor = True
	for info in info_consumidor:
	    if info is None or info.strip() is None or info.startswith(" "):
	        id_consumidor = False   
                break

        # Habilita o metodo para email
        id_email = True 

        #if not id_consumidor:
        #    if args.serie and args.nnf:
        #        # Numeracao Nao Automatica
        #        status = self.aCFAbrirNumSerie_NFCe_Daruma(nnf, serie, "", "", "", "", "", "", "", "", "")
        #
        #    else:
        #        # Imprime apenas venda consumidor
        #        status = self.dll.aCFAbrir_NFCe_Daruma("", "", "", "", \
	#                                           "", "", "", "", "", "")
        #elif id_email:
        #    print 'ENDERECE DE EMAIL...', id_email
        #    # Imprime informacoes do consumidor  + email
        #    status = self.dll.aCFAbrir_NFCe_Daruma("", "", "", "", \
	#		                           "", "", "", "", "", "")
        #    status = self.dll.aCFIdentificarConsumidor_NFCe_Daruma(
        #             cpf, nome, logradouro, numero, bairro, municipio,
        #             cidade, uf, cep, email)
        #else:
        #    # Imprime informacoes do consumidor (nao imprime email)
        #    status = self.dll.aCFAbrir_NFCe_Daruma(              \
        #             cpf, nome, logradouro, numero, bairro, municipio,
        #             cidade, uf, cep)


        if args.serie and args.nnf:
            # Numeracao Nao Automatica
            nnf =  int(args.nnf) -1
            status = self.dll.aCFAbrirNumSerie_NFCe_Daruma(str(nnf), args.serie, "", "", 
		     "", "", "", "", "", "", "")
        else:
            # Numeracao Automatica
            status = self.dll.aCFAbrir_NFCe_Daruma("", "", "", "", "", "", "", "", "", "")

        if id_consumidor:
            # Identificacao do consumidor
            status = self.dll.aCFIdentificarConsumidor_NFCe_Daruma(
                     cpf, nome, logradouro, numero, bairro, municipio,
                     cidade, uf, cep, email)

	if status !=1:
	    if status == -1:
		raise Exception("-1: Erro encontrado na execucao do metodo.")
            elif status == -52:
		raise Exception("-52: Erro ao gravar em arquivo temporario.")
	    elif status == -99:
		raise Exception("-99: Parametros invalidos ou ponteiro nulo.")
            elif status == -100:
		raise Exception("-100: Estado invalido para execucao do metodo.")
	    elif status == -103:
		raise Exception("-103: Dll auxiliar nao encontrada.")
	    elif status == -120:
		raise Exception("-120: Encontrada tag invalida.")
	    elif status == -131:
		raise Exception("-131: NFCe nao aberta.")
            else:
                raise Exception("0: Erro ao executar metodo de abertura.")
        return {"status": status}

    def item_nfce_com_xml(self):
        diretorio = '/u1/caixa/dev/tty1/docimp.xml'
        xml_string = self.ler_arquivo_xml(diretorio)
        itens = self.xml_para_dicionario(xml_string, multi=True)

        for item in itens:
            aliquota = item["vl_aliq_icms"]
            quantidade = item["qt_produto"]
            preco_unitario = item["vl_preco_uni"]
            tipo_desconto_acrescimo =  "D$" ##  'D$' desconto ou 'A$' acrescimo
            valor_desconto_acrescimo = item["vl_desconto"]
            unidade_medida = "und"
            descricao_item = item["no_descricao"]
	    ncm = item["cd_ncm"]
            cfop = "5102"
            codigo_item = item["cd_produto"] 

            self.item_nfce(aliquota, quantidade, preco_unitario, 
	                  tipo_desconto_acrescimo, valor_desconto_acrescimo, codigo_item, 
                          ncm, cfop, unidade_medida, descricao_item)

    def item_nfce(self, aliquota, quantidade, preco_unitario, 
	         tipo_desconto_acrescimo, valor_desconto_acrescimo, codigo_item, 
		 ncm, cfop, unidade_medida, descricao_item):
        """Envia ao DarumaFramework os itens a serem impressos no Danfe NFCe.
        Os itens sao carregados de uma arquivo XML.
        """
        # O desconto esta sendo no item e o acrescimo no subtotal.
        self.dll.aCFVender_NFCe_Daruma.argstypes = [c_char_p * 11]
        self.dll.aCFVender_NFCe_Daruma.restype = c_int

        tipo_desconto_acrescimo =  "D$" # 'D$' desconto, 'A$' acrescimo
        unidade_medida = "und"
        cfop = "5102"
        uso_futuro = ""

	if valor_desconto_acrescimo[0] == ".":
           valor_desconto_acrescimo = "0" + valor_desconto_acrescimo

        status = self.dll.aCFVenderCompleto_NFCe_Daruma(
	    aliquota, quantidade, preco_unitario, tipo_desconto_acrescimo, 
	    valor_desconto_acrescimo, codigo_item, ncm, cfop, unidade_medida, 
	    descricao_item, uso_futuro)
	if status !=1:
	    if status == -1:
		raise Exception("-1: Erro encontrado na execucao do metodo.")
	    elif status == -52:
		raise Exception("-52: Erro ao gravar em arquivo temporario.")
            elif status == -99:
		raise Exception("-99: Parametros invalidos ou ponteiro nulo.")
	    elif status == -103:
		raise Exception("-103: Dll auxiliar nao encontrada.")
	    elif status == -121:
		raise Exception("-121: Estrutura invalida.")
	    elif status == -122:
		raise Exception("-122: Tag obrigatoria nao foi informada.")
	    elif status == -123:
		raise Exception("-123: Tag obrigatoria nao tem valor preenchido.")
	    elif status == -132:
		raise Exception("-132: NFCe nao em fase de venda.")
            else:
                raise Exception("0: Erro ao executar metodo de venda de itens.")
        return {"status": status}

    def totaliza_nfce_com_xml(self):
        diretorio = '/u1/caixa/dev/tty1/dcret.xml'
        xml_string = self.ler_arquivo_xml(diretorio)
        header = self.xml_para_dicionario(xml_string, multi=False)

        tipo_desconto_acrescimo = "A$"  # 'D$' Desconto ou 'A$' Acrescimo
        valor_desconto_acrescimo = header["vl_desp_finan"]
        self.totaliza_nfce(valor_desconto_acrescimo, tipo_desconto_acrescimo)


    def totaliza_nfce(self, valor_desconto_acrescimo, tipo_desconto_acrescimo="A$"):
        """Totalizacao do Danfe NFCe.
        Pode-se informar despesa financeira ou desconto na totalizacao.
 
        Argumentos:
        tipo_desconto_acrescimo = 'D$' Desconto ou 'A$' Acrescimo
        """
        # Estao sendo feitos apenas acrescimos no subtotal, o desconto
	# esta sendo no item.
        self.dll.aCFTotalizar_NFCe_Daruma.argstypes = [c_char_p * 2]

        status = self.dll.aCFTotalizar_NFCe_Daruma(tipo_desconto_acrescimo,
			                           valor_desconto_acrescimo)
	if status !=1:
	    if status == -1:
		raise Exception("-1: Erro encontrado na execucao do metodo.")
	    elif status == -35:
		raise Exception("-35: Desconto ou Acrescimo nao pode ser maior que o valor total.")
	    elif status == -52:
		raise Exception("-52: Erro ao gravar em arquivo temporario.")
            elif status == -99:
		raise Exception("-99: Parametros invalidos ou ponteiro nulo.")
	    elif status == -103:
		raise Exception("-103: Dll auxiliar nao encontrada.")
	    elif status == -133:
		raise Exception("-133: NFCe nao em fase de totalizacao.")
	    elif status == -120:
		raise Exception("-120: Encontrada tag invalida.")
	    elif status == -121:
		raise Exception("-121: Estrutura invalida.")
	    elif status == -122:
		raise Exception("-122: Tag obrigatoria nao foi informada.")
            else:
                raise Exception("0: Erro ao executar metodo de venda de itens.")
        return {"status": status}


    def pagamento_nfce_com_xml(self):

        diretorio = '/u1/caixa/dev/tty1/pagamento.xml'
        xml_string = self.ler_arquivo_xml(diretorio)
        pagamentos = self.xml_para_dicionario(xml_string, multi=True)

        for pagamento in pagamentos:
            forma = pagamento["tipo"]
            valor = pagamento["valor"]
            self.dll.aCFEfetuarPagamento_NFCe_Daruma(forma, valor)



    def pagamento_nfce(self, forma, valor):
        """Descriçãdodos meio de pagamentos.
        As descrições pré-definidpela legislaçãda NFCe são:

        01- Dinheiro
        02- Cheque
        03- Cartão de Crédito
        04- Cartão de Débito
        05- Crédito Loja
        10- Vale Alimentação
        11- Vale Refeição
        12- Vale Presente
        13- Vale Combustível
        99- Outros
        """
        self.dll.aCFEfetuarPagamento_NFCe_Daruma.argstypes = [c_char_p * 2]
        self.dll.aCFEfetuarPagamento_NFCe_Daruma.restype = c_int

        if "Credito" in forma:        # Cartao de Credito
            forma = 'Cart' + chr(227) + 'o de Cr' + chr(233) + 'dito'
        if "Debito" in forma:         # Cartao de Debito
            forma = 'Cart' + chr(227) + 'o de D' + chr(233) + 'bito'
        if "Crediario" in forma:      # Crediario
            forma = 'Cr' + chr(233) + 'dito Loja'

        valor = valor 
        status = self.dll.aCFEfetuarPagamento_NFCe_Daruma(forma, valor)
	if status !=1:
	    if status == -1:
		raise Exception("-1: Erro encontrado na execucao do metodo.")
	    elif status == -34:
		raise Exception("-34: Valor Total ja foi pago.")
	    elif status == -52:
		raise Exception("-52: Erro ao gravar em arquivo temporario.")
            elif status == -99:
		raise Exception("-99: Parametros invalidos ou ponteiro nulo.")
	    elif status == -103:
		raise Exception("-103: Dll auxiliar nao encontrada.")
	    elif status == -134:
		raise Exception("-134: NFCe nao em fase de pagamento.")
	    elif status == -120:
		raise Exception("-120: Encontrada tag invalida.")
	    elif status == -121:
		raise Exception("-121: Estrutura invalida.")
	    elif status == -122:
		raise Exception("-122: Tag obrigatoria nao foi informada.")
	    elif status == -123:
		raise Exception("-123: Tag obrigatoria nao tem valor preenchido.")
            else:
                raise Exception("0: Erro ao executar metodo de venda de itens.")
        return {"status": status}

    def informar_valor_imposto(self, valor_imposto=None):
        # informar valor da tributacao - nao utilizado
        valor_imposto = 10.00   
        self.dll.aCFValorLeiImposto_NFCe_Daruma.argstypes = [c_char_p]
        self.dll.aCFValorLeiImposto_NFCe_Daruma.restype = c_int
        self.dll.aCFValorLeiImposto_NFCe_Daruma(str(valor_imposto));

    def informar_mensagem_do_imposto(self, valor_imposto=None):
        mensagem_imposto = self.ler_mensagem_imposto()
        self.alterar_gne_framework("MSGIMPOSTO",mensagem_imposto)
        time.sleep(50)

    def finaliza_nfce_com_xml(self):
        """Template para finalizar o Danfe NFCe.  """
        mensagem = self.mensagem_promocional()
        status = self.finaliza_nfce(mensagem)
        info_ultima_nfce = self.informacoes_ultima_nfce()  # informacoes ultima nfce emitida
        info_ultima_nfce["CONTINGENCIA"] = status    # 1- Autorizada, 2- Ctg.Offline, 3- Ctg.OnLine

	if status in (1, 2, 3):
            # Atualiza serie/nnf no gne.ini para reconfiguracao caso necessario
            self.set_param_section_config_ini(args.file, args.loja, 'NNF', info_ultima_nfce['nrnota'])
            self.set_param_section_config_ini(args.file, args.loja, 'SERIE', info_ultima_nfce['nrserie'])

        return info_ultima_nfce

    def finaliza_nfce(self, mensagem):
        self.dll.tCFEncerrar_NFCe_Daruma.argstypes = [c_char_p]
        self.dll.tCFEncerrar_NFCe_Daruma.restype = c_int

        status = self.dll.tCFEncerrar_NFCe_Daruma(mensagem)
	if status not in (1, 2, 3):
            # 1- NFCe Autorizaca; 
	    # 2- Emitida em contingencia offLine;
	    # 3- Emitida em contingencia onLine;
	    if status == -1:
		raise Exception("-1: Erro encontrado na execucao do metodo.")
	    elif status == -2:
		raise Exception("-2: Chave invalida.")
	    elif status == -3:
		raise Exception("-3: Falha no esquema XML.")
	    elif status == -4:
		raise Exception("-4: XML fora do padrao.")
	    elif status == -5:
		raise Exception("-5: Erro generico.")
            elif status == -6:
		raise Exception("-6: Nota ja cadastrada na base de dados.")
	    elif status == -8:
		raise Exception("-8: Usuario nao autorizado.")
	    elif status == -9:
		raise Exception("-9: Usuario nao licenciado.")
	    elif status == -10:
		raise Exception("-10: Documento e ambiente nao identificados.")
	    elif status == -13:
		raise Exception("-13: Tipo de documento nao identificado.")
	    elif status == -14:
		raise Exception("-14: Erro retornado pelo Web Service.")
	    elif status == -52:
		raise Exception("-52: Erro ao gravar arquivo temporario.")
	    elif status == -99:
		raise Exception("-99: Parametros invalidos ou ponteiro nulo.")
	    elif status == -103:
		raise Exception("-103: Nao foram encontradas as dll auxiliares.")
	    elif status == -108:
		raise Exception("-108: O valor da nota obriga a identificacao do cliente.")
	    elif status == -120:
		raise Exception("-120: Encontrada tag invalida.")
	    elif status == -121:
		raise Exception("-121: Estrutura invalida.")
	    elif status == -135:
		raise Exception("-135: NFCe nao em fase de encerramento.")
            else:
		raise Exception("0: Erro ao executar metodo de encerramento.")
        return status

  
    def mensagem_promocional(self):

        diretorio = '/u1/caixa/dev/tty1/mensagem.xml'
        xml_string = self.ler_arquivo_xml(diretorio)
        mensxml = self.xml_para_dicionario(xml_string, multi=False)

	mensdict = collections.OrderedDict()
	mensdict.update(sorted(mensxml.items()))
	#mensagem = "\n".join(mensdict.values())
	# formatacao para mensagem promocional: 
        # http://www.desenvolvedoresdaruma.com.br/home/downloads/Site_2011/Help/DarumaFrameworkHelpOnline/DarumaFramework/Mini_Impressora/Metodos_para_Autenticacao_e_Impressao/iImprimirTexto_DUAL_Daruma_Framework.htm
	mensagem = "<l></l>".join(mensdict.values())
	#mensagem = "<linha></linha>".join(mensdict.values())
        return mensagem

    def ler_mensagem_imposto(self):

        diretorio = '/u1/caixa/dev/tty1/mensagem-imposto.xml'
        xml_string = self.ler_arquivo_xml(diretorio)
        mensxml = self.xml_para_dicionario(xml_string, multi=False)

	mensdict = collections.OrderedDict()
	mensdict.update(sorted(mensxml.items()))
	#mensagem = "\n".join(mensdict.values())
	# formatacao para mensagem promocional: 
        # http://www.desenvolvedoresdaruma.com.br/home/downloads/Site_2011/Help/DarumaFrameworkHelpOnline/DarumaFramework/Mini_Impressora/Metodos_para_Autenticacao_e_Impressao/iImprimirTexto_DUAL_Daruma_Framework.htm
	mensagem_imposto = "<l></l>".join(mensdict.values())
        # formatacao para inclusao de nova linha
	#mensagem = "<linha></linha>".join(mensdict.values())
        return mensagem_imposto

    def cancela_ultimo_nfce(self):
        """Cancela ultimo NFCe sem informar valores para os parametros."""
        # Esta retornando erro 'Usuario nao licenciado...'
        nnf = ""
        serie = ""
        chave_acesso = ""
        protocolo = ""
        justificativa = ""
        self.cancela_nfce(nnf, serie, chave_acesso, protocolo, justificativa)


    def cancela_nfce_por_xml(self):

        diretorio = '/u1/caixa/dev/tty1/cancelamento.xml'
        xml_string = self.ler_arquivo_xml(diretorio)
        cancelamento = self.xml_para_dicionario(xml_string, multi=False)

        nnf = cancelamento["nr_nnf"]
        serie = cancelamento["nr_serie"]
        chave_acesso = cancelamento["ch_acesso"]
        protocolo = cancelamento["nr_protocolo"]
        justificativa = cancelamento["dc_justificativa"]

        info_cancelamento = [nnf, serie, chave_acesso, protocolo, justificativa]
	for info in info_cancelamento:
	    if info is None or info.strip() is None:
                raise Exception("XML de cancelamento com valor nulo.")

        self.cancela_nfce(nnf, serie, chave_acesso, protocolo, justificativa)

    def cancela_nfce(self, nnf, serie, chave_acesso, protocolo, justificativa=None):
        """Cancelamento de um Danfe NFCe. """
        if not justificativa:
            justificativa = "Problema na impressao."

        self.dll.tCFCancelar_NFCe_Daruma.argstypes = [c_char_p * 5]
        status = self.dll.tCFCancelar_NFCe_Daruma(nnf, serie, chave_acesso, protocolo, justificativa)
	if status !=1:
            if status == 0:
		raise Exception("0: Erro, nao foi possivel comunicar " + 
		                "com a impressora nao fiscal.")
	    if status == -1:
		raise Exception("-1: Cancelamento nao autorizado.")
	    elif status == -2:
		raise Exception("-2: Chave invalida.")
	    elif status == -3:
		raise Exception("-3: Falha no esquema XML.")
	    elif status == -4:
		raise Exception("-4: XML fora do padrao.")
	    elif status == -5:
		raise Exception("-5: Erro generico.")
	    elif status == -8:
		raise Exception("-8: Usuario nao autorizado.")
	    elif status == -9:
		raise Exception("-9: Usuario nao licenciado.")
	    elif status == -10:
		raise Exception("-10: Documento e ambiente nao identificados.")
	    elif status == -13:
		raise Exception("-13: Tipo de documento nao identificado.")
	    elif status == -14:
		raise Exception("-14: Erro retornado pelo Web Service.")
	    elif status == -52:
		raise Exception("-52: Erro ao gravar em arquivo temporario.")
	    elif status == -99:
		raise Exception("-99: Parametros invalidos ou ponteiro nulo.")
	    elif status == -103:
		raise Exception("-103: Nao foram encontradas as DLLs auxiliares.")
	    else:
		raise Exception("Erro ao executar metodo de cancelamento.")
	return {"status": status}

    def informacoes_ultima_nfce(self):
        """Retorna dicionario contendo informacoes sobre o utilmo NFCE emitido.
        As chaves retornadas sao as seguintes:
	   "tlnota", "nrnota", "chacesso", "nrprotocolo", "nrserie", 
	   "dtautorizacao", e "vldigest".
	"""
        info = {} 
        for x in range(1,8):
            value = self.informacao_ultimo_nfce(x)
            info[value[0]] = value[1]
        return info

    def informacao_ultimo_nfce(self, info):
        """Retorna informacoes sobre o ultimo Danfe autorizado.
        As informacoes retornadas sao de acordo com o parametro informado:

        Param  Informacao Retornada
        "1"    - Total da Nota
        "2"    - Numero da nota
        "3"    - Retorna chave de acesso
        "4"    - Protocolo da autorizacao
        "5"    - Serie da NFCe
        "6"    - Data e hora de autorizacao da Sefaz
        "7"    - Digest value

        Aviso: Neste versao do DarumaFramework dever ser chamado imediatamente apos
        o encerramento do Danfe, caso contrario as informacoes nao serao recupedadas.
        """
        info = info
        if not info:
            # Parametros insuficientes...
            raise Exception("709 - Parametros insuficientes!")

        self.dll.rInfoEstendida_NFCe_Daruma.argtypes = [c_char_p, c_char_p]
        self.dll.rInfoEstendida_NFCe_Daruma.restype = c_int
        psz_indice = str(info)
        psz_retorno = " "*44

	indice = {"1":"tlnota", 
	          "2":"nrnota",
		  "3":"chacesso",
		  "4":"nrprotocolo",
                  "5":"nrserie",
                  "6":"dtautorizacao",
                  "7":"vldigest"}

        status = self.dll.rInfoEstendida_NFCe_Daruma(psz_indice, psz_retorno)
	return [indice[psz_indice], psz_retorno]

    def ler_arquivo_xml(self, diretorio):
        """Ler arquivo no formato XML e retorna uma string do XML
	"""
        with open(diretorio, 'r') as fxml:
	    strfx =  fxml.readlines()
	    string = "".join(strfx).replace("&"," e ")
        return string

    def xml_para_dicionario(self, string, multi=False):
        """Converte uma String XML para dicionario.
	"""
        try:
	    root = xml.fromstring(string)
            itens = []
            for cclass in root:
                mykeys = []
                myvalues = []
                for item in cclass:
                    children = item.getchildren() # Em caso de tags encadeadas
                    if children:
                        for child in children:
                            mykeys.append(child.tag.lower())
                            myvalues.append(child.text )
	            else:
                        mykeys.append(item.tag.lower())
                        myvalues.append(item.text )
                    it = dict(zip(mykeys, myvalues))
                itens.append(it)

            if multi:  # Retorna uma lista de dicionarios 
                return itens
            return itens[0] # Retorna apenas um dicionario

	except Exception, e:
            return None


    def busca_por_data(self, data_inicial, data_final):
        """Busca notas NFCE por data."""
        # data_inicial/data_final formato 'DDMMYYYY'
	serie = ""          
	chave_acesso = ""  
        self.__busca_notas("DATA", data_inicial, data_final, serie, chave_acesso) 

    def busca_por_nnf_bloco(self, nnf_inicial, nnf_final, serie, intervalo):
        
	# Busca por bloco para evitar erro de 'Segmentation fault'
        listagem = [] 
        blocos = build_chunks(range(int(nnf_inicial), int(nnf_final) + 1), int(intervalo))
        lista = []
	for bloco in blocos:
            self.busca_por_nnf(str(bloco[0]), str(bloco[-1]), serie)
            diretorio = '/usr/local/lib/documentosRetorno.xml'
            string_xml = self.ler_arquivo_xml(diretorio)
            # Testar aqui se o arquivo eh um XML valido.
            string_xml = "".join("<notas>" + string_xml + "</notas>")
            notas = self.xml_para_dicionario(string_xml, multi=True)
            # 'notas' corresponde a uma lista de dicionarios (notas)
            if notas: # ignorar listas de notas vazias.
                for nota in notas:
                    listagem.append(nota) 
        if not listagem:
            raise Exception("Nao foram encontradas notas!")
        return listagem   # retorna lista de notas no formato dicionario.

    def busca_por_nnf(self, nnf_inicial, nnf_final, serie):
        """Busca notas NFCE por NNF e Serie."""
        chave_acesso = ""
        self.__busca_notas("NUM", nnf_inicial, nnf_final, serie, chave_acesso) 


    def busca_por_chave(self, chave_acesso, serie):
        """Busca notas NFCE por Chave de Acesso."""
	nnf_inicial = ""
        nnf_final = ""
        self.__busca_notas("CHAVE", nnf_inicial, nnf_final, serie, chave_acesso) 


    def __busca_notas(self, tipo_busca, intervalo_inicial, intervalo_final, serie, 
		     chave_acesso):
        """Busca notas NFCe de acordo com o tipo de busca informado."""
        info_consulta = "11" # padrao 1
	resposta = " "*231  # padrao 230
	#resposta = None 

        status = self.dll.rRetornarInformacao_NFCe_Daruma(tipo_busca, 
            intervalo_inicial, intervalo_final, serie, chave_acesso, 
	    info_consulta, resposta) 
	if status !=1:
	    if status == -1:
		raise Exception("-1: Erro encontrado na execucao do metodo")
            elif status == -2:
		raise Exception("-2: Chave Invalida")
	    elif status == -3:
		raise Exception("-3: Falha no schema XML.")
	    elif status == -4:
		raise Exception("-4: XML fora do padrao")
	    elif status == -5:
		raise Exception("-5: Erro generico")
	    elif status == -8:
		raise Exception("-8: Usuario nao Autorizado")
            elif status == -9:
		raise Exception("-9: Usuario nao Licenciado")
	    elif status == -10:
		raise Exception("-10: Documento e Ambiente nao identificados")
	    elif status == -13:
		raise Exception("-13: Tipo de Documento nao identificado")
            elif status == -14:
		raise Exception("-14: Erro retornado pelo WebService.")
            elif status == -52:
		raise Exception("-52: Erro ao gravar em arquivo temporario")
            elif status == -99:
		raise Exception("-99: Parametros invalidos ou ponteiro nulo de pametros")
            elif status == -99:
		raise Exception("-103: Nao foram encontradas as DLLs auxiliaes")
	    else:
		raise Exception("Erro ao executar o metodo Retornar Informacao.")

    def inutiliza_por_lote(self, notas, serie, justificativa): #ok
        """Inutiliza uma lista de notas"""
        # notas eh uma lista
        notas = notas          # notas
        serie = str(serie)     # serie
        if not justificativa:
            justificativa = "Numeracao nao utilizada!" 

        for i in notas:
            nnf = str(i)
            #serie = "0"
            self.inutiliza_por_nota(nnf, serie, justificativa)

    def inutiliza_por_nota(self, nnf, serie, justificativa):  
        """Inutiliza NFCe"""
        nnf_inicial = nnf
        nnf_final = nnf
        self.dll.tCFInutilizar_NFCe_Daruma.argstypes = [ c_char_p * 4]
        self.dll.tCFInutilizar_NFCe_Daruma.restype = c_int

        status = self.dll.tCFInutilizar_NFCe_Daruma(nnf_inicial, nnf_final, serie, justificativa)
	if status !=1:
	    if status == -1:
		raise Exception("-1: Erro encontrado na execucao do metodo.")
            elif status == -2:
		raise Exception("-2: Chave Invalida.")
	    elif status == -5:
		raise Exception("-5: Erro generico.")
	    elif status == -8:
		raise Exception("-8: XML fora do padrao.")
	    elif status == -9:
		raise Exception("-9: Usuario nao licenciado.")
	    elif status == -10:
		raise Exception("-10: Usuario nao licenciado.")
	    elif status == -13:
		raise Exception("-13: Tipo de documento nao identificado.")
	    elif status == -14:
		raise Exception("-14: Erro retornado pelo WebService.")
	    elif status == -52:
		raise Exception("-52: Erro ao gravar em arquivo temporario.")
	    elif status == -99:
		raise Exception("-99: Parametros invalidos ou ponteiro nulo.")
            else:
                raise Exception("Erro ao inutilizar Nota.")

    def tratamentos(f_executa_metodo):
        """Decorator para tratamento das Exceptions.
        """
        @wraps(f_executa_metodo) # recupera informacoes sobre o metodo
        def executa_metodo(*arguments):
            instancia = arguments[0]
            resposta = collections.OrderedDict()
            try:
                # Em casos de segmentation fault
                resposta["resposta"] = "ERRO"
                resposta["mensagem"] = "Processo interrompido."  
                instancia.escreve_resposta(resposta)

                retorno = f_executa_metodo(*arguments) # deve retornar apenas um dicionario 
                resposta["resposta"] = "OK"
                resposta["mensagem"] = "Processo realizado com sucesso"
                if retorno:
                    resposta.update(retorno)
            except Exception, erro:
                resposta["resposta"] = "ERRO"
                resposta["mensagem"] = erro
                resposta["traceback"] = traceback.format_exc() 
            finally:
                instancia.escreve_resposta(resposta)
		if args.terminal:
                   subprocess.call("cat /u1/caixa/dev/tty1/resposta",shell=True)
                   #print "TRACEBACK: ", traceback.format_exc()
        return executa_metodo 

    def escreve_resposta(self, resposta,
                         arquivo = "/u1/caixa/dev/tty1/resposta"):
        with open(arquivo,"w") as file:
            for key, value in resposta.iteritems():
                line = key.upper() + "=" + str(value) + "\n"
                file.write(line)

    def formata_listagem(self, listagem, diretorio=None):
        """Formata listagem para demonstracao em relatorios.
        2014-09-09T12:57:13-04:00  080  00000225  13140871445811000306650800000002251171025534  107
                                   080  00000259  Sequencia nao utilizada                       999
        *Metodo em construcao
	"""
        listagem = sorted(listagem, key=lambda k: int(k['docnumero'])) 
        if not diretorio:
            diretorio="/u1/caixa/dev/tty1/listagem"
        with open(diretorio,"w") as file:
            for oc in listagem:
		if int(oc["docsitcodigo"]) == 999:  # Sequencia nao utilizadas
		    line = "{:25s}  {:0>3d}  {:0>8d}  {:44s}  {:3d}  \n".format(" ", 
		           int(oc["docserie"]), int(oc["docnumero"]), oc["descricao"],
			   int(oc["docsitcodigo"])) 
                else:
		    line = "{}  {:0>3d}  {:0>8d}  {}  {:3d}  {:7.2f}\n".format(oc["dhrecbto"], 
		           int(oc["docserie"]), int(oc["docnumero"]), oc["docchaacesso"],
			   int(oc["docsitcodigo"]), float(oc["docvlrtotal"])) 
	        file.write(line)

    def sequencia_nao_utilizada(self, serie, sequencia_utilizada):
        """Identifica sequencia de notas nao utilizadas e retorna lista de dicionarios"""
        # python /u1/caixa/nfce.py -p listagem -n 1 300 -s 80 -ib 1

        sequencia_utilizada = sorted(sequencia_utilizada)
        inicial = sequencia_utilizada[0]
        final = sequencia_utilizada[-1] + 1
	dic = collections.Counter(sequencia_utilizada)
	notas_nao_utilizadas = [i for i in range(inicial, final) if dic[i] == 0]
 
        nova_listagem = []
        for nota in notas_nao_utilizadas:
            dnot = {}
            dnot["docsitcodigo"] = 999 
            dnot["descricao"] = "Sequencia nao utilizada"
	    dnot["docnumero"] = nota
            dnot["docserie"] = serie
	    nova_listagem.append(dnot)
        return nova_listagem

    def quantidade_contingencia_off(self):
        """Retorna quantidade de documentos em contingencia offline"""
        self.dll.rInfoEstendida_NFCe_Daruma.argtypes = [c_char_p]
        self.dll.rInfoEstendida_NFCe_Daruma.restype = c_int
        retorno = " "*10
        qtd_contingencia = self.dll.rNumDocsContingencia_NFCe_Daruma(retorno)
        return {"qdt_contingencia:": qtd_contingencia}


    def autorizar_contingencias(self):
        """Autoriza documentos em contingencia"""
        self.dll.rInfoEstendida_NFCe_Daruma.argtypes = [c_char_p]
        self.dll.rInfoEstendida_NFCe_Daruma.restype = c_int
        qtd = 0
        status = self.dll.tEnviarContingenciaOffline_NFCe_Daruma(qtd)
        # status -- retorna status da autorizacao de contingencia
	if status !=1:
	    if status == 0:
		raise Exception(" 0: Erro, nao existem vendas em Contingencia OffLine para enviar")
            elif status == 3:
		raise Exception(" 3: Nota enviada em Contingencia OnLine")
	    elif status == 4:
		raise Exception(" 4: Retorno TimeOut ao enviar.")
	    elif status == -1:
		raise Exception("-1: Erro encontrado na execucao do metodo.")
	    elif status == -2:
		raise Exception("-2: Chave Invalida.")
	    elif status == -3:
		raise Exception("-3: Falha no schema XML.")
	    elif status == -4:
		raise Exception("-4: XML fora do padrao.")
	    elif status == -5:
		raise Exception("-5: Erro generico.")
	    elif status == -8:
		raise Exception("-8: Usuario nao autorizado.")
	    elif status == -9:
		raise Exception("-9: Usuario nao licenciado.")
	    elif status == -10:
		raise Exception("-10: Documento e ambiente nao identificados.")
	    elif status == -13:
		raise Exception("-13: Tipo de documento nao identificado.")
	    elif status == -14:
		raise Exception("-14: Erro retornado pelo WebService.")
	    elif status == -52:
		raise Exception("-52: Erro ao gravar arquivo temporario.")
	    elif status == -99:
		raise Exception("-99: Parametros invalidos ou ponteiro nulo.")
	    elif status == -103:
		raise Exception("-103: Nao foram encontradas DLLs auxiliares.")
            else:
                raise Exception("Erro ao inutilizar Nota.")

    def search_gne(self):
        xfile = '/usr/local/lib/GNE_Framework.xml'
        tag = '<emppk>'
        with open(xfile, 'r') as fil:
            lines = fil.readlines()
            for line in lines:
                if tag in  line.lower():
	            m=re.compile('{0}(.*?)</'.format(tag)).search(line.lower())
                    return m.group(1)
                    #if (m.group(1) and tag == '<emppk>'):
                    #   return m.group(1)
        return ''

    def search_daruma(self):
        xfile = '/usr/local/lib/DarumaFrameWork.xml'
        tag = '<produto>'
        with open(xfile, 'r') as fil:
            lines = fil.readlines()
            for line in lines:
                if tag in  line.lower():
	            m=re.compile('{0}(.*?)</'.format(tag)).search(line.lower())
                    return m.group(1)
                    #if (m.group(1) == 'nfce' and tag == '<produto>'):
                    #   return m.group(1)
        return ''

    def retorna_xmls(self, data, status, diretorio):
        # Nao esta funcionando... metodo nao existe
        # status = self.dll.rRecuperarXML_NFCe_Daruma(data[0], data[1], status, diretorio) 
        status = self.dll.rRecuperarXML_NFCe_Daruma("11022015", "11022015", "", "/tmp/") 

    def get_config_ini(self, cfile):
        """Retorna objeto config"""
        if not cfile:
            cfile = '/usr/local/lib/gne.ini'
        config = ConfigParser()
        config.read(cfile)
        return config

    def get_section_config_ini(self, cfile, section, dict_format=False):
        """Retorna sessao do objeto config"""

        config = self.get_config_ini(cfile)
        if dict_format:
            # Retorno um dicionario
            return dict(config.items(section.upper()))
        else:
            # Retorna um objeto config
            return config.items(section.upper())

    def get_param_section_config_ini(self, cfile, section, key):
        tags = self.get_section_config_ini(cfile, section, dict_format=True)
	return {key:tags[key]}  # Ex: {"nnf":115}
            
    def set_param_section_config_ini(self, cfile, section, key, value):
        config = self.get_config_ini(cfile)
        config.set(section, key, value)
        if not cfile:
            cfile = '/usr/local/lib/gne.ini'
        with open(cfile, 'wb') as configfile:
            config.write(configfile)
        new_value = config.get(section, key)
	return {key:new_value}  # Ex: {"nnf":115}
            
    @carrega_dll
    @tratamentos
    def comando_reload(self): 
        """Parse para o comando 'reload'
        Syntax: # python nfce.py reload --loja 'XXX'	
	"""
	if args.opcao == 'gne':
            configs = self.reload_gne_framework(args.file, args.loja, args.serie, args.nnf)
            return configs
        else:
            configs = self.reload_daruma_framework(args.file)
            return configs

    #@carrega_dll
    @tratamentos
    def comando_checagem(self):
        try:
            if args.opcao.upper() == 'GNE':
                status = self.search_gne()
                return {'EMPPK':status}
            else:
                status = self.search_daruma()
                return {'PRODUTO':status}
        except:
            if args.opcao.upper() == 'GNE':
                return {'EMPPK':''}
            else:
                return {'PRODUTO':''}

    @carrega_dll
    @tratamentos
    def comando_contingencia(self):
        if args.opcao == 'qtd':
            return self.quantidade_contingencia_off()
        if args.opcao == 'ctg':
            return self.autorizar_contingencias()
            
    @carrega_dll
    @tratamentos
    def comando_inutiliza(self):  
        """Parse para o comando 'inutiliza'"""
        if args.xml:
           # para inutilizacoes atraves de xml -- fazer teste
           return 

        if not args.serie:
           parser.error("informe a opcao -s para serie")
        if not args.notas:
           parser.error("informe a opcao -n para as notas")

        self.inutiliza_por_lote(args.notas, args.serie, args.justificativa)

    @carrega_dll
    @tratamentos
    def comando_listagem(self): 
        """Parse para o comando listagem.
        *Metodo em construcao...
	"""
        if not args.data and not args.nnf and not args.chave:
           parser.error("informe a opcao -d, -n ou -c para listagem de notas.")

	if args.data:
           # Usuario nao autorizado
           self.busca_por_data(args.data[0], args.data[1])
           return

        if not args.serie:
           parser.error("informe a opcao -s para serie")

	if args.nnf:
           if args.bloco: # processa as notas em bloco por causa de erros de
		          # Segmentation fault
               listagem = self.busca_por_nnf_bloco(args.nnf[0], args.nnf[1], 
			                   args.serie, args.bloco)
               # Criar formatacao para as outras buscas
	       # Em caso de Exception: A listagem nao esta sendo atualizada.
               if args.irregular: # Inclui notas nao utilizadas
                   # python /u1/caixa/nfce.py -p listagem -n 256 270 -s 80 -ib 1
                   sequencia = [] # Lista contendo numeros de notas utilizadas
                   for nota in listagem:
                       sequencia.append(int(nota["docnumero"]))
                   serie = listagem[0]["docserie"] 
                   notas_nao_utilizadas = self.sequencia_nao_utilizada(serie, sequencia)
                   for nota in notas_nao_utilizadas:
                       listagem.append(nota) # Append das notas nao utilizadas
          
               #diretorio = None
               self.formata_listagem(listagem)
           else:
               self.busca_por_nnf(args.nnf[0], args.nnf[1], args.serie)
           return

	if args.chave:
           self.busca_por_chave(args.chave, args.serie)

    @carrega_dll
    @tratamentos
    def comando_nfce(self):  
        """Parse para o comando 'nfce'"""
        return self.template_nfce()

    @carrega_dll
    @tratamentos
    def comando_status(self):  
        """Parse para o comando 'status'"""
	if args.tipo == 'web':
            return self.status_web()

	if args.tipo == 'nfce':
            return self.consulta_status_nfce()

	if args.tipo == 'dual':
            return self.status_impressora_dual()

    @carrega_dll
    @tratamentos
    def comando_cancela(self):
        """Parse para o comando 'cancela'"""
        if args.xml:
            # Cancela utilizando XML
            self.cancela_nfce_por_xml()
            return

        if args.ultimo:
            # Cancela ultimo NFCe
            self.cancela_ultimo_nfce()
	    return

        if not args.nnf or not args.serie or not args.protocolo or not args.chave:
            parser.error("informe as opcoes -n, -s, -p e -c para cancelamento.")

        self.cancela_nfce(args.nnf, args.serie, args.chave, args.protocolo)

    @carrega_dll
    @tratamentos 
    def comando_informacao(self):
        """Parse para o comando 'info'"""
        return self.informacoes_ultima_nfce()

    @carrega_dll
    @tratamentos
    def comando_mensagem(self): 
        """Parse para o comando de mensagens."""
        return self.carrega_mensagem(args.codigo)

    @carrega_dll
    @tratamentos
    def comando_gne(self): 
        """Parse para o comando 'gne'."""
        if args.tag:
	    if args.value:
                tags = self.alterar_gne_framework(args.tag, args.value)
	    else:
                tags = self.ler_gne_framework(args.tag)
	    return {args.tag:tags[args.tag]}  # Ex: {"nnf":115}

    @carrega_dll
    @tratamentos
    def comando_daruma(self): 
        """Parse para o comando 'daruma'."""
        if args.tag:
	    if args.value:
                tags = self.alterar_daruma_framework(args.tag, args.value)
	    else:
                tags = self.ler_daruma_framework(args.tag)
	    return {args.tag:tags[args.tag]}  # Ex: {"nnf":115}

    @carrega_dll
    @tratamentos
    def comando_config(self): 
        """Parse para o comando 'gne'."""
        if args.tag:
            cfile = args.file
	    if args.opcao == 'daruma' and not cfile:
                 cfile = '/usr/local/lib/daruma.ini'
	    if args.value:
                dictags = self.set_param_section_config_ini(cfile, args.loja, args.tag, args.value)
                return dictags
                # modificar
	    else:
                dictag = self.get_param_section_config_ini(cfile, args.loja, args.tag)
                return dictag  #retorna dicicionario

    @carrega_dll
    @tratamentos
    def comando_xmls(self): 
        """Parse para o comando 'xmls'"""
        status = self.retorna_xmls(args.data, args.status, args.local)
        return 
    def teste(self):
        print 'executando....'


if __name__ == "__main__":
    nfce = NFCE()

    parser = argparse.ArgumentParser(description="Comandos para utilizacao da NFCe.")
    parser.add_argument('-p','--print', action='store_true', dest='terminal',
		       help='exibe informacao no terminal')
    subparsers = parser.add_subparsers()

    # Parse para o comando "nfce" 
    parser_foo = subparsers.add_parser('nfce', help='Emite NFCe.')
    parser_foo.add_argument('-f','--file', help="informa arquivo .ini para para configuracao")
    parser_foo.add_argument('-l','--loja', type=str, help="informa loja para para configuracao")
    parser_foo.add_argument('-s','--serie', help="informa a serie para configuracao")
    parser_foo.add_argument('-n','--nnf', help="informa o nnf para para configuracao")
    parser_foo.set_defaults(func=nfce.comando_nfce)

    # Parse para o comando "status" 
    parser_foo = subparsers.add_parser('status', help='Informa status de comunicacao.')
    parser_foo.add_argument('tipo', default='web', choices = ['web', 'nfce', 'dual'], 
                           help="informa status de comunicacao [web, nfce ou dual].")
    parser_foo.set_defaults(func=nfce.comando_status)

    # Parse para o comando "cancela"
    parser_foo = subparsers.add_parser('cancela', help='Cancela NFCe')
    parser_foo.add_argument('-u','--ultimo', action='store_true', 
		           help='cancela ultimo nfce')
    parser_foo.add_argument('-x','--xml', action='store_true', 
		           help='utiliza xml para cancelamento')
    parser_foo.add_argument('-n','--nnf', type=str, help='informa NFCe para cancelamento')
    parser_foo.add_argument('-s','--serie', type=str, 
		           help='informa serie para cancelamento')
    parser_foo.add_argument('-p','--protocolo', type=str, 
		           help='informa protocolo para cancelamento')
    parser_foo.add_argument('-c','--chave', type=str, 
		           help='informa chave de acesso para cancelamento')
    parser_foo.add_argument('-j','--justificativa', type=str, 
		           default='Numeracao nao utilizada',
		           help='justificativa para cancelamento')
    parser_foo.set_defaults(func=nfce.comando_cancela)

    # Parse para o comando "info" 
    parser_foo = subparsers.add_parser('info', help='Exibe informacoes sobre o Cupom.')
    parser_foo.set_defaults(func=nfce.comando_informacao)

    # Parse para o comando "inutiliza" 
    parser_foo = subparsers.add_parser('inutiliza', help='Inutiliza NFCe.')
    parser_foo.add_argument('-n','--notas', type=int, nargs='+',
		           help='informa notas para inutilizacao')
    parser_foo.add_argument('-s','--serie', type=int, 
		           help='informa serie para inutilizacao')
    parser_foo.add_argument('-j','--justificativa', default='Numeracao nao utilizada', 
		           help='justificativa para inutilizacao')
    parser_foo.add_argument('-x','--xml', help='utiliza xml para inutilizacao')
    parser_foo.set_defaults(func=nfce.comando_inutiliza)

    # Parse para o comando "mensagem" 
    parser_foo = subparsers.add_parser('mensagem', help='Descricao da mensagem de erro')
    parser_foo.add_argument('codigo', type=int, help="codigo da mensagem")
    parser_foo.set_defaults(func=nfce.comando_mensagem)

    # Parse para o comando "gne" (alteracao ou leitura do gne_framework.xml)
    parser_foo = subparsers.add_parser('gne', help='Faz leitura/gravacao do GNE Framework.')
    parser_foo.add_argument('-t','--tag', help="leitura de tags do GNE_Framework")
    parser_foo.add_argument('-v','--value', 
		           help="informa valor da tag para alterar GNE_Framework")
    parser_foo.set_defaults(func=nfce.comando_gne)

    # Parse para o comando "daruma" (alteracao ou leitura do DarumaFramework.xml)
    parser_foo = subparsers.add_parser('daruma', help='Faz leitura/gravacao do DarumaFramework.')
    parser_foo.add_argument('-t','--tag', help="leitura de tags do DarumaFramework")
    parser_foo.add_argument('-v','--value', 
		           help="informa valor da tag para alterar DarumaFramework")
    parser_foo.set_defaults(func=nfce.comando_daruma)

    # Parse para o comando "config" (alteracao ou leitura do config.ini/gne.ini 
    parser_foo = subparsers.add_parser('config', help='Faz leitura/gravacao do config.ini/gne.ini')
    parser_foo.add_argument('opcao', default='gne', choices=['gne','daruma'], 
		    help="reconfigura Gne_Framewoek ou DarumaFramework")
    parser_foo.add_argument('-f','--file', help="informa arquivo config.ini/gne.ini")
    parser_foo.add_argument('-l','--loja', type=str, help="informa sessao do config.ini/gne.ini")
    parser_foo.add_argument('-t','--tag', help="leitura de tags do config.ini/gne.ini")
    parser_foo.add_argument('-v','--value', 
		           help="informa valor da tag para alterar config.ini/gne.ini")
    parser_foo.set_defaults(func=nfce.comando_config)
    # apto para alterar/ler config.ini mas nao daruma.ini 

    # Parse para o comando "reload" (atualiza gne framework utilizando config.ini/gne.ini)
    parser_foo = subparsers.add_parser('reload', help='Faz gravacao do GNE Framework.')
    parser_foo.add_argument('opcao', default='daruma', choices=['gne','daruma'], 
		    help="reconfigura Gne_Framewoek ou DarumaFramework")
    parser_foo.add_argument('-f','--file', help="informa arquivo .ini para para configuracao")
    parser_foo.add_argument('-l','--loja', help="informa loja para para configuracao")
    parser_foo.add_argument('-s','--serie', help="informa a serie para configuracao")
    parser_foo.add_argument('-n','--nnf', help="informa o nnf para para configuracao")
    parser_foo.set_defaults(func=nfce.comando_reload)

    # Parse para o comando "listagem"
    parser_foo = subparsers.add_parser('listagem', help='Listagem de notas por data.')
    parser_foo.add_argument('-d','--data', nargs=2,
		           help='intervalo de data no formato DDMMYYYY')
    parser_foo.add_argument('-n','--nnf', nargs=2,
		           help='intervalo de nota')
    parser_foo.add_argument('-c','--chave', help='chave de acesso')
    parser_foo.add_argument('-s','--serie', help='serie para consulta')
    parser_foo.add_argument('-b','--bloco', help='quantidade de notas a processar por bloco')
    parser_foo.add_argument('-i','--irregular', action='store_true', help='lista notas irregulares')
    parser_foo.set_defaults(func=nfce.comando_listagem)

    # Parse para o comando "contingencia" 
    # USAGE: python /u1/caixa/nfce.py contingencia ctg
    parser_foo = subparsers.add_parser('contingencia', help='Operacoes para NNFs em Contingencia OffLine.')
    parser_foo.add_argument('opcao', default='qtd', choices=['qtd','ctg'], help="retorna total de notas em contingencia")
    parser_foo.set_defaults(func=nfce.comando_contingencia)

    # Parse para o comando "listagem"
    parser_foo = subparsers.add_parser('xmls', help='Download de XMLs por data.')
    parser_foo.add_argument('-d','--data', nargs=2,
		           help='intervalo de data no formato DDMMYYYY')
    parser_foo.add_argument('-s','--status', help='status para consulta')
    parser_foo.add_argument('-l','--local', help='diretorio para armazenamento')
    parser_foo.set_defaults(func=nfce.comando_xmls)

    # Parse para o comando "listagem"
    parser_foo = subparsers.add_parser('checagem', help='Faz checagem do XML GNE_Framework e DarumaFramework.')
    parser_foo.add_argument('opcao', default='gne', choices=['gne','daruma'], help="checagem de XML para GNE ou Daruma")
    parser_foo.set_defaults(func=nfce.comando_checagem)

    # Parse do 'sys.argv' automaticamente e em seguida chama o metodo correspondente.
    args = parser.parse_args()
    args.func()


