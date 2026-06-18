from fireREST.defaults import API_RELEASE_1000
from fireREST.fmc import ChildResource


class IdentityRule(ChildResource):
    """Retrieves, creates, updates, or deletes identity rules for the specified identity policy.

    **Tags:** Policy

    **Supported operations:** GET, CREATE, UPDATE, DELETE

    **Operation IDs:**

    - `getAllIdentityRule` (GET (list))
    - `getIdentityRule` (GET)
    - `createIdentityRule` (CREATE)
    - `updateIdentityRule` (UPDATE)
    - `deleteIdentityRule` (DELETE)
    """

    CONTAINER_NAME = 'IdentityPolicy'
    CONTAINER_PATH = '/policy/identitypolicies/{uuid}'
    PATH = '/policy/identitypolicies/{container_uuid}/identityrules/{uuid}'
    MINIMUM_VERSION_REQUIRED_CREATE = API_RELEASE_1000
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_1000
    MINIMUM_VERSION_REQUIRED_UPDATE = API_RELEASE_1000
    MINIMUM_VERSION_REQUIRED_DELETE = API_RELEASE_1000
