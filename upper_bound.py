import params
from data_conversion import load_attributions, json_to_objects_requests, json_to_objects_rooms, dictionary_from_requests, dictionary_from_rooms
from milp import milp_solve
from local_solver import compute_score_no_penalisation


def get_upper_bound_with_milp(requests_list, rooms_list, max_iter=1):
    """
    Applies the MILP on increasingly large portion of the requests, ordered by primary criteria.
    Once max_iter iterations were applied, if all the rooms are not filled, constraints are removed on the remaining
    rooms to force their filling.
    Almost more of a heuristic than an upper-bound giver, really.
    """
    requests_list.sort(reverse=True, key=lambda request: request.get_absolute_score())
    total_capacity = sum([room.capacity for room in rooms_list])

    iteration = 0
    attributions = []
    while total_capacity - len(attributions) > 0 and iteration < max_iter:
        print(f"========== ITERATION N°{iteration+1} ==========")
        selected_requests_dictonary = dictionary_from_requests(requests_list[:total_capacity + iteration])  # requests are progressively added if all the rooms are not filled
        # process selected requests to remove inconsistent friend requests
        for request in selected_requests_dictonary.values():
            if request.has_mate and not str(request.mate_id) in selected_requests_dictonary.keys(): # Not optimal but good enough
                request.has_mate = False
                request.mate_id = None

        selected_requests_list = list(selected_requests_dictonary.values())
        attributions = milp_solve(selected_requests_list, rooms_list)

        iteration += 1

    if len(attributions) < total_capacity:
        unfilled_rooms_selection = [True for _ in range(len(rooms))]
        unassigned_selected_requests_selection = [True for _ in range(len(selected_requests_list))]
        rooms_id_to_idx = {room.room_id: k for k, room in enumerate(rooms)}
        requests_id_to_idx = {request.student_id: k for k, request in enumerate(selected_requests_list)}
        for attribution in attributions:
            room = rooms[rooms_id_to_idx[attribution.room.room_id]]
            if room.capacity == len(room.students):
                unfilled_rooms_selection[rooms_id_to_idx[attribution.room.room_id]] = False
            unassigned_selected_requests_selection[requests_id_to_idx[attribution.request.student_id]] = False
        unfilled_rooms = [room for k, room in enumerate(rooms) if unfilled_rooms_selection[k]]
        unassigned_selected_requests_dictionary = {str(request.student_id): request for k, request in enumerate(selected_requests_list) if unassigned_selected_requests_selection[k]}
        for room in unfilled_rooms:  # Empty the half-filled rooms
            if room.students:
                evicted_students = room.students
                room.students = []
                for student in evicted_students:
                    unassigned_selected_requests_dictionary[student] = selected_requests_list[requests_id_to_idx[student]]
        for request in unassigned_selected_requests_dictionary.values():
            if request.has_mate and not str(request.mate_id) in unassigned_selected_requests_dictionary.keys():
                request.has_mate = False
                request.mate_id = None

        constraint_less_attributions = milp_solve(list(unassigned_selected_requests_dictionary.values()), unfilled_rooms, constraints=False)
        attributions += constraint_less_attributions

    return compute_score_no_penalisation(attributions, selected_requests_dictonary)


if __name__ == "__main__":
    instance = "medium"
    # instance = "real"

    print("Loading attributions...")
    rooms_file, requests_file = params.files[instance]
    # rooms_file, requests_file = "db/chambre.json", "db/eleves_demande.json"
    attributions = load_attributions(rooms_file, requests_file, instance)

    print("Loading requests and rooms [", instance, "] ...")
    requests = json_to_objects_requests(requests_file)
    rooms = json_to_objects_rooms(rooms_file)

    print("upper bound :", get_upper_bound_with_milp(requests, rooms))
