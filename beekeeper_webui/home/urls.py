from django.urls import path
from .views import HomePageView
urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('home', HomePageView.saveXml, name='save_xml'),
    path('retrieveXml', HomePageView.retrieveXml, name='retrieve_xml'),
    path('upload_image', HomePageView.upload_images, name='upload_image'),
    path('get_devices',HomePageView.get_devices, name='get_devices'),
    path('post_device_form', HomePageView.post_device_form, name='post_device_form'),
    path('remove_device', HomePageView.remove_device, name='remove_device')
]