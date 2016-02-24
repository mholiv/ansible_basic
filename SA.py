try:
    import atexit
    import time
    import ssl
    # requests is required for exception handling of the ConnectionError
    import requests
    from pyVim import connect
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

import sys

path = '/JONS/clonedVM'
state = 'present'
nic_type = 'vmxnet3'
hostname = 'vc.lab.local'
username = 'administrator'
password = 'VMware1#'
datacenter = 'Lab'
network_name =  'Servers'
count = 1
module = None


def get_all_objs(content, vimtype):

    obj = {}
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for managed_object_ref in container.view:
        obj.update({managed_object_ref: managed_object_ref.name})
    
    return obj

def connect_to_api(disconnect_atexit=True):

    try:
        service_instance = connect.SmartConnect(host=hostname, user=username, pwd=password)
    except vim.fault.InvalidLogin, invalid_login:
        module.fail_json(msg=invalid_login.msg, apierror=str(invalid_login))
    except requests.ConnectionError, connection_error:
        if '[SSL: CERTIFICATE_VERIFY_FAILED]' in str(connection_error):
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            context.verify_mode = ssl.CERT_NONE
            service_instance = connect.SmartConnect(host=hostname, user=username, pwd=password, sslContext=context)
        else:
            sys.exit("Unable to connect to vCenter or ESXi API on TCP/443.", apierror=str(connection_error))

    # Disabling atexit should be used in special cases only.
    # Such as IP change of the ESXi host which removes the connection anyway.
    # Also removal significantly speeds up the return of the module
    if disconnect_atexit:
        atexit.register(connect.Disconnect, service_instance)
    return service_instance.RetrieveContent()


def get_vm_object(module, conn, path, datacenter):
    all_vms = get_all_objs(conn, [vim.VirtualMachine])
    matching_vms = []
    path_list = filter(None, vm_path.split('/'))
    name = path_list.pop()

    for vm_obj, label in all_vms.iteritems():
        if label == name:
            matching_vms.append(vm_obj)

    if len(matching_vms) > 1:
        return name, path_list

    if len(matching_vms < 1):
        sys.exit("No VM with the name %s could be found" % name)




def main():
    conn = connect_to_api()
    proper_vm = get_vm_object(module, conn, path, datacenter)
    print proper_vm


main()