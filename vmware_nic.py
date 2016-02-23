#!/bin/python

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
                vm_name=dict(required=True, type='str'),
                state=dict(required=True, choices=['present', 'absent'], type='str'),
                )
        )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    vm_name = module.params.get('vm_name')
    state = module.params.get('state')
    hostname = module.params.get('hostname')
    username = module.params.get('username')
    password = module.params.get('password')
    module.params['validate_certs'] = False

    conn = connect_to_api(module)

    module.exit_json(changed=False)



from ansible.module_utils.basic import *
from ansible.module_utils.vmware import *

if __name__ == '__main__':
    main()