from fireREST.defaults import API_RELEASE_740
from fireREST.fmc import ChildResource


class ExtendedCommunityListOverride(ChildResource):
    CONTAINER_NAME = 'ExtendedCommunityList'
    CONTAINER_PATH = '/object/extendedcommunitylists/{uuid}'
    PATH = '/object/extendedcommunitylists/{container_uuid}/overrides/{uuid}'
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_740
