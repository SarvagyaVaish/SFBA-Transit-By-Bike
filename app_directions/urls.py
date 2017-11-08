from django.conf.urls import url

from . import views

urlpatterns = [

	# API
	# Example: /?from_loc=37.4258,-122.1001&to_loc=37.7927,-122.3970&start_time=18:00:00
	url(r'^api$', views.api, name='api'),

	# GUI
	url(r'^$', views.index, name='index'),
	url(r'^search$', views.search, name='search'),
	url(r'^result$', views.result, name='result'),
]
