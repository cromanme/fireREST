from fireREST.defaults import API_RELEASE_740
from fireREST.fmc import Resource


class GlobalSearch(Resource):
    PATH = '/search/global'
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_740
