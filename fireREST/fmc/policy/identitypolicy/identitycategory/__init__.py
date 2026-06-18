from fireREST.defaults import API_RELEASE_1000
from fireREST.fmc import ChildResource


class IdentityCategory(ChildResource):
    """Retrieves, creates, updates, or deletes identity categories for the specified identity policy.

    **Tags:** Policy

    **Supported operations:** GET, CREATE, UPDATE, DELETE

    **Operation IDs:**

    - `getAllIdentityCategory` (GET (list))
    - `getIdentityCategory` (GET)
    - `createIdentityCategory` (CREATE)
    - `updateIdentityCategory` (UPDATE)
    - `deleteIdentityCategory` (DELETE)
    """

    CONTAINER_NAME = 'IdentityPolicy'
    CONTAINER_PATH = '/policy/identitypolicies/{uuid}'
    PATH = '/policy/identitypolicies/{container_uuid}/identitycategories/{uuid}'
    MINIMUM_VERSION_REQUIRED_CREATE = API_RELEASE_1000
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_1000
    MINIMUM_VERSION_REQUIRED_UPDATE = API_RELEASE_1000
    MINIMUM_VERSION_REQUIRED_DELETE = API_RELEASE_1000
