from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

# from scripts.main import find_routes


def index(request):
    from_coordinate = request.GET.get('from_loc', '')
    to_coordinate = request.GET.get('to_loc', '')
    start_time = request.GET.get('start_time', '')


    # office_coordinate = (37.425822, -122.100192)
    # embarcadero_coordinate = (37.792740, -122.397068)
    # departure_time = "18:00:00"
    # solutions = find_routes(office_coordinate, embarcadero_coordinate, departure_time)
    # return JsonResponse(solutions)

    return HttpResponse("Searching for directions: <br> from {} <br> to {} <br> at {}".format(
        from_coordinate,
        to_coordinate,
        start_time
        )
    )
