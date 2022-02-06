import params
from params import parameters


def compute_score(attributions, requests, rooms):
    score = 0
    for attribution in attributions:
        score += 1
        score += parameters["room_preference_bonus_parameter"]*(attribution.request.prefered_room_type == attribution.room.room_type)
        score -= parameters["room_preference_malus_parameter"]*(attribution.request.prefered_room_type != attribution.room.room_type)*(1-attribution.request.accept_other_type)
        if attribution.mate is not None:
            for request in requests:  # use a dict for the requests
                if request.student_id == attribution.mate:
                    mate_request = request
            score -= parameters["gender_mix_parameter"]*(1-attribution.request.has_mate)*abs(attribution.request.gender*mate_request.gender*(attribution.request.gender-mate_request.gender))/2
            if request.has_mate:
                score += parameters["buddy_preference_parameter"]*(attribution.request.mate_id == mate_request.student_id)/2
        score += parameters["grant_parameter"]*attribution.request.scholarship
        if attribution.request.distance > params.paris_threshold:
            score += parameters["distance_parameter"]
        if attribution.request.distance > params.foreign_threshold:
            score += parameters["foreign_parameter"]
        score -= parameters["shotgun_parameter"]*attribution.request.distance
    return score


def local_changes(attributions):
    return attributions  # Do local changes here


def local_solver(attributions, requests, rooms, N):
    score = compute_score(attributions, requests, rooms)
    for k in range(N):
        temp_attributions = local_changes(attributions)
        temp_score = compute_score(temp_attributions, requests, rooms)
        if temp_score < score:
            score = temp_score
            attributions = temp_attributions
        print("LocalSolver score : ", score)
    return attributions

if __name__ == "__main__":
    print("Done")
