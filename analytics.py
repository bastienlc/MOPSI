import params
from data_conversion import load_attributions, json_to_objects_requests, json_to_objects_rooms
import operator
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as mlines


def distance_selection_ratio(attributions, requests_list, threshold):
    """
    With selected_ratio being the ratio of requests with distance>threshold among the selected requests
    and overall_ratio being the ratio of requests with distance>threshold among all the requests,
    computes selected_ratio/overall_ratio
    :param attributions: attributions of the solution
    :param requests_list: requests of the instance
    :param threshold: threshold above which a student is considered far away from the school
    :return: number of requests with distance>threshold, selected_ratio/overall_ratio
    """
    # work out selected_ratio
    nb_selected_requests = len(attributions)
    nb_selected_distant = 0
    for attribution in attributions:
        nb_selected_distant += attribution.request.distance > threshold
    selected_ratio = nb_selected_distant/nb_selected_requests

    # work out overall_ratio
    nb_requests = len(requests_list)
    nb_distant = 0
    for request in requests_list:
        nb_distant += request.distance > threshold
    overall_ratio = nb_distant/nb_requests

    ratio = selected_ratio/overall_ratio if overall_ratio else -1
    return nb_distant, ratio


def scholarship_selection_ratio(attributions, requests_list):
    """
    With selected_ratio being the ratio of requests with scholarship among the selected requests
    and overall_ratio being the ratio of requests with scholarship among all the requests,
    computes selected_ratio/overall_ratio
    :param attributions: attributions of the solution
    :param requests_list: requests of the instance
    :return: number of requests with scholarship, selected_ratio/overall_ratio
    """
    # work out selected_ratio
    nb_selected_requests = len(attributions)
    nb_selected_scholarship = 0
    for attribution in attributions:
        nb_selected_scholarship += attribution.request.scholarship
    selected_ratio = nb_selected_scholarship/nb_selected_requests

    # work out overall_ratio
    nb_requests = len(requests_list)
    nb_scholarship = 0
    for request in requests_list:
        nb_scholarship += request.scholarship
    overall_ratio = nb_scholarship/nb_requests

    ratio = selected_ratio/overall_ratio if overall_ratio else -1
    return nb_scholarship, ratio


def neutral_selection_ratio(attributions, requests_list):
    """
    With selected_ratio being the ratio of requests with neutral gender among the selected requests
    and overall_ratio being the ratio of requests with neutral gender among all the requests,
    computes selected_ratio/overall_ratio
    :param attributions: attributions of the solution
    :param requests_list: requests of the instance
    :return: number of requests with neutral gender, selected_ratio/overall_ratio
    """
    # work out selected_ratio
    nb_selected_requests = len(attributions)
    nb_selected_neutral = 0
    for attribution in attributions:
        nb_selected_neutral += attribution.request.gender == 0
    selected_ratio = nb_selected_neutral/nb_selected_requests

    # work out overall_ratio
    nb_requests = len(requests_list)
    nb_neutral = 0
    for request in requests_list:
        nb_neutral += request.gender == 0
    overall_ratio = nb_neutral/nb_requests

    ratio = selected_ratio/overall_ratio if overall_ratio else -1
    return nb_neutral, ratio


def mean_median_std(attributions, requests, attribute):
    attribute_getter = operator.attrgetter(attribute)
    overall_attributes = [attribute_getter(request) for request in requests]
    selected_attributes = [attribute_getter(attribution.request) for attribution in attributions]

    return (int(np.mean(overall_attributes)), int(np.median(overall_attributes)), int(np.std(overall_attributes)),
            int(np.mean(selected_attributes)), int(np.median(selected_attributes)), int(np.std(selected_attributes)))


def primary_criteria_overview(attributions, requests_list, solution_name, threshold=None):
    if threshold:
        requests_list = [request for request in requests_list if request.distance < threshold]
        attributions = [attribution for attribution in attributions if attribution.request.distance < threshold]
    id_to_idx = {request.student_id: k for k, request in enumerate(requests_list)}
    distances = [request.distance for request in requests_list]
    ranks = [request.shotgun_rank for request in requests_list]
    scholarships = [['x', 's'][request.scholarship] for request in requests_list]  # requests with scholarship are identified by a square
    selected_requests = ['b' for _ in range(len(requests_list))]
    for attribution in attributions:
        selected_requests[id_to_idx[attribution.request.student_id]] = 'r'  # selected requests are identified in red

    # plot
    plt.figure()
    for (distance, rank, scholarship, selection) in zip(distances, ranks, scholarships, selected_requests):
        plt.scatter(distance, rank, color=selection, marker=scholarship)
    plt.title("Synthèse des critères primaires des demandes et de leur sélection")
    plt.xlabel("Distance des Ponts")
    plt.ylabel("Rang dans le shotgun")
    blue_dot = mlines.Line2D([], [], color='b', linewidth=0, marker='o', label='Étudiant disqualifié')
    red_dot = mlines.Line2D([], [], color='r', linewidth=0, marker='o', label='Étudiant sélectionnée')
    cross = mlines.Line2D([], [], color='k', linewidth=0, marker='x', label='Étudiant non boursier')
    square = mlines.Line2D([], [], color='k', linewidth=0, marker='s', label='Étudiant boursier')
    plt.legend(handles=[blue_dot, red_dot, cross, square])
    plt.plot()
    plt.savefig(f"figures/solutions_analytics/primary-criteria-overview_{solution_name}")


def room_type_preference_satfisfaction(attributions, solution_name):
    """ Plots the stacked bar charts of the distribution of room type preferences in the different room types """
    room_labels = ["simple", "binomee", "double"]
    nb_room_types = len(room_labels)
    # pref_vs_rec_matrix[0][2] is the number of requests prefering a simple room that received a double room
    pref_vs_rec_matrix = np.zeros((nb_room_types, nb_room_types))
    for attribution in attributions:
        pref_vs_rec_matrix[attribution.request.prefered_room_type][attribution.room.room_type] += 1

    # plot bar charts
    plt.figure()
    x = range(nb_room_types)
    width = 0.8
    chart_layers = []
    bottom = np.zeros(nb_room_types)
    for room_type in range(nb_room_types):
        chart_layers.append(plt.bar(x, pref_vs_rec_matrix[room_type], width, bottom=bottom))
        bottom += pref_vs_rec_matrix[room_type]
    plt.title("Distribution des préférences dans chaque type de chambre")
    plt.ylabel("Nombre d'étudiants")
    plt.xlabel("Type de chambre reçu")
    plt.xticks(x, room_labels)
    chart_layers = np.array(chart_layers)
    plt.legend(chart_layers[-1::-1, 0], room_labels[-1::-1], title="Préférence de chambre", loc="upper right")

    plt.plot()
    plt.savefig(f"figures/solutions_analytics/room-type-preference_{solution_name}")


def friendship_satisfaction(attributions):
    """
    Returns the number of selected students who asked to be with a friend,
    the number among those who had their friend selected,
    and the number of students who had their friendship satisfied.
    """
    attributions_asking_mate = {attribution.request.student_id: attribution
                                for attribution in attributions if attribution.request.has_mate}
    number_students_asking_mate = len(attributions_asking_mate)
    number_students_with_mate_selected = 0
    for attribution in attributions_asking_mate.values():
        if attribution.request.mate_id in attributions_asking_mate.keys():
            number_students_with_mate_selected += 1
    number_students_satisfied = 0
    for attribution in attributions_asking_mate.values():
        if attribution.mate and (attribution.mate == attribution.request.mate_id):
            number_students_satisfied += 1
    return number_students_asking_mate, number_students_with_mate_selected, number_students_satisfied


if __name__ == "__main__":
    # instance = "medium"
    instance = "real"

    print("Loading attributions...")
    # rooms_file, requests_file = params.files[instance]
    rooms_file, requests_file = "db/chambre.json", "db/eleves_demande.json"
    attributions = load_attributions(rooms_file, requests_file, instance)

    print("Loading requests and rooms [", instance, "] ...")
    requests = json_to_objects_requests(requests_file)
    rooms = json_to_objects_rooms(rooms_file)

    # Primary criteria
    print("number of requests :", len(requests))
    print("total capacity:", sum([room.capacity for room in rooms]))
    overall_distance_mean, overall_distance_median, overall_distance_std, selected_distance_mean, selected_distance_median, selected_distance_std = mean_median_std(attributions, requests, "distance")
    print("overall distance mean, median and std :", overall_distance_mean, overall_distance_median, overall_distance_std)
    print("selected distance mean, median and std :", selected_distance_mean, selected_distance_median, selected_distance_std)
    _, _, _, shotgun_mean, shotgun_median, _ = mean_median_std(attributions, requests, "shotgun_rank")
    print("shotgun mean and median :", shotgun_mean, shotgun_median)
    nb_distant, distant_ratio = distance_selection_ratio(attributions, requests, 800)
    print("number of distant:", nb_distant)
    print("distant (selected_ratio/overall_ratio) :", distant_ratio)
    nb_scholarships, scholarship_ratio = scholarship_selection_ratio(attributions, requests)
    print("number of scholarships:", nb_scholarships)
    print("scholarship (selected_ratio/overall_ratio) :", scholarship_ratio)
    nb_neutrals, neutral_ratio = neutral_selection_ratio(attributions, requests)
    print("number of neutral:", nb_neutrals)
    print("neutral (selected_ratio/overall_ratio) :", neutral_ratio)
    primary_criteria_overview(attributions, requests, instance, threshold=10000)

    # Secondary criteria
    room_type_preference_satfisfaction(attributions, instance)
    number_students_asking_mate, number_students_with_mate_selected, number_students_satisfied = friendship_satisfaction(attributions)
    print(f"Among those selected, {number_students_asking_mate} asked to be with a specific mate, "
          f"{number_students_satisfied} were with their friend, "
          f"{number_students_asking_mate - number_students_satisfied} were not and "
          f"{number_students_with_mate_selected - number_students_satisfied} were not whereas their friend was selected.")
