import operator

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np

import params
from data_conversion import (
    dictionary_from_requests,
    json_to_objects_requests,
    json_to_objects_rooms,
    load_attributions,
)
from local_solver import compute_score


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
    selected_ratio = nb_selected_distant / nb_selected_requests

    # work out overall_ratio
    nb_requests = len(requests_list)
    nb_distant = 0
    for request in requests_list:
        nb_distant += request.distance > threshold
    overall_ratio = nb_distant / nb_requests

    ratio = selected_ratio / overall_ratio if overall_ratio else -1
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
    selected_ratio = nb_selected_scholarship / nb_selected_requests

    # work out overall_ratio
    nb_requests = len(requests_list)
    nb_scholarship = 0
    for request in requests_list:
        nb_scholarship += request.scholarship
    overall_ratio = nb_scholarship / nb_requests

    ratio = selected_ratio / overall_ratio if overall_ratio else -1
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
    selected_ratio = nb_selected_neutral / nb_selected_requests

    # work out overall_ratio
    nb_requests = len(requests_list)
    nb_neutral = 0
    for request in requests_list:
        nb_neutral += request.gender == 0
    overall_ratio = nb_neutral / nb_requests

    ratio = selected_ratio / overall_ratio if overall_ratio else -1
    return nb_neutral, ratio


def mean_median_std(attributions, requests, attribute, threshold=None):
    if threshold:
        requests = [request for request in requests if request.distance < threshold]
        attributions = [
            attribution
            for attribution in attributions
            if attribution.request.distance < threshold
        ]
    attribute_getter = operator.attrgetter(attribute)
    overall_attributes = [attribute_getter(request) for request in requests]
    selected_attributes = [
        attribute_getter(attribution.request) for attribution in attributions
    ]

    return (
        int(np.mean(overall_attributes)),
        int(np.median(overall_attributes)),
        int(np.std(overall_attributes)),
        int(np.mean(selected_attributes)),
        int(np.median(selected_attributes)),
        int(np.std(selected_attributes)),
    )


def distances_box_plot(attributions, requests, solution_name, threshold=None):
    if threshold:
        requests = [request for request in requests if request.distance < threshold]
        attributions = [
            attribution
            for attribution in attributions
            if attribution.request.distance < threshold
        ]
    overall_distances = [request.distance for request in requests]
    selected_distances = [attribution.request.distance for attribution in attributions]
    plt.figure()
    plt.boxplot([overall_distances, selected_distances])
    boxnames = ["Toutes demandes", "Demandes sélectionnées"]
    plt.xticks([1, 2], boxnames)
    plt.ylabel("Distance")
    plt.savefig(
        f"figures/solutions_analytics/distances-boxplot_{solution_name}", dpi=400
    )


def shotgun_box_plot(attributions, requests, solution_name):
    overall_shotgun = [request.shotgun_rank for request in requests]
    selected_shotgun = [
        attribution.request.shotgun_rank for attribution in attributions
    ]
    plt.figure()
    plt.boxplot([overall_shotgun, selected_shotgun])
    boxnames = ["Toutes demandes", "Demandes sélectionnées"]
    plt.xticks([1, 2], boxnames)
    plt.ylabel("Rang au shotgun")
    plt.savefig(f"figures/solutions_analytics/shotgun-boxplot_{solution_name}", dpi=400)


def primary_criteria_overview(
    attributions, requests_list, solution_name, threshold=None
):
    if threshold:
        requests_list = [
            request for request in requests_list if request.distance < threshold
        ]
        attributions = [
            attribution
            for attribution in attributions
            if attribution.request.distance < threshold
        ]
    id_to_idx = {request.student_id: k for k, request in enumerate(requests_list)}
    distances = [request.distance for request in requests_list]
    ranks = [request.shotgun_rank for request in requests_list]
    scholarships = [
        ["x", "s"][request.scholarship] for request in requests_list
    ]  # requests with scholarship are identified by a square
    selected_requests = ["tab:blue" for _ in range(len(requests_list))]
    for attribution in attributions:
        selected_requests[
            id_to_idx[attribution.request.student_id]
        ] = "tab:red"  # selected requests are identified in red

    # plot
    plt.figure()
    for distance, rank, scholarship, selection in zip(
        distances, ranks, scholarships, selected_requests
    ):
        plt.scatter(distance, rank, color=selection, marker=scholarship)
    plt.plot(
        [params.paris_threshold, params.paris_threshold],
        [0, len(requests_list)],
        "k--",
        linewidth=2,
    )
    plt.plot(
        [params.foreign_threshold, params.foreign_threshold],
        [0, len(requests_list)],
        "k-.",
        linewidth=2,
    )
    plt.xscale("log")
    # plt.title("Synthèse des critères primaires des demandes et de leur sélection")
    plt.xlabel("Distance des Ponts")
    plt.ylabel("Rang dans le shotgun")
    blue_dot = mlines.Line2D(
        [], [], color="tab:blue", linewidth=0, marker="o", label="Étudiant disqualifié"
    )
    red_dot = mlines.Line2D(
        [], [], color="tab:red", linewidth=0, marker="o", label="Étudiant sélectionné"
    )
    cross = mlines.Line2D(
        [], [], color="k", linewidth=0, marker="x", label="Étudiant non boursier"
    )
    square = mlines.Line2D(
        [], [], color="k", linewidth=0, marker="s", label="Étudiant boursier"
    )
    dashed_line = mlines.Line2D(
        [0, 0], [0, 1], linestyle="--", linewidth=2, color="k", label="Seuil $50 km$"
    )
    dash_dotted_line = mlines.Line2D(
        [0, 0], [0, 1], linestyle="-.", linewidth=2, color="k", label="Seuil $800 km$"
    )
    plt.legend(
        handles=[blue_dot, red_dot, cross, square, dashed_line, dash_dotted_line]
    )
    plt.plot()
    plt.savefig(
        f"figures/solutions_analytics/primary-criteria-overview_{solution_name}",
        dpi=400,
    )


def room_type_preference_satfisfaction(attributions, solution_name):
    """Plots the stacked bar charts of the distribution of room type preferences in the different room types"""
    room_labels = ["simple", "binomee", "double"]
    nb_room_types = len(room_labels)
    # pref_vs_rec_matrix[0][2] is the number of requests prefering a simple room that received a double room
    pref_vs_rec_matrix = np.zeros((nb_room_types, nb_room_types))
    for attribution in attributions:
        pref_vs_rec_matrix[attribution.request.prefered_room_type][
            attribution.room.room_type
        ] += 1

    # plot bar charts
    plt.figure()
    x = range(nb_room_types)
    width = 0.8
    chart_layers = []
    bottom = np.zeros(nb_room_types)
    for room_type in range(nb_room_types):
        chart_layers.append(
            plt.bar(x, pref_vs_rec_matrix[room_type], width, bottom=bottom)
        )
        bottom += pref_vs_rec_matrix[room_type]
    # plt.title("Distribution des préférences dans chaque type de chambre")
    plt.ylabel("Nombre d'étudiants")
    plt.xlabel("Type de chambre reçu")
    plt.xticks(x, room_labels)
    chart_layers = np.array(chart_layers)
    plt.legend(
        chart_layers[-1::-1, 0],
        room_labels[-1::-1],
        title="Préférence de chambre",
        loc="upper right",
    )

    plt.plot()
    plt.savefig(
        f"figures/solutions_analytics/room-type-preference_{solution_name}", dpi=400
    )


def friendship_satisfaction(attributions):
    """
    Returns the number of selected students who asked to be with a friend,
    the number among those who had their friend selected,
    and the number of students who had their friendship satisfied.
    """
    attributions_asking_mate = {
        attribution.request.student_id: attribution
        for attribution in attributions
        if attribution.request.has_mate
    }
    number_students_asking_mate = len(attributions_asking_mate)
    number_students_with_mate_selected = 0
    for attribution in attributions_asking_mate.values():
        if attribution.request.mate_id in attributions_asking_mate.keys():
            number_students_with_mate_selected += 1
    number_students_satisfied = 0
    for attribution in attributions_asking_mate.values():
        if attribution.mate and (attribution.mate == attribution.request.mate_id):
            number_students_satisfied += 1
    return (
        number_students_asking_mate,
        number_students_with_mate_selected,
        number_students_satisfied,
    )


def cost_analysis(attributions, requests_dictionary, solution_name):
    score_primary = [0, 0, 0, 0, 0]
    score_secondary = [0, 0]
    for attribution in attributions:
        score_primary[0] += 1
        if attribution.request.prefered_room_type == attribution.room.room_type:
            score_secondary[0] += params.parameters["room_preference_bonus_parameter"]
        if attribution.mate is not None:
            mate_request = requests_dictionary[str(attribution.mate)]
            if (
                attribution.request.has_mate
                and attribution.request.mate_id == mate_request.student_id
            ):
                score_secondary[1] += (
                    params.parameters["buddy_preference_parameter"] / 2
                )  # every pair is seen twice
        if attribution.request.scholarship:
            score_primary[1] += params.parameters["grant_parameter"]
        if attribution.request.distance > params.paris_threshold:
            score_primary[2] += params.parameters["distance_parameter"]
        if attribution.request.distance > params.foreign_threshold:
            score_primary[3] += params.parameters["foreign_parameter"]
        score_primary[4] += (
            params.parameters["shotgun_parameter"] * attribution.request.shotgun_rank
        )

    labels_primary = [
        "Remplissage des chambres",
        "Boursier",
        "Distance (50km)",
        "Distance (800km)",
        "Shotgun",
    ]
    labels_secondary = ["Chambre préférée", "Demandes à 2"]

    def absolute_value(val):
        a = np.round(val / 100.0 * sum(score_primary), 0)
        return a

    fig, ax = plt.subplots()
    ax.pie(
        score_primary,
        labels=labels_primary,
        normalize=True,
        textprops={"fontsize": 14},
        autopct=absolute_value,
    )
    plt.show()
    fig.savefig(
        f"figures/solutions_analytics/score_analysis_primary_{solution_name}", dpi=400
    )

    fig, ax = plt.subplots()
    ax.pie(
        score_secondary,
        labels=labels_secondary,
        normalize=True,
        textprops={"fontsize": 14},
    )
    plt.show()
    fig.savefig(
        f"figures/solutions_analytics/score_analysis_secondary_{solution_name}", dpi=400
    )


def analysis(instance_size, solution_type):
    """
    Carries out the analysis of the passed instance and solution, printing statistical data and exporting graphics
    :param instance_size: either "real", "small"/"medium"/"large", or a number giving the size of the instance
    :param solution_type: the algorithm used to solve the instance
    :return:
    """
    if instance_size == "real":
        print(
            f"======================================== ANALYSIS REAL DATA ========================================"
        )
        rooms_file, requests_file = "db/chambre.json", "db/eleves_demande.json"
        instance = "real" + "_" + solution_type
    else:
        print(
            f"======================================== ANALYSIS {instance_size} {solution_type} ========================================"
        )
        rooms_file, requests_file = params.files[instance_size]
        instance = instance_size + "_" + solution_type
    print(requests_file)
    attributions = load_attributions(rooms_file, requests_file, instance)
    requests = json_to_objects_requests(requests_file)
    requests_dictionary = dictionary_from_requests(requests)
    rooms = json_to_objects_rooms(rooms_file)

    print("solution score :", compute_score(attributions, requests_dictionary))
    print(
        "number of unoccupied rooms :",
        sum([room.capacity for room in rooms]) - len(attributions),
    )

    # Primary criteria
    print("number of requests :", len(requests))
    print("total capacity:", sum([room.capacity for room in rooms]))
    (
        overall_distance_mean,
        overall_distance_median,
        overall_distance_std,
        selected_distance_mean,
        selected_distance_median,
        selected_distance_std,
    ) = mean_median_std(attributions, requests, "distance", threshold=3000)
    print(
        "number of simple rooms:", sum([True for room in rooms if room.room_type == 0])
    )
    print(
        "number of binom rooms:", sum([True for room in rooms if room.room_type == 1])
    )
    print(
        "number of double rooms:", sum([True for room in rooms if room.room_type == 2])
    )
    print(
        "overall distance mean, median and std :",
        overall_distance_mean,
        overall_distance_median,
        overall_distance_std,
    )
    print(
        "selected distance mean, median and std :",
        selected_distance_mean,
        selected_distance_median,
        selected_distance_std,
    )
    _, _, _, shotgun_mean, shotgun_median, _ = mean_median_std(
        attributions, requests, "shotgun_rank"
    )
    print("shotgun mean and median :", shotgun_mean, shotgun_median)
    shotgun_box_plot(attributions, requests, instance)
    nb_distant, distant_ratio = distance_selection_ratio(attributions, requests, 800)
    print("number of distant:", nb_distant)
    print("distant (selected_ratio/overall_ratio) :", distant_ratio)
    distances_box_plot(attributions, requests, instance, threshold=3000)
    nb_scholarships, scholarship_ratio = scholarship_selection_ratio(
        attributions, requests
    )
    print("number of scholarships:", nb_scholarships)
    print("scholarship (selected_ratio/overall_ratio) :", scholarship_ratio)
    nb_neutrals, neutral_ratio = neutral_selection_ratio(attributions, requests)
    print("number of neutral:", nb_neutrals)
    print("neutral (selected_ratio/overall_ratio) :", neutral_ratio)
    primary_criteria_overview(attributions, requests, instance, threshold=3000)

    # Secondary criteria
    room_type_preference_satfisfaction(attributions, instance)
    (
        number_students_asking_mate,
        number_students_with_mate_selected,
        number_students_satisfied,
    ) = friendship_satisfaction(attributions)
    print(
        f"Among those selected, {number_students_asking_mate} asked to be with a specific mate, "
        f"{number_students_satisfied} were with their friend, "
        f"{number_students_asking_mate - number_students_satisfied} were not and "
        f"{number_students_with_mate_selected - number_students_satisfied} were not even though their friend was selected."
    )

    cost_analysis(attributions, requests_dictionary, instance)


if __name__ == "__main__":
    analysis("real", "heuristic")
