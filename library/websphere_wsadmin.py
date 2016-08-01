#!/usr/bin/python

import subprocess

def main():

    # Read arguments
    module = AnsibleModule(
        argument_spec = dict(
            host = dict(default='localhost', required=False),
            port = dict(default='8879', required=False),
            username = dict(required=False, type='str'),
            password = dict(required=False, type='str'),
            script = dict(required=True, type='str'),
            wasdir = dict(required=True, type='str'),
            cluster = dict(required=True, type='str')
        )
    )

    host = module.params['host']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']
    script = module.params['script']
    wasdir = module.params['wasdir']
    cluster = module.params['cluster']

    # Run wsadmin command server

    child = subprocess.Popen([wasdir+"/bin/wsadmin.sh -lang jython -conntype SOAP -host %s -port %s -username %s -password %s -f %s %s "% (host, port, username, password, script, cluster)], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_value, stderr_value = child.communicate()
    if child.returncode != 0:
        module.fail_json(msg="Failed executing wsadmin script: " + script, stdout=stdout_value, stderr=stderr_value)

    module.exit_json(changed=True, msg="Script executed successfully: " + script, stdout=stdout_value)


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()