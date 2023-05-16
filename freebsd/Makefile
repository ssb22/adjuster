PORTNAME=		adjuster
DISTVERSIONPREFIX=	v
DISTVERSION=		3.23-23
DISTVERSIONSUFFIX=	-g7c06b0f
CATEGORIES=		www

MAINTAINER=	ssb22@cam.ac.uk
COMMENT=	Apply custom processing to Web pages
WWW=	http://ssb22.user.srcf.net/adjuster/

LICENSE=	APACHE20
LICENSE_FILE=	${WRKSRC}/LICENSE

USES=	python shebangfix
SHEBANG_FILES=	*.py

RUN_DEPENDS=	${PYTHON_SITELIBDIR}/tornado:www/py-tornado@${PY_FLAVOR}

USE_GITHUB=	yes

GH_ACCOUNT=	ssb22

PLIST_FILES=	bin/adjuster bin/annogen bin/termlayout

.include <bsd.port.mk>
