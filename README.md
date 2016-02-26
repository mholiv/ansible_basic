# VMware Modules for Ansible

Included are some useful VMWare Utilities 

## vmware_clone_to_folder

An ansible module that enables to cloning of arbitrarily located templates and vms to selected folders.

Requires pyVmomi

This module will not work with templates and vms located directly in the root folder.

##vmware_add_hdd

An ansible module that enables adding drives to an iscsi interface on an arbitrary VM.

Requires pyVmomi
