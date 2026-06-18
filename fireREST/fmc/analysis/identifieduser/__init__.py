from fireREST.defaults import API_RELEASE_760
from fireREST.fmc import Resource


class IdentifiedUser(Resource):
    """Retrieves or deletes all identified users.

    **Tags:** Analysis

    **Supported operations:** GET, DELETE

    **Operation IDs:**

    - `getAllIdentifiedUser` (GET (list))
    - `deleteIdentifiedUsers` (DELETE)
    """

    PATH = '/analysis/identifiedusers'
    MINIMUM_VERSION_REQUIRED_CREATE = '99.99.99'
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_760
    MINIMUM_VERSION_REQUIRED_UPDATE = '99.99.99'
    MINIMUM_VERSION_REQUIRED_DELETE = API_RELEASE_760
