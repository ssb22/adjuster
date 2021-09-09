PORTNAME=		adjuster
DISTVERSIONPREFIX=	v
DISTVERSION=		3.148-20
DISTVERSIONSUFFIX=	-g261c397
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
	${CP} {WRKSRC}/freebsd/Makefile.tmp ${WRKSRC}/Makefile # temporary line until we get the commit id of THIS commit
	for N in ${WRKSRC}/*.py ; do ${SED} -I '' -e 's|#!/usr/bin/env python$$|#!/usr/bin/env '${PYTHON_FLAVOR}'|' "$$N"; done

.include <bsd.port.mk>
