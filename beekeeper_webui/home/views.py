from django.contrib import messages
from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.encoding import smart_str
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.core.serializers import serialize
from django.conf import settings
from django.urls import reverse
from django.template import Context, Template
from .services import connect_to_internet, disconnect_from_internet, connect_ethernet_cable, disconnect_cable, plug_cable_in_devices, destroy_network, create_network, create_ethernet_ports, generate_error_message, get_vm_status, create_device_req, lookup_domain, get_domain_vnc_socket, create_virtual_machine, remove_machine, turn_off_devices, turn_on_devices
from .models import EthernetCable, EthernetPorts, ImageForm, DiskImage, Device, DeviceForm
from urllib.parse import urlencode
import os
import json

# Create your views here.

class HomePageView(TemplateView):
  template_name = 'home.html'

  def get_context_data( *args, **kwargs):
    context = {
      'form': ImageForm(),
      'device_form': DeviceForm(),
      'disk_images': DiskImage.objects.all(),
      'devices': serialize('json', Device.objects.all())
    }
    return context

  def upload_images(request):
    next = request.POST.get('next', '/')
    if request.method == "POST":
      form = ImageForm(request.POST, request.FILES)
      if form.is_valid():
        if form.save():
          messages.success(request, 'Disk Image uploaded successfully', extra_tags='alert-success')
        else:
          messages.error(request, 'Unable to save Disk Image 3', extra_tags='alert-danger')
      else:
        messages.error(request, 'Unable to save Disk Image 1', extra_tags='alert-danger')
      return HttpResponseRedirect(next)
    else:
      messages.error(request, 'Unable to save Disk Image 2', extra_tags='alert-danger')
      return HttpResponseRedirect(next)

  def retrieveXml(request):
    if request.is_ajax and request.method == "GET":
      xml_file_path = os.path.join(settings.STATIC_ROOT, 'graph.xml')
      xml_file = open(xml_file_path, 'r')
      xml_string = xml_file.read()
      xml_file.close()
      return JsonResponse({"response":xml_string}, status = 200)

  def saveXml(request):
    if request.is_ajax and request.method == "GET":
      xml_string = request.GET.get("XML", None)
      xml_file_path = os.path.join(settings.STATIC_ROOT, 'graph.xml')
      xml_file = open(xml_file_path, 'w')
      xml_file.write(xml_string)
      xml_file.close()
      return JsonResponse({"saved":True}, status = 200)
    return JsonResponse({"saved":False}, status = 400)

  def get_images(request):
    if request.is_ajax and request.method == "GET":
      disk_images = json.loads(serialize('json', DiskImage.objects.all()))
      return JsonResponse({"disk_images":disk_images}, status = 200)
    return JsonResponse({'disk_images': 'None'}, status = 400)

  def create_device(request):
    if request.method == "POST":
      modified_request = create_device_req(request)
      cell_id = modified_request.get('cell_id', None)
      form = DeviceForm(modified_request)
      if form.is_valid():
        if form.save():
          create_virtual_machine(cell_id)
          return JsonResponse({'response':'success'}, status=200)

          # Ethernet ports were due to be produced manually but now automated.

          #ethernet_ports = int(modified_request.get('ethernetports', None))
          #if create_ethernet_ports(cell_id, ethernet_ports):
            #create_virtual_machine(cell_id)
            #return JsonResponse({'response':'success'}, status=200)
          #else:
            #return generate_error_message('Unable to create ethernet ports for device', cell_id)
        else:
          return generate_error_message('Unable to add device: Unable to save Device in the database', cell_id)
      else:
        return generate_error_message('Unable to add device: Data entered is not valid', cell_id)
    else:
      return generate_error_message('Unable to add device: Wrong HTTP request', None)

  def remove_device(request):
    if request.is_ajax and request.method == "GET":
      retrieved_cell_id = json.loads(request.GET.get('cell_id',None))
      vm_record = Device.objects.get(cell_id=retrieved_cell_id)
      if vm_record.delete():
        remove_machine(vm_record)
        return JsonResponse({'result': 'success'},status = 200)
      else:
        return JsonResponse({'result': f'Unable to remove device {vm_record.name} from the database at this time'},status = 500)
  
  def change_vm_state(request):
    if request.is_ajax and request.method == "GET":
      device_list = json.loads(request.GET.get('cells', None))
      if request.GET.get('state',None) == 'start':
        turn_on_devices(device_list)
        return JsonResponse({'result': 'success'}, status=200)
      else:
        turn_off_devices(device_list)
        return JsonResponse({'result': 'success'}, status=200)
    return JsonResponse({'result': 'wrong request'}, status=400)

  def get_device_vnc(request):
    if request.is_ajax and request.method == "GET":
      cell_id = request.GET.get('cell_id', None)
      token = Device.objects.get(cell_id=cell_id).token
      base_url = reverse('load_device_vnc')
      path = urlencode({'path':'websockify'})
      token = urlencode({'token':token})
      url = '{}?{}?{}'.format(base_url,path,token)
      return HttpResponseRedirect(url)
    return JsonResponse({'result': 'wrong request'}, status=400)

  def load_device_vnc(request):
    return render(request, 'vnc.html')

  def get_device_status(request):
    if request.method == "GET":
      cell_id = request.GET.get('cell_id',None)
      device_status = get_vm_status(cell_id)
      return JsonResponse({'device_status':device_status},status=200)
    return JsonResponse({'result': 'wrong request'}, status=400)

  def reload_body(request):
    if request.method == 'GET':
      context = {
        'form': ImageForm(),
        'device_form': DeviceForm()
      }
      return render(request, '_body.html', context)
    return JsonResponse({'result': 'wrong_request'},status=200)

  def remove_image(request):
    if request.method == 'POST':
      next = request.POST.get('next', '/')
      images = request.POST.getlist('diskImages', None)
      for image in images:
        disk_image = DiskImage.objects.get(name=image)
        disk_image.disk_image.delete()
        disk_image.delete()
      return HttpResponseRedirect(next)
    return JsonResponse({'result': 'wrong request'}, status=400)

  def create_network_bridge(request):
    if request.method == "GET":
      name = request.GET.get('bridge_name', None)
      cell_id = request.GET.get('cell_id', None)
      #device_one_ethernet = request.GET.get('device_one_ethernet', None)
      #device_two_ethernet = request.GET.get('device_two_ethernet', None)
      network = create_network(name)
      if network == 'success': # if network creation was successful
        # create entry for ethernet cable in the database
        ethernet_cable = EthernetCable(name=name,cell_id=int(cell_id))
        ethernet_cable.save()
        return JsonResponse({'response': network}, status=200)

        # Experimented with plugging cables into certain ports

        #cable_plugged = plug_cable_in_devices(name, device_one_ethernet, device_two_ethernet)
        #if cable_plugged == 'success':
          #return JsonResponse({'response': network})
        #else:
          #return JsonResponse({'error': cable_plugged}) # Because the error here is to do with plugging in the cables
      else:
        return JsonResponse({'error': network}, status=500)
    return JsonResponse({'result': 'wrong request'}, status=400)
        
  def destroy_network_bridge(request):
    if request.method == "GET":
      cell_id = request.GET.get('cell_id', None)
      remove_network = destroy_network(cell_id)
      if remove_network == 'success':
        return JsonResponse({'response': remove_network}, status=200)
      else:
        return JsonResponse({'error': remove_network}, status=500)
    return JsonResponse({'result': 'wrong request'}, status=400)

  def get_ethernet_ports(request):
    cell_id = request.GET.get('cell_id', None)
    if request.method == 'GET':
      vm = Device.objects.get(cell_id=cell_id)
      ethernet_ports = json.loads(serialize('json', vm.ethernetports_set.all()))
      return JsonResponse({'ethernet_ports': ethernet_ports}, status=200)
    return JsonResponse({'error':'wrong request'}, status=400)
  
  def get_devices(request):
    if request.is_ajax and request.method == "GET":
      devices = json.loads(serialize('json', Device.objects.all()))
      return JsonResponse({"devices":devices}, status = 200)
    return JsonResponse({'result': 'wrong request'}, status=400)

  def connect_cable(request):
    if request.is_ajax and request.method == "GET":
      cell_id = request.GET.get('cell_id', None)
      device = request.GET.get('device', None)
      endpoint = request.GET.get('endpoint', None)
      connect_ethernet_cable(cell_id, device, endpoint)
      return JsonResponse({'result': 'success'},status = 200)
    return JsonResponse({'result': 'wrong request'}, status=400)

  def disconnect_cable(request):
    if request.is_ajax and request.method == "GET":
      cell_id = request.GET.get('cell_id', None)
      endpoint = request.GET.get('endpoint', None)
      disconnect_cable(cell_id, endpoint)
      return JsonResponse({'result': 'success'},status = 200)
    return JsonResponse({'result': 'wrong request'}, status=400)

  def lookup_device(request):
    cell_id = request.GET.get('cell_id', None)
    try:
      vm = Device.objects.get(cell_id=cell_id)
      return JsonResponse({'response': vm.name, 'console_port': vm.console_port}, status=200)
    except:
      return JsonResponse({'response': 'Not Found'})

  def connect_device_to_internet(request):
    if request.is_ajax and request.method == "GET":
      cell_id = request.GET.get('cell_id', None)
      device_name = Device.objects.get(cell_id=cell_id).name
      if connect_to_internet(device_name):
        return JsonResponse({'result': 'success'}, status=200)
      else:
        return JsonResponse({'result': 'failure'}, status=500)
    return JsonResponse({'result': 'wrong request'}, status=400)

  def disconnect_device_from_internet(request):
    if request.is_ajax and request.method == "GET":
      cell_id = request.GET.get('cell_id', None)
      device_name = Device.objects.get(cell_id=cell_id).name
      if disconnect_from_internet(device_name):
        return JsonResponse({'result': 'success'}, status=200)
      else:
        return JsonResponse({'result': 'failure'}, status=500)
    return JsonResponse({'result': 'wrong request'}, status=400)

  def get_started_guide(request):
    return render(request, 'get_started_guide.html')
