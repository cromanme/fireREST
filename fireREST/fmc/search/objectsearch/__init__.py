from fireREST.defaults import API_RELEASE_740
from fireREST.fmc import Resource


class ObjectSearch(Resource):
    PATH = '/search/object'
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_740
