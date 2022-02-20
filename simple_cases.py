from objects import Request, Room, Attribution
from data_conversion import *
import params


def sort_requests_by_absolute_score(requests):
    requests.sort(reverse=True, key=lambda request: (
            request.get_absolute_score()
            + params.parameters["room_preference_bonus_parameter"]*(request.prefered_room_type == 0)
            - params.parameters["room_preference_malus_parameter"]*(
                    1 - (request.prefered_room_type == 0))*(1 - request.accept_other_type)
    ))
    return requests


def simple_rooms_only(requests, rooms):
    requests = sort_requests_by_absolute_score(requests)
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
    write_solutions(attributions, requests, rooms, "simple-rooms-only")


def double_room_pair_score(request_1, request_2):
    request_1_score = (
            request_1.get_absolute_score()
            + params.parameters["room_preference_bonus_parameter"]*(request_1.prefered_room_type == 2)
            - params.parameters["room_preference_malus_parameter"]*(
                    1 - (request_1.prefered_room_type == 2))*(1 - request_1.accept_other_type)
    )
    request_2_score = (
            request_2.get_absolute_score()
            + params.parameters["room_preference_bonus_parameter"]*(request_2.prefered_room_type == 2)
            - params.parameters["room_preference_malus_parameter"]*(
                    1 - (request_1.prefered_room_type == 2))*(1 - request_2.accept_other_type)
    )
    friendship = (request_1.mate_id==request_2.student_id)
    gender_mix = request_1.gender and request_2.gender and (request_1.gender!=request_2.gender)
    interaction_score = (
            params.parameters["buddy_preference_parameter"]*friendship
            - params.parameters["gender_mix_parameter"]*gender_mix
    )
    return request_1_score + request_2_score + interaction_score


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
            score = double_room_pair_score(*pair)
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
    write_solutions(attributions, requests, rooms, "double-rooms-only")


def find_gender_heterogeneous_buddy_pair(buddy_pairs):
    heterogeneous_genders = [(-1, 1), (1, -1), (-1, 0), (0, -1), (1, 0), (0, 1), (0, 0)]
    heterogeneous_pair = None
    for pair in buddy_pairs:
        request_1, request_2 = pair
        if (request_1.gender, request_2.gender) in heterogeneous_genders:
            heterogeneous_pair = pair
            break
    return heterogeneous_pair


def find_buddy_and_put_back_in_gender_list(request, buddy_pairs, selected_males, selected_females, selected_neutrals):
    for pair_idx in range(len(buddy_pairs)):
        (roommate_1, roommate_2) = buddy_pairs[pair_idx]
        if roommate_1 == request:
            del buddy_pairs[pair_idx]
            if roommate_2.gender == -1:
                selected_males.append(roommate_2)
            elif roommate_2.gender == 1:
                selected_females.append(roommate_2)
            else:
                selected_neutrals.append(roommate_2)
        elif roommate_2 == request:
            del buddy_pairs[pair_idx]
            if roommate_1.gender == -1:
                selected_males.append(roommate_1)
            elif roommate_1.gender == 1:
                selected_females.append(roommate_1)
            else:
                selected_neutrals.append(roommate_1)
    return buddy_pairs, selected_males, selected_females, selected_neutrals


def double_rooms_only(requests, rooms):
    attributions = []
    requests = [request for request in requests if request.accept_other_type or request.prefered_room_type==2]
    requests = sort_requests_by_absolute_score(requests)
    total_capacity = sum([room.capacity for room in rooms])
    selected_requests, failed_requests = requests[:total_capacity], requests[total_capacity:]
    id_to_idx = {selected_requests[k].student_id: k for k in range(total_capacity)}

    # Build buddy-pairs and male, female and non-gender-speicified ("neutral") sets
    buddy_pairs = []
    selected_males = []
    selected_females = []
    selected_neutrals = []
    classified_requests = {request: False for request in selected_requests}
    for request in selected_requests:
        if not classified_requests[request]:
            buddy_id = request.mate_id
            if request.has_mate and id_to_idx[buddy_id] < total_capacity:
            # If the request has a buddy that has been selected, put them in a pair
                buddy = selected_requests[id_to_idx[buddy_id]]
                buddy_pairs.append((request, buddy))
                classified_requests[buddy] = True
            else:
                if request.gender == -1:
                    selected_males.append(request)
                elif request.gender == 1:
                    selected_females.append(request)
                else:
                    selected_neutrals.append(request)
        classified_requests[request] = True

        # Detect and handle gender-conflicting cases
        gender_conflicting_case = False
        unsolvabe_conflict = False  # True if nothing can be done to avoid gender_conflict but leaving a room unfilled
        if len(selected_females) % 2 == 1:
            if not selected_neutrals:
                gender_conflicting_case = not find_gender_heterogeneous_buddy_pair(buddy_pairs)
        if gender_conflicting_case:  # Then handle conflict
            f_o = None
            h_n = None
            h_n_buddy = None
            f_o_gap = None
            if selected_females:
                f_o = selected_females[-1]
            if f_o:
                buddy_pairs, selected_males, selected_females, selected_neutrals = \
                    find_buddy_and_put_back_in_gender_list(f_o, buddy_pairs, selected_males, selected_females,
                                                           selected_neutrals)
                for failed_request in failed_requests:
                    if failed_request.gender in [-1, 0]:
                        h_n = failed_request
                    elif failed_request.has_mate:
                        mate_id = failed_request.mate_id
                        if mate_id in id_to_idx.keys():
                            mate = selected_requests[id_to_idx[mate_id]]
                            if mate.gender in [-1, 0]:
                                h_n = failed_request
                                h_n_buddy = mate
                f_o_gap = f_o.absolute_score() - h_n.absolute_score()
            h_o = None
            f_n = None
            f_n_buddy = None
            h_o_gap = None
            if selected_females:
                h_o = selected_males[-1]
            if h_o:
                buddy_pairs, selected_males, selected_females, selected_neutrals = \
                    find_buddy_and_put_back_in_gender_list(f_o, buddy_pairs, selected_males, selected_females,
                                                           selected_neutrals)
                for failed_request in failed_requests:
                    if failed_request.gender in [1, 0]:
                        f_n = failed_request
                    elif failed_request.has_mate:
                        mate_id = failed_request.mate_id
                        if mate_id in id_to_idx.keys():
                            mate = selected_requests[id_to_idx[mate_id]]
                            if mate.gender in [1, 0]:
                                f_n = failed_request
                                f_n_buddy = mate
                h_o_gap = h_o.absolute_score() - f_n.absolute_score()
            operate = None
            if f_o and h_o:
                if f_o_gap > h_o_gap:
                    operate = "h_o"
                else:
                    operate = "f_o"
            elif f_o:
                operate = "f_o"
            elif h_o:
                operate = "h_o"
            else:
                unsolvabe_conflict = True
            if operate == "f_o":






if __name__ == "__main__":
    requests = json_to_objects_requests("simple_cases_instances/double-rooms-only_requests.json")
    rooms = json_to_objects_rooms("simple_cases_instances/double-rooms-only_rooms.json")
    double_rooms_only_inexact(requests, rooms)
