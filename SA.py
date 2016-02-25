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
state = 'update'
nic_type = 'vmxnet3'
hostname = 'vc.lab.local'
username = 'administrator'
password = 'VMware1#'
datacenter = 'Lab'
network_name =  'Servers'
count = 2
module = None
dvs = False

def wait_for_task(task):

    while True:
        if task.info.state == vim.TaskInfo.State.success:
            return True, task.info.result
        if task.info.state == vim.TaskInfo.State.error:
            try:
                raise TaskError(task.info.error)
            except AttributeError:
                raise TaskError("An unknown error has occurred")
        if task.info.state == vim.TaskInfo.State.running:
            time.sleep(15)
        if task.info.state == vim.TaskInfo.State.queued:
            time.sleep(15)

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
            nics.append(dict(
                network=device.deviceInfo.summary,
                type=device.__class__.__name__,
                key=device.key,
                label=device.deviceInfo.label,
                nic_obj=device
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


def update_nic(module, conn, vm, desired_nic, all_nics):
    vm_spec = vim.vm.ConfigSpec()
    nic_spec = vim.vm.device.VirtualDeviceSpec()
    changes = []
    nic_obj = None

    for nic in all_nics:
        if nic['key'] == desired_nic['key']:
            nic_obj = nic['nic_obj']

    if not nic_obj:
        sys.exit("Nic with id not found")

    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
    nic_spec.device = nic_obj
    nic_spec.device.key = nic_obj.key
    nic_spec.device.macAddress = nic_obj.macAddress

    if desired_nic['dvs']:
        pg_obj = get_obj(content, [vim.dvs.DistributedVirtualPortgroup], desired_nic['network'])
        dvs_port_connection = vim.dvs.PortConnection()
        dvs_port_connection.portgroupKey= pg_obj.key
        dvs_port_connection.switchUuid= pg_obj.config.distributedVirtualSwitch.uuid
        nicspec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
        nicspec.device.backing.port = dvs_port_connection
    else:
        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        nic_spec.device.backing.network = get_obj_by_name(conn, [vim.Network], desired_nic['network'])
    
    nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    nic_spec.device.connectable.startConnected = True
    nic_spec.device.connectable.allowGuestControl = True
    nic_spec.device.wakeOnLanEnabled = True
    nic_spec.device.deviceInfo = vim.Description()
    nic_spec.device.deviceInfo.summary = desired_nic['network']     
    nic_spec.device.backing.deviceName = desired_nic['network']

    changes.append(nic_spec)
    spec = vim.vm.ConfigSpec()
    spec.deviceChange = changes
    task = vm.ReconfigVM_Task(spec=spec)
    success, result = wait_for_task(task)

    if success:
        return desired_nic
    else:
        sys.exit('failure')



def remove_nic(module, conn, vm, desired_nic, all_nics):
    vm_spec = vim.vm.ConfigSpec()
    nic_spec = vim.vm.device.VirtualDeviceSpec()
    changes = []
    nic_obj = None

    for nic in all_nics:
        if nic['key'] == desired_nic['key']:
            nic_obj = nic['nic_obj']

    if not nic_obj:
        sys.exit("Nic with id not found")

    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
    nic_spec.device = nic_obj
    changes.append(nic_spec)
    spec = vim.vm.ConfigSpec()
    spec.deviceChange = changes
    task = vm.ReconfigVM_Task(spec=spec)
    success, result = wait_for_task(task)


    if success:
        return desired_nic
    else:
        sys.exit('failure')

def create_nic(module, conn, vm, desired_nic):
    vm_spec = vim.vm.ConfigSpec()
    nic_spec = vim.vm.device.VirtualDeviceSpec()
    changes = []

    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    nic_spec.device = getattr(vim.vm.device, desired_nic['type'])()

    if desired_nic['dvs']:
        pg_obj = get_obj(content, [vim.dvs.DistributedVirtualPortgroup], desired_nic['network'])
        dvs_port_connection = vim.dvs.PortConnection()
        dvs_port_connection.portgroupKey= pg_obj.key
        dvs_port_connection.switchUuid= pg_obj.config.distributedVirtualSwitch.uuid
        nicspec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
        nicspec.device.backing.port = dvs_port_connection
    else:
        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        nic_spec.device.backing.network = get_obj_by_name(conn, [vim.Network], desired_nic['network'])
    
    nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    nic_spec.device.connectable.startConnected = True
    nic_spec.device.connectable.allowGuestControl = True
    nic_spec.device.wakeOnLanEnabled = True
    nic_spec.device.deviceInfo = vim.Description()
    nic_spec.device.deviceInfo.summary = desired_nic['network']     
    nic_spec.device.backing.deviceName = desired_nic['network']
    nic_spec.device.addressType = 'generated'
    # The two below do not work, label and key, they are ignored by the API
    # nic_spec.device.deviceInfo.label = desired_nic['label']
    # nic_spec.device.key = desired_nic['id']

    changes.append(nic_spec)
    vm_spec.deviceChange = changes
    task = vm.ReconfigVM_Task(spec=vm_spec)

    success, result = wait_for_task(task)

    if success:
        return desired_nic
    else:
        sys.exit('failure')

# def needs_update(desired_nic, all_nics):
#     for nic in all_nics:
#         if nic['nic_obj']['backing']['deviceName'] == desired_nic['network']


def main():
    nic_type_map = dict(
        vmxnet3 = 'VirtualVmxnet3',
        vmxnet2 = 'VirtualVmxnet2',
        vmxnet  = 'VirtualVmxnet',
        e1000   = 'VirtualE1000',
        e1000e  = 'VirtualE1000e',
        pcnet32 = 'VirtualPCNet32'
        )

    desired_nic = dict(
        network='VM Network',
        type=nic_type_map[nic_type],
        dvs=False,
        key=4000
        )
    
    conn = connect_to_api()
    proper_vm = get_vm_object(module, conn, path, datacenter)
    all_nics = get_nics(proper_vm)
    print all_nics
    if state == 'create':
        print create_nic(module, conn, proper_vm, desired_nic)
    elif state == 'absent':
        print remove_nic(module, conn, proper_vm, desired_nic, all_nics)
    elif state == 'update':
        for nic in all_nics:
            print nic['nic_obj'].backing
        # if needs_update(desired_nic, all_nics):
        #     print update_nic(module, conn, proper_vm, desired_nic, all_nics)
    else:
        print "Not here"

main()