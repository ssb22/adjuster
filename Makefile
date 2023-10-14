# for bsd.port.mk:
all:
install:
	$(INSTALL_SCRIPT) adjuster.py $(DESTDIR)/$(PREFIX)/bin/adjuster
	$(INSTALL_SCRIPT) annogen.py $(DESTDIR)/$(PREFIX)/bin/annogen
	$(INSTALL_SCRIPT) termlayout.py $(DESTDIR)/$(PREFIX)/bin/termlayout
	$(INSTALL_MAN) man/adjuster.1 $(DESTDIR)/$(PREFIX)/man/man1/
	$(INSTALL_MAN) man/annogen.1 $(DESTDIR)/$(PREFIX)/man/man1/
	$(INSTALL_MAN) man/termlayout.1 $(DESTDIR)/$(PREFIX)/man/man1/
INSTALL_SCRIPT ?= cp
INSTALL_MAN ?= cp
DESTDIR ?= /usr
PREFIX ?= local

# other:
update-readme:
	awk -- 'BEGIN {p=1} /Options for Web Adjuster/ {p=0} // {if(p) print}' < README.md > n
	python adjuster.py --markdown-options >> n
	echo >> n
	COLUMNS=32767 python annogen.py --markdown-options >> n
	echo >> n
	awk -- 'BEGIN {p=0} /^Copyright and Trademarks/ {p=1} // {if(p) print}' < README.md >> n
	mv n README.md
	(echo "# adjuster";echo) > adjuster.1.ronn
	awk -- 'BEGIN {p=0} /^Web Adjuster is a/ {p=1} /^Installation/ {p=0} // {if(p) print}' < README.md | sed -e 's/“/"/g' -e 's/”/"/g' -e "s/’/'/g" >> adjuster.1.ronn
	python adjuster.py --markdown-options | sed -e 's/[|]/\\|/g' >> adjuster.1.ronn
	(echo "# annogen";echo) > annogen.1.ronn
	awk -- 'BEGIN {p=0} /^Annotator Generator is a/ {p=1} /^Legal considerations/ {p=0} // {if(p) print}' < README.md | sed -e 's/“/"/g' -e 's/”/"/g' -e "s/’/'/g" >> annogen.1.ronn
	python annogen.py --markdown-options >> annogen.1.ronn
	echo >> annogen.1.ronn
	awk -- 'BEGIN {p=0} /^Legal considerations/ {p=1} /^TermLayout/ {p=0} // {if(p) print}' < README.md | sed -e 's/“/"/g' -e 's/”/"/g' -e "s/’/'/g" >> annogen.1.ronn
	(echo "# termlayout";echo) > termlayout.1.ronn
	awk -- 'BEGIN {p=0} /^TermLayout/ {p=1} /^Options for Web Adjuster/ {p=0} // {if(p) print}' < README.md | sed -e 's/“/"/g' -e 's/”/"/g' -e "s/’/'/g" >> termlayout.1.ronn
	ronn -r --organization="Silas S. Brown" *.ronn
	rm adjuster.1.ronn annogen.1.ronn termlayout.1.ronn
	mv *.1 man/
