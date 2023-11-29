import csv
import json

import numpy as np

from objects import Attribution, Request, Room


def dictionary_from_requests(requests):
    requests_dictionary = {}
    for request in requests:
        requests_dictionary[str(request.student_id)] = request
    return requests_dictionary


def dictionary_from_rooms(rooms):
    rooms_dictionary = {}
    for room in rooms:
        rooms_dictionary[str(room.room_id)] = room
    return rooms_dictionary


def json_to_objects_requests(requests_file):
    """
    Converts a json database into a list of python "Request" objects. Conventions on encoding are converted from those
    of the database to those of the python classes; see the classes documentation for details.
    :param requests_file: a json containing the inner join of 'demande' and 'eleve', of the form :
    (id_request, email, room_type_preference, rigid_preference, gender, mate, mate_email, grant, distance, demand_time)
    :return: the list of Request python objects created from the json file.
    """
    requests_list = []

    with open(requests_file) as file:
        requests_raw = json.load(file)[2]["data"]
    nb_requests = len(requests_raw)

    # Work out shotgun ranks
    demand_times = [
        (demand_id, int(requests_raw[demand_id]["demand_time"]))
        for demand_id in range(nb_requests)
    ]
    demand_times.sort(key=lambda time: time[1])
    shotgun_ranks = [0 for _ in range(nb_requests)]
    for rank in range(nb_requests):
        demand_id = demand_times[rank][0]
        shotgun_ranks[demand_id] = rank

    gender_convention_conversion = [1, -1, 0]

    for request_i, request in enumerate(requests_raw):
        student_id = int(request["id_demande"])
        gender = gender_convention_conversion[int(request["gender"]) - 1]
        scholarship = bool(int(request["boursier"]))
        distance = int(request["distance"])
        prefered_room_type = int(request["type_chambre"]) - 1
        accept_other_type = bool(int(request["remplace"]))
        shotgun_rank = shotgun_ranks[request_i]
        has_mate = bool(int(request["mate"]))
        mate_id = None
        if has_mate:
            mate_email = request["mate_email"]
            consistent_mate_request = False
            for other_resquest in requests_raw:
                if other_resquest["mail"] == mate_email:
                    consistent_mate_request = (
                        bool(int(other_resquest["mate"]))
                        and other_resquest["mate_email"] == request["mail"]
                    )
                    mate_id = int(other_resquest["id_demande"])
                    break
            has_mate = consistent_mate_request
            if not consistent_mate_request:
                mate_id = None

        request_object = Request(
            student_id,
            gender,
            scholarship,
            distance,
            prefered_room_type,
            accept_other_type,
            has_mate,
            mate_id,
            shotgun_rank,
        )
        requests_list.append(request_object)

    return requests_list


def json_to_objects_rooms(rooms_file):
    """
    Converts a json database into a list of python "Room" objects. Conventions on encoding are converted from those
    of the database to those of the python classes; see the classes documentation for details.
    :param requests_file: a json containing the content of the "room" database.
    :return: the list of Room python objects created from the json file.
    """
    with open(rooms_file) as file:
        rooms_raw = json.load(file)[2]["data"]
    rooms_list = [
        Room(int(room["numero"]), int(room["type"]) - 1) for room in rooms_raw
    ]
    return rooms_list


def write_attribution_matrix(attributions, requests, solution_name):
    """
    Export solution as a matrix where cell (i, j) gives the room assigned to the students of id i and j.
    :param attributions: list of Attributions given by the solution.
    :param requests: list of the requests of the instance.
    :param instance_name: name of the instance used to write the file name.
    :return: Nothing. Writes a csv containing the matrix.
    """
    nb_requests = len(requests)
    requests.sort(key=lambda request: request.student_id)
    id_to_idx = {requests[k].student_id: k for k in range(nb_requests)}
    attribution_matrix = np.array(
        [[None for _ in range(nb_requests)] for _ in range(nb_requests)]
    )
    for attribution in attributions:
        request_idx = id_to_idx[attribution.request.student_id]
        room_id = attribution.room.room_id
        mate_id = attribution.mate
        if mate_id:
            mate_idx = id_to_idx[mate_id]
            attribution_matrix[request_idx][mate_idx] = room_id
        else:
            attribution_matrix[request_idx][request_idx] = room_id
    with open(f"solutions/sol_{solution_name}_matrix.csv", "w", newline="") as csvfile:
        solution_writer = csv.writer(csvfile, delimiter=";")
        solution_writer.writerow(
            ["La cellule (i,j) indique la chambre logeant le(s) eleve(s) d'id i et j."]
        )
        solution_writer.writerow(
            ["id eleve"] + [request.student_id for request in requests]
        )
        for row_idx in range(nb_requests):
            row = [requests[row_idx].student_id]
            for column_idx in range(nb_requests):
                cell = attribution_matrix[row_idx][column_idx]
                if cell:
                    row += [cell]
                else:
                    row += [""]
            solution_writer.writerow(row)


def write_attributions_requests_wise(attributions, requests, solution_name):
    """
    Exports the solutions as a list of requests with their assigned room and their roommate, if any.
    :param attributions: list of Attributions given by the solution.
    :param requests: list of the requests of the instance.
    :param instance_name: name of the instance used to write the file name.
    :return: Nothing. Writes a csv file containing the list of attributions and the list of unsatisfied requests.
    """
    attributions.sort(key=lambda attribution: attribution.request.student_id)
    satisfied_requests = {request.student_id: False for request in requests}
    with open(
        f"solutions/sol_{solution_name}_request-wise.csv", "w", newline=""
    ) as csvfile:
        solution_writer = csv.writer(csvfile, delimiter=";")
        solution_writer.writerow(
            [
                "id eleve",
                "genre",
                "boursier",
                "distance",
                "preference de chambre",
                "preference souple",
                "shotgun",
                "colocataire souhaite",
                "",
                "id chambre",
                "type chambre",
                "",
                "colocataire",
            ]
        )
        for attribution in attributions:
            request = attribution.request
            room = attribution.room
            row = [request.student_id]
            if request.gender == -1:
                row.append("homme")
            elif request.gender == 1:
                row.append("femme")
            else:
                row.append("non precise")
            row += [request.scholarship, request.distance]
            if request.prefered_room_type < 0:
                row.append("sans preference")
            elif request.prefered_room_type == 0:
                row.append("simple")
            elif request.prefered_room_type == 1:
                row.append("binomee")
            else:
                row.append("double")
            row += [request.accept_other_type, request.shotgun_rank]
            if request.has_mate:
                row.append(request.mate_id)
            else:
                row.append("")
            row.append("")
            row += [room.room_id, room.what_room_type()]
            row.append("")
            mate = attribution.mate
            if mate:
                row += [mate]
            solution_writer.writerow(row)
            satisfied_requests[request.student_id] = True

        solution_writer.writerow(
            [
                "=========================================================================================================================================================="
            ]
        )
        solution_writer.writerow(["Demandes non satisfaites :"])
        for request in requests:
            if not satisfied_requests[request.student_id]:
                row = [request.student_id]
                if request.gender == -1:
                    row.append("homme")
                elif request.gender == 1:
                    row.append("femme")
                else:
                    row.append("non precise")
                row += [request.scholarship, request.distance]
                if request.prefered_room_type < 0:
                    row.append("sans preference")
                elif request.prefered_room_type == 0:
                    row.append("simple")
                elif request.prefered_room_type == 1:
                    row.append("binomee")
                else:
                    row.append("double")
                row += [request.accept_other_type, request.shotgun_rank]
                if request.has_mate:
                    row.append(request.mate_id)
                else:
                    row.append("")
                solution_writer.writerow(row)


def write_attributions_rooms_wise(rooms, solution_name):
    """
    Exports the solutions as a list of rooms with their assigned students.
    :param rooms: list of Rooms with their students field filled during the resolution.
    :param instance_name: name of the instance used to write the file name.
    :return: Nothing. Writes a csv file containing the list of rooms with their students.
    """
    rooms.sort(key=lambda room: room.room_id)
    with open(
        f"solutions/sol_{solution_name}_rooms-wise.csv", "w", newline=""
    ) as csvfile:
        solution_writer = csv.writer(csvfile, delimiter=";")
        solution_writer.writerow(
            ["id chambre", "type chambre", "id eleve 1", "id eleve 2"]
        )
        for room in rooms:
            row = [room.room_id, room.what_room_type()] + room.students
            solution_writer.writerow(row)


def write_solutions(attributions, requests, rooms, solution_name):
    write_attribution_matrix(attributions, requests, solution_name)
    write_attributions_requests_wise(attributions, requests, solution_name)
    write_attributions_rooms_wise(rooms, solution_name)


def save_attributions(attributions, solution_name):
    """
    Stores the given attributions as a list of dictionaries and saves it in a json file.
    """
    with open(f"solutions/attributions/att_{solution_name}.json", "w") as jsonfile:
        attributions_as_dict = [
            {
                "request": attribution.request.student_id,
                "room": attribution.room.room_id,
                "mate": attribution.mate,
            }
            for attribution in attributions
        ]
        json.dump(attributions_as_dict, jsonfile)


def load_attributions(rooms_file, requests_file, solution_name):
    """
    Loads attributions from an attributions file and the files of the corresponding instance's requests and rooms
    :param requests_file: path to the file containing the requests of the isntance
    :param rooms_file: path to the file containing the rooms of the isntance
    :param solution_name: name of the solution, used to find the attributions file
    :return: the loaded list of Attribution
    """
    requests_dict = dictionary_from_requests(json_to_objects_requests(requests_file))
    rooms_dict = dictionary_from_rooms(json_to_objects_rooms(rooms_file))
    attributions = []
    with open(f"solutions/attributions/att_{solution_name}.json", "r") as jsonfile:
        attributions_as_dict = json.load(jsonfile)
        for attribution_as_dict in attributions_as_dict:
            request = requests_dict[str(attribution_as_dict["request"])]
            room = rooms_dict[str(attribution_as_dict["room"])]
            mate_id = attribution_as_dict["mate"]
            attributions.append(Attribution(request, room, mate_id))
    return attributions
