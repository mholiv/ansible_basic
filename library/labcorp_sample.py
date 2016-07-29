#!/usr/bin/python

# MODULE LOGIC
# Step 1: Get your vars
# Step 2: Check if work needs to get done
# Step 3: If no changed needs to be done return no change
# Step 4: If work does need to be done return change
# Step 5: If errors return fail.

def check_if_change_needs_to_happen(params):
    # In real life we would do python stuff to check if work needs to be done here.
    return True


def do_the_work(params):
    # We would actually do the work here

    version = params['version']

    # Simulated change
    if int(version[0]) > 2:
        status_change = 'Way too high of a version'
        info = None

    # Simulated not change error
    else:
        status_change = None
        info = "Could not change"

    return {'status_change':status_change, 'info': info}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            version=dict(required=True, type='str'),
            state=dict(required=True, type='str', choices=['present', 'absent']),
            do_stuff=dict(default=True,required=False,type='bool')
        )
    )

    params = module.params

    #Emergency got to catch them all
    try:
        #We check if work needs to be done
        does_work_need_to_be_done = check_if_change_needs_to_happen(params)

        #If word does in fact need to be done...
        if does_work_need_to_be_done:

            #Actually doing the changes
            do_the_work_results = do_the_work(params)

            # If there we can do a status_changes...
            if do_the_work_results['status_change'] is not None:
                module.exit_json(changed=True,
                                 msg='Version is good',
                                 info=do_the_work_results['info'])

            # If can not do a status changes
            else:
                module.fail_json(msg='Could not change',
                                 error=do_the_work_results['info'])


        # If we dont need to do work...
        else:
            module.exit_json(msg='All is good. Did not do anything.')

    except Exception:
        module.fail_json(msg='I really messed up.',
                         error=Exception)



# this is magic, see ansible/lib/ansible/module_utils/basic.py
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()