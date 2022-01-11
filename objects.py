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


class Room:
    def __init__(self, room_id, room_type):
        self.id = room_id
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
        if self.room_type == 1:
            print("simple")
        elif self.room_type == 2:
            print("binômée")
        else:
            print("double")


class Attribution:
    def __init__(self, request: Request, room: Room):
        self.request = request
        self.room = room

    def __str__(self):
        return "Student " + str(self.request.student_id) + " -- " + "Room " + str(self.room.id)
