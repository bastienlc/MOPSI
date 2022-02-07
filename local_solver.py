import params
from params import parameters
from copy import deepcopy
import random


def compute_score(attributions, requests_dictionary, rooms):
    score = 0
    for attribution in attributions:
        score += 1
        if attribution.request.prefered_room_type == attribution.room.room_type:
            score += parameters["room_preference_bonus_parameter"]
        if attribution.request.prefered_room_type != attribution.room.room_type and not attribution.request.accept_other_type:
            score -= parameters["room_preference_malus_parameter"]
        if attribution.mate is not None:
            mate_request = requests_dictionary[str(attribution.mate)]
            if not attribution.request.has_mate and attribution.request.gender != mate_request.gender:
                if attribution.request.gender != 0 and mate_request.gender != 0:
                    score -= parameters["gender_mix_parameter"]/2  # every pair is seen twice
            if attribution.request.has_mate and attribution.request.mate_id == mate_request.student_id:
                score += parameters["buddy_preference_parameter"]/2  # every pair is seen twice
        if attribution.request.scholarship:
            score += parameters["grant_parameter"]
        if attribution.request.distance > params.paris_threshold:
            score += parameters["distance_parameter"]
        if attribution.request.distance > params.foreign_threshold:
            score += parameters["foreign_parameter"]
        score -= parameters["shotgun_parameter"]*attribution.request.shotgun_rank
    return score


def switch_students_in_double_rooms(attributions):
    attribution_1 = None
    attribution_2 = None
    for k, attribution in enumerate(attributions):
        if attribution.room.capacity == 2:
            if attribution_1 is None:
                if random.randint(k, len(attributions))/len(attributions) > 0.5:  # randomization
                    attribution_1 = attribution
            elif attribution_2 is None:
                if random.randint(k, len(attributions)) / len(attributions) > 0.5:  # randomization
                    attribution_2 = attribution
            else:
                break

    if attribution_2 is None:
        return attributions

    attribution_1.room, attribution_1.mate, attribution_2.room, attribution_2.mate = attribution_2.room, attribution_2.mate, attribution_1.room, attribution_1.mate
    return attributions


def switch_student_in_simple_room_and_student_in_double_room(attributions):
    attribution_1 = None
    attribution_2 = None
    for k, attribution in enumerate(attributions):
        if attribution.room.capacity == 1:
            if attribution_1 is None:
                if random.randint(k, len(attributions)) / len(attributions) > 0.5:  # randomization
                    attribution_1 = attribution
            if attribution_1 is not None and attribution_2 is not None:
                break
        elif attribution.room.capacity == 2:
            if attribution_2 is None:
                if random.randint(k, len(attributions)) / len(attributions) > 0.5:  # randomization
                    attribution_2 = attribution
            if attribution_1 is not None and attribution_2 is not None:
                break

    if attribution_1 is None or attribution_2 is None:
        return attributions

    attribution_1.room, attribution_1.mate, attribution_2.room, attribution_2.mate = attribution_2.room, attribution_2.mate, attribution_1.room, None
    return attributions


def local_changes(attributions):
    if random.randint(0, 1) == 0:
        return switch_students_in_double_rooms(attributions)
    else:
        return switch_student_in_simple_room_and_student_in_double_room(attributions)


def local_solver(attributions, requests_dictionary, rooms, N):
    score = compute_score(attributions, requests_dictionary, rooms)
    for k in range(N):
        temp_attributions = local_changes(deepcopy(attributions))
        temp_score = compute_score(temp_attributions, requests_dictionary, rooms)
        if temp_score < score:
            score = temp_score
            attributions = temp_attributions
        if k % 10 == 0:
            print("LocalSolver score : ", score)
    return attributions


if __name__ == "__main__":
    print("Done")
