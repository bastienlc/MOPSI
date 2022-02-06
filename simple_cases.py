from objects import Request, Room, Attribution
from data_conversion import *
import params


def simple_rooms_only(requests, rooms):
    requests.sort(reverse=True, key=lambda request: (
            request.get_absolute_score()
            + params.parameters["room_preference_bonus_parameter"]*(request.prefered_room_type == 0)
            - params.parameters["room_preference_malus_parameter"]*(
                    1 - (request.prefered_room_type == 0))*(1 - request.accept_other_type)
    ))
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
    for room in rooms:
        pairs = []
        for i1 in range(nb_requests):
            if processed_requests[requests[i1]]:
                break
            for i2 in range(i1+1, nb_requests):
                if processed_requests[requests[i2]]:
                    break
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


if __name__ == "__main__":
    requests = json_to_objects_requests("simple_cases_instances/double-rooms-only_requests.json")
    rooms = json_to_objects_rooms("simple_cases_instances/double-rooms-only_rooms.json")
    double_rooms_only_inexact(requests, rooms)
