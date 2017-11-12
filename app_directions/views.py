from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib import messages

from scripts.main import find_routes

import logging
logger = logging.getLogger(__name__)


# Helper function
def get_lat_lon_tuple(coordinate_str):
	coordinates = coordinate_str.split(",")
	lat = float(coordinates[0])
	lon = float(coordinates[1])
	coordinate_tuple = (lat, lon)
	return coordinate_tuple


def log_session(session):
	# Print current session variables
	for key in session.keys():
		logger.warn("{}, {}".format(key, session[key]))


def flush_session(session):
	session.flush()


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

	context = {
		"input" : {
			"from_coordinate" : get_lat_lon_tuple(from_coordinate),
			"to_coordinate" : get_lat_lon_tuple(to_coordinate),
			"start_time" : start_time,
		},
		"solution_count" : len(solutions),
		"solutions" : solutions
	}

	return JsonResponse(context)


def search(request):
	# flush_session(request.session)
	context = {}
	if "from_address" in request.session:
		context["from_address"] = request.session["from_address"]
	if "to_address" in request.session:
		context["to_address"] = request.session["to_address"]
	log_session(request.session)
	return render(request, 'app_directions/search_form.html', context)


def result(request):
	# Check data
	redirect_back = False
	try:
		from_coordinate = request.POST["input_name_from_coords"]
		# Save from addresses in session
		from_text = request.POST["input_name_from_text"]
		if from_text != "":
			request.session["from_address"] = from_text
	except:
		messages.error(request, 'Start location incorrect.')
		redirect_back = True

	try:
		to_coordinate = request.POST["input_name_to_coords"]
		# Save to addresses in session
		to_text = request.POST["input_name_to_text"]
		if to_text != "":
			request.session["to_address"] = to_text
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

	# Find solution
	start_time = start_time + ":00"
	solutions = find_routes(
			get_lat_lon_tuple(from_coordinate),
			get_lat_lon_tuple(to_coordinate),
			start_time
		)

	context = {
		"input" : {
			"from_coordinate" : get_lat_lon_tuple(from_coordinate),
			"to_coordinate" : get_lat_lon_tuple(to_coordinate),
			"start_time" : start_time,
		},
		"solution_count" : len(solutions),
	}

	# Check if solutions exist
	if len(solutions) == 0:
		messages.error(request, 'No route found.')
		return render(request, 'app_directions/results_page.html', context)

	# Format solution for view
	context["solution"] = []
	solution = solutions[0]
	for node in solution:
		# Add data for Connection
		if node["id"] != "departure":
			connection_data = {
				"type" : "connection",
				"name" : node["arrival_mode"],
				"time" : node["moving_time"],
			}
			context["solution"].append(connection_data)

		# Add data for Node
		if node["arrival_time"] == node["departure_time"]:
			time_data = node["arrival_time_str"]
		else:
			time_data = node["arrival_time_str"] + " : " + node["departure_time_str"]

		node_data = {
			"type" : "node",
			"name" : node["name"],
			"time" : time_data,
		}
		context["solution"].append(node_data)

	return render(request, 'app_directions/results_page.html', context)
