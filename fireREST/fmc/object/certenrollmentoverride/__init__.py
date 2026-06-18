from fireREST.defaults import API_RELEASE_770
from fireREST.fmc import ChildResource


class CertEnrollmentOverride(ChildResource):
    """Retrieves overrides for the specified certificate enrollment object.

    **Tags:** Object

    **Supported operations:** GET

    **Operation IDs:**

    - `getAllCertEnrollmentOverride` (GET (list))
    """

    CONTAINER_NAME = 'CertEnrollment'
    CONTAINER_PATH = '/object/certenrollments/{uuid}'
    PATH = '/object/certenrollments/{container_uuid}/overrides'
    MINIMUM_VERSION_REQUIRED_CREATE = '99.99.99'
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_770
    MINIMUM_VERSION_REQUIRED_UPDATE = '99.99.99'
    MINIMUM_VERSION_REQUIRED_DELETE = '99.99.99'
