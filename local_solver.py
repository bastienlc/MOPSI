import params
from params import parameters
from copy import deepcopy
import random
from objects import Attribution
import bisect


def dictionary_from_requests(requests):
    requests_dictionary = {}
    for request in requests:
        requests_dictionary[str(request.student_id)] = request
    return requests_dictionary


def list_of_students_without_room(attributions, number_of_requests):  # assumes attributions is sorted according to attribution.request.student_id
    results = []
    last_seen = 0  # demands start at id 1
    for attribution in attributions:
        if attribution.request.student_id != last_seen + 1:
            results += [i for i in range(last_seen+1, attribution.request.student_id)]
        last_seen = attribution.request.student_id
    results += [i for i in range(last_seen+1, number_of_requests+1)]
    return results


def insert_attribution(attributions, attribution):
    a = 0
    b = len(attributions) - 1
    while a <= b:
        m = (a + b) // 2
        if attributions[m] == attribution:
            return attributions
        elif attributions[m].request.student_id < attribution.request.student_id:
            a = m + 1
        else:
            b = m - 1
    attributions.insert(a, attribution)
    return attributions


def compute_score(attributions, requests_dictionary):
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

    for attribution in attributions:  # too complex
        if attribution.request.student_id == attribution_1.mate:
            attribution.mate = attribution_2.request.student_id
        if attribution.request.student_id == attribution_2.mate:
            attribution.mate = attribution_1.request.student_id

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

    for attribution in attributions:  # too complex
        if attribution.request.student_id == attribution_2.mate:
            attribution.mate = attribution_1.request.student_id

    attribution_1.room, attribution_1.mate, attribution_2.room, attribution_2.mate = attribution_2.room, attribution_2.mate, attribution_1.room, None
    return attributions


def switch_student_not_chosen_and_student_chosen(attributions, requests_dictionary):
    attribution_1 = None
    for k, attribution in enumerate(attributions):
        if attribution_1 is None:
            if random.randint(k, len(attributions)) / len(attributions) > 0.5:  # randomization
                attribution_1 = attribution
        else:
            break

    if attribution_1 is None:
        return attributions

    students_without_room = list_of_students_without_room(attributions, len(requests_dictionary))
    if len(students_without_room) == 0:
        return attributions

    student_to_add = random.choice(students_without_room)

    new_attribution = Attribution(requests_dictionary[str(student_to_add)], attribution_1.room, attribution_1.mate)
    attributions = insert_attribution(attributions, new_attribution)  # to keep attributions sorted

    if attribution_1.mate is not None:
        for attribution in attributions:  # too complex, use a dictionary for attributions too
            if attribution.request.student_id == attribution_1.mate:
                attribution.mate = student_to_add
    attributions.remove(attribution_1)

    return attributions


def add_student_in_room_not_full(attributions, requests_dictionary):
    return attributions


def local_changes(attributions, requests_dictionary):
    random_number = random.randint(0, 2)
    if random_number == 0:
        return switch_students_in_double_rooms(attributions)
    elif random_number == 1:
        return switch_student_in_simple_room_and_student_in_double_room(attributions)
    else:
        return switch_student_not_chosen_and_student_chosen(attributions, requests_dictionary)


def local_solver(attributions, requests_dictionary, rooms, N):
    score = compute_score(attributions, requests_dictionary)
    for k in range(N):
        temp_attributions = local_changes(deepcopy(attributions), requests_dictionary)
        temp_score = compute_score(temp_attributions, requests_dictionary)
        if temp_score > score:
            score = temp_score
            attributions = temp_attributions
        if k % 10 == 0:
            print("LocalSolver score : ", score)
    return attributions


if __name__ == "__main__":
    print("Done")
