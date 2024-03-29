from datetime import datetime

import gurobipy as gp
from termcolor import colored

import params
from data_conversion import *
from local_solver import compute_score
from objects import Attribution
from params import files


def get_z_mat(requests_range, rooms_range, m):
    z = [[[0 for k in rooms_range] for j in requests_range] for i in requests_range]

    has_roommate = [False for i in requests_range]

    for i in requests_range:
        for j in requests_range:
            if j > i:
                for k in rooms_range:
                    z_i_j_k = m.getVarByName(f"z[{i},{j},{k}]")
                    if z_i_j_k.x == 1:
                        z[i][j][k] = 1
                        z[j][i][k] = 1
                        has_roommate[i] = True
                        has_roommate[j] = True
                        break
        if not has_roommate[i]:
            for k in rooms_range:
                x_i_k = m.getVarByName(f"x[{i},{k}]")
                if x_i_k.x == 1:
                    z[i][i][k] = 1
                    break
    return z


def print_pairings(requests_range, rooms_range, m, g):
    z = get_z_mat(requests_range, rooms_range, m)
    print("   ", end="")
    for i in requests_range:
        print(" ", end="")
        if g[i] == -1:
            print(colored(i, "red"), end="")
        elif g[i] == 0:
            print(colored(i, "blue"), end="")
        else:
            print(colored(i, "green"), end="")
        print(" ", end="")
    print("\n", end="")
    for i in requests_range:
        print("\n", end="")
        print(" ", end="")
        if g[i] == -1:
            print(colored(i, "red"), end="")
        elif g[i] == 0:
            print(colored(i, "blue"), end="")
        else:
            print(colored(i, "green"), end="")
        print(" ", end="")
        for j in requests_range:
            found = False
            for k in rooms_range:
                if z[i][j][k] == 1:
                    print(" X ", end="")
                    found = True
                    break
            if not found:
                print("   ", end="")


def milp_solve(
    requests, rooms, parameters=params.parameters, verbose=True, constraints=True
):
    """
    Solves the MILP version of the allocation problem.
    :param requests: list of the requests of the student, in the shape:
    (preference, rigid_preference, gender, buddy_request, grant, distance, foreign, shotgun_rank)
        preference: -1 if no preference, k if preference for type k (k=0, 1 and 2; see 'rooms' for room type encoding).
        rigid_preference: 1 if the student accepts to receive a room of different type from prefered, else 0.
        gender: -1 if man, 0 if not given, 1 if woman.
        buddy_request: -1 if no buddy requested, else index (starting from 0) of the budddy in the list.
        grant: 1 if the student receives a grant, else 0.
        distance: distance from Ponts ParisTech in km.
        foreign: 1 if the student lives outside metropolitan France, else 0.
        shotgun_rank: shotgun rank.
    :param rooms: list of available rooms. 0 for simple, 1 for 'binome', 2 for double.
    :param parameters: penalty and bonus factors for the problem.
    :return: None. Solves the MILP and prints solution.
    """
    nb_requests = len(requests)
    nb_rooms = len(rooms)
    requests_range = range(nb_requests)
    rooms_range = range(nb_rooms)
    nb_room_types = 3

    # Parameters
    room_preference_bonus_parameter = parameters["room_preference_bonus_parameter"]
    buddy_preference_parameter = parameters["buddy_preference_parameter"]
    grant_parameter = parameters["grant_parameter"]
    distance_parameter = parameters["distance_parameter"]
    foreign_parameter = parameters["foreign_parameter"]
    shotgun_parameter = parameters["shotgun_parameter"]

    # Import data and make notations match the overleaf
    c = [room.room_type for room in rooms]
    p = [
        [int(request.prefered_room_type == k) for k in range(nb_room_types)]
        for request in requests
    ]
    q = [int(not request.accept_other_type) for request in requests]
    g = [request.gender for request in requests]
    b = [
        [
            int(request.has_mate and request.mate_id == request2.student_id)
            for request2 in requests
        ]
        for request in requests
    ]
    s = [request.scholarship for request in requests]
    d = [int(request.distance > params.paris_threshold) for request in requests]
    f = [request.distance > params.foreign_threshold for request in requests]
    r = [request.shotgun_rank for request in requests]

    # Model
    m = gp.Model("admissibles_MILP")

    # Create variables
    x = m.addVars(nb_requests, nb_rooms, vtype="B", name="x")
    z_indices = [
        (i_1, i_2, j)
        for i_1 in requests_range
        for i_2 in range(i_1 + 1, nb_requests)
        for j in rooms_range
    ]
    z = m.addVars(z_indices, vtype="B", name="z")

    # Set objective
    coeff_on_x = {
        (i, j): (
            1
            + distance_parameter * d[i]
            + foreign_parameter * f[i]
            + grant_parameter * s[i]
            - shotgun_parameter * r[i]
            + room_preference_bonus_parameter * p[i][c[j]]
        )
        for i in requests_range
        for j in rooms_range
    }
    sum_on_x = x.prod(coeff_on_x)

    coeff_on_z = {
        (i_1, i_2, j): buddy_preference_parameter * b[i_1][i_2]
        for i_1 in requests_range
        for i_2 in range(i_1 + 1, nb_requests)
        for j in rooms_range
    }
    sum_on_z = z.prod(coeff_on_z)

    m.setObjective(sum_on_x + sum_on_z, gp.GRB.MAXIMIZE)

    # Add constraints
    m.addConstrs(x.sum(i, "*") <= 1 for i in requests_range)
    m.addConstrs(x.sum("*", j) <= min(2, c[j] + 1) for j in rooms_range)

    m.addConstrs(
        z[i_1, i_2, j] <= x[i_1, j]
        for i_1 in requests_range
        for i_2 in range(i_1 + 1, nb_requests)
        for j in rooms_range
    )
    m.addConstrs(
        z[i_1, i_2, j] <= x[i_2, j]
        for i_1 in requests_range
        for i_2 in range(i_1 + 1, nb_requests)
        for j in rooms_range
    )
    m.addConstrs(
        z[i_1, i_2, j] >= x[i_1, j] + x[i_2, j] - 1
        for i_1 in requests_range
        for i_2 in range(i_1 + 1, nb_requests)
        for j in rooms_range
    )

    if constraints:
        coeff_on_z_constraints = [
            {
                (i_1, i_2, j): abs(g[i_1] * g[i_2] * (g[i_1] - g[i_2]))
                * (1 - b[i_1][i_2])
                for i_1 in requests_range
                for i_2 in range(i_1 + 1, nb_requests)
            }
            for j in rooms_range
        ]
        m.addConstrs(
            z.prod(coeff_on_z_constraints[j]) == 0 for j in rooms_range if c[j] >= 1
        )
        m.addConstrs(
            x[i, j] * (1 - p[i][c[j]]) * q[i] == 0
            for i in requests_range
            for j in rooms_range
        )

    # Solve problem
    m.update()
    m.optimize()

    # Fill attributions corresponding to the solution
    attributions = []
    filled_attributions = [False] * nb_requests
    for i in requests_range:
        if not filled_attributions[i]:
            for j in rooms_range:
                x_i_j = m.getVarByName(f"x[{i},{j}]")
                if x_i_j.x == 1:
                    attribution = Attribution(requests[i], rooms[j])
                    for i_mate in range(i + 1, nb_requests):
                        z_i_imate_j = m.getVarByName(f"z[{i},{i_mate},{j}]")
                        if z_i_imate_j.x == 1:
                            attribution.set_mate(requests[i_mate].student_id)
                            mate_attribution = Attribution(
                                requests[i_mate], rooms[j], requests[i].student_id
                            )
                            attributions.append(mate_attribution)
                            filled_attributions[i_mate] = True
                            break
                    attributions.append(attribution)
                    filled_attributions[i] = True

    # Fill the rooms accordingly
    for j in rooms_range:
        for i in requests_range:
            x_i_j = m.getVarByName(f"x[{i},{j}]")
            if x_i_j.x == 1:
                rooms[j].students.append(requests[i].student_id)

    if verbose:
        attributions.sort(key=lambda attribution: attribution.request.student_id)
        print("solution :")
        for attribution in attributions:
            print(attribution)

    return attributions


if __name__ == "__main__":
    instance = "small"

    print("Loading requests and rooms [", instance, "] ...")
    if instance == "real":
        requests = json_to_objects_requests("db/eleves_demande.json")
        rooms = json_to_objects_rooms("db/chambre.json")
    else:
        rooms_file, requests_file = files[instance]
        requests = json_to_objects_requests(requests_file)
        rooms = json_to_objects_rooms(rooms_file)
    print("Requests and rooms loaded.")
    print("Launching MILP solver :")
    attributions = milp_solve(requests, rooms, params.parameters)
    score = compute_score(attributions, dictionary_from_requests(requests))
    score_json = {"score": score, "date": str(datetime.now()).replace(" ", "-")}
    with open(f"solutions/score.json", "w") as f:
        json.dump(score_json, f)
    print("Writing solution files...")
    solution_name = f"{instance}_milp"
    write_solutions(attributions, requests, rooms, solution_name)
    save_attributions(attributions, solution_name)
    print("Done.")
