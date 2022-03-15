import operator
from objects import Request, Room, Attribution


def get_buddy_request(requests_list, buddy_id):
    for request in requests_list:
        if request.student_id == buddy_id:
            return request


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


def attribution_with_buddy(requests, rooms):
    attributions = []
    requests.sort(key=operator.attrgetter('score'), reverse=True)
    ranks = {}
    for rank, request in enumerate(requests):
        ranks[request.student_id] = rank+1
    rooms.sort(key=operator.attrgetter('capacity'))

    simple_iterator = 0
    double_iterator = 0
    while rooms[double_iterator].capacity == 1:
        double_iterator += 1
    double_limit = len(rooms)
    simple_limit = double_iterator

    number_of_places = 0
    for room in rooms:
        number_of_places += room.capacity
    if len(requests) > number_of_places:
        requests = requests[:number_of_places]
    for request in requests:
        if request.has_buddy and ranks[request.buddy_id] > number_of_places:
            request.has_buddy = False


    for rank, request in enumerate(requests):

        if request.has_buddy and double_iterator < double_limit:
            if len(rooms[double_iterator].students)==0:
                attributions.append(Attribution(request, rooms[double_iterator]))
                rooms[double_iterator].students.append(request.student_id)
                buddy_request = get_buddy_request(requests[rank:], request.buddy_id)
                requests.remove(buddy_request)
                attributions.append(Attribution(buddy_request, rooms[double_iterator]))
                rooms[double_iterator].students.append(buddy_request.student_id)
                double_iterator += 1
            elif double_iterator+1 < double_limit:
                attributions.append(Attribution(request, rooms[double_iterator+1]))
                rooms[double_iterator].students.append(request.student_id)
                buddy_request = get_buddy_request(requests[rank:], request.buddy_id)
                requests.remove(buddy_request)
                attributions.append(Attribution(buddy_request, rooms[double_iterator+1]))
                rooms[double_iterator].students.append(buddy_request.student_id)
            else:
                buddy_request = get_buddy_request(requests[rank:], request.buddy_id)
                buddy_request.has_buddy = False
                if simple_iterator < simple_limit:
                    attributions.append(Attribution(request, rooms[simple_iterator]))
                    rooms[simple_iterator].students.append(request.student_id)
                    simple_iterator += 1
                else:
                    if len(rooms[double_iterator].students) == 2:
                        double_iterator += 1
                    attributions.append(Attribution(request, rooms[double_iterator]))
                    rooms[double_iterator].students.append(request.student_id)
                    if len(rooms[double_iterator].students) == 2:
                        double_iterator += 1
        else:
            if simple_iterator < simple_limit:
                attributions.append(Attribution(request, rooms[simple_iterator]))
                rooms[simple_iterator].students.append(request.student_id)
                simple_iterator += 1
            else:
                if len(rooms[double_iterator].students)==2:
                    double_iterator += 1
                attributions.append(Attribution(request, rooms[double_iterator]))
                rooms[double_iterator].students.append(request.student_id)
                if len(rooms[double_iterator].students) == 2:
                    double_iterator += 1

    return attributions


if __name__ == '__main__':
    # requests = []
    # rooms = []
    # for k in range(8):
    #     requests.append(Request(k+1, 10*k))
    # requests.append(Request(9, 10*8, 10))
    # requests.append(Request(10, 10 * 9, 9))
    # for k in range(5):
    #     rooms.append(Room(k+1, 1))
    # rooms.append(Room(6, 2))
    #
    # #attributions = simple_attribution(requests, rooms)
    # attributions = attribution_with_buddy(requests, rooms)
    # for attribution in attributions:
    #     print(attribution)
    pass
