all: clean build dist

pypi: clean build dist

clean:
	rm -rf build dist nfce.egg-info

build:
	python2.7 setup.py build

dist:
	python2.7 setup.py bdist
	python2.7 setup.py sdist
	python2.7 setup.py bdist_egg

sdist:
	python2.7 setup.py sdist


install:
	python2.7 setup.py install -f
	python2.7 /usr/local/lib/nfce.py -p reload daruma
	python2.7 /usr/local/lib/nfce.py -p reload gne -l AIT
	mkdir -p /usr/local/share/DarumaFramework
	mkdir -p /usr/local/share/Daruma/Contingencia
	mkdir -p /usr/local/share/Daruma/Contingencia/`hostname`
	chmod -R 777 /usr/local/share/
	chmod 755 /etc/rc.d/rc.nfce

#test:
#	python2.7 -m unittest -v test


# Get the file remotely using wget
deploy: clean 
	python2.7 setup.py sdist
	cp dist/*.gz /var/www/html/nfce/nfce.tar.gz
	cp dist/*.gz /var/www/html/nfce/.

