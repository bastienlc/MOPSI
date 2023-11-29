import math
import random
from copy import deepcopy

import params
from objects import Attribution
from params import parameters


def list_of_students_without_room(attributions, requests_dictionary):
    requests_list = list(requests_dictionary.values())
    id_to_idx = {request.student_id: idx for idx, request in enumerate(requests_list)}
    has_room = [False for _ in range(len(requests_list))]
    for attribution in attributions:
        has_room[id_to_idx[attribution.request.student_id]] = True
    results = []
    for i, request in enumerate(requests_list):
        if not has_room[i]:
            results.append(request.student_id)
    return results


def list_of_rooms_not_full(attributions, rooms_dictionary):
    rooms_capacities = {}
    for id, room in rooms_dictionary.items():
        rooms_capacities[str(room.room_id)] = room.capacity
    for attribution in attributions:
        rooms_capacities[str(attribution.room.room_id)] -= 1
    results = []
    for room_id, capacity_left in rooms_capacities.items():
        if capacity_left > 0:
            results.append(int(room_id))
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
        if (
            attribution.request.prefered_room_type != attribution.room.room_type
            and not attribution.request.accept_other_type
        ):
            score -= parameters["room_preference_malus_parameter"]
        if attribution.mate is not None:
            mate_request = requests_dictionary[str(attribution.mate)]
            if (
                not attribution.request.has_mate
                and attribution.request.gender != mate_request.gender
            ):
                if attribution.request.gender != 0 and mate_request.gender != 0:
                    score -= (
                        parameters["gender_mix_parameter"] / 2
                    )  # every pair is seen twice
            if (
                attribution.request.has_mate
                and attribution.request.mate_id == mate_request.student_id
            ):
                score += (
                    parameters["buddy_preference_parameter"] / 2
                )  # every pair is seen twice
        if attribution.request.scholarship:
            score += parameters["grant_parameter"]
        if attribution.request.distance > params.paris_threshold:
            score += parameters["distance_parameter"]
        if attribution.request.distance > params.foreign_threshold:
            score += parameters["foreign_parameter"]
        score -= parameters["shotgun_parameter"] * attribution.request.shotgun_rank
    return score


def compute_score_no_penalisation(attributions, requests_dictionary):
    score = 0
    for attribution in attributions:
        score += 1
        if attribution.request.prefered_room_type == attribution.room.room_type:
            score += parameters["room_preference_bonus_parameter"]
        if attribution.mate is not None:
            mate_request = requests_dictionary[str(attribution.mate)]
            if (
                attribution.request.has_mate
                and attribution.request.mate_id == mate_request.student_id
            ):
                score += (
                    parameters["buddy_preference_parameter"] / 2
                )  # every pair is seen twice
        if attribution.request.scholarship:
            score += parameters["grant_parameter"]
        if attribution.request.distance > params.paris_threshold:
            score += parameters["distance_parameter"]
        if attribution.request.distance > params.foreign_threshold:
            score += parameters["foreign_parameter"]
        score -= parameters["shotgun_parameter"] * attribution.request.shotgun_rank
    return score


def switch_students_in_double_rooms(attributions):
    attribution_1 = None
    attribution_2 = None
    for k, attribution in enumerate(attributions):
        if attribution.room.capacity == 2:
            if attribution_1 is None:
                if (
                    random.randint(k, len(attributions)) / len(attributions) > 0.5
                ):  # randomization
                    attribution_1 = attribution
            elif attribution_2 is None:
                if (
                    random.randint(k, len(attributions)) / len(attributions) > 0.5
                ):  # randomization
                    attribution_2 = attribution
            else:
                break

    if attribution_2 is None:
        return attributions

    if attribution_1.mate != attribution_2.request.student_id:
        for attribution in attributions:  # too complex
            if attribution.request.student_id == attribution_1.mate:
                attribution.mate = attribution_2.request.student_id
            if attribution.request.student_id == attribution_2.mate:
                attribution.mate = attribution_1.request.student_id
        (
            attribution_1.room,
            attribution_1.mate,
            attribution_2.room,
            attribution_2.mate,
        ) = (
            attribution_2.room,
            attribution_2.mate,
            attribution_1.room,
            attribution_1.mate,
        )

    return attributions


def switch_student_in_simple_room_and_student_in_double_room(attributions):
    attribution_1 = None
    attribution_2 = None
    for k, attribution in enumerate(attributions):
        if attribution.room.capacity == 1:
            if attribution_1 is None:
                if (
                    random.randint(k, len(attributions)) / len(attributions) > 0.5
                ):  # randomization
                    attribution_1 = attribution
            if attribution_1 is not None and attribution_2 is not None:
                break
        elif attribution.room.capacity == 2:
            if attribution_2 is None:
                if (
                    random.randint(k, len(attributions)) / len(attributions) > 0.5
                ):  # randomization
                    attribution_2 = attribution
            if attribution_1 is not None and attribution_2 is not None:
                break

    if attribution_1 is None or attribution_2 is None:
        return attributions

    for attribution in attributions:  # too complex
        if attribution.request.student_id == attribution_2.mate:
            attribution.mate = attribution_1.request.student_id

    attribution_1.room, attribution_1.mate, attribution_2.room, attribution_2.mate = (
        attribution_2.room,
        attribution_2.mate,
        attribution_1.room,
        None,
    )
    return attributions


def switch_student_not_chosen_and_student_chosen(attributions, requests_dictionary):
    attribution_1 = None
    for k, attribution in enumerate(attributions):
        if attribution_1 is None:
            if (
                random.randint(k, len(attributions)) / len(attributions) > 0.5
            ):  # randomization
                attribution_1 = attribution
        else:
            break

    if attribution_1 is None:
        return attributions

    students_without_room = list_of_students_without_room(
        attributions, requests_dictionary
    )
    if len(students_without_room) == 0:
        return attributions
    student_to_add = random.choice(students_without_room)

    new_attribution = Attribution(
        requests_dictionary[str(student_to_add)], attribution_1.room, attribution_1.mate
    )
    attributions = insert_attribution(
        attributions, new_attribution
    )  # to keep attributions sorted

    if attribution_1.mate is not None:
        for (
            attribution
        ) in attributions:  # too complex, use a dictionary for attributions too
            if attribution.request.student_id == attribution_1.mate:
                attribution.mate = student_to_add
    attributions.remove(attribution_1)

    return attributions


def add_student_in_room_not_full(attributions, requests_dictionary, rooms_dictionary):
    rooms_not_full = list_of_rooms_not_full(attributions, rooms_dictionary)
    if len(rooms_not_full) == 0:
        return attributions
    room_not_full = random.choice(rooms_not_full)

    students_without_room = list_of_students_without_room(
        attributions, requests_dictionary
    )
    if len(students_without_room) == 0:
        return attributions
    student_to_add = random.choice(students_without_room)

    mate = None
    for attribution in attributions:
        if attribution.room.room_id == room_not_full:
            mate = attribution.request.student_id
            attribution.mate = student_to_add

    new_attribution = Attribution(
        requests_dictionary[str(student_to_add)],
        rooms_dictionary[str(room_not_full)],
        mate,
    )
    attributions = insert_attribution(
        attributions, new_attribution
    )  # to keep attributions sorted

    return attributions


def remove_attribution(attributions):
    if len(attributions) == 0:
        return attributions
    attribution_to_remove = random.choice(attributions)
    if attribution_to_remove.mate is not None:
        for attribution in attributions:
            if attribution.request.student_id == attribution_to_remove.mate:
                attribution.mate = None
    attributions.remove(attribution_to_remove)
    return attributions


def local_changes(attributions, requests_dictionary, rooms_dictionary):
    random_number = random.randint(0, 4)
    if random_number == 0:
        return switch_students_in_double_rooms(attributions)
    elif random_number == 1:
        return switch_student_in_simple_room_and_student_in_double_room(attributions)
    elif random_number == 2:
        return switch_student_not_chosen_and_student_chosen(
            attributions, requests_dictionary
        )
    elif random_number == 3:
        return add_student_in_room_not_full(
            attributions, requests_dictionary, rooms_dictionary
        )
    else:
        return remove_attribution(attributions)


def local_solver(
    attributions, requests_dictionary, rooms_dictionary, n, T=0.01, alpha=0.9999
):
    score = compute_score(attributions, requests_dictionary)
    best_score = score
    best_attributions = deepcopy(attributions)
    iterations_without_increase = 0
    k = 0
    while k < n and T > 1e-5:
        k += 1
        temp_attributions = local_changes(
            deepcopy(attributions), requests_dictionary, rooms_dictionary
        )
        temp_score = compute_score(temp_attributions, requests_dictionary)
        if temp_score > score:
            score = temp_score
            attributions = temp_attributions
            T *= alpha
        else:
            iterations_without_increase += 1
            if (
                random.random() < math.exp((temp_score - score) / T)
                and (best_score - temp_score) / best_score < T
            ):
                score = temp_score
                attributions = temp_attributions
            if iterations_without_increase == 10:
                T /= alpha
                iterations_without_increase = 0
        if score > best_score:
            best_score = score
            best_attributions = deepcopy(attributions)
        if k % (n // 100) == 0:
            print("LocalSolver score : ", score, " ------ Température : ", T)
    return best_attributions
