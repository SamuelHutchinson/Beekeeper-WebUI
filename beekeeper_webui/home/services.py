from django.http import JsonResponse
from .models import DiskImage, Device, EthernetPorts, EthernetCable
from django.conf import settings
from xml.dom import minidom
import os
import uuid
import libvirt
import sys
import random

def lookup_domain(cell_id):
  dom = None
  conn = libvirt.open('qemu:///system')
  try:
    vm_record = Device.objects.get(cell_id=cell_id)
    dom = conn.lookupByName(vm_record.name)
  except:
    dom = None
  finally:
    conn.close()
  return dom

# Can still be useful for another day, maybe when a user decides to VNC into a VM? 
def get_domain_vnc_socket(domain):
  host_and_port = []
  port = 5900 # default port
  host = '127.0.0.1' # default host
  raw_xml = domain.XMLDesc(0)
  xml = minidom.parseString(raw_xml)
  graphicsTypes = xml.getElementsByTagName('graphics')
  for graphicsType in graphicsTypes:
    port = graphicsType.getAttribute('port')
    host = graphicsType.getAttribute('listen')
  host_and_port.append(host)
  host_and_port.append(port)
  return host_and_port

def create_virtual_machine(cell_id):
  # create a .img file first then use that as the hard disk for the VM.
  # disk image goes into the cdrom compartment of the XML.
  # x.ethernetports_set.all()

  # token generation happens here
  token = str(uuid.uuid4())
  console_port = "1{:04d}".format(int(cell_id))
  vm = Device.objects.get(cell_id=cell_id)
  vm.token = token
  vm.console_port = console_port
  vm.save()

  name = vm.name
  memory = vm.ram
  disk_size = vm.disk_size
  cpus = vm.cpus
  disk_image = vm.disk_image


  # Here I was experimenting with adding ethernet ports to a device manually

  #ethernet_ports = """ """
  #for port in vm.ethernetports_set.all():
    #xml = """
    #<interface>

    #</interface>\n
    #"""
    #ethernet_ports += xml

  xml = f"""
  <domain type='kvm' xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'>
    <name>{name}</name>
    <memory unit='MB'>{memory}</memory>
    <currentmemory unit='MB'>{memory}</currentmemory>
    <vcpu placement='static'>{cpus}</vcpu>
    <clock sync='localtime'/>
    <resource>
      <partition>/machine</partition>
    </resource>
    <on_poweroff>destroy</on_poweroff>
    <on_reboot>restart</on_reboot>
    <on_crash>destroy</on_crash>
    <os>
      <type arch='x86_64' machine='pc'>hvm</type>
      <boot dev='hd'/>
      <boot dev='cdrom'/>
    </os>
    <features>
      <acpi/>
      <apic/>
    </features>
    <devices>
      <emulator>/usr/bin/kvm-spice</emulator>
      {create_disks(name, disk_image)}
      <serial type='tcp'>
        <source mode='bind' host='0.0.0.0' service='{console_port}' tls='no'/>
        <protocol type='telnet'/>
        <target port='0'/>
        <alias name='serial1'/>
      </serial>
      <input type='mouse' bus='ps2'/>
      <input type='keyboard' bus='ps2'/>
      <graphics type='vnc' port='-1' autoport='yes' listen='0.0.0.0'/>
    </devices>
  </domain>"""
       #<serial type='pty'>
        #<target port='0'/>
      #</serial>
      #<console type='pty'>
       #<target type='serial' port='0'/>
      #</console>
  #print(xml)
  spawn_machine(disk_size, name, xml, token, disk_image.extension())

def create_disks(device_name, disk_image):
  if disk_image.extension() == 'iso':
    return disks_for_iso(device_name, disk_image)
  if disk_image.extension() == 'qcow2':
    return disks_for_qcow2(disk_image, device_name)

def disks_for_iso(device_name, disk_image):
  xml = f"""
    <disk type='file' device='disk'>
      <source file='/var/lib/libvirt/images/{device_name}.qcow2'/>
      <backingstore/>
      <driver name='qemu' type='raw'/>
      <target dev='vda' bus='virtio'/>
    </disk>
    <disk type='file' device='cdrom'>
      <driver name='qemu' type='raw'/>
      <source file='{settings.MEDIA_ROOT}/{disk_image.disk_image}'/>
      <backingstore/>
      <target dev='hda' bus='ide'/>
      <readonly/>
    </disk>
    """
  return xml

def disks_for_qcow2(disk_image, device_name):
  image_file = disk_image.disk_image
  full_image_file_path = os.path.join(f'{settings.MEDIA_ROOT}/', image_file.name)
  new_image_file_path = '/var/lib/libvirt/images/'
  os.system(f'cp {full_image_file_path} {new_image_file_path}')
  image_name = image_file.name.replace('disk_images/', '')
  os.system(f'mv {new_image_file_path}{image_name} {new_image_file_path}{device_name}.qcow2') # Change the name of the copied qcow2 file to be the name of the device
  xml = f"""
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2' cache='none'/>
      <source file='{new_image_file_path}{device_name}.qcow2'/> # uses the qcow2 file copied over from the media directory
      <backingstore/>
      <driver name='qemu' type='raw'/>
      <target dev='vda' bus='virtio'/>
    </disk>
  """
  return xml

def spawn_machine(disk_size, name, xml, token, image_file_type):
  config = xml
  conn = libvirt.open('qemu:///system')
  dom = conn.defineXML(config)
  if dom == None:
    print('Failed to define a domain from an XML definition.', file=sys.stderr)
  else:
    if image_file_type == 'iso': # if disk image is qcow2, no need to create another qcow2 image which overwrites it
      os.system(f'qemu-img create -f raw /var/lib/libvirt/images/{name}.qcow2 {disk_size}G')
    if dom.create() < 0:
      print('Can not boot guest domain.', file=sys.stderr)
    else:
      dom.setAutostart(1)
      print('Guest '+dom.name()+' has booted', file=sys.stderr)
      socket = get_domain_vnc_socket(dom)
      create_device_token(socket, token)
  conn.close()

def generate_error_message(message, cell_id):
  try:
    vm = Device.objects.get(cell_id=cell_id)
    remove_machine(vm)
  finally:
    return JsonResponse({'response':'error', 'message': message}, status=400)

def create_device_token(socket, token):
  token_mapping = "{}: {}:{}".format(token, socket[0], socket[1])
  token_filepath = os.path.join(settings.BASE_DIR, f'assets/javascript/novnc/vnc_tokens/{token}.ini')
  token_file = open(token_filepath, 'w')
  token_file.write(token_mapping)
  token_file.close

def remove_machine(virtual_machine):
  conn = libvirt.open('qemu:///system')
  dom = conn.lookupByName(virtual_machine.name)
  dom.undefine()
  dom.destroy()
  print(f'domain {virtual_machine.name} destroyed')

  # remove img associated with the VM
  os.system(f'rm -rf /var/lib/libvirt/images/{virtual_machine.name}.qcow2')

  # remove the VNC token too
  token_filepath = os.path.join(settings.BASE_DIR, f'assets/javascript/novnc/vnc_tokens/{virtual_machine.token}.ini')
  os.remove(token_filepath)

def turn_off_devices(devices):
  conn = libvirt.open('qemu:///system')
  if len(devices) == 0:
    # shut off all devices
    domains = conn.listAllDomains(0)
    for domain in domains:
      if domain.isActive(): # If device is not already turned off
        domain.destroy()
  else:
    #shut off selected devices
    for device in devices:
      vm_name = Device.objects.get(cell_id=device).name
      dom = conn.lookupByName(vm_name)
      if dom.isActive(): # If device is not already turned off
        dom.destroy()
  conn.close()

def turn_on_devices(devices):
  conn = libvirt.open('qemu:///system')
  if len(devices) == 0:
    # turn on all devices
    domains = conn.listAllDomains(0)
    for domain in domains:
      if domain.isActive() < 1: # If device is already turned on
        domain.create()
  else:
    #turn on selected devices
    for device in devices:
      vm_name = Device.objects.get(cell_id=device).name
      dom = conn.lookupByName(vm_name)
      if dom.isActive() < 1: # If device is already turned on
        dom.create()
  conn.close()

def create_device_req(request):
  if request.method == 'POST':
    update_request = request.POST.copy()
    name = update_request['name'].replace(" ", '_') # ensure spaces in the name are replaced with underscores
    update_request.update({'name':name})
    return update_request

def get_vm_status(cell_id):
  vm = lookup_domain(cell_id)
  if vm is None:
    return 'status_unknown'
  else:
    if vm.isActive():
      return 'status_online'
    if vm.isActive() < 1:
      return 'status_offline'

def create_network(name):
  xml = f""" 
  <network>
    <name>{name}</name>
    <bridge name="{name}" stp='off' macTableManager="libvirt"/> 
    <mtu size="9216"/> 
  </network>
  """
  conn = libvirt.open('qemu:///system')
  if conn == None:
    conn.close()
    return 'Failed to open connection to QEMU'
  try:
    network = conn.networkDefineXML(xml)
  except:
    conn.close()
    return 'Failed to create an ethernet cable in the backend'
  network.setAutostart(1) # Sets the network to autostart upon bootup of libvirt
  network.create()
  conn.close()
  return 'success'

def destroy_network(cell_id):
  conn = libvirt.open('qemu:///system')
  if conn == None:
    conn.close()
    return 'Failed to open connection to QEMU'
  cable_record = EthernetCable.objects.get(cell_id=cell_id)
  network = conn.networkLookupByName(cable_record.name)
  network.destroy()
  network.undefine()
  if cable_record.source:
    cable_record.source.delete()
    libvirt_disconnect_cable(cable_record.name, cable_record.source.virtual_machine.name, cable_record.source.mac_address)
  if cable_record.target:
    cable_record.target.delete()
    libvirt_disconnect_cable(cable_record.name, cable_record.target.virtual_machine.name, cable_record.target.mac_address)
  cable_record.delete()
  conn.close()
  return 'success'

def connect_ethernet_cable(cable_cell_id, device, endpoint):
  cable = EthernetCable.objects.get(cell_id=cable_cell_id)
  delete_endpoint(endpoint, cable)
  device_record = Device.objects.get(cell_id=device)
  if endpoint == "source":
    cable.source = create_ports(device_record)
    cable.save()
    libvirt_connect_cable(cable.name, device_record.name, cable.source.mac_address)
  if endpoint == "target":
    cable.target = create_ports(device_record)
    cable.save()
    libvirt_connect_cable(cable.name, device_record.name, cable.target.mac_address)

def create_ports(vm):
  mac_address = generate_mac_address()
  ethernet_port = EthernetPorts(virtual_machine=vm, mac_address=mac_address)
  ethernet_port.save()
  # search it up again as the object before saving is different to the object stored in the DB.
  db_ethernet_port = EthernetPorts.objects.get(id=ethernet_port.id)
  return db_ethernet_port

def libvirt_connect_cable(cable_name, device_name, mac_address):
  conn = libvirt.open('qemu:///system')
  domain = conn.lookupByName(device_name)
  xml = f"""
    <interface type='bridge'>
      <mac address='{mac_address}'/>
      <source bridge='{cable_name}'/>
      <model type='e1000'/>
    </interface>
  """
  domain.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_LIVE)#libvirt.VIR_DOMAIN_AFFECT_LIVE)#libvirt.VIR_DOMAIN_AFFECT_CONFIG)
  domain.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG) # Persist to the xml config of a virtual machine

def disconnect_cable(cell_id, endpoint):
  print(cell_id)
  cable = EthernetCable.objects.get(cell_id=cell_id)
  mac_address = ''
  virtual_machine_name = ''
  if endpoint == "source":
    # saving a source doesn't work
    virtual_machine_name = cable.source.virtual_machine.name
    mac_address = cable.source.mac_address
    cable.source.delete()
  if endpoint == "target":
    virtual_machine_name = cable.target.virtual_machine.name
    mac_address = cable.target.mac_address
    cable.target.delete()
  #cable.save()
  print(cable.name)
  libvirt_disconnect_cable(cable.name, virtual_machine_name, mac_address)

def libvirt_disconnect_cable(cable_name, device_name, mac_address):
  conn = libvirt.open('qemu:///system')
  domain = conn.lookupByName(device_name)
  xml = f"""
    <interface type='bridge'>
      <mac address='{mac_address}'/>
      <source bridge='{cable_name}'/>
    </interface>
  """
  domain.detachDevice(xml)
  domain.detachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG)

def delete_endpoint(endpoint, cable):
  # remove any previous ethernet ports the cable was connected to
  if endpoint == 'source':
    if cable.source != None: # if the cable is already connected to a source point
      cable.source.delete()
  if endpoint == 'target': 
    if cable.target != None: # if the cable is already connected to a target point
      cable.target.delete()
  #cable.save()

def generate_mac_address():
  # credit to Russ (https://stackoverflow.com/questions/8484877/mac-address-generator-in-python)
  # for this (accessed 02/04/2020)
  mac_address = "02:00:00:%02x:%02x:%02x" % (
    random.randint(0, 255),
    random.randint(0, 255),
    random.randint(0, 255),
  )
  return mac_address

def connect_to_internet(device_name):
  conn = libvirt.open('qemu:///system')
  domain = conn.lookupByName(device_name)
  xml = f"""
    <interface type='network'>
      <source network='default'/>
      <model type='e1000'/>
    </interface>
  """
  domain.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_LIVE)#libvirt.VIR_DOMAIN_AFFECT_LIVE)#libvirt.VIR_DOMAIN_AFFECT_CONFIG)
  domain.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG) # Persist to the xml config of a virtual machine
  return True

def disconnect_from_internet(device_name):
  conn = libvirt.open('qemu:///system')
  domain = conn.lookupByName(device_name)
  xml = f"""
    <interface type='network'>
      <source network='default'/>
    </interface>
  """
  domain.detachDevice(xml)
  domain.detachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG)
  return True

#-----------------------------------------------------

# Code under this line is research and does not contribute to the running of the program

def create_ethernet_ports(cell_id, ethernet_ports):
  vm = Device.objects.get(cell_id=cell_id)
  i = 0
  for port in range(ethernet_ports):
    ethernet_port = EthernetPort(virtual_machine=vm,port_no=i)
    ethernet_port.save()
    i += 1
  return True

def plug_cable_in_devices(name, device_one_ethernet, device_two_ethernet):
  # Needs more work!
  eth_one = EthernetPorts.objects.get(id=device_one_ethernet)
  eth_two = EthernetPorts.objects.get(id=device_two_ethernet)
  device_one_record = eth_one.virtual_machine
  device_two_record = eth_two.virtual_machine
  if plug_cable_in_device(eth_one, device_one_record, name):
    if plug_cable_in_device(eth_two, device_two_record, name):
      return 'success'
    else:
      return f'Unable to plug ethernet cable to {device_two_record.name}'
  else:
    return f'Unable to plug ethernet cable to {device_one_record.name}'

def plug_cable_in_device(eth, device, name):
  conn = libvirt.open('qemu:///system')
  if conn == None:
    conn.close()
    return False
  dom = conn.lookupByName(device.name)
  #device_xml = get_device_xml_from_domain(dom)
  new_xml = return_int_xml_from_domain(name, eth, dom)
  if new_xml:
    dom.updateDeviceFlags(new_xml)
    #if dom.updateDeviceFlags(new_xml): # If updating the device XML was successful
      #conn.close()
      #return True
    #else:
      #conn.close()
      #return False
  else:
    return False
  
def get_device_xml_from_domain(dom):
  raw_xml = dom.XMLDesc(0)
  dom_xml = minidom.parseString(raw_xml)
  devices = dom_xml.getElementsByTagName('devices')
  return devices

def return_int_xml_from_domain(name, eth, dom):
  raw_xml = dom.XMLDesc(0)
  dom_xml = minidom.parseString(raw_xml)
  new_xml = minidom.parseString(f"""
  <interface type='bridge'>
    <source bridge='{name}'/>
    <model type='virtio'/>
  </interface>
  """)
  eth_port = int(eth.port_no)
  count = 0
  for interface in dom_xml.getElementsByTagName('interface'):
    if eth_port == count: # if the target ethernet port is found
      interface = new_xml
      print(dom_xml.toxml().replace('<?xml version="1.0" ?>', ''))
      return dom_xml.toxml()
    else:
      count += 1
  return False

