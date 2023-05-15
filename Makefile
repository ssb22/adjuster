# for bsd.port.mk:
all:
install:
	$(INSTALL_SCRIPT) adjuster.py $(DESTDIR)/$(PREFIX)/bin/adjuster
	$(INSTALL_SCRIPT) annogen.py $(DESTDIR)/$(PREFIX)/bin/annogen
	$(INSTALL_SCRIPT) termlayout.py $(DESTDIR)/$(PREFIX)/bin/termlayout
INSTALL_SCRIPT ?= cp
