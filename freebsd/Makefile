PORTNAME=		adjuster
DISTVERSIONPREFIX=	v
DISTVERSION=		3.148-21
DISTVERSIONSUFFIX=	-gf1a405c
CATEGORIES=		www

MAINTAINER=	ssb22@cam.ac.uk
COMMENT=	Apply custom processing to Web pages

LICENSE=	APACHE20
LICENSE_FILE=	${WRKDIR}/${GH_PROJECT}-${PORTVERSION}/LICENSE

USES=	python

PYTHON_FLAVOR=	${PY_FLAVOR:C/py([2-9])/python\1./1}

RUN_DEPENDS=	${LOCALBASE}/lib/${PYTHON_FLAVOR}/site-packages/tornado:www/py-tornado@${PY_FLAVOR}

USE_GITHUB=	yes

GH_ACCOUNT=	ssb22
GH_PROJECT=	adjuster

INSTALL_TARGET=	install
PLIST_FILES=	bin/adjuster bin/annogen bin/termlayout

post-patch:
	for N in ${WRKSRC}/*.py ; do ${SED} -I '' -e 's|#!/usr/bin/env python$$|#!/usr/bin/env '${PYTHON_FLAVOR}'|' "$$N"; done

.include <bsd.port.mk>
