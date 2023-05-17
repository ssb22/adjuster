# for bsd.port.mk:
all:
install:
	$(INSTALL_SCRIPT) adjuster.py $(DESTDIR)/$(PREFIX)/bin/adjuster
	$(INSTALL_SCRIPT) annogen.py $(DESTDIR)/$(PREFIX)/bin/annogen
	$(INSTALL_SCRIPT) termlayout.py $(DESTDIR)/$(PREFIX)/bin/termlayout
INSTALL_SCRIPT ?= cp

# other:
update-readme:
	awk -- 'BEGIN {p=1} /Options for Web Adjuster/ {p=0} // {if(p) print}' < README.md > n
	python adjuster.py --markdown-options >> n
	echo >> n
	COLUMNS=32767 python annogen.py --markdown-options >> n
	echo >> n
	awk -- 'BEGIN {p=0} /^Copyright and Trademarks/ {p=1} // {if(p) print}' < README.md >> n
	mv n README.md
