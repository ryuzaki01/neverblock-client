import os
import uuid
import sys

APP_NAME = 'neverblock_client'
APP_NAME_FORMATED = 'Neverblock Client'

LINUX = 'linux'
SHELL = 'shell'
WIN = 'win'
OSX = 'osx'

if sys.platform.startswith('linux'):
    PLATFORM = LINUX
else:
    raise ValueError('Unknown platform %s' % sys.platform)

CONF_DIR = os.path.expanduser(os.path.join('~', '.config', APP_NAME))
LOG_PATH = os.path.join(CONF_DIR, '%s.log' % APP_NAME)
PROFILES_DIR = os.path.join(CONF_DIR, 'profiles')
SHARE_DIR = os.path.join(os.path.abspath(os.sep), 'usr', 'share', APP_NAME)
LINUX_ETC_DIR = os.path.join(os.path.abspath(os.sep), 'etc', APP_NAME)
TMP_DIR = os.path.join(os.path.abspath(os.sep), 'tmp')
SOCK_PATH = os.path.join(TMP_DIR, 'neverblock_%s.sock' % uuid.uuid4().hex)
USB_DISK_PATH = '/dev/disk/by-label/PRITUNL'
CONNECT_TIMEOUT = 30
OVPN_START_TIMEOUT = 5
OVPN_STOP_TIMEOUT = 5
SYNC_CONF_TIMEOUT = 5
IMPORT_TIMEOUT = 10
DAEMON_SOCKET_TIMEOUT = 10
LOG_DEBUG_TYPES = set()

LOGO_DEFAULT_PATH = None
CONNECTED_LOGO_DEFAULT_PATH = None
DISCONNECTED_LOGO_DEFAULT_PATH = None
IMG_ROOTS = [
    SHARE_DIR,
    os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'img'),
]

_LOGO_NAME = 'logo.png'
if PLATFORM == LINUX:
    _CONNECTED_LOGO_NAME = 'logo_connected_light.svg'
    _DISCONNECTED_LOGO_NAME = 'logo_disconnected_light.svg'
elif PLATFORM == SHELL:
    _CONNECTED_LOGO_NAME = None
    _DISCONNECTED_LOGO_NAME = None
else:
    raise NotImplementedError('Platform %s not supported' % PLATFORM)

for img_root in IMG_ROOTS:
    img_path = os.path.join(img_root, 'logo.png')
    if os.path.exists(img_path) and not LOGO_DEFAULT_PATH:
        LOGO_DEFAULT_PATH = img_path
    img_path = os.path.join(img_root, _CONNECTED_LOGO_NAME)
    if os.path.exists(img_path) and not CONNECTED_LOGO_DEFAULT_PATH:
        CONNECTED_LOGO_DEFAULT_PATH = img_path
    img_path = os.path.join(img_root, _DISCONNECTED_LOGO_NAME)
    if os.path.exists(img_path) and not DISCONNECTED_LOGO_DEFAULT_PATH:
        DISCONNECTED_LOGO_DEFAULT_PATH = img_path

CONNECTING = 'connecting'
RECONNECTING = 'reconnecting'
CONNECTED = 'connected'
ENDED = 'ended'
ERROR = 'error'
AUTH_ERROR = 'auth_error'
TIMEOUT_ERROR = 'timeout_error'
ACTIVE_STATES = set([CONNECTING, RECONNECTING, CONNECTED])
INACTIVE_STATES = set([ENDED, ERROR, AUTH_ERROR, TIMEOUT_ERROR])
ERROR_STATES = set([ERROR, AUTH_ERROR, TIMEOUT_ERROR])

START = 'start'
AUTOSTART = 'autostart'

BUTTONS_OK = 'buttons_ok'
BUTTONS_CANCEL = 'buttons_cancel'
BUTTONS_OK_CANCEL = 'buttons_ok_cancel'

MESSAGE_INFO = 'message_info'
MESSAGE_QUESTION = 'message_question'
MESSAGE_ERROR = 'message_error'
MESSAGE_LOADING = 'message_loading'

def set_shell():
    global PLATFORM
    PLATFORM = SHELL
    global CONF_DIR
    CONF_DIR = os.path.join(os.path.abspath(os.sep), 'etc', APP_NAME)
    global LOG_PATH
    LOG_PATH = os.path.join(os.path.abspath(os.sep), 'var', 'log',
        '%s.log' % APP_NAME)
    global LOGO_DEFAULT_PATH
    LOGO_DEFAULT_PATH = None
    global CONNECTED_LOGO_DEFAULT_PATH
    CONNECTED_LOGO_DEFAULT_PATH = None
    global DISCONNECTED_LOGO_DEFAULT_PATH
    DISCONNECTED_LOGO_DEFAULT_PATH = None
