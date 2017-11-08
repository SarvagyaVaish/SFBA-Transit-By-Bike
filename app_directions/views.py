from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from scripts.main import find_routes


# Helper function
def get_lat_lon_tuple(coordinate_str):
	coordinates = coordinate_str.split(",")
	lat = float(coordinates[0])
	lon = float(coordinates[1])
	coordinate_tuple = (lat, lon)
	return coordinate_tuple


def index(request):
	return HttpResponse("Hi Kurt!")


def api(request):
	from_coordinate = request.GET.get('from_loc', '')
	to_coordinate = request.GET.get('to_loc', '')
	start_time = request.GET.get('start_time', '')

	solutions = find_routes(
			get_lat_lon_tuple(from_coordinate),
			get_lat_lon_tuple(to_coordinate),
			start_time
		)
	return JsonResponse(solutions)


def search(request):
	return HttpResponse("search")


def result(request):
	return HttpResponse("result")