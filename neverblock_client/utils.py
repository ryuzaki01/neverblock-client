from neverblock_client.constants import *
from neverblock_client.exceptions import *

if PLATFORM != SHELL:
    from neverblock_client import interface

import json
import time
import uuid
import hmac
import hashlib
import base64
import requests
import subprocess
import re

_disk_device_match = re.compile(r'(\/dev\/[a-z0-9]*)')
_disk_size_match = re.compile(r'([0-9]*) bytes')

def check_output(*args, **kwargs):
    if 'stdout' in kwargs or 'stderr' in kwargs:
        raise ValueError('Output arguments not allowed, it will be overridden')

    process = subprocess.Popen(
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,  *args, **kwargs)

    stdoutdata, stderrdata = process.communicate()
    return_code = process.poll()

    if return_code:
        raise subprocess.CalledProcessError(
            return_code, kwargs.get('args', args[0]), output=stdoutdata)

    return stdoutdata

def check_call_silent(*args, **kwargs):
    if 'stdout' in kwargs or 'stderr' in kwargs:
        raise ValueError('Output arguments not allowed, it will be overridden')

    process = subprocess.Popen(stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        *args, **kwargs)
    return_code = process.wait()

    if return_code:
        cmd = kwargs.get('args', args[0])
        raise subprocess.CalledProcessError(return_code, cmd)

def auth_request(method, host, path, token, secret,
        json_data=None, timeout=None):
    if json_data:
        headers = {'Content-Type', 'application/json'}
        data = json.dumps(json_data)
    else:
        headers = None
        data = None
    auth_timestamp = str(int(time.time()))
    auth_nonce = uuid.uuid4().hex
    auth_string = '&'.join([token, auth_timestamp, auth_nonce,
        method.upper(), path] + ([data] if data else []))

    auth_signature = base64.b64encode(hmac.new(
        secret.encode(), auth_string, hashlib.sha512).digest())
    auth_headers = {
        'Auth-Token': token,
        'Auth-Timestamp': auth_timestamp,
        'Auth-Nonce': auth_nonce,
        'Auth-Signature': auth_signature,
    }
    if headers:
        auth_headers.update(headers)
    return getattr(requests, method.lower())(
        host + path,
        headers=auth_headers,
        data=data,
        timeout=timeout,
        verify=False,
    )

def get_logo():
    if PLATFORM == LINUX:
        logo_path = interface.lookup_icon('neverblock_client')
        if logo_path:
            return logo_path
    return LOGO_DEFAULT_PATH

def get_connected_logo():
    if PLATFORM == LINUX:
        logo_path = interface.lookup_icon('neverblock_client_connected')
        if logo_path:
            return logo_path
    return CONNECTED_LOGO_DEFAULT_PATH

def get_disconnected_logo():
    if PLATFORM == LINUX:
        logo_path = interface.lookup_icon('neverblock_client_disconnected')
        if logo_path:
            return logo_path
    return DISCONNECTED_LOGO_DEFAULT_PATH

def get_usb_drives():
    disks_output = check_output(['fdisk', '-l'])
    disks_devices = {}
    disks = {}

    for disks_line in disks_output.splitlines():
        disks_line = disks_line.lower()
        if not disks_line.startswith('disk'):
            continue

        matches = _disk_device_match.findall(disks_line)
        if not matches:
            continue
        disk_device = matches[0]

        matches = _disk_size_match.findall(disks_line)
        if not matches:
            continue

        try:
            disk_size = int(matches[0])
        except ValueError:
            continue

        if disk_size < 1000000000:
            disk_size = '%s MB' % int(round(disk_size / 1000000.))
        else:
            disk_size = int(round(disk_size / 1000000000.))
            if disk_size == 7:
                disk_size = 8
            elif disk_size == 15:
                disk_size = 16
            elif disk_size == 31:
                disk_size = 32
            elif disk_size == 63:
                disk_size = 64
            elif disk_size == 127:
                disk_size = 128
            elif disk_size == 255:
                disk_size = 256
            elif disk_size == 511:
                disk_size = 512
            disk_size = '%s GB' % disk_size

        disks_devices[disk_device] = disk_size

    for disk_device, disk_size in disks_devices.items():
        vendor = 'USB Device'
        model = ''
        bus = ''

        try:
            info_output = check_output([
                'udevadm', 'info', '--query=all', '-n', disk_device])
        except subprocess.CalledProcessError:
            continue

        for info_line in info_output.splitlines():
            info_val = info_line.split('=', 1)[-1]

            if 'ID_BUS=' in info_line:
                bus = info_val.strip()
            elif 'ID_MODEL=' in info_line:
                model = info_val.strip().replace('_', ' ')
            elif 'ID_VENDOR=' in info_line:
                vendor = info_val.strip().replace('_', ' ')

        vendor = vendor.title()
        model = model.title()

        if bus.lower() != 'usb':
            continue

        disks[disk_device] = vendor + (' ' + model if model else '') + \
            ' (%s)' % disk_size

    return disks

def get_disk_size(disk_device):
    disks_output = check_output(['fdisk', '-l'])

    for disks_line in disks_output.splitlines():
        disks_line = disks_line.lower()
        if not disks_line.startswith('disk'):
            continue

        matches = _disk_device_match.findall(disks_line)
        if not matches:
            continue

        if matches[0] != disk_device:
            continue

        matches = _disk_size_match.findall(disks_line)
        if not matches:
            continue

        try:
            disk_size = int(matches[0])
        except ValueError:
            continue

        return disk_size

def get_disk_type(disk_device):
    info_output = check_output([
        'udevadm', 'info', '--query=all', '-n', disk_device])

    for info_line in info_output.splitlines():
        if 'ID_BUS=' in info_line:
            return info_line.split('=', 1)[-1].strip().lower()

def format_disk(disk_device):
    disk_size = get_disk_size(disk_device)
    disk_type = get_disk_type(disk_device)

    if not disk_size or disk_type != 'usb':
        raise TypeError('Invalid disk device')

    process = subprocess.Popen(['fdisk', disk_device],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if disk_size < 64000000:
        process.communicate('o\nn\np\n\n\n\n\nw\n')
    else:
        process.communicate('o\nn\np\n\n\n+15625K\n\nw\n')

    process.wait()

    check_call_silent(['mkfs.fat', '-n', 'PRITUNL', disk_device + '1'])

def get_disk_profile(profile_id, timeout=3):
    start = time.time()

    while True:
        if os.path.exists(USB_DISK_PATH):
            break
        time.sleep(0.1)
        if time.time() - start >= timeout:
            return {}

    disk_size = get_disk_size(USB_DISK_PATH)
    disk_type = get_disk_type(USB_DISK_PATH)

    if disk_size > 128000000 or disk_type != 'usb':
        raise TypeError('Invalid disk device')

    mount_dir = os.path.join(TMP_DIR, uuid.uuid4().hex)
    os.makedirs(mount_dir)

    try:
        check_call_silent(['umount', USB_DISK_PATH])
    except subprocess.CalledProcessError:
        pass

    try:
        check_call_silent([
            'mount',
            '-o', 'umask=0277,dmask=0277,fmask=0377',
            USB_DISK_PATH,
            mount_dir,
        ])

        for file_name in os.listdir(mount_dir):
            if not file_name.endswith('.json') or \
                    profile_id != file_name.split('.')[0]:
                continue

            file_path = os.path.join(mount_dir, file_name)
            try:
                with open(file_path, 'r') as profile_file:
                    return json.loads(profile_file.read())
            except:
                pass
    finally:
        try:
            check_call_silent(['umount', USB_DISK_PATH])
        except subprocess.CalledProcessError:
            pass
        try:
            os.removedirs(mount_dir)
        except:
            pass

    return {}

def set_disk_profile(profile_id, profile_iv, profile_key, timeout=30):
    start = time.time()

    while True:
        if os.path.exists(USB_DISK_PATH):
            break
        time.sleep(0.1)
        if time.time() - start >= timeout:
            return False

    mount_dir = os.path.join(TMP_DIR, uuid.uuid4().hex)
    os.makedirs(mount_dir)

    try:
        check_call_silent(['umount', USB_DISK_PATH])
    except subprocess.CalledProcessError:
        pass

    try:
        check_call_silent([
            'mount',
            '-o', 'umask=0077,dmask=0077,fmask=0177',
            USB_DISK_PATH,
            mount_dir,
        ])

        file_path = os.path.join(mount_dir, profile_id + '.json')
        with open(file_path, 'w') as profile_file:
            profile_file.write(json.dumps({
                'iv': profile_iv,
                'key': profile_key,
            }))
    finally:
        try:
            check_call_silent(['umount', USB_DISK_PATH])
        except subprocess.CalledProcessError:
            pass
        try:
            os.removedirs(mount_dir)
        except:
            pass

    return True

def write_env(env_data):
    env_path = os.path.join(TMP_DIR, uuid.uuid4().hex)
    with open(env_path, 'w') as env_file:
        os.chmod(env_path, 0200)
        env_file.write(json.dumps(env_data))
    return '--env=' + env_path

def generate_secret():
    return re.sub(r'[\W_]+', '', base64.b64encode(os.urandom(64)))[:32]
