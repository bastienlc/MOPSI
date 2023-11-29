import json
import random

paris_threshold = 50
foreign_threshold = 800

parameters = {
    "room_preference_bonus_parameter": 0.000001,  # Bp
    "room_preference_malus_parameter": 100,  # Pp
    "gender_mix_parameter": 100,  # Pg
    "buddy_preference_parameter": 0.001,  # Bb
    "grant_parameter": 0.2,  # Bs
    "distance_parameter": 0.3,  # Bd
    "foreign_parameter": 1,  # Bf
    "shotgun_parameter": 0.0001,  # Pr
}

files = {
    "50": ("instances/chambre_50.json", "instances/eleves_demande_50.json"),
    "100": ("instances/chambre_100.json", "instances/eleves_demande_100.json"),
    "200": ("instances/chambre_200.json", "instances/eleves_demande_200.json"),
    "300": ("instances/chambre_300.json", "instances/eleves_demande_300.json"),
    "400": ("instances/chambre_400.json", "instances/eleves_demande_400.json"),
    "500": ("instances/chambre_500.json", "instances/eleves_demande_500.json"),
    "small": ("instances/chambre_small.json", "instances/eleves_demande_small.json"),
    "medium": ("instances/chambre_medium.json", "instances/eleves_demande_100.json"),
    "intermediate": (
        "instances/chambre_intermediate.json",
        "instances/eleves_demande_200.json",
    ),
    "large": ("instances/chambre_large.json", "instances/eleves_demande_500.json"),
    "double_rooms_only": (
        "simple_cases_instances/double-rooms-only_rooms.json",
        "simple_cases_instances/double-rooms-only_requests.json",
    ),
    "simple_rooms_only": (
        "simple_cases_instances/simple-rooms-only_rooms.json",
        "simple_cases_instances/simple-rooms-only_requests.json",
    ),
}


def random_requests_json(number_of_requests):
    requests = []
    for k in range(1, number_of_requests + 1):
        new_request = {}
        new_request["id_demande"] = k
        new_request["mail"] = "eleve" + str(k) + "@test.com"
        new_request["type_chambre"] = random.choice([1, 2, 3])
        new_request["remplace"] = random.choice([0, 1])
        new_request["gender"] = int(random.choice([1, 2]) + (random.random() > 0.99))
        new_request["mate"] = int(k > 1 and random.random() > 0.96)
        new_request["mate_email"] = None
        new_request["boursier"] = int(random.random() > 0.7)
        new_request["distance"] = (
            random.randint(1000, 4000)
            if random.random() > 0.9
            else random.randint(1, 1000)
        )
        new_request["demand_time"] = random.randint(1600000000, 1700000000)

        # find a mate for this request :
        if new_request["mate"]:
            for request in random.choices(requests, k=len(requests)):
                if not request["mate"]:
                    request["mate"] = 1
                    request["mate_email"] = new_request["mail"]
                    new_request["mate_email"] = request["mail"]
                    break
            if new_request["mate_email"] is None:  # if we could not find a mate
                new_request["mate"] = 0

        requests.append(new_request)

    new_json = []
    new_json.append(
        {
            "type": "header",
            "version": "5.1.1",
            "comment": "Export to JSON plugin for PHPMyAdmin",
        }
    )
    new_json.append({"type": "database", "name": "admissibles"})
    new_json.append(
        {"type": "table", "name": "eleves", "database": "admissibles", "data": []}
    )
    new_json[2]["data"] = requests
    with open(f"instances/eleves_demande_{number_of_requests}.json", "w") as f:
        json.dump(new_json, f)


if __name__ == "__main__":
    random_requests_json(500)
