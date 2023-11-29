import itertools
import sys
import time

import params
from data_conversion import *
from local_solver import compute_score_no_penalisation
from milp import milp_solve
from objects import Attribution


def get_semi_absolute_score(request, room_type):
    return (
        request.get_absolute_score()
        + params.parameters["room_preference_bonus_parameter"]
        * (request.prefered_room_type == room_type)
        - params.parameters["room_preference_malus_parameter"]
        * (1 - (request.prefered_room_type == room_type))
        * (1 - request.accept_other_type)
    )


def get_pair_score(pair, room_type):
    request_1, request_2 = pair
    request_1_score = get_semi_absolute_score(request_1, room_type)
    request_2_score = get_semi_absolute_score(request_2, room_type)
    friendship = (
        request_1.has_mate
        and request_2.has_mate
        and request_1.mate_id == request_2.student_id
    )
    gender_mix = (
        request_1.gender and request_2.gender and (request_1.gender != request_2.gender)
    )
    interaction_score = params.parameters[
        "buddy_preference_parameter"
    ] * friendship - params.parameters["gender_mix_parameter"] * gender_mix * (
        1 - friendship
    )
    return request_1_score + request_2_score + interaction_score


def simple_rooms_only(requests, rooms):
    requests.sort(reverse=True, key=lambda request: get_semi_absolute_score(request, 0))
    for request in requests:
        print(request.student_id)
        print(
            request.get_absolute_score()
            + params.parameters["room_preference_bonus_parameter"]
            * (request.prefered_room_type == 0)
            - params.parameters["room_preference_malus_parameter"]
            * (1 - (request.prefered_room_type == 0))
            * (1 - request.accept_other_type)
        )
        print("")
    attributions = []
    for k, room in enumerate(rooms):
        attributions.append(Attribution(requests[k], room))
    return attributions


def double_rooms_only_inexact(requests, rooms):
    nb_requests = len(requests)
    processed_requests = {request: False for request in requests}
    attributions = []
    for room in rooms:  # Assumes there are more (or as many) requests than rooms
        pairs = []
        for i1 in range(nb_requests):
            if processed_requests[requests[i1]]:
                continue
            for i2 in range(i1 + 1, nb_requests):
                if processed_requests[requests[i2]]:
                    continue
                pairs.append((requests[i1], requests[i2]))
        pairs_scores = []
        for pair in pairs:
            score = get_pair_score(pair, 2)
            pairs_scores.append(score)
        pairs_and_scores = [(pairs[k], pairs_scores[k]) for k in range(len(pairs))]
        selected_pair_and_score = pairs_and_scores[0]
        for pair_and_score in pairs_and_scores:
            if pair_and_score[1] > selected_pair_and_score[1]:
                selected_pair_and_score = pair_and_score
        attributions.append(
            Attribution(
                selected_pair_and_score[0][0],
                room,
                selected_pair_and_score[0][1].student_id,
            )
        )
        attributions.append(
            Attribution(
                selected_pair_and_score[0][1],
                room,
                selected_pair_and_score[0][0].student_id,
            )
        )
        processed_requests[selected_pair_and_score[0][0]] = True
        processed_requests[selected_pair_and_score[0][1]] = True
    return attributions


def double_rooms_only_exact(requests, rooms, return_raw=False):
    """It is assumed that the total capacity is greater than the number of requests with vaid preference"""
    valid_requests = [
        request
        for request in requests
        if request.accept_other_type or request.prefered_room_type == 2
    ]
    attributions = []
    solution = []
    value = -sys.maxsize
    total_capacity = 2 * len(rooms)
    for selected_requests in itertools.combinations(valid_requests, total_capacity):
        selection_solution, selection_value = allocate_selected_students_in_rooms(
            list(selected_requests)
        )
        if selection_value > value:
            value = selection_value
            solution = selection_solution
    room_to_fill = 0
    for request_1, request_2 in solution:
        room = rooms[room_to_fill]
        attributions.append(Attribution(request_1, room, request_2.student_id))
        attributions.append(Attribution(request_2, room, request_1.student_id))
        room.students = [request_1.student_id, request_2.student_id]
        room_to_fill += 1
    if return_raw:
        return solution, value
    else:
        return attributions


def allocate_selected_students_in_rooms(selected_requests):
    selection_value = -sys.maxsize
    selection_solution = []

    def partition_recursion(students, solution_rec, value_rec):
        nonlocal selection_value
        nonlocal selection_solution
        if not students:
            if value_rec > selection_value:
                selection_value = value_rec
                selection_solution = solution_rec
        for i_1 in range(len(students)):
            for i_2 in range(i_1 + 1, len(students)):
                student_1 = students[i_1]
                student_2 = students[i_2]
                friendship = (
                    student_1.has_mate
                    and student_2.has_mate
                    and student_1.mate_id == student_2.student_id
                )
                gender_conflict = (student_1.gender, student_2.gender) in (
                    (-1, 1),
                    (1, -1),
                ) and not friendship
                if not gender_conflict:
                    new_students = students.copy()
                    del new_students[i_1]
                    del new_students[i_2 - 1]
                    new_solution_rec = solution_rec.copy()
                    new_solution_rec.append((student_1, student_2))
                    partition_recursion(
                        new_students,
                        new_solution_rec,
                        value_rec + get_pair_score((student_1, student_2), 2),
                    )

    partition_recursion(selected_requests, [], 0)
    return selection_solution, selection_value


def many_double_one_simple_rooms(requests, rooms):
    valid_requests = [
        request
        for request in requests
        if request.accept_other_type or request.prefered_room_type != 1
    ]
    attributions = []
    solution = []
    lonely_student = None
    value = -sys.maxsize
    double_rooms = rooms.copy()
    simple_room = None
    for i in range(len(double_rooms)):
        if double_rooms[i].room_type == 0:
            simple_room = double_rooms.pop(i)
            break
    for i in range(len(valid_requests)):
        simple_room_candidate = valid_requests[i]
        if (
            simple_room_candidate.accept_other_type
            or simple_room_candidate.prefered_room_type == 0
        ):
            single_score = get_semi_absolute_score(simple_room_candidate, 0)
            leftover_requests = valid_requests.copy()
            del leftover_requests[i]
            solution_step, value_step = double_rooms_only_exact(
                leftover_requests, double_rooms, return_raw=True
            )
            if value_step + single_score > value:
                value = value_step + single_score
                solution = solution_step
                lonely_student = simple_room_candidate
    room_to_fill = 0
    for request_1, request_2 in solution:
        room = rooms[room_to_fill]
        attributions.append(Attribution(request_1, room, request_2.student_id))
        attributions.append(Attribution(request_2, room, request_1.student_id))
        room.students = [request_1.student_id, request_2.student_id]
        room_to_fill += 1
    attributions.append(Attribution(lonely_student, simple_room))
    return attributions


def test_simple_case_and_compare_with_milp(simple_case, algorithm, test_case):
    """
    Tests a simple case algorithm on a given test case and compares the result with the one given by the MILP.
    :param simple_case: string naming the simple case to be tested
    :param algorithm: function implementing the algorithm to be tested
    :param test_case: number of the test case to be tested on
    :return: Nothing. Prints the gap between the values of the objective returned by the algorithm and the MILP.
    Prints the execution time difference between the algorithm and the MILP. Also, writes the solution in csv files.
    """
    requests = json_to_objects_requests(
        f"simple_cases_instances/{simple_case}/{simple_case}_test_{test_case}_requests.json"
    )
    requests_dictionary = {str(request.student_id): request for request in requests}
    rooms = json_to_objects_rooms(
        f"simple_cases_instances/{simple_case}/{simple_case}_test_{test_case}_rooms.json"
    )
    t0_algo = time.time()
    algo_attributions = algorithm(requests, rooms)
    time_algo = time.time() - t0_algo
    algo_score = compute_score_no_penalisation(algo_attributions, requests_dictionary)
    write_solutions(algo_attributions, requests, rooms, simple_case)
    t0_milp = time.time()
    milp_attributions = milp_solve(requests, rooms)
    time_milp = time.time() - t0_milp
    milp_score = compute_score_no_penalisation(milp_attributions, requests_dictionary)
    write_solutions(milp_attributions, requests, rooms, "test")
    print("objective gap :", algo_score - milp_score)
    print("time gap :", time_algo - time_milp)


if __name__ == "__main__":
    test_simple_case_and_compare_with_milp("simple-rooms-only", simple_rooms_only, 0)
