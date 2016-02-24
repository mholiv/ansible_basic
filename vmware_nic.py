#!/bin/python

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

def get_vm_object(module, conn, path, datacenter):
    all_vms = get_all_objs(conn, [vim.VirtualMachine])
    matching_vms = []

    for vm_obj, label in all_vms.iteritems():
        if label == name:
            matching_vms.append(vm_obj)

    if len(matching_vms) > 1:
        path_list = filter(None, vm_path.split('/'))
        name = path_list.pop()

    if len(matching_vms < 1):
        module.fail_json(msg="No VM with the name %s could be found" % name)

def get_matching_nics():
    pass

def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
                vm_path=dict(required=True, type='str'),
                state=dict(required=True, choices=['create', 'absent', 'update'], type='str'),
                type=dict(required=True, type='str'),
                network_name=dict(required=True, type='str'),
                datacenter=dict(required=True, type='str'),
                count=dict(required=False, type='int', default=1))
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

    module.exit_json(changed=False, vals=str(conn))



from ansible.module_utils.basic import *
from ansible.module_utils.vmware import *

if __name__ == '__main__':
    main()