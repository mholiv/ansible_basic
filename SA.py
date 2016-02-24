try:
    import atexit
    import time
    import ssl
    from collections import Mapping, Set, Sequence 
    # requests is required for exception handling of the ConnectionError
    import requests
    from pyVim import connect
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

import sys

path = '/JONS/megladon/DONT_MESS_WITH-1'
state = 'present'
nic_type = 'vmxnet3'
hostname = 'vc.lab.local'
username = 'administrator'
password = 'VMware1#'
datacenter = 'Lab'
network_name =  'Servers'
count = 2
module = None
dvs = False

def get_obj_by_name(content, vimtype, name):
    """
     Get the vsphere object associated with a given text name
    """    
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

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

def get_nics(vm_obj):
    nics = []

    for device in vm_obj.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualEthernetCard):
            print device.backing
            nics.append(dict(
                network=device.deviceInfo.summary,
                type=device.__class__.__name__.lower(),
                key=device.key,
                label=device.deviceInfo.label
                ))

    return nics


def objwalk(obj, path_elements):
    if hasattr(obj, 'parent'):
        new_obj = getattr(obj, 'parent')
        if new_obj:
            if new_obj.name != 'vm':
                # 'vm' is an invisible folder that exists at the datacenter root so we ignore it
                path_elements.append(new_obj.name)
            
            objwalk(new_obj, path_elements)

    return path_elements


def get_vm_object(module, conn, path, datacenter):

    all_vms = get_all_objs(conn, [vim.VirtualMachine])
    matching_vms = []
    path_list = filter(None, path.split('/'))
    name = path_list.pop()

    for vm_obj, label in all_vms.iteritems():
        if label == name:
            matching_vms.append(vm_obj)

    try:
        if len(matching_vms) > 1:
            
            for vm_obj in matching_vms:
                elements = []
                if set(path_list).issubset(set(objwalk(vm_obj, elements))):
                    return vm_obj

        else:
            return matching_vms[0]

    except TypeError:
        sys.exit("No matching VM found")

def create_nic(module, conn, vm, desired_nic):
    vm_spec = vim.vm.ConfigSpec()
    nic_spec = vim.vm.device.VirtualDeviceSpec()
    changes = []

    nic_spec.fileOperation = "create"
    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    nic_spec.device = vim.vm.device.VirtualEthernetCard()

    if dvs:
        sys.exit('dvs not supported yet')
    else:
        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        nic_spec.device.backing.network = get_obj_by_name(conn, [vim.Network], desired_nic['network'])
    
    nic_spec.device.wakeOnLanEnabled = True
    nic_spec.device.deviceInfo = vim.Description()
    # nic_spec.device.deviceInfo.label = desired_nic['label']
    nic_spec.device.deviceInfo.summary = desired_nic['network']     
    nic_spec.device.backing.deviceName = desired_nic['network']
    nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    nic_spec.device.connectable.startConnected = True
    nic_spec.device.connectable.allowGuestControl = True
    nic_spec.device.addressType = 'generated'
    # nic_spec.device.key = desired_nic['id']

    changes.append(nic_spec)
    vm_spec.deviceChange = changes
    vm.ReconfigVM_Task(spec=vm_spec)

    return desired_nic



def main():
    nic_type_map = dict(
        vmxnet3 = 'vim.vm.device.VirtualVmxnet3',
        vmxnet2 = 'vim.vm.device.VirtualVmxnet2',
        vmxnet  = 'vim.vm.device.VirtualVmxnet',
        e1000   = 'vim.vm.device.VirtualE1000',
        e1000e  = 'vim.vm.device.VirtualE1000e',
        pcnet32 = 'vim.vm.device.VirtualPCNet32'
        )

    desired_nic = dict(
        network='Servers',
        type=nic_type_map[nic_type],
        label='from script',
        id=4010
        )
    
    conn = connect_to_api()
    proper_vm = get_vm_object(module, conn, path, datacenter)
    all_nics = get_nics(proper_vm)

    if state == 'present':
        print create_nic(module, conn, proper_vm, desired_nic)
        

    else:
        print "Not here"

main()