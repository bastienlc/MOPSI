from objects import Request, Room, Attribution
import time
from local_solver import compute_score_no_penalisation
from milp import milp_solve
from data_conversion import *
import sys
import itertools
import params


def get_semi_absolute_score(request, room_type):
    return (request.get_absolute_score()
            + params.parameters["room_preference_bonus_parameter"]*(request.prefered_room_type == room_type)
            - params.parameters["room_preference_malus_parameter"]*(
            1 - (request.prefered_room_type == room_type))*(1 - request.accept_other_type))


def get_pair_score(pair, room_type):
    request_1, request_2 = pair
    request_1_score = get_semi_absolute_score(request_1, room_type)
    request_2_score = get_semi_absolute_score(request_2, room_type)
    friendship = (request_1.has_mate and request_2.has_mate and request_1.mate_id==request_2.student_id)
    gender_mix = request_1.gender and request_2.gender and (request_1.gender!=request_2.gender)
    interaction_score = (
            params.parameters["buddy_preference_parameter"]*friendship
            - params.parameters["gender_mix_parameter"]*gender_mix*(1-friendship)
    )
    return request_1_score + request_2_score + interaction_score


def simple_rooms_only(requests, rooms):
    requests.sort(reverse=True, key=lambda request: get_semi_absolute_score(request, 0))
    for request in requests:
        print(request.student_id)
        print(request.get_absolute_score()
            + params.parameters["room_preference_bonus_parameter"]*(request.prefered_room_type == 0)
            - params.parameters["room_preference_malus_parameter"]*(
                    1 - (request.prefered_room_type == 0))*(1 - request.accept_other_type))
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
            for i2 in range(i1+1, nb_requests):
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
        attributions.append(Attribution(selected_pair_and_score[0][0], room, selected_pair_and_score[0][1].student_id))
        attributions.append(Attribution(selected_pair_and_score[0][1], room, selected_pair_and_score[0][0].student_id))
        processed_requests[selected_pair_and_score[0][0]] = True
        processed_requests[selected_pair_and_score[0][1]] = True
    return attributions


def double_rooms_only_exact(requests, rooms, return_raw=False):
    """ It is assumed that the total capacity is greater than the number of requests with vaid preference """
    valid_requests = [request for request in requests if request.accept_other_type or request.prefered_room_type==2]
    attributions = []
    solution = []
    value = -sys.maxsize
    total_capacity = 2*len(rooms)
    for selected_requests in itertools.combinations(valid_requests, total_capacity):
        selection_solution, selection_value = allocate_selected_students_in_rooms(list(selected_requests))
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
            for i_2 in range(i_1+1, len(students)):
                student_1 = students[i_1]
                student_2 = students[i_2]
                friendship = (student_1.has_mate and student_2.has_mate and student_1.mate_id == student_2.student_id)
                gender_conflict = ((student_1.gender, student_2.gender) in ((-1, 1), (1, -1))
                                   and not friendship)
                if not gender_conflict:
                    new_students = students.copy()
                    del new_students[i_1]
                    del new_students[i_2-1]
                    new_solution_rec = solution_rec.copy()
                    new_solution_rec.append((student_1, student_2))
                    partition_recursion(
                        new_students, new_solution_rec, value_rec + get_pair_score((student_1, student_2), 2)
                    )

    partition_recursion(selected_requests, [], 0)
    return selection_solution, selection_value


# To be tested and fixed if deemed useful :

# def find_gender_heterogeneous_buddy_pair_idx(buddy_pairs):
#     heterogeneous_genders = [(-1, 1), (1, -1), (-1, 0), (0, -1), (1, 0), (0, 1), (0, 0)]
#     buddy_pair_idx = None
#     for pair_idx in range(len(buddy_pairs)):
#         request_1, request_2 = buddy_pairs[pair_idx]
#         if (request_1.gender, request_2.gender) in heterogeneous_genders:
#             buddy_pair_idx = pair_idx
#             break
#     return buddy_pair_idx
#
#
# def find_buddy_and_pair_idx(request, buddy_pairs):
#     buddy = None
#     buddy_pair_idx = None
#     for pair_idx in range(len(buddy_pairs)):
#         (roommate_1, roommate_2) = buddy_pairs[pair_idx]
#         if roommate_1 == request:
#             buddy = roommate_2
#             buddy_pair_idx = pair_idx
#         elif roommate_2 == request:
#             buddy = roommate_1
#             buddy_pair_idx = pair_idx
#     return buddy, buddy_pair_idx
#
#
# def double_rooms_only(requests, rooms):
#     """ It is assumed that the number of requests with valid preference > total_capacity """
#     attributions = []
#     requests = [request for request in requests if request.accept_other_type or request.prefered_room_type==2]
#     requests.sort(reverse=True, key=lambda request: get_semi_absolute_score(request, 2))
#     total_capacity = sum([room.capacity for room in rooms])
#     selected_requests, failed_requests = requests[:total_capacity], requests[total_capacity:]
#     id_to_idx = {selected_requests[k].student_id: k for k in range(total_capacity)}
#
#     # Build buddy-pairs and male, female and non-gender-speicified ("neutral") sets
#     buddy_pairs = []
#     selected_males = []
#     selected_females = []
#     selected_neutrals = []
#     classified_requests = {request: False for request in selected_requests}
#     for request in selected_requests:
#         if not classified_requests[request]:
#             buddy_id = request.mate_id
#             if request.has_mate and id_to_idx[buddy_id] < total_capacity:
#             # If the request has a buddy that has been selected, put them in a pair
#                 buddy = selected_requests[id_to_idx[buddy_id]]
#                 buddy_pairs.append((request, buddy))
#                 classified_requests[buddy] = True
#             else:
#                 if request.gender == -1:
#                     selected_males.append(request)
#                 elif request.gender == 1:
#                     selected_females.append(request)
#                 else:
#                     selected_neutrals.append(request)
#         classified_requests[request] = True
#
#     # Detect and handle gender-conflicting cases
#     gender_conflicting_case = False
#     if len(selected_females) % 2 == 1:
#         if not selected_neutrals:
#             gender_conflicting_case = (find_gender_heterogeneous_buddy_pair_idx(buddy_pairs) is None)
#     if gender_conflicting_case:  # Then handle conflict
#         # Fetch worst selected requests and their buddy
#         f_o = None
#         h_o = None
#         f_o_buddy = None
#         f_o_pair_idx = None
#         h_o_buddy = None
#         h_o_pair_idx = None
#         for idx in range(total_capacity):
#             request = selected_requests[-idx]
#             if request.gender == 1:
#                 f_o = request
#                 if request.has_mate:
#                     f_o_buddy, f_o_pair_idx = find_buddy_and_pair_idx(f_o, buddy_pairs)
#                 break
#         for idx in range(total_capacity):
#             request = selected_requests[-idx]
#             if request.gender == -1:
#                 h_o = request
#                 if request.has_mate:
#                     h_o_buddy, h_o_pair_idx = find_buddy_and_pair_idx(h_o, buddy_pairs)
#                 break
#         # Get best failed requests
#         f_n = None
#         h_n = None
#         for request in failed_requests:
#             if request.gender == 1:
#                 f_n = request
#                 break
#         for request in failed_requests:
#             if request.gender == 1:
#                 h_n = request
#                 break
#         # Decide what change to make, if any
#         replaced_gender = None
#         f_o_score = get_semi_absolute_score(f_o, 2)
#         h_o_score = get_semi_absolute_score(h_o, 2)
#         if f_n and h_n:
#             h_n_score = get_semi_absolute_score(h_n, 2)
#             f_n_score = get_semi_absolute_score(f_n, 2)
#             f_to_h_gap = f_o_score - h_n_score
#             h_to_f_gap = h_o_score - f_n_score
#             if f_to_h_gap > h_to_f_gap:
#                 replaced_gender = -1
#             else:
#                 replaced_gender = 1
#         elif h_n:
#             replaced_gender = -1
#         elif f_n:
#             replaced_gender = 1
#
#         # Make the change
#         if replaced_gender == -1:
#             # Remove h_o and put back h_o_buddy into gender lists if necessary
#             if h_o_pair_idx:
#                 del buddy_pairs[h_o_pair_idx]
#                 selected_males.append(h_o_buddy)
#             else :
#                 del selected_males[-1]
#             # Add f_n. Begin by looking for an eventual selected buddy.
#             f_n_paired = None
#             if f_n.has_mate():
#                 for male_idx in range(len(selected_males)):
#                     male = selected_males[male_idx]
#                     if male.student_id == f_n.mate_id:
#                         del selected_males[male_idx]
#                         buddy_pairs.append((male, f_n))
#                         f_n_paired = True
#                         break
#             if not f_n_paired:
#                 selected_females.append(f_n)
#         elif replaced_gender == 1:
#             # Remove f_o and put back f_o_buddy into gender lists if necessary
#             if f_o_pair_idx:
#                 del buddy_pairs[f_o_pair_idx]
#                 selected_females.append(f_o_buddy)
#             else :
#                 del selected_females[-1]
#             # Add h_n. Begin by looking for an eventual selected buddy.
#             h_n_paired = None
#             if h_n.has_mate():
#                 for female_idx in range(len(selected_females)):
#                     female = selected_females[female_idx]
#                     if female.student_id == h_n.mate_id:
#                         del selected_females[female_idx]
#                         buddy_pairs.append((female, h_n))
#                         h_n_paired = True
#                         break
#             if not h_n_paired:
#                 selected_males.append(h_n)
#         else:
#             if f_o_score < h_o_score:
#                 if f_o_pair_idx:
#                     del buddy_pairs[f_o_pair_idx]
#                     selected_females.append(f_o_buddy)
#                 else:
#                     del selected_females[-1]
#                 room = rooms.pop()
#                 attributions.append(Attribution(h_o, room))
#             else:
#                 if h_o_pair_idx:
#                     del buddy_pairs[h_o_pair_idx]
#                     selected_males.append(h_o_buddy)
#                 else:
#                     del selected_males[-1]
#                 room = rooms.pop()
#                 attributions.append(Attribution(f_o, room))
#
#     # Build attributions
#     # Fill with females
#     if len(selected_females) % 2 == 1:
#         if selected_neutrals:
#             neutral = selected_neutrals.pop()
#             female = selected_females.pop()
#             room = rooms.pop()
#             attributions.append(Attribution(female, room, neutral.student_id))
#             attributions.append(Attribution(neutral, room, female.student_id))
#         elif not gender_conflicting_case:  # Meaning that there is an heterogeneous buddy pair
#             female = selected_females.pop()
#             male = selected_males.pop()  # Necessarily not empty at this point
#             buddy_pair_idx = find_gender_heterogeneous_buddy_pair_idx(buddy_pairs)
#             roommate_1, roommate_2 = buddy_pairs[buddy_pair_idx]
#             del buddy_pairs[buddy_pair_idx]
#             room = rooms.pop()
#             if roommate_1.gender == 1:
#                 attributions.append(Attribution(female, room, roommate_1.student_id))
#                 attributions.append(Attribution(roommate_1, room, female.student_id))
#                 attributions.append(Attribution(male, room, roommate_2.student_id))
#                 attributions.append(Attribution(roommate_2, room, male.student_id))
#             else:
#                 attributions.append(Attribution(male, room, roommate_1.student_id))
#                 attributions.append(Attribution(roommate_1, room, male.student_id))
#                 attributions.append(Attribution(female, room, roommate_2.student_id))
#                 attributions.append(Attribution(roommate_2, room, female.student_id))
#     while selected_females:
#         female_1 = selected_females.pop()
#         female_2 = selected_females.pop()
#         room = rooms.pop()
#         attributions.append(Attribution(female_1, room, female_2.student_id))
#         attributions.append(Attribution(female_2, room, female_1.student_id))
#     # Fill with males
#     if len(selected_males) % 2 == 1:
#         if selected_neutrals:
#             neutral = selected_neutrals.pop()
#             male = selected_males.pop()
#             room = rooms.pop()
#             attributions.append(Attribution(male, room, neutral.student_id))
#             attributions.append(Attribution(neutral, room, male.student_id))
#     while selected_males:
#         male_1 = selected_males.pop()
#         male_2 = selected_males.pop()
#         room = rooms.pop()
#         attributions.append(Attribution(male_1, room, male_2.student_id))
#         attributions.append(Attribution(male_2, room, male_1.student_id))
#     # Fill with buddy pairs
#     while buddy_pairs:
#         roommate_1, roommate_2 = buddy_pairs.pop()
#         room = rooms.pop()
#         attributions.append(Attribution(roommate_1, room, roommate_2.student_id))
#         attributions.append(Attribution(roommate_2, room, roommate_1.student_id))
#
#     return attributions


def many_double_one_simple_rooms(requests, rooms):
    valid_requests = [request for request in requests if request.accept_other_type or request.prefered_room_type != 1]
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
        if simple_room_candidate.accept_other_type or simple_room_candidate.prefered_room_type == 0:
            single_score = get_semi_absolute_score(simple_room_candidate, 0)
            leftover_requests = valid_requests.copy()
            del leftover_requests[i]
            solution_step, value_step = double_rooms_only_exact(leftover_requests, double_rooms, return_raw=True)
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
    requests = json_to_objects_requests(f"simple_cases_instances/{simple_case}/{simple_case}_test_{test_case}_requests.json")
    requests_dictionary = {str(request.student_id): request for request in requests}
    rooms = json_to_objects_rooms(f"simple_cases_instances/{simple_case}/{simple_case}_test_{test_case}_rooms.json")
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
