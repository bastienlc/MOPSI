import gurobipy as gp
import numpy as np


def milp_solve(requests, rooms, parameters):
    """
    Solves the MILP version of the allocation problem.
    :param requests: list of the requests of the student, in the shape:
    (preference, genre, buddy_request, grant, distance, foreign, shotgun_rank)
        preference: -1 if no preference, k if preference for type k (k=0, 1 and 2; see 'rooms' for room type encoding).
        genre: -1 if man, 0 if not given, 1 if woman.
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
    room_preference_malus_parameter = parameters["room_preference_malus_parameter"]
    gender_mix_parameter = parameters["gender_mix_parameter"]
    buddy_preference_parameter = parameters["buddy_preference_parameter"]
    grant_parameter = parameters["grant_parameter"]
    distance_parameter = parameters["distance_parameter"]
    foreign_parameter = parameters["foreign_parameter"]
    shotgun_parameter = parameters["shotgun_parameter"]

    # Import data and make notations match the overleaf
    r = [request.room_type for request in requests]
    p = [[int(request.prefered_room_type == k) for k in range(nb_room_types)] for request in requests]
    g = [request.gender for request in requests]
    b = [[int(request.has_mate and request.mate_id == i_2) for i_2 in range(request.student_id+1, nb_requests)] for request in requests]
    a = [request.scholarship for request in requests]
    d = [int(request.distance > 50) for request in requests]
    f = [request.distance > 800 for request in requests]
    s = [request.shotgun_rank for request in requests]

    # Model
    m = gp.Model("admissibles_MILP")

    # Create variables
    x = m.addVars(nb_requests, nb_rooms, vtype="B", name="x")
    z_indices = [(i_1, i_2, j) for i_1 in requests_range for i_2 in range(i_1 + 1, nb_requests) for j in rooms_range]
    z = m.addVars(z_indices, vtype="B", name="z")

    # Set objective
    coeff_on_x = {
        (i, j): 1 + room_preference_bonus_parameter*p[i][r[j]] - room_preference_malus_parameter*(1-p[i][r[j]])
                + grant_parameter*a[i] + distance_parameter*d[i] + foreign_parameter*f[i] - shotgun_parameter*s[i]
        for i in requests_range
        for j in rooms_range
    }
    sum_on_x = x.prod(coeff_on_x)

    coeff_on_z = {
        (i_1, i_2, j): - gender_mix_parameter*abs(g[i_1]*g[i_2]*(g[i_1] - g[i_2]))*(1 - b[i_1][i_2-(i_1+1)])
                       + buddy_preference_parameter*b[i_1][i_2-(i_1+1)]
        for i_1 in requests_range
        for i_2 in range(i_1 + 1, nb_requests)
        for j in rooms_range
    }
    sum_on_z = z.prod(coeff_on_z)

    m.setObjective(sum_on_x + sum_on_z, gp.GRB.MAXIMIZE)

    # Add constraints
    m.addConstrs(
        z[i_1, i_2, j] <= x[i_1, j]
        for i_1 in requests_range for i_2 in range(i_1 + 1, nb_requests) for j in rooms_range
    )
    m.addConstrs(
        z[i_1, i_2, j] <= x[i_2, j]
        for i_1 in requests_range for i_2 in range(i_1 + 1, nb_requests) for j in rooms_range
    )
    m.addConstrs(
        z[i_1, i_2, j] >= x[i_1, j] + x[i_2, j] - 1
        for i_1 in requests_range for i_2 in range(i_1 + 1, nb_requests) for j in rooms_range
    )

    m.addConstrs(x.sum(i, '*') <= 1 for i in requests_range)
    m.addConstrs(x.sum('*', j) <= min(2, r[j] + 1) for j in rooms_range)

    # Solve problem
    m.update()
    m.optimize()

    print("solution :")
    for i in requests_range:
        for j in rooms_range:
            x_i_j = m.getVarByName(f"x[{i},{j}]")
            if x_i_j.x == 1:
                print(f"Request {i} satisfied with chamber {j}.")

    # for i_1 in requests_range:
    #     for i_2 in range(i_1+1, nb_requests):
    #         for j in rooms_range:
    #             z_i_j = m.getVarByName(f"z[{i_1},{i_2},{j}]")
    #             if z_i_j.x == 1:
    #                 print(z_i_j.varName, z_i_j.x)

    return


if __name__ == "__main__":
    # parameters
    room_preference_bonus_parameter = 0.1
    room_preference_malus_parameter = 0.1
    gender_mix_parameter = 0.2
    buddy_preference_parameter = 0.2

    grant_parameter = 0.3
    distance_parameter = 0.3
    foreign_parameter = 1
    shotgun_parameter = 0.001

    parameters = {
        "room_preference_bonus_parameter": room_preference_bonus_parameter,
        "room_preference_malus_parameter": room_preference_malus_parameter,
        "gender_mix_parameter": gender_mix_parameter,
        "buddy_preference_parameter": buddy_preference_parameter,
        "grant_parameter": grant_parameter,
        "distance_parameter": distance_parameter,
        "foreign_parameter": foreign_parameter,
        "shotgun_parameter": shotgun_parameter
    }

    # data
    requests = [
        # (preference, genre, buddy_request, grant, distance, foreign, shotgun_rank)
        (0, -1, -1, 0, 30, 0, 0),
        (0, 1, -1, 1, 45, 0, 1),
        (-1, 1, -1, 0, 40, 0, 2),
        (2, -1, 5, 0, 80, 0, 3),
        (0, 0, -1, 0, 50, 0, 4),
        (2, 1, 3, 0, 85, 0, 5),
        (1, 1, -1, 1, 50, 0, 6),
        (0, 1, -1, 0, 1000, 1, 7),
        (0, -1, -1, 1, 42, 0, 8),
        (2, -1, -1, 0, 20, 0, 9),
        (0, 1, -1, 1, 150, 0, 10),
        (0, -1, -1, 0, 10, 0, 11)
    ]

    rooms = [0, 0, 1, 1, 2, 2]

    milp_solve(requests, rooms, parameters)
