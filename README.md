C$&4 Custom Code
================

Here is the custom code developed as part of the engagement.


## Instructions 

To use either the VMWare or Windows stuff, you'll want to place this at the root level of your Ansible project directory (be careful not to include the `.git` folder).


### VMWare Modules

There are currently 2 modules, one more on the way:

1. `vmware_clone_to_folder`

2. `vmware_nic`

3. `vmware_disk` (WIP)

For documentation you can see the source code of each module under the `DOCUMENTATION` string or alternatively, from within this top level directory you can do:

`ansible-doc -M ./library $MODULE_NAME`

and it will give you a `less` like format for reading the documentation.


### Windows Reboot

This code stack will work up through the release of Ansible 2.1 (target release of late April). Once 2.1 is released you'll want to use the native features for rebooting Windows.

_USAGE_

```yaml
## run_this.yml 
- hosts: win
  tasks:
  - include: updatereboot.yml
    with_sequence: start=1 end=5

## updatereboot.yml
- name: win_update
  win_updates:
  register: wu_result
  when: wu_result | default({"changed":"true"}) | changed

- name: reboot
  win_reboot:
  when: wu_result.reboot_required | default(False)
```

