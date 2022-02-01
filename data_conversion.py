import json
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
        gender = gender_convention_conversion[int(request["gender"])-1]
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
    rooms_list = [Room(int(room["numero"]), int(room["type"])-1) for room in rooms_raw]
    return rooms_list


if __name__ == "__main__":
    requests_filename = "db\eleves_demande.json"
    rooms_filename = "db\chambre.json"
    print(json_to_objects_requests(requests_filename)[18])
    print(json_to_objects_rooms(rooms_filename)[0])
