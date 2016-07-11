#!/usr/bin/python

DOCUMENTATION = '''
---
module: vmware_clone_to_folder
short_description: Clone a template or vm and place it in a given location through VMware vSphere.
description:
     - Clones a given VM or template and places it in a specified location
options:
  resource_pool:
    description:
      - The name of the resource_pool to create the VM in.
    required: false
    default: Resources
  template_location:
    description:
      - The file path to the template.
    required: True
  destination:
    description:
      - The file path to place the VM.
    required: True
extends_documentation_fragment: vmware.documentation

notes:
  - This module should run from a system that can access vSphere directly.
    Either by using local_action, or using delegate_to. This module will not
    be able to find nor place VMs or templates in the root folder.
author: "Caitlin Campbell <cacampbe@redhat.com>"
requirements:
  - "python >= 2.6"
  - pyVmomi
'''


EXAMPLES = '''
# Clone an existing template or VM into a specified folder.
- vvmware_clone_to_folder:
    hostname: vcenter.mydomain.local
    username: myuser
    password: mypass
    template_location: /templates/clienta/template436
    destination: /clients/clienta/clientaVM
'''

def main():

    argument_spec = argument_spec()

    argument_spec.update(
        dict(
            nginx_version=dict(required=True, type='str'),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)
    nginx_version = module.params['nginx_version']

    
    
    # DO you stuff
    try:
        changed_status, myThing = doStuff(nginx_version)
    except Exception as e:
        module.fail_json(msg='Something Went very very wrong Error: %s.' % str(e))
    
    if changed_status is True:
        module.exit_json(changed=True, thing=myThing)
    else:
        module.exit_json(changed=False, thing=myThing)
        
        
def doStuff(nginx_version):
    
    nginx_status = check_if_nginx_installed(nginx_version)
    
    if nginx_status is True:
        return False, nginx_version
    else:
        # Do stuff to install nginx
        return True, nginx_version
        
def check_if_nginx_installed():
    return True, '1.9.3'
        

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.vmware import *
if __name__ == '__main__':
    main()