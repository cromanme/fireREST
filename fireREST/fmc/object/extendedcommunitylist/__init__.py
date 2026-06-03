from fireREST.defaults import API_RELEASE_740
from fireREST.fmc import Connection, Resource
from fireREST.fmc.object.extendedcommunitylist.override import ExtendedCommunityListOverride


class ExtendedCommunityList(Resource):
    PATH = '/object/extendedcommunitylists/{uuid}'
    MINIMUM_VERSION_REQUIRED_CREATE = API_RELEASE_740
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_740
    MINIMUM_VERSION_REQUIRED_UPDATE = API_RELEASE_740
    MINIMUM_VERSION_REQUIRED_DELETE = API_RELEASE_740

    def __init__(self, conn: Connection):
        super().__init__(conn)

        self.override = ExtendedCommunityListOverride(conn)
