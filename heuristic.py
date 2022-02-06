from data_conversion import json_to_objects_rooms, json_to_objects_requests
import operator
import random
from milp import milp_solve
from local_solver import local_solver, compute_score

# parameters
room_preference_bonus_parameter = 0.1
room_preference_malus_parameter = 100
gender_mix_parameter = 0.2
buddy_preference_parameter = 0.2

grant_parameter = 0.3
distance_parameter = 0.3
foreign_parameter = 1
shotgun_parameter = 0.001

parameters = {
    "room_preference_bonus_parameter": room_preference_bonus_parameter,
    "room_preference_malus_parameter": room_preference_malus_parameter,
    "gender_mix_parameter": gender_mix_parameter,
    "buddy_preference_parameter": buddy_preference_parameter,
    "grant_parameter": grant_parameter,
    "distance_parameter": distance_parameter,
    "foreign_parameter": foreign_parameter,
    "shotgun_parameter": shotgun_parameter
}

LARGE = True

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
    requests = json_to_objects_requests("eleves_demande_small.json")
    requests.sort(key=operator.methodcaller('absolute_score', parameters), reverse=True)
    print("Students requests loaded.")
    print("Loading rooms...")
    rooms = json_to_objects_rooms("chambre_small.json")
    random.shuffle(rooms)
    print("Rooms loaded.")
    GROUP_SIZE = 3

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

if NUMBER_OF_GROUPS*ROOM_GROUPS_SIZE<len(rooms):
    ROOM_GROUPS[-1] += rooms[NUMBER_OF_GROUPS*ROOM_GROUPS_SIZE:]

print(GROUPS)
print(ROOM_GROUPS)

attributions = []
for k in range(NUMBER_OF_GROUPS):
    attributions += milp_solve(GROUPS[k], ROOM_GROUPS[k], parameters)

print("Score before local solving : ", compute_score(attributions, requests, rooms))

local_solver(attributions, requests, rooms, 1000)
