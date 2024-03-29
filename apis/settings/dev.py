from .base import *
import re
import dj_database_url
import os


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("APIS_SECRET_KEY", "TO_CHANGE")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# REDMINE_ID = "14590"
APIS_LIST_VIEWS_ALLOWED = False
APIS_DETAIL_VIEWS_ALLOWED = False
FEATURED_COLLECTION_NAME = "FEATURED"
# MAIN_TEXT_NAME = "ÖBL Haupttext"
BIRTH_REL_NAME = "geboren in"
BIRTH_REL_ID = 64
DEATH_REL_NAME = "verstorben in"
DEATH_REL_ID = 3054
APIS_LOCATED_IN_ATTR = ["located in"]
APIS_BASE_URI = "https://paas.acdh.oeaw.ac.at/"
# APIS_OEBL_BIO_COLLECTION = "ÖBL Biographie"

LOGIN_URL = "webpage:user_login"

APIS_SKOSMOS = {
    "url": os.environ.get("APIS_SKOSMOS", "https://vocabs.acdh-dev.oeaw.ac.at"),
    "vocabs-name": os.environ.get("APIS_SKOSMOS_THESAURUS", "apisthesaurus"),
    "description": "Thesaurus of the APIS project. Used to type entities and relations.",
}

ALLOWED_HOSTS = re.sub(
    r"https?://",
    "",
    os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,paas.acdh-dev.oeaw.ac.at,paas.acdh.oeaw.ac.at,apis-mine-main.acdh-cluster-2.arz.oeaw.ac.at,mine.acdh-ch-dev.oeaw.ac.at,mine.acdh.oeaw.ac.at"),
).split(",")
# You need to allow '10.0.0.0/8' for service health checks.
ALLOWED_CIDR_NETS = ["10.0.0.0/8", "127.0.0.0/8"]

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.solr_backend.SolrEngine",
        #"URL": "https://solr.acdh-dev.oeaw.ac.at/solr/#/apis/",
        "URL": f"http://{os.environ.get('PAAS_HAYSTACK_URL', 'solr')}:8983/solr/{os.environ.get('PAAS_HAYSTACK_CORE', 'paas_solr')}",
        "ADMIN_URL": f"http://{os.environ.get('PAAS_HAYSTACK_URL', 'paassolr')}:8983/solr/admin/cores",
    }
}


APIS_PAAS_IMAGE_FOLDER = "member_images/Portraits_bis_1955"

STATICFILES_DIRS = [
    f"{BASE_DIR}/{APIS_PAAS_IMAGE_FOLDER}",
]


REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] = (
    # "rest_framework.permissions.DjangoModelPermissions",
    "rest_framework.permissions.IsAuthenticated",
    # "rest_framework.permissions.DjangoObjectPermissions",
    # use IsAuthenticated for every logged in user to have global edit rights
)
CRISPY_TEMPLATE_PACK = "acdh_mine"
CRISPY_ALLOWED_TEMPLATE_PACKS = ("bootstrap", "acdh_mine")

# HAYSTACK_DEFAULT_OPERATOR = "OR"
INSTALLED_APPS += ["haystack", "paas_theme", "leaflet", "sass_processor"]

CSP_DEFAULT_SRC = ("'self' data:","'self'", "'unsafe-inline'", 'cdnjs.cloudflare.com', 'cdn.jsdelivr.net', 'fonts.googleapis.com', 
                    'ajax.googleapis.com', 'cdn.rawgit.com', "*.acdh.oeaw.ac.at", "unpkg.com", "fonts.gstatic.com", 
                    "cdn.datatables.net", "code.highcharts.com", "*.acdh-dev.oeaw.ac.at", "*.acdh.oeaw.ac.at",
                    "openstreetmap.org", "*.openstreetmap.org", "oeaw.ac.at", "*.oeaw.ac.at", "commons.wikimedia.org", "*.wikimedia.org")
CSP_FRAME_SRC = ('sennierer.github.io',)

SECRET_KEY = (
    os.environ.get("APIS_SECRET_KEY", "TO_CHANGE")
)
DEBUG = True
DEV_VERSION = False

SPECTACULAR_SETTINGS["COMPONENT_SPLIT_REQUEST"] = True
SPECTACULAR_SETTINGS["COMPONENT_NO_READ_ONLY_REQUIRED"] = True

DATABASES = {}

DATABASES["default"] = dj_database_url.config(conn_max_age=600)

MAIN_TEXT_NAME = "ÖBL Haupttext"

LANGUAGE_CODE = "de"


SASS_ROOT = os.path.join(BASE_DIR, 'paas_theme', 'static','theme', 'css')
SASS_PROCESSOR_ROOT = SASS_ROOT

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',
]

COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)

# APIS_COMPONENTS = ['deep learning']

# APIS_BLAZEGRAPH = ('https://blazegraph.herkules.arz.oeaw.ac.at/metaphactory-play/sparql', 'metaphactory-play', 'KQCsD24treDY')


APIS_RELATIONS_FILTER_EXCLUDE += ["annotation", "annotation_set_relation"]

PAAS_STORIES = [
    {"title": "Nationalsozialismus und Entnazifizierung", "url": "ns-zeit", "description": "Description <a href='/ns-zeit'>test</a>"},
]
