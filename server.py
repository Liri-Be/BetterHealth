import socket
import select
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
    ideal = 10 * int(p_weight) + 6.25 * int(p_height) - 5 * int(p_age)
    if p_sex == 'f':
        ideal = ideal - 161
    else:
        ideal = ideal + 5
    ideal = round(ideal)
    return str(ideal)


def enter_food(p_client_soc, p_food, p_amount, p_name, db):
    """
    add the calories from the food to the document of the user in the database and send to the server appropriate msg
    :param p_client_soc: teh client socket
    :param p_food: the type of food
    :param p_amount: the amount of the food
    :param p_name: the username
    :param db: reference to the database
    :return: None
    """
    cal = get_food(p_food, db)

    if cal == "Not Found.":
        p_client_soc.send(b"Didn't find the food.")

    cal_to_add = round(int(cal) * int(p_amount) / 100)
    doc_ref = db.collection(u'Names').document(p_name)
    data = doc_ref.get().to_dict()
    current = int(data['current cal']) + cal_to_add
    data['current cal'] = str(current)
    doc_ref.set(data)
    p_client_soc.send(b"Finished.")


def enter_sport(p_client_soc, p_sport, p_amount, p_name, db):
    """
    add the calories from the food to the document of the user in the database and send to the server appropriate msg
    :param p_client_soc: the client socket
    :param p_sport: the type of sport
    :param p_amount: the amount
    :param p_name: the username
    :param db: reference to the database
    :return: None
    """
    doc_ref = db.collection(u'Names').document(p_name)
    data = doc_ref.get().to_dict()
    p_weight = data['weight']

    cal = get_sport(p_sport, p_weight, db)

    if cal == "Not Found.":
        p_client_soc.send(b"Didn't find the sport.")

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
    coll_ref = db.collection(u'Names').get()  # reference to the collection of users
    t = time.localtime()
    current_time = time.strftime("%H:%M", t)  # get the current time
    hour = int(current_time.split(":")[0])
    minute = int(current_time.split(":")[1])
    if hour == 0 and 0 <= minute <= 10:  # if the day had passed, reset the current calories of the users
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
        p_name = p_client_soc.recv(1024).decode()

    # the username is not taken and can sign in
    p_client_soc.send(b"Send data")
    data = p_client_soc.recv(1024).decode().split(" ")

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
    :param db: reference to
    :return:
    """
    doc_ref = db.collection(u'Names').document(p_name)
    dict_data = doc_ref.get().to_dict()
    data = dict_data['current cal'] + " " + dict_data['ideal cal']
    p_client_soc.send(data.encode())


def main():
    open_sockets = []

    server_socket = socket.socket()
    server_socket.bind(('192.168.56.1', 10000))
    server_socket.listen(10)

    cred = credentials.Certificate(r".\sample-3ae1d-firebase-adminsdk-wzkym-7e9ac9fcc9.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()  # reference to database

    new_soc = ""

    while True:
        r, w, e = select.select([server_socket] + open_sockets, open_sockets, [])
        for soc in r:
            if soc is server_socket:
                (new_soc, address) = server_socket.accept()
                open_sockets.append(new_soc)
                data = new_soc.recv(1024).decode()
                print(data)
                if data != "":
                    data = data.split(" ")
                    commend = data[0]
                    username = data[1]
                    if commend == "log":
                        log_in(new_soc, username, db)
                    elif commend == "sign":
                        sign_up(new_soc, username, db)
            else:
                data = new_soc.recv(1024).decode()
                if data != "":
                    data = data.split(" ")
                    commend = data[0]
                    username = data[1]
                    if commend == "log":
                        log_in(new_soc, username, db)
                    elif commend == "sign":
                        sign_up(new_soc, username, db)
                    elif commend == "update":
                        info = new_soc.recv(1024).decode().split(" ")
                        print(info)
                        update_info(new_soc, username, info, db)
                    elif commend == 'main':
                        send_calories(new_soc, username, db)
                    elif commend == 'error':
                        new_soc.send(b"Invalid.")

        reset(db)


if __name__ == '__main__':
    main()
