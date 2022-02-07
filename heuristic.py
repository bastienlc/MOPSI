from data_conversion import json_to_objects_rooms, json_to_objects_requests
import operator
import random
from milp import milp_solve, dictionnary_from_requests
from local_solver import local_solver, compute_score

from params import parameters

LARGE = False

if LARGE:
    print("Loading students requests...")
    requests = json_to_objects_requests("eleves_demande.json")
    requests.sort(key=operator.methodcaller('absolute_score', parameters), reverse=True)
    print("Students requests loaded.")
    print("Loading rooms...")
    rooms = json_to_objects_rooms("chambre.json")
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

requests_dictionary = dictionnary_from_requests(requests)

number_of_places = 0
for room in rooms:
    number_of_places += room.capacity

GROUPS = []

for k, request in enumerate(requests):
    if k % GROUP_SIZE == 0:
        if k > 0:
            GROUPS.append(group)
        group = []
    group.append(request)
GROUPS.append(group)

NUMBER_OF_GROUPS = len(GROUPS)

ROOM_GROUPS_SIZE = len(rooms)//NUMBER_OF_GROUPS
ROOM_GROUPS = [[] for k in range(NUMBER_OF_GROUPS)]

for k in range(NUMBER_OF_GROUPS):
    ROOM_GROUPS[k] = rooms[k*ROOM_GROUPS_SIZE:(k+1)*ROOM_GROUPS_SIZE]

if NUMBER_OF_GROUPS*ROOM_GROUPS_SIZE < len(rooms):
    ROOM_GROUPS[-1] += rooms[NUMBER_OF_GROUPS*ROOM_GROUPS_SIZE:]

attributions = []
for k in range(NUMBER_OF_GROUPS):
    attributions += milp_solve(GROUPS[k], ROOM_GROUPS[k], parameters)

print("Score before local solving : ", compute_score(attributions, requests_dictionary, rooms))

attributions = local_solver(attributions, requests_dictionary, rooms, 1000)

attributions.sort(key=lambda attribution: attribution.request.student_id)
print("Solution :")
for attribution in attributions:
    print(attribution)
