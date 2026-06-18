from fireREST.defaults import API_RELEASE_770
from fireREST.fmc import ChildResource


class OutOfBandChange(ChildResource):
    """Retrieves or creates out-of-band change records for the specified device.

    **Tags:** Devices

    **Supported operations:** GET, CREATE

    **Operation IDs:**

    - `getAllOutOfBandChange` (GET (list))
    - `createOutOfBandChange` (CREATE)
    """

    CONTAINER_NAME = 'DeviceRecord'
    CONTAINER_PATH = '/devices/devicerecords/{uuid}'
    PATH = '/devices/devicerecords/{container_uuid}/operational/outofbandchanges'
    MINIMUM_VERSION_REQUIRED_CREATE = API_RELEASE_770
    MINIMUM_VERSION_REQUIRED_GET = API_RELEASE_770
    MINIMUM_VERSION_REQUIRED_UPDATE = '99.99.99'
    MINIMUM_VERSION_REQUIRED_DELETE = '99.99.99'
