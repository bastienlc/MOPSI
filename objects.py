class Request:
    def __init__(self, student_id, gender, scholarship, distance, prefered_room_type, accept_other_type, has_mate, mate_id, shotgun_rank):
        self.student_id = student_id
        self.gender = gender
        self.scholarship = scholarship
        self.distance = distance
        self.prefered_room_type = prefered_room_type
        self.accept_other_type = accept_other_type
        if not has_mate:
            self.has_mate = False
            self.mate_id = None
        else:
            self.has_mate = True
            self.mate_id = mate_id
        self.shotgun_rank = shotgun_rank

    def __str__(self):
        return "\nstudent_id: " + str(self.student_id)\
               + "\ngender: " + str(self.gender)\
               + "\nscholarship: " + str(self.scholarship)\
               + "\ndistance: " + str(self.distance)\
               + "\nprefered_room_type: " + str(self.prefered_room_type)\
               + "\naccept_other_type: " + str(self.accept_other_type)\
               + "\nhas_mate: " + str(self.has_mate)\
               + "\nmate_id: " + str(self.mate_id)\
               + "\nshotgun_rank: " + str(self.shotgun_rank)



class Room:
    def __init__(self, room_id, room_type):
        self.room_id = room_id
        self.room_type = room_type
        if room_type == 0:  # chambre simple
            self.capacity = 1
            self.students = []
        elif room_type == 1:  # chambre binomée
            self.capacity = 2
            self.students = []
        elif room_type == 2:  # chambre double
            self.capacity = 2
            self.students = []
        else:
            print("Room type error")

    def what_room_type(self):
        if self.room_type == 0:
            return "simple"
        elif self.room_type == 1:
            return "binômée"
        else:
            return "double"

    def __str__(self):
        return "\nroom_type: " + str(self.room_type)\
               + "\nroom_id: " + str(self.room_id)\
               + "\ncapacity: " + str(self.capacity)\
               + "\nstudents: " + str(self.students)


class Attribution:
    def __init__(self, request: Request, room: Room, mate_id=None):
        self.request = request
        self.room = room
        self.mate = mate_id

    def set_mate(self, mate_id):
        self.mate = mate_id

    def __str__(self):
        if self.mate:
            return ("Student " + str(self.request.student_id) +
                    " -- " + "Room " + str(self.room.room_id) +
                    " -- " + "With " + str(self.mate))
        else:
            return "Student " + str(self.request.student_id) + " -- " + "Room " + str(self.room.room_id) + " -- "  + "Alone"
