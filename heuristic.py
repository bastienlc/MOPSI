from data_conversion import json_to_objects_rooms, json_to_objects_requests
import operator
import random
from milp import milp_solve
from local_solver import local_solver, compute_score, dictionary_from_requests

from params import parameters

LARGE = False

if LARGE:
    print("Loading students requests...")
    requests = json_to_objects_requests("instances/eleves_demande_large.json")
    requests.sort(key=operator.methodcaller('absolute_score', parameters), reverse=True)
    print("Students requests loaded.")
    print("Loading rooms...")
    rooms = json_to_objects_rooms("instances/chambre_large.json")
    random.shuffle(rooms)
    print("Rooms loaded.")
    GROUP_SIZE = 50
else:
    print("Loading students requests...")
    requests = json_to_objects_requests("instances/eleves_demande_small.json")
    requests.sort(key=operator.methodcaller('absolute_score', parameters), reverse=True)
    print("Students requests loaded.")
    print("Loading rooms...")
    rooms = json_to_objects_rooms("instances/chambre_small.json")
    random.shuffle(rooms)
    print("Rooms loaded.")
    GROUP_SIZE = 3

requests_dictionary = dictionary_from_requests(requests)

number_of_places = 0
for room in rooms:
    number_of_places += room.capacity

requests_groups = []

for k, request in enumerate(requests):
    if k % GROUP_SIZE == 0:
        if k > 0:
            requests_groups.append(group)
        group = []
    group.append(request)
requests_groups.append(group)

number_of_groups = len(requests_groups)

ROOM_GROUPS_SIZE = len(rooms) // number_of_groups
room_groups = [[] for k in range(number_of_groups)]

room_index = 0
group_index = 0
capacity = 0
objective = 0
while room_index < len(rooms) and group_index < number_of_groups:
    if objective == 0:
        objective = len(requests_groups[group_index])

    if capacity < objective:
        room_groups[group_index].append(rooms[room_index])
        capacity += rooms[room_index].capacity
        room_index += 1
    else:
        objective = 0
        capacity = 0
        group_index += 1

attributions = []
for k in range(number_of_groups):
    attributions += milp_solve(requests_groups[k], room_groups[k], parameters)

print("Score before local solving : ", compute_score(attributions, requests_dictionary))

attributions.sort(key=lambda attribution: attribution.request.student_id)
attributions = local_solver(attributions, requests_dictionary, rooms, 1000)

print("Solution :")
for attribution in attributions:
    print(attribution)
