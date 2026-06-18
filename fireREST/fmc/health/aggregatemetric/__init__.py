from fireREST.defaults import API_RELEASE_770
from fireREST.fmc import Resource


class AggregateMetric(Resource):
    """Retrieves aggregate health metrics across all managed devices.

    **Tags:** Health

    **Supported operations:** GET

    **Operation IDs:**

    - `getAllAggregateMetric` (GET (list))
    """

    PATH = '/health/aggregatemetrics'
    MINIMUM_VERSION_REQUIRED_CREATE = '99.99.99'
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_770
    MINIMUM_VERSION_REQUIRED_UPDATE = '99.99.99'
    MINIMUM_VERSION_REQUIRED_DELETE = '99.99.99'
