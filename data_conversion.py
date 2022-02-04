import json
import numpy as np
import csv
from objects import Request, Room


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
    demand_times = [(demand_id, int(requests_raw[demand_id]["demand_time"])) for demand_id in range(nb_requests)]
    demand_times.sort(key=lambda time: time[1])
    shotgun_ranks = [0 for _ in range(nb_requests)]
    for rank in range(nb_requests):
        demand_id = demand_times[rank][0]
        shotgun_ranks[demand_id] = rank

    gender_convention_conversion = [1, -1, 0]

    for (request_i, request) in enumerate(requests_raw):
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

        request_object = Request(student_id, gender, scholarship, distance, prefered_room_type, accept_other_type,
                                 has_mate, mate_id, shotgun_rank)
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
    rooms_list = [Room(int(room["numero"]), int(room["type"]) - 1) for room in rooms_raw]
    return rooms_list


def write_attribution_matrix(attributions, requests, instance_name):
    nb_requests = len(requests)
    requests.sort(key=lambda request: request.student_id)
    id_to_idx = {requests[k].student_id: k for k in range(nb_requests)}
    attribution_matrix = np.array([[None for _ in range(nb_requests)] for _ in range(nb_requests)])
    for attribution in attributions:
        request_idx = id_to_idx[attribution.request.student_id]
        room_id = attribution.room.room_id
        mate_id = attribution.mate
        if mate_id:
            mate_idx = id_to_idx[mate_id]
            attribution_matrix[request_idx][mate_idx] = room_id
        else:
            attribution_matrix[request_idx][request_idx] = room_id
    with open(f'solutions/sol_{instance_name}_matrix.csv', 'w', newline='') as csvfile:
        solution_writer = csv.writer(csvfile, delimiter=';')
        solution_writer.writerow(["La cellule (i,j) indique la chambre logeant le(s) eleve(s) d'id i et j."])
        solution_writer.writerow(["id eleve"] + [request.student_id for request in requests])
        for row_idx in range(nb_requests):
            row = [requests[row_idx].student_id]
            for column_idx in range(nb_requests):
                cell = attribution_matrix[row_idx][column_idx]
                if cell:
                    row += [cell]
                else:
                    row += [""]
            solution_writer.writerow(row)


def write_attributions_requests_wise(attributions, instance_name):
    attributions.sort(key=lambda attribution: attribution.request.student_id)
    with open(f'solutions/sol_{instance_name}_request-wise.csv', 'w', newline='') as csvfile:
        solution_writer = csv.writer(csvfile, delimiter=';')
        solution_writer.writerow(
            ["id eleve", "genre", "boursier", "distance", "preference de chambre", "preference souple", "shotgun",
             "colocataire souhaite", "", "id chambre", "type chambre", "", "colocataire"])
        for attribution in attributions:
            request = attribution.request
            room = attribution.room
            row = [
                request.student_id,
                request.gender,
                request.scholarship,
                request.distance,
                request.prefered_room_type,
                request.accept_other_type,
                request.shotgun_rank,
            ]
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


def write_attributions_rooms_wise(rooms, instance_name):
    rooms.sort(key=lambda room: room.room_id)
    with open(f'solutions/sol_{instance_name}_rooms-wise.csv', 'w', newline='') as csvfile:
        solution_writer = csv.writer(csvfile, delimiter=';')
        solution_writer.writerow(["id chambre", "type chambre", "id eleve 1", "id eleve 2"])
        for room in rooms:
            row = [room.room_id, room.what_room_type()] + room.students
            solution_writer.writerow(row)


def write_solutions(attributions, requests, rooms, instance_name):
    write_attribution_matrix(attributions, requests, instance_name)
    write_attributions_requests_wise(attributions, instance_name)
    write_attributions_rooms_wise(rooms, instance_name)


if __name__ == "__main__":
    requests_filename = "db\eleves_demande.json"
    rooms_filename = "db\chambre.json"
