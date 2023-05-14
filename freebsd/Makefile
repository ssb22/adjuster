PORTNAME=		adjuster
DISTVERSIONPREFIX=	v
DISTVERSION=		3.23-21
DISTVERSIONSUFFIX=	-g0d47f0d
CATEGORIES=		www

MAINTAINER=	ssb22@cam.ac.uk
COMMENT=	Apply custom processing to Web pages
WWW=	http://ssb22.user.srcf.net/adjuster/

LICENSE=	APACHE20
LICENSE_FILE=	${WRKSRC}/LICENSE

USES=	python shebangfix

PYTHON_FLAVOR=	${PY_FLAVOR:C/py([2-9])/python\1./1}

RUN_DEPENDS=	${LOCALBASE}/lib/${PYTHON_FLAVOR}/site-packages/tornado:www/py-tornado@${PY_FLAVOR}

USE_GITHUB=	yes

GH_ACCOUNT=	ssb22

PLIST_FILES=	bin/adjuster bin/annogen bin/termlayout

.include <bsd.port.mk>
