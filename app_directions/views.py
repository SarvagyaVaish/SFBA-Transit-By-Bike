from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib import messages

from scripts.main import find_routes


# Helper function
def get_lat_lon_tuple(coordinate_str):
	coordinates = coordinate_str.split(",")
	lat = float(coordinates[0])
	lon = float(coordinates[1])
	coordinate_tuple = (lat, lon)
	return coordinate_tuple


def index(request):
	return HttpResponseRedirect("/directions/search")


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
	return render(request, 'app_directions/search_form.html')


def result(request):
	# Check data
	redirect_back = False
	try:
		from_coordinate = request.POST["input_from_loc"]
	except:
		messages.error(request, 'Start location incorrect.')
		redirect_back = True

	try:
		to_coordinate = request.POST["input_to_loc"]
	except:
		messages.error(request, 'Destination location incorrect.')
		redirect_back = True

	try:
		start_time = request.POST["input_start_time"]
	except:
		messages.error(request, 'Start time incorrect.')
		redirect_back = True

	if not redirect_back:
		if len(from_coordinate) == 0:
			messages.error(request, 'Start location empty.')
			redirect_back = True

		if len(to_coordinate) == 0:
			messages.error(request, 'Destination location empty.')
			redirect_back = True

		if len(start_time) == 0:
			messages.error(request, 'Start time not provided.')
			redirect_back = True

	if redirect_back:
		return HttpResponseRedirect("/directions")

	start_time = start_time + ":00"
	solutions = find_routes(
			get_lat_lon_tuple(from_coordinate),
			get_lat_lon_tuple(to_coordinate),
			start_time
		)

	result = {
		"input" : {
			"from_coordinate" : get_lat_lon_tuple(from_coordinate),
			"to_coordinate" : get_lat_lon_tuple(to_coordinate),
			"start_time" : start_time,
		},
		"solutions" : solutions,
	}

	return JsonResponse(result)
	# return HttpResponse("Correct")
