import operator
import random

from data_conversion import (
    dictionary_from_requests,
    dictionary_from_rooms,
    json_to_objects_requests,
    json_to_objects_rooms,
    save_attributions,
    write_solutions,
)
from local_solver import compute_score, local_solver
from milp import milp_solve
from params import files, parameters

print(
    "========================================= PREPARING HEURISTIC ========================================"
)

instance = "real"

print("Loading requests and rooms [", instance, "] ...")
if instance == "real":
    requests = json_to_objects_requests("db/eleves_demande.json")
    rooms = json_to_objects_rooms("db/chambre.json")
else:
    rooms_file, requests_file = files[instance]
    requests = json_to_objects_requests(requests_file)
    rooms = json_to_objects_rooms(rooms_file)
requests.sort(key=operator.methodcaller("get_absolute_score", parameters), reverse=True)
random.shuffle(rooms)
requests_dictionary = dictionary_from_requests(requests)
rooms_dictionary = dictionary_from_rooms(rooms)
print("Requests and rooms loaded.")

if instance == "small":
    GROUP_SIZE = 3
else:
    GROUP_SIZE = 40

if instance == "small" or instance == "medium":
    n = 10000
else:
    n = 2000


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

print(
    "=========================================== SOLVING GROUPS ==========================================="
)

attributions = []
for k in range(number_of_groups):
    print("-------- SOLVING GROUP ", k + 1, "--------")
    attributions += milp_solve(requests_groups[k], room_groups[k], parameters)

print(
    "=========================================== GROUPS SOLVED ==========================================="
)
print(
    "====================================== LAUNCHING LOCAL SOLVER ======================================="
)

print("Score before local solving : ", compute_score(attributions, requests_dictionary))

attributions.sort(key=lambda attribution: attribution.request.student_id)
attributions = local_solver(attributions, requests_dictionary, rooms_dictionary, n)

print(
    "======================================== LOCAL SOLVER ENDED ========================================"
)

print(
    "================================= FINE-TUNING ATTRIBUTION WITH MILP ================================"
)

selected_requests = [attribution.request for attribution in attributions]
for room in rooms:
    room.empty()
attributions = milp_solve(selected_requests, rooms)

print(
    "========================================= FINE-TUNING ENDED ========================================"
)

print(
    "============================================= SOLUTION ============================================="
)
for attribution in attributions:
    print(attribution)
print("Final score : ", compute_score(attributions, requests_dictionary))
print(
    "========================================= WRITING SOLUTION ========================================="
)
solution_name = f"{instance}_heuristic"
write_solutions(attributions, requests, rooms, solution_name)
save_attributions(attributions, solution_name)
print(
    "=============================================== DONE ==============================================="
)
