from django.db import models
from django import forms
from .services import get_image_vector

# Create your models here.

DEVICE_TYPES = (
  ('router','ROUTER'),
  ('pc','PC'),
  ('switch','SWITCH'),
  ('mlswitch','MULTI-LAYER SWITCH'),
  ('server', 'SERVER')
)

class DiskImage(models.Model):
  name = models.CharField(max_length=100)
  devicetype = models.CharField(max_length=8,choices=DEVICE_TYPES, default='pc')
  disk_image = models.FileField(upload_to='disk_images/')
  image = models.ImageField(default='../static/devices/computer.svg')

class ImageForm(forms.ModelForm):
  class Meta:
    model = DiskImage
    fields = ['name', 'devicetype', 'disk_image']
    image = get_image_vector(model.devicetype)
