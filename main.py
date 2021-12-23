import operator


class Request:
    def __init__(self, person_id, score):
        self.student_id = person_id
        self.score = score


class Room:
    def __init__(self, room_id, capacity):
        self.id = room_id
        self.capacity = capacity
        self.students = []


class Attribution:
    def __init__(self, request: Request, room: Room):
        self.request = request
        self.room = room

    def __str__(self):
        return "Student " + str(self.request.student_id) + " -- " + "Room " + str(self.room.id)


def simple_attribution(requests, rooms):
    attributions = []
    requests.sort(key=operator.attrgetter('score'), reverse=True)
    rooms.sort(key=operator.attrgetter('capacity'))

    rooms_iterator = 0
    rooms_number = len(rooms)

    for request in requests:

        if rooms_iterator >= rooms_number:
            break

        attributions.append(Attribution(request, rooms[rooms_iterator]))
        rooms[rooms_iterator].students.append(request.student_id)

        if len(rooms[rooms_iterator].students) == rooms[rooms_iterator].capacity:
            rooms_iterator += 1

    return attributions


if __name__ == '__main__':
    requests = []
    rooms = []
    for k in range(10):
        requests.append(Request(k+1, 10*k))
    for k in range(5):
        rooms.append(Room(k+1, 1))
    rooms.append(Room(6, 2))

    attributions = simple_attribution(requests, rooms)
    for attribution in attributions:
        print(attribution)
