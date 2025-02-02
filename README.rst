DANFE NFCe
----------
O DANFE NFCe ou apenas DANFE � uma Nota Fiscal Consumidor Eletronica que tem o formato de funcionamento semelhante ao da NFE - Nota Fiscal Eletr�nica.
A documenta��o � enviada diretamente � SEFAZ, onde o consumidor poder� prontamente fazer a consulta da NFCe. A proposta do DANFE tamb�m prev� o 
envio das informa��es diretamente para um dispositivo m�vel ao inv�s de sua impress�o. 

O DANFE NFCe � uma alternativa ao tradicional Cupom Fical, hoje, com homologa��o PAF.

  .. image:: nfce.png


Integra��o do ambiente ZIM com o DarumaFramework
-----------------------------------------------
A comunica��o do Zim com o DarumaFramework � feita atrav�s de um *binding* escrito em python - ``nfce.py`` - que viabiliza a utiliza��o de
metodos dispon�veis no DarumaFramework para emiss�o da NFCe. De forma semelhante, existe tamb�m o modulo ``base.py`` que � uma ponte para os m�todos 
voltados para o ECF - Emissor de Cupom Fiscal. 

Em um cen�rio mais espec�fico de integra��o, o ZIM se comunica com Python atrav�s de arquivos XMLs e este por sua vez carrega o DarumaFramework. Em seguida, 
para a emiss�o da NFCe, o DarumaFramework se comunica com o Portal Invoicy da Migrate e o web service faz a valida�ao das informa��es que foram enviadas, 
transmitindo-as para a SEFAZ. N�o havendo restri��es a SEFAZ autoriza a emiss�o do DANFE e a NFCe � emitida. 


Requisitos para emiss�o da NFCe
-------------------------------
Os requisitos abaixo s�o de acordo com o nosso ambiente de desenvolvimento. Hoje, utilizando uma solu��o NFCe proposta pela parceria entre a 
Migrate e a Daruma:

  * *Certificado digital para a empresa emitente do NFCe* - Certificados e senhas s�o obtidos junto � sefaz
  
  * *Biblioteca DarumaFramework* - O download pode ser feito a partir do site `Desenvolvedores Daruma <http://www.desenvolvedoresdaruma.com.br/home/index.php>`_ na p�gina da NFCe.
  
  * *Migrate Web Service* - Web Service respons�vel por fazer a comunica��o com a SEFAZ.
  
  * *Slackware 13.37.0 ou superior* - A Daruma pode fornecer compila��es para outras distribui��es do Linux, como o Ubuntu.
  
  * *Obten��o das chaves EmpPK e EmpCK* - As chaves s�o fornecidas pela Daruma e Migrate respectivamente. 

Instalacao
----------  
Para instalar siga conforme abaixo:

  Copie o arquivo de instalacao - de acordo com a versao desejada - para o diretorio /u1 
  # tar -xvf /u1/nfce.X.X.X.tar.gz
  # cd  /u1/nfce.X.X.X

  Edite o arquivo Makefile e altere a sigla da loja. Neste exemplo, esta a sigla 'MTO' ("python2.7 /usr/local/lib/nfce.py -p reload gne -l MTO")
  # vim Makefile
  # sudo make install


  Adicione ao arquivo /etc/rc.d/rc.local as linhas abaixo:

  if [ -x /etc/rc.d/rc.nfce ]; then
    /etc/rc.d/rc.nfce
  fi



