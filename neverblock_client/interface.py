from neverblock_client.constants import *
from neverblock_client.exceptions import *

if PLATFORM == LINUX:
    from interface_gtk import *
else:
    raise NotImplementedError('Interface not available for platform')
