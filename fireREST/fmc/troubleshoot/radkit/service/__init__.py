from fireREST.defaults import API_RELEASE_770
from fireREST.fmc import Resource


class RadKitService(Resource):
    """Retrieves or creates RADKit service entries.

    **Tags:** Troubleshoot

    **Supported operations:** GET, CREATE

    **Operation IDs:**

    - `getAllRadKitService` (GET (list))
    - `getRadKitService` (GET)
    - `createRadKitService` (CREATE)
    """

    NAMESPACE = 'troubleshoot'
    PATH = '/radkit/services/{uuid}'
    MINIMUM_VERSION_REQUIRED_CREATE = API_RELEASE_770
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_770
    MINIMUM_VERSION_REQUIRED_UPDATE = '99.99.99'
    MINIMUM_VERSION_REQUIRED_DELETE = '99.99.99'
