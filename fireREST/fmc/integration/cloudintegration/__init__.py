from fireREST.defaults import API_RELEASE_770
from fireREST.fmc import Resource


class CloudIntegration(Resource):
    """Retrieves cloud integrations configured on the FMC.

    **Tags:** Integration

    **Supported operations:** GET

    **Operation IDs:**

    - `getAllCloudIntegration` (GET (list))
    """

    PATH = '/integration/cloudintegrations/cloudintegrations'
    MINIMUM_VERSION_REQUIRED_CREATE = '99.99.99'
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_770
    MINIMUM_VERSION_REQUIRED_UPDATE = '99.99.99'
    MINIMUM_VERSION_REQUIRED_DELETE = '99.99.99'
