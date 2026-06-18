from fireREST.defaults import API_RELEASE_770
from fireREST.fmc import Resource


class ManageCertificate(Resource):
    """Initiates certificate management operations on devices.

    **Tags:** Devices

    **Supported operations:** CREATE

    **Operation IDs:**

    - `createManageCertificate` (CREATE)
    """

    PATH = '/devices/operational/managecertificates'
    MINIMUM_VERSION_REQUIRED_CREATE = API_RELEASE_770
    MINIMUM_VERSION_REQUIRED_GET = '99.99.99'
    MINIMUM_VERSION_REQUIRED_UPDATE = '99.99.99'
    MINIMUM_VERSION_REQUIRED_DELETE = '99.99.99'
