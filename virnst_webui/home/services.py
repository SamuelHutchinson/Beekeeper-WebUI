import libvirt
from xml.dom import minidom

def get_domains():
  domain_list = []
  conn = libvirt.open('qemu:///system')
  domains = conn.listAllDomains(0)
  for domain in domains:
    domain_list.append(domain.name())
    port = get_domain_port(domain)
    domain_list.append(port)
  conn.close()
  return domain_list

def get_domain_port(domain):
  port = 5900 #first port a domain attaches to if there are no other domains
  raw_xml = domain.XMLDesc(0)
  xml = minidom.parseString(raw_xml)
  graphicsTypes = xml.getElementsByTagName('graphics')
  for graphicsType in graphicsTypes:
    port = graphicsType.getAttribute('port')
  return port

def create_virtual_machine(request):
  # create a .img file first then use that as the hard disk for the VM.
  # disk image goes into the cdrom compartment of the XML.
  name = request.POST.get('name',None)
  memory = request.POST.get('ram',None)
  disk_size = request.POST.get('disk_size',None)
  cpus = request.POST.get('cpus',None)
  disk_image = request.POST.get('disk_image',None)
  xml = f"""
  <domain type='kvm'>
    <name>{name}</name>
    <memory units='MB'>{memory}</memory>
    <vcpu>{cpus}</vcpu>
    <clock sync='localtime'/>
    <on_poweroff>destroy</on_poweroff>
    <on_reboot>restart</on_reboot>
    <on_crash>destroy</on_crash>
    <os>
      <type arch='x86_64' machine='pc'>hvm</type>
      <boot dev='hd'/>
      <boot dev='cdrom'/>
    </os>
    <devices>
      <emulator>/usr/bin/qemu-kvm</emulator>
      <disk type='file' device='disk'>
        <source file='/var/lib/libvirt/images/{name}.img'/>
        <driver name='qemu' type='raw'/>
        <target dev='hda'/>
      </disk>
      <disk type='file' device='cdrom'>
        <source file='{disk_image}'/>
        <target dev='hdc' bus='ide' tray='open'/>
        <readonly/>
      </disk>
      <input type='mouse' bus='ps2'/>
      <graphics type='vnc' port='-1' listen='127.0.0.1'/>
    </devices>
  </domain>"""
  print(xml)
