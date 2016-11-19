from constants import *
from exceptions import *
from neverblock_client import profile
from neverblock_client import utils

import os
import time
import subprocess
import hashlib

class ProfileLinux(profile.Profile):
    def _get_profile_hash(self):
        if self.encrypted and not self.decrypted_data:
            return

        if os.path.exists(self.path):
            return hashlib.sha512(self.get_vpn_conf()).hexdigest()

    def _get_profile_hash_path(self):
        profile_hash = self._get_profile_hash()
        if profile_hash:
            return os.path.join(os.path.abspath(os.sep),
                'etc', 'neverblock_client', profile_hash)

    def _start(self, status_callback, connect_callback, passwd, mode=START,
            retry=0):
        if self.autostart or mode == AUTOSTART:
            if not os.path.exists(self._get_profile_hash_path()):
                self.set_autostart(False)
                if mode == AUTOSTART:
                    return
            else:
                mode = AUTOSTART

        def on_exit(data, return_code):
            # Canceled
            if return_code == 126:
                self._set_status(ENDED)
            # Random error, retry
            elif return_code == -15 and not data['started'] and retry < 200:
                data['status_callback'] = None
                data['connect_callback'] = None
                time.sleep(0.05)
                self._start(status_callback, connect_callback, passwd, mode,
                    retry=retry)
            else:
                if self.status in ACTIVE_STATES:
                    self._set_status(ERROR)

        args = ['pkexec', '/usr/bin/neverblock-client-pk-%s' % mode]

        env = {'VPN_CONF': self.get_vpn_conf()}
        if passwd:
            env['VPN_PASSWORD'] = passwd

        self._run_ovpn(status_callback, connect_callback,
            args, on_exit, env=env)

    def _start_autostart(self, status_callback, connect_callback):
        self._start(status_callback, connect_callback, None, AUTOSTART)

    def _stop(self, silent, retry=0):
        retry += 1
        data = profile._connections.get(self.id)
        if data:
            process = data.get('process')
            data['process'] = None
            if process and not process.poll():
                stop_process = subprocess.Popen(['pkexec',
                    '/usr/bin/neverblock-client-pk-stop', str(process.pid)])
                stop_process.wait()

                # Canceled
                if stop_process.returncode == 126:
                    return
                # Random error, retry
                elif stop_process.returncode == -15 and retry < 200:
                    time.sleep(0.05)
                    stop_process = None
                    self._stop(silent=silent, retry=retry)
                    return
                elif stop_process.returncode != 0:
                    raise ProcessCallError(
                        'Neverblock polkit process returned error %s.' % (
                            stop_process.returncode))
        if not silent:
            self._set_status(ENDED)
        self.pid = None
        self.commit()

    def _set_profile_autostart(self, retry=0):
        retry += 1
        process = subprocess.Popen([
            'pkexec',
            '/usr/bin/neverblock-client-pk-set-autostart',
            utils.write_env({'VPN_CONF': self.get_vpn_conf()}),
        ])
        process.wait()

        # Canceled
        if process.returncode == 126:
            return False
        # Random error, retry
        elif process.returncode == -15 and retry < 200:
            time.sleep(0.05)
            process = None
            return self._set_profile_autostart(retry=retry)
        elif process.returncode != 0:
            raise ProcessCallError(
                'Neverblock polkit process returned error %s.' % (
                    process.returncode))
        return True

    def _clear_profile_autostart(self, retry=0):
        retry += 1
        process = subprocess.Popen(['pkexec',
            '/usr/bin/neverblock-client-pk-clear-autostart',
            self._get_profile_hash()])
        process.wait()

        # Canceled
        if process.returncode == 126:
            return False
        # Random error, retry
        elif process.returncode == -15 and retry < 200:
            time.sleep(0.05)
            process = None
            return self._clear_profile_autostart(retry=retry)
        elif process.returncode != 0:
            raise ProcessCallError(
                'Neverblock polkit process returned error %s.' % (
                    process.returncode))
        return True

    def _kill_pid(self, pid, retry=0):
        retry += 1
        process = subprocess.Popen(['pkexec',
            '/usr/bin/neverblock-client-pk-stop', str(pid)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()

        # Random error, retry
        if process.returncode == -15 and retry < 200:
            time.sleep(0.05)
            process = None
            self._kill_pid(pid, retry=retry)

    def commit(self):
        profile_hash_path = self._get_profile_hash_path()
        if profile_hash_path and \
                os.path.exists(profile_hash_path) != self.autostart:
            if self.autostart:
                if not self._set_profile_autostart():
                    return
            else:
                if not self._clear_profile_autostart():
                    return
        profile.Profile.commit(self)

    def delete(self):
        profile_hash_path = self._get_profile_hash_path()
        if profile_hash_path and os.path.exists(profile_hash_path):
            if not self._clear_profile_autostart():
                return
        profile.Profile.delete(self)
