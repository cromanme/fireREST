from fireREST.defaults import API_RELEASE_720
from fireREST.fmc import Resource


class S2sVpnSummary(Resource):
    PATH = '/policy/s2svpnsummaries'
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_720
