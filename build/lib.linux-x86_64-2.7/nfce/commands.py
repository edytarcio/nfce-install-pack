#!/usr/bin/python2.7
import sys
import argparse

# package level
from nfce import NFCE as NFCe

# This is the python script executed by shell command
def nfce():
    nfcec = NFCe()

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
    parser_foo.set_defaults(func=nfcec.comando_nfce)

    # Parse para o comando "status" 
    parser_foo = subparsers.add_parser('status', help='Informa status de comunicacao.')
    parser_foo.add_argument('tipo', default='web', choices = ['web', 'nfce', 'dual'], 
                           help="informa status de comunicacao [web, nfce ou dual].")
    parser_foo.set_defaults(func=nfcec.comando_status)

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
    parser_foo.set_defaults(func=nfcec.comando_cancela)

    # Parse para o comando "info" 
    parser_foo = subparsers.add_parser('info', help='Exibe informacoes sobre o Cupom.')
    parser_foo.set_defaults(func=nfcec.comando_informacao)

    # Parse para o comando "inutiliza" 
    parser_foo = subparsers.add_parser('inutiliza', help='Inutiliza NFCe.')
    parser_foo.add_argument('-n','--notas', type=int, nargs='+',
		           help='informa notas para inutilizacao')
    parser_foo.add_argument('-s','--serie', type=int, 
		           help='informa serie para inutilizacao')
    parser_foo.add_argument('-j','--justificativa', default='Numeracao nao utilizada', 
		           help='justificativa para inutilizacao')
    parser_foo.add_argument('-x','--xml', help='utiliza xml para inutilizacao')
    parser_foo.set_defaults(func=nfcec.comando_inutiliza)

    # Parse para o comando "mensagem" 
    parser_foo = subparsers.add_parser('mensagem', help='Descricao da mensagem de erro')
    parser_foo.add_argument('codigo', type=int, help="codigo da mensagem")
    parser_foo.set_defaults(func=nfcec.comando_mensagem)

    # Parse para o comando "gne" (alteracao ou leitura do gne_framework.xml)
    parser_foo = subparsers.add_parser('gne', help='Faz leitura/gravacao do GNE Framework.')
    parser_foo.add_argument('-t','--tag', help="leitura de tags do GNE_Framework")
    parser_foo.add_argument('-v','--value', 
		           help="informa valor da tag para alterar GNE_Framework")
    parser_foo.set_defaults(func=nfcec.comando_gne)

    # Parse para o comando "daruma" (alteracao ou leitura do DarumaFramework.xml)
    parser_foo = subparsers.add_parser('daruma', help='Faz leitura/gravacao do DarumaFramework.')
    parser_foo.add_argument('-t','--tag', help="leitura de tags do DarumaFramework")
    parser_foo.add_argument('-v','--value', 
		           help="informa valor da tag para alterar DarumaFramework")
    parser_foo.set_defaults(func=nfcec.comando_daruma)

    # Parse para o comando "config" (alteracao ou leitura do config.ini/gne.ini 
    parser_foo = subparsers.add_parser('config', help='Faz leitura/gravacao do config.ini/gne.ini')
    parser_foo.add_argument('opcao', default='gne', choices=['gne','daruma'], 
		    help="reconfigura Gne_Framewoek ou DarumaFramework")
    parser_foo.add_argument('-f','--file', help="informa arquivo config.ini/gne.ini")
    parser_foo.add_argument('-l','--loja', type=str, help="informa sessao do config.ini/gne.ini")
    parser_foo.add_argument('-t','--tag', help="leitura de tags do config.ini/gne.ini")
    parser_foo.add_argument('-v','--value', 
		           help="informa valor da tag para alterar config.ini/gne.ini")
    parser_foo.set_defaults(func=nfcec.comando_config)
    # apto para alterar/ler config.ini mas nao daruma.ini 

    # Parse para o comando "reload" (atualiza gne framework utilizando config.ini/gne.ini)
    parser_foo = subparsers.add_parser('reload', help='Faz gravacao do GNE Framework.')
    parser_foo.add_argument('opcao', default='daruma', choices=['gne','daruma'], 
		    help="reconfigura Gne_Framewoek ou DarumaFramework")
    parser_foo.add_argument('-f','--file', help="informa arquivo .ini para para configuracao")
    parser_foo.add_argument('-l','--loja', help="informa loja para para configuracao")
    parser_foo.add_argument('-s','--serie', help="informa a serie para configuracao")
    parser_foo.add_argument('-n','--nnf', help="informa o nnf para para configuracao")
    parser_foo.set_defaults(func=nfcec.comando_reload)

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
    parser_foo.set_defaults(func=nfcec.comando_listagem)

    # Parse para o comando "contingencia" 
    # USAGE: python /u1/caixa/nfce.py contingencia ctg
    parser_foo = subparsers.add_parser('contingencia', help='Operacoes para NNFs em Contingencia OffLine.')
    parser_foo.add_argument('opcao', default='qtd', choices=['qtd','ctg'], help="retorna total de notas em contingencia")
    parser_foo.set_defaults(func=nfcec.comando_contingencia)

    # Parse para o comando "listagem"
    parser_foo = subparsers.add_parser('xmls', help='Download de XMLs por data.')
    parser_foo.add_argument('-d','--data', nargs=2,
		           help='intervalo de data no formato DDMMYYYY')
    parser_foo.add_argument('-s','--status', help='status para consulta')
    parser_foo.add_argument('-l','--local', help='diretorio para armazenamento')
    parser_foo.set_defaults(func=nfcec.comando_xmls)

    # Parse para o comando "listagem"
    parser_foo = subparsers.add_parser('checagem', help='Faz checagem do XML GNE_Framework e DarumaFramework.')
    parser_foo.add_argument('opcao', default='gne', choices=['gne','daruma'], help="checagem de XML para GNE ou Daruma")
    parser_foo.set_defaults(func=nfcec.comando_checagem)

    # Parse do 'sys.argv' automaticamente e em seguida chama o metodo correspondente.
    args = parser.parse_args()
    args.func()


