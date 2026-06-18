from fireREST.defaults import API_RELEASE_770
from fireREST.fmc import Resource


class AiConfiguration(Resource):
    """Retrieves or creates AI Operations configuration.

    **Tags:** Integration

    **Supported operations:** GET, CREATE

    **Operation IDs:**

    - `getAllAiConfiguration` (GET (list))
    - `createAiConfiguration` (CREATE)
    """

    PATH = '/integration/aiops/configure'
    MINIMUM_VERSION_REQUIRED_CREATE = API_RELEASE_770
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_770
    MINIMUM_VERSION_REQUIRED_UPDATE = '99.99.99'
    MINIMUM_VERSION_REQUIRED_DELETE = '99.99.99'
