from fireREST.defaults import API_RELEASE_740
from fireREST.fmc import Resource


class PolicySearch(Resource):
    PATH = '/search/policy'
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_740
