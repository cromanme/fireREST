from fireREST.defaults import API_RELEASE_770
from fireREST.fmc import Resource


class TsdbUploadStatus(Resource):
    """Retrieves the status of TSDB upload operations.

    **Tags:** Integration

    **Supported operations:** GET

    **Operation IDs:**

    - `getAllTsdbUploadStatus` (GET (list))
    """

    PATH = '/integration/aiops/tsdbupload/status'
    MINIMUM_VERSION_REQUIRED_CREATE = '99.99.99'
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_770
    MINIMUM_VERSION_REQUIRED_UPDATE = '99.99.99'
    MINIMUM_VERSION_REQUIRED_DELETE = '99.99.99'
