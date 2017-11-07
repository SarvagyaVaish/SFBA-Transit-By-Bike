from django.conf.urls import url

from . import views

urlpatterns = [
	# Example: /?from_loc=37.4258,-122.1001&to_loc=37.7927,-122.3970&start_time=18:00:00
	url(r'^$', views.index, name='index'),
]
