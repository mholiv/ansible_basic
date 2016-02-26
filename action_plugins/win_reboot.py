# (c) 2016, Matt Davis <mdavis@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from ansible.plugins.action import ActionBase
from ansible.utils.boolean import boolean
from ansible.utils.unicode import to_unicode
from ansible.errors import AnsibleUndefinedVariable

import socket
import time
import traceback

from datetime import datetime, timedelta

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

class ActionModule(ActionBase):
    TRANSFERS_FILES = False

    DEFAULT_SHUTDOWN_TIMEOUT_SEC = 300
    DEFAULT_REBOOT_TIMEOUT_SEC = 300
    DEFAULT_CONNECT_TIMEOUT_SEC = 5
    DEFAULT_PRE_REBOOT_DELAY_SEC = 2

    def do_until_success_or_timeout(self, what, timeout_sec, fail_sleep_sec=1, what_desc=None):
        max_end_time = datetime.utcnow() + timedelta(seconds=timeout_sec)
        
        while datetime.utcnow() < max_end_time:
            try:
                what()
                if what_desc:
                    display.debug("win_reboot: %s success" % what_desc)
                return
            except:
                if what_desc:
                    display.debug("win_reboot: %s fail (expected), sleeping before retry..." % what_desc)
                time.sleep(fail_sleep_sec)

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        # TODO: allow override via task args

        shutdown_timeout_sec = self.DEFAULT_SHUTDOWN_TIMEOUT_SEC
        reboot_timeout_sec = self.DEFAULT_REBOOT_TIMEOUT_SEC
        connect_timeout_sec = self.DEFAULT_CONNECT_TIMEOUT_SEC
        pre_reboot_delay_sec = self.DEFAULT_PRE_REBOOT_DELAY_SEC

        winrm_host = self._connection._winrm_host
        winrm_port = self._connection._winrm_port

        result = super(ActionModule, self).run(tmp, task_vars)
        
        # initiate reboot
        (rc, stdout, stderr) = self._connection.exec_command("shutdown /r /t %d" % pre_reboot_delay_sec)

        if rc != 0:
            result['failed'] = True
            result['rebooted'] = False
            result['msg'] = "Shutdown command failed, error text was %s" % stderr
            return result

        def raise_if_port_open(): 
            try:
                sock = socket.create_connection((winrm_host, winrm_port), connect_timeout_sec)
                sock.close()
            except:
                return False

            raise Exception("port is open")

        self.do_until_success_or_timeout(raise_if_port_open, shutdown_timeout_sec, what_desc="port down")

        def connect_winrm_port():
            sock = socket.create_connection((winrm_host, winrm_port), connect_timeout_sec)
            sock.close()
        
        self.do_until_success_or_timeout(connect_winrm_port, reboot_timeout_sec, what_desc="port up")

        def run_test_command():
              display.vvv("attempting command")
              # sucky, connection needs a "reset" function
              self._connection.protocol = None
              self._connection.shell_id = None
              self._connection._connect()
              (rc, stdout, stderr) = self._connection.exec_command("whoami")

        # TODO: validate that a reboot actually occurred via last boot time fact

        self.do_until_success_or_timeout(run_test_command, reboot_timeout_sec, what_desc="post-reboot test command")

        result['rebooted'] = True
        result['changed'] = True

        return result

