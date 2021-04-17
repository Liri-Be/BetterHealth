import socket
import threading
import time
import firebase_admin
from firebase_admin import credentials, firestore


def update_info(p_client_soc, p_name, data, db):
    """
    update the info of a member in the database
    :param p_client_soc: the client socket - socket
    :param p_name: the username - string
    :param data: the data of the user - array of data
    :param db: reference to the database
    :return: None
    """
    if data[0] == "error":
        p_client_soc.send(b"Invalid.")
        return

    p_preferences = ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]
    for i in range(0, len(data) - 5):  # fill preferences arr
        p_preferences[i] = data[i + 4]

    doc_ref = db.collection(u'Names').document(p_name)
    dict_data = doc_ref.get().to_dict()

    # update the data dict
    dict_data['height'] = data[0]
    dict_data['weight'] = data[1]
    dict_data['age'] = data[2]
    dict_data['sex'] = data[3]
    dict_data['ideal cal'] = calc_ideal_cal(data[0], data[1], data[2], data[3])
    dict_data['preferences'] = p_preferences
    dict_data['socket'] = str(p_client_soc)

    # save the changes
    doc_ref.set(dict_data)
    p_client_soc.send(b"Successfully updated info.")


def calc_ideal_cal(p_height, p_weight, p_age, p_sex):
    """
    calculate the ideal amount of calories for a day
    :param p_height: the height of the user
    :param p_weight: the weight of the user
    :param p_age: the age of the user
    :param p_sex: the sex of the user
    :return: the ideal amount of calories for a day - in string for the database
    """
    if p_sex == 'm':
        ideal = 66 + 6.2 * int(p_weight) + 12.7 * int(p_height) - 6.76 * int(p_age)
    else:
        ideal = 655.1 + 4.35 * int(p_weight) + 4.7 * int(p_height) - 4.76 * int(p_age)
    ideal = round(ideal)
    return str(ideal)


def enter_food(p_client_soc, p_name, db):
    """
    add the calories from the food to the document of the user in the database and send to the server appropriate msg
    :param p_client_soc: teh client socket

    :param p_name: the username
    :param db: reference to the database
    :return: None
    """
    # get data from user
    data = p_client_soc.recv(1024).decode().split(" ")

    if data[0] == "error":  # error state
        p_client_soc.send(b"Invalid.")
        return

    # good input
    p_food = data[0]
    p_amount = data[1]

    # get amount of calories
    cal = get_food(p_food, db)

    if cal == "Not Found.":
        p_client_soc.send(b"Didn't find the food.")
        return

    cal_to_add = round(int(cal) * int(p_amount) / 100)
    doc_ref = db.collection(u'Names').document(p_name)
    data = doc_ref.get().to_dict()
    current = int(data['current cal']) + cal_to_add
    data['current cal'] = str(current)
    doc_ref.set(data)
    p_client_soc.send(b"Finished.")


def enter_sport(p_client_soc, p_name, db):
    """
    add the calories from the food to the document of the user in the database and send to the server appropriate msg
    :param p_client_soc: the client socket
    :param p_name: the username
    :param db: reference to the database
    :return: None
    """
    # get data from user
    data = p_client_soc.recv(1024).decode().split(" ")

    if data[0] == "error":  # error state
        p_client_soc.send(b"Invalid.")
        return

    # good input
    p_sport = data[0]
    p_amount = data[1]

    doc_ref = db.collection(u'Names').document(p_name)
    data = doc_ref.get().to_dict()
    p_weight = data['weight']

    cal = get_sport(p_sport, p_weight, db)

    if cal == "Not Found.":
        p_client_soc.send(b"Didn't find the sport.")
        return

    cal_split = cal.split(".")
    cal_to_dec = int(cal_split[0]) + int(cal_split[1]) / 10
    cal_to_dec = round(cal_to_dec * int(p_amount))
    current = int(data['current cal']) - cal_to_dec
    if current < 0:
        data['current cal'] = "0"
    else:
        data['current cal'] = str(current)

    doc_ref.set(data)
    p_client_soc.send(b"Finished.")


def reset(db):
    """
    reset the current calories when the day changes
    :param db: reference to the database
    :return: None
    """
    while True:
        t = time.localtime()
        current_time = time.strftime("%H:%M", t)  # get the current time
        hour = int(current_time.split(":")[0])
        minute = int(current_time.split(":")[1])
        if hour == 0 and 0 <= minute <= 2:  # if the day had passed, reset the current calories of the users
            coll_ref = db.collection(u'Names').get()  # reference to the collection of users
            for doc in coll_ref:
                doc_dict = doc.to_dict()
                doc_dict['current cal'] = "0"
                username = doc_dict['user name']
                doc_ref = db.collection(u'Names').document(username)
                doc_ref.set(doc_dict)


def suggestions():
    # TODO write the function - get suggestions from member preferences and machine learning?
    pass


def sign_up(p_client_soc, p_name, db):
    """
    gets username from client, check if it's in the database, if not sign up, otherwise send appropriate msg
    :param p_client_soc: the client socket
    :param p_name: the username of the client user
    :param db: reference to the database
    :return: None
    """
    if find_name(p_name, db):  # the username is taken
        p_client_soc.send(b"Username is taken.")
        return

    # the username is not taken and can sign in
    p_client_soc.send(b"Send data")
    data = p_client_soc.recv(1024).decode().split(" ")

    if data[0] == "error":
        p_client_soc.send(b"Invalid.")
        return

    p_preferences = ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]
    for i in range(0, len(data) - 5):  # fill preferences arr
        p_preferences[i] = data[i + 4]

    dict_data = {'height': data[0],
                 'weight': data[1],
                 'age': data[2],
                 'sex': data[3],
                 'current cal': "0",
                 'ideal cal': calc_ideal_cal(data[0], data[1], data[2], data[3]),
                 'user name': p_name,
                 'preferences': p_preferences,
                 'socket': str(p_client_soc)}

    doc_ref = db.collection(u"Names").document(p_name)
    doc_ref.set(dict_data)

    p_client_soc.send(b"Successfully signed up.")


def log_in(p_client_soc, p_name, db):
    """
    gets username from client, check if it's in the database, if so log in, otherwise send appropriate msg
    :param p_name: the username of the client user
    :param p_client_soc: the client socket
    :param db: reference to the database
    :return: None
    """
    if not find_name(p_name, db):  # the username not found, wait until it found
        p_client_soc.send(b"Username is not found.")
        return

    # username found
    doc_ref = db.collection(u'Names').document(p_name)
    doc_dict = doc_ref.get().to_dict()
    doc_dict['socket'] = str(p_client_soc)
    doc_ref.set(doc_dict)  # save the socket in the database
    p_client_soc.send(b"Successfully log in.")


def find_name(p_name, db):
    """
    check if the username in the database
    :param p_name: the username we are checking
    :param db: reference to the database
    :return True/False: True if the username in the database, and false otherwise
    """
    doc_ref = db.collection(u'Names').document(p_name)
    doc = doc_ref.get()
    if doc.exists:
        return True
    return False


def get_food(p_food, db):
    """
    get the calories for 100 gram of a specific type of food from database
    :param p_food: the food
    :param db: reference to the database
    :return: the amount of calories - string
    """
    doc_ref = db.collection(u'Food').document(p_food)
    dict_food = doc_ref.get().to_dict()
    if dict_food is None:
        return "Not Found."
    return dict_food['cal']


def get_sport(p_sport, p_weight, db):
    """
    get the calories that burned in 1 min of a specific type of sport from database
    :param p_sport: the sport
    :param p_weight: the weight of the person
    :param db: reference to the database
    :return: the amount of calories - string
    """
    doc_ref = db.collection(u'Sport').document(p_sport)
    dict_food = doc_ref.get().to_dict()
    if dict_food is None:
        return "Not Found."
    if int(p_weight) <= 55:
        return dict_food['55']
    elif 55 < int(p_weight) <= 65:
        return dict_food['65']
    elif 65 < int(p_weight) <= 75:
        return dict_food['75']
    else:
        return dict_food['85']


def send_calories(p_client_soc, p_name, db):
    """
    sends the current and the ideal amount of calories to the client
    :param p_client_soc: the client soc
    :param p_name: the username
    :param db: reference to the database
    :return: None
    """
    doc_ref = db.collection(u'Names').document(p_name)
    dict_data = doc_ref.get().to_dict()
    data = dict_data['current cal'] + " " + dict_data['ideal cal']
    p_client_soc.send(data.encode())


def handle_client(c_soc, db):
    """
    handles threads (clients) requests
    :param c_soc: client socket
    :param db: reference to the database
    :return: None
    """
    while True:
        data = c_soc.recv(1024).decode()
        if data != "":
            # get the commend and the username
            data = data.split(" ")
            commend = data[0]
            username = data[1]

            if commend == "log":
                log_in(c_soc, username, db)
            elif commend == "sign":
                sign_up(c_soc, username, db)
            elif commend == "update":
                info = c_soc.recv(1024).decode().split(" ")
                print(info)
                update_info(c_soc, username, info, db)
            elif commend == "main":
                send_calories(c_soc, username, db)
            elif commend == "food":
                enter_food(c_soc, username, db)
            elif commend == "sport":
                enter_sport(c_soc, username, db)
            elif commend == "error":
                c_soc.send(b"Invalid.")
            elif commend == "off":
                c_soc.send(b"Goodbye.")
                c_soc.close()
                break


def main():
    open_sockets = []

    server_socket = socket.socket()
    server_socket.bind(('', 10000))
    server_socket.listen(10)

    cred = credentials.Certificate(r".\sample-3ae1d-firebase-adminsdk-wzkym-7e9ac9fcc9.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()  # reference to database

    th = threading.Thread(target=reset, args=(db,))  # make a thread that will take care of resetting the database
    th.start()

    while True:
        (c_soc, address) = server_socket.accept()
        print("someone connected")
        open_sockets.append(c_soc)
        th = threading.Thread(target=handle_client, args=(c_soc, db))
        th.start()


if __name__ == '__main__':
    main()
