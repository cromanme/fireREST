from fireREST.defaults import API_RELEASE_770
from fireREST.fmc import Resource


class Certificate(Resource):
    """Retrieves certificates across all managed devices.

    **Tags:** Devices

    **Supported operations:** GET

    **Operation IDs:**

    - `getAllCertificate` (GET (list))
    """

    PATH = '/devices/certificates'
    MINIMUM_VERSION_REQUIRED_CREATE = '99.99.99'
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_770
    MINIMUM_VERSION_REQUIRED_UPDATE = '99.99.99'
    MINIMUM_VERSION_REQUIRED_DELETE = '99.99.99'
