import socket
import threading
import time
import datetime
import firebase_admin
from cryptography.hazmat.primitives import hashes
from firebase_admin import credentials, firestore
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dh, rsa, padding
from cryptography.hazmat.primitives.serialization import PublicFormat, Encoding, load_der_public_key


# entering the app
def sign_up(p_client_soc, p_name, p_pass, db):
    """
    gets username from client, check if it's in the database, if not sign up, otherwise send appropriate msg
    :param p_client_soc: the client socket
    :param p_name: the username of the client user
    :param p_pass: the password of the client user
    :param db: reference to the database
    :return: None
    """
    if find_name(p_name, db):  # the username is taken
        p_client_soc.send(b"Username is taken.")
        return

    doc_ref = db.collection(u'Users').document(p_name)
    doc_ref.set({'password': p_pass, 'socket': str(p_client_soc)})  # save the password and the socket in the database
    p_client_soc.send(b"Good username")
    return


def log_in(p_client_soc, p_name, p_pass, db):
    """
    gets username from client, check if it's in the database, if so log in, otherwise send appropriate msg
    :param p_name: the username of the client user
    :param p_pass: the password of the client user
    :param p_client_soc: the client socket
    :param db: reference to the database
    :return: None
    """
    if not find_name(p_name, db):  # the username not found, wait until it found
        p_client_soc.send(b"Username is not found.")
        return

    # username found
    doc_ref_user = db.collection(u'Users').document(p_name)
    doc_dict_user = doc_ref_user.get().to_dict()
    doc_ref_info = db.collection(u'Users').document(p_name)
    doc_dict_info = doc_ref_info.get().to_dict()
    if doc_dict_user['password'] == p_pass:
        doc_dict_info['socket'] = str(p_client_soc)
        doc_ref_info.set(doc_dict_info)  # save the socket in the database
        p_client_soc.send(b"Successfully log in.")
    else:
        p_client_soc.send(b"Wrong password.")


def find_name(p_name, db):
    """
    check if the username in the database
    :param p_name: the username we are checking
    :param db: reference to the database
    :return True/False: True if the username in the database, and false otherwise
    """
    doc_ref = db.collection(u'Users').document(p_name)
    doc = doc_ref.get()
    if doc.exists:
        return True
    return False


# update the info of a member in the database
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

    doc_ref = db.collection(u'UsersInfo').document(p_name)
    dict_data = doc_ref.get().to_dict()
    if dict_data is None:
        curr_cal = "0"
        curr_water = "0"
        curr_sleep = "00:00"
        week_cal = ["0", "0", "0", "0", "0", "0", "0"]
        week_water = ["0", "0", "0", "0", "0", "0", "0"]
        week_sleep = ["00:00", "00:00", "00:00", "00:00", "00:00", "00:00", "00:00"]

    else:
        curr_cal = dict_data['current cal']
        curr_water = dict_data['current water']
        curr_sleep = dict_data['current sleep']
        week_cal = dict_data['week_cal']
        week_water = dict_data['week_water']
        week_sleep = dict_data['week_sleep']

    # update the data dict
    dict_data = {'height': data[0],
                 'weight': data[1],
                 'age': data[2],
                 'sex': data[3],
                 'current cal': curr_cal,
                 'ideal cal': calc_ideal_cal(data[0], data[1], data[2], data[3]),
                 'user name': p_name,
                 'preferences': p_preferences,
                 'current water': curr_water,
                 'ideal water': calc_ideal_water(data[3]),
                 'current sleep': curr_sleep,
                 'ideal sleep': calc_ideal_sleep(data[2]),
                 'week_cal': week_cal,
                 'week_water': week_water,
                 'week_sleep': week_sleep,
                 'socket': str(p_client_soc)}

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


def calc_ideal_water(p_sex):
    """
    calculate the ideal amount of cups of water a person should drink a day
    :param p_sex: the sex of the user
    :return: the ideal amount of cups of water for a day - in string for the database
    """
    if p_sex == 'f':
        return str(12)
    return str(16)


def calc_ideal_sleep(p_age):
    """
    calculate the ideal amount hours a person should sleep a day
    :param p_age: the age of the user
    :return: the ideal amount of hours of sleep for a day - in string for the database
    """
    p_age = int(p_age)
    if p_age <= 13:
        return "11:00"
    if 14 <= p_age <= 17:
        return "10:00"
    if 18 <= p_age <= 25:
        return "09:00"
    if 26 <= p_age <= 64:
        return "08:00"
    return "07:00"


# update the health data of a member in the database
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

    if "_" in p_food:  # fix _ to space - the format in database
        p_food = p_food.replace("_", " ")

    # get amount of calories
    cal = get_food(p_food, db)

    if cal == "Not Found.":
        p_client_soc.send(b"Didn't find the food.")
        return

    cal_to_add = round(int(cal) * int(p_amount) / 100)
    doc_ref = db.collection(u'UsersInfo').document(p_name)
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

    doc_ref = db.collection(u'UsersInfo').document(p_name)
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


def enter_water(p_client_soc, p_name, db):
    """
    add the water cups the user drank to the document of the user in the database and send to the server appropriate msg
    :param p_client_soc: the client socket
    :param p_name: the username
    :param db: reference to the database
    :return: None
    """
    # get data from user
    data = p_client_soc.recv(1024).decode()

    if "error" in data:  # error state
        p_client_soc.send(b"Invalid.")
        return

    # get user data from database
    doc_ref = db.collection(u'UsersInfo').document(p_name)
    user_data = doc_ref.get().to_dict()

    # put new data in database
    curr_cups = int(user_data['current water']) + int(data)
    user_data['current water'] = str(curr_cups)
    doc_ref.set(user_data)
    p_client_soc.send(b"Finished.")
    return


def enter_sleep(p_client_soc, p_name, db):
    """
    add the water cups the user drank to the document of the user in the database and send to the server appropriate msg
    :param p_client_soc: the client socket
    :param p_name: the username
    :param db: reference to the database
    :return: None
    """
    # get data from user
    data = p_client_soc.recv(1024).decode()

    if "error" in data:  # error state
        p_client_soc.send(b"Invalid.")
        return

    start = data.split(" ")[0]  # start hour
    finish = data.split(" ")[1]  # finish hour

    # get user data from database
    doc_ref = db.collection(u'UsersInfo').document(p_name)
    user_data = doc_ref.get().to_dict()

    # calc the hours of sleep
    start_hour = start.split(":")[0]
    start_min = start.split(":")[1]
    finish_hour = finish.split(":")[0]
    finish_min = finish.split(":")[1]

    # check for errors
    if not (start_hour.isnumeric() and start_min.isnumeric() and finish_hour.isnumeric() and finish_min.isnumeric()):
        p_client_soc.send(b"Invalid.")
        return

    start_hour = int(start_hour)
    start_min = int(start_min)
    finish_hour = int(finish_hour)
    finish_min = int(finish_min)

    if start_hour > 23 or finish_hour > 23 or start_min > 59 or finish_min > 59:
        p_client_soc.send(b"Invalid.")
        return

    # hours
    if start_hour > 12:
        hours_this_time = finish_hour + 24 - start_hour
    else:
        hours_this_time = finish_hour - start_hour

    # minutes
    if finish_min < start_min:
        hours_this_time -= 1
        min_this_time = finish_min + 60 - start_min
    else:
        min_this_time = finish_min - start_min

    # fix for string
    if hours_this_time < 10:
        str_hours_this_time = "0" + str(hours_this_time)
    else:
        str_hours_this_time = str(hours_this_time)

    if min_this_time < 10:
        str_min_this_time = "0" + str(min_this_time)
    else:
        str_min_this_time = str(min_this_time)

    # error
    if hours_this_time < 0 or min_this_time < 0:
        p_client_soc.send(b"Invalid.")
        return

    sleep_time = str_hours_this_time + ":" + str_min_this_time

    # put new data in database
    user_data['current sleep'] = sleep_time
    doc_ref.set(user_data)
    p_client_soc.send(b"Finished.")
    return


# get data from database
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


# send data to client from database
def send_calories(p_client_soc, p_name, db):
    """
    sends the current and the ideal amount of calories to the client
    :param p_client_soc: the client soc
    :param p_name: the username
    :param db: reference to the database
    :return: None
    """
    doc_ref = db.collection(u'UsersInfo').document(p_name)
    dict_data = doc_ref.get().to_dict()
    data = dict_data['current cal'] + " " + dict_data['ideal cal']
    p_client_soc.send(data.encode())


def send_water(p_client_soc, p_name, db):
    """
    sends the current and the ideal amount of water cups to the client
    :param p_client_soc: the client soc
    :param p_name: the username
    :param db: reference to the database
    :return: None
    """
    doc_ref = db.collection(u'UsersInfo').document(p_name)
    dict_data = doc_ref.get().to_dict()
    data = dict_data['current water'] + " " + dict_data['ideal water']
    p_client_soc.send(data.encode())


def send_sleep(p_client_soc, p_name, db):
    """
    sends the current and the ideal amount of sleep hours to the client
    :param p_client_soc: the client soc
    :param p_name: the username
    :param db: reference to the database
    :return: None
    """
    doc_ref = db.collection(u'UsersInfo').document(p_name)
    dict_data = doc_ref.get().to_dict()
    data = dict_data['current sleep'] + " " + dict_data['ideal sleep']
    p_client_soc.send(data.encode())


def send_profile(p_client_soc, p_name, db):
    """
    sends the info of the user to the client
    :param p_client_soc: the client soc
    :param p_name: the username
    :param db: reference to the database
    :return: None
    """
    doc_ref = db.collection(u'UsersInfo').document(p_name)
    dict_data = doc_ref.get().to_dict()
    data = dict_data['age'] + " " + dict_data['height'] + " " + dict_data['weight'] + " " + dict_data['sex']
    p_client_soc.send(data.encode())


def weekly_report(p_client_soc, p_name, db):
    """
    get weekly report
    :param p_client_soc: the client socket
    :param p_name: the username
    :param db: reference to the database
    :return: None
    """
    doc_ref = db.collection(u'UsersInfo').document(p_name)
    dict_data = doc_ref.get().to_dict()

    # get data from database
    cal_arr = dict_data['week_cal']
    water_arr = dict_data['week_water']
    sleep_arr = dict_data['week_sleep']
    # initialize data to send
    cal_arr_data = ""
    water_arr_data = ""
    sleep_arr_data = ""

    # get curr day num
    today_date = datetime.date.today().strftime("%d %m %Y")
    # weekday assign mon. = 0 -> sun. = 6, I switch to sun. = 1 -> saturday = 7
    day_ref = (datetime.datetime.strptime(today_date, '%d %m %Y').weekday() + 1) % 7 + 1

    # update arrays in current data (-1, so we won't overflow the array)
    cal_arr[day_ref - 1] = dict_data['current cal']
    water_arr[day_ref - 1] = dict_data['current water']
    sleep_arr[day_ref - 1] = dict_data['current sleep']

    # calc avg cal
    sum_amount = 0
    for day in cal_arr:
        sum_amount += int(day)
        cal_arr_data += day + " "
    avg_cal = round(sum_amount / day_ref)

    # calc avg water cups
    sum_amount = 0
    for day in water_arr:
        sum_amount += int(day)
        water_arr_data += day + " "
    avg_water = round(sum_amount / day_ref)

    # calc avg sleep hours
    sum_amount = 0
    for day in sleep_arr:
        sum_amount += int(day.split(":")[0])*60
        sum_amount += int(day.split(":")[1])
        sleep_arr_data += day + " "
    avg_sleep_in_min = round(sum_amount / day_ref)  # the avg in minutes
    # calc avg hour
    avg_hour = round(avg_sleep_in_min / 60)
    if avg_hour < 10:
        avg_hour = "0" + str(avg_hour)
    else:
        avg_hour = str(avg_hour)
    # calc avg min
    avg_min = avg_sleep_in_min % 60
    if avg_min < 10:
        avg_min = "0" + str(avg_min)
    else:
        avg_min = str(avg_min)

    avg_sleep = avg_hour + ":" + avg_min

    # send data to client
    avg_data = str(avg_cal) + " " + str(avg_water) + " " + avg_sleep
    total_data = avg_data + "," + cal_arr_data + "," + water_arr_data + "," + sleep_arr_data
    for part in total_data.split(","):
        p_client_soc.send(part.encode())
        print(p_client_soc.recv(1024).decode())  # response for checking it got to client
    # p_client_soc.send(total_data.encode())
    return


# to be soon - suggestions for the members - based on their preferences and machine learning
def suggestions():
    # TODO write the function - get suggestions from member preferences and machine learning?
    pass


# some crypto :o
def switchKeysDH(p, g, c_soc):
    """
    switch keys diffie-hellman
    :param p: prime of the group
    :param g: generator of the group
    :param c_soc: the communication socket
    :type c_soc: socket.socket
    :return: the key
    """
    # parameters
    pn = dh.DHParameterNumbers(p, g)
    parameters = pn.parameters()

    # send p to client
    len_p = len(str(p))
    c_soc.send(len_p.to_bytes(2, "big") + p.to_bytes(len_p, "big"))
    feedback = c_soc.recv(1024).decode()
    if feedback != "good":  # sanity check
        return None

    # send g to client
    len_g = len(str(g))
    c_soc.send(len_g.to_bytes(2, "big") + g.to_bytes(len_g, "big"))
    feedback = c_soc.recv(1024).decode()
    if feedback != "good":  # sanity check
        return None

    # sk
    sk_server = parameters.generate_private_key()
    # pk = g^sk
    pk_server = sk_server.public_key()
    pk_server_bytes = pk_server.public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)  # encode to bytes

    # send to client pk
    c_soc.send(len(pk_server_bytes).to_bytes(2, "big") + pk_server_bytes)  # send also the len in bytes (for the recv)
    print(b"server sent: " + pk_server_bytes)

    # recv pk from client
    pk_client_len = int.from_bytes(c_soc.recv(2), "big")  # encode back to int from bytes
    pk_client_bytes = c_soc.recv(pk_client_len)
    print(b"server recv: " + pk_client_bytes)  # sanity check
    pk_client = load_der_public_key(pk_client_bytes, default_backend())  # decode back to dh object

    # create the shared key
    shared_key = sk_server.exchange(pk_client)

    return shared_key


# handle the client func for thread
def handle_client(c_soc, db):
    """
    handles threads (clients) requests
    :param c_soc: client socket
    :param db: reference to the database
    :return: None
    """
    # parameters for key
    p = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AAAC42DAD33170D04507A33A85521ABDF1CBA64ECFB850458DBEF0A8AEA71575D060C7DB3970F85A6E1E4C7ABF5AE8CDB0933D71E8C94E04A25619DCEE3D2261AD2EE6BF12FFA06D98A0864D87602733EC86A64521F2B18177B200CBBE117577A615D6C770988C0BAD946E208E24FA074E5AB3143DB5BFCE0FD108E4B82D120A92108011A723C12A787E6D788719A10BDBA5B2699C327186AF4E23C1A946834B6150BDA2583E9CA2AD44CE8DBBBC2DB04DE8EF92E8EFC141FBECAA6287C59474E6BC05D99B2964FA090C3A2233BA186515BE7ED1F612970CEE2D7AFB81BDD762170481CD0069127D5B05AA993B4EA988D8FDDC186FFB7DC90A6C08F4DF435C93402849236C3FAB4D27C7026C1D4DCB2602646DEC9751E763DBA37BDF8FF9406AD9E530EE5DB382F413001AEB06A53ED9027D831179727B0865A8918DA3EDBEBCF9B14ED44CE6CBACED4BB1BDB7F1447E6CC254B332051512BD7AF426FB8F401378CD2BF5983CA01C64B92ECF032EA15D1721D03F482D7CE6E74FEF6D55E702F46980C82B5A84031900B1C9E59E7C97FBEC7E8F323A97A7E36CC88BE0F1D45B7FF585AC54BD407B22B4154AACC8F6D7EBF48E1D814CC5ED20F8037E0A79715EEF29BE32806A1D58BB7C5DA76F550AA3D8A1FBFF0EB19CCB1A313D55CDA56C9EC2EF29632387FE8D76E3C0468043E8F663F4860EE12BF2D5B0B7474D6E694F91E6DCC4024FFFFFFFFFFFFFFFF
    g = 2
    key = switchKeysDH(p, g, c_soc)
    print(key)
    while True:
        data = c_soc.recv(1024).decode()
        if data != "":
            # get the commend and the username
            data = data.split(" ")
            commend = data[0]
            username = data[1]

            if commend == "log":
                log_in(c_soc, username, data[2], db)
            elif commend == "sign":
                sign_up(c_soc, username, data[2], db)
            elif commend == "update":
                info = c_soc.recv(1024).decode().split(" ")
                print(info)
                update_info(c_soc, username, info, db)
            elif commend == "cal":
                send_calories(c_soc, username, db)
            elif commend == "water":
                send_water(c_soc, username, db)
            elif commend == "sleep":
                send_sleep(c_soc, username, db)
            elif commend == "profile":
                send_profile(c_soc, username, db)
            elif commend == "report":
                weekly_report(c_soc, username, db)
            elif commend == "cups":
                enter_water(c_soc, username, db)
            elif commend == "hours":
                enter_sleep(c_soc, username, db)
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


# handling the database
def reset(db):
    """
    reset the current calories, cups of water and sleep hours when the day changes and update weekly data
    :param db: reference to the database
    :return: None
    """
    while True:
        t = time.localtime()
        current_time = time.strftime("%H:%M", t)  # get the current time
        hour = int(current_time.split(":")[0])
        minute = int(current_time.split(":")[1])
        today_date = datetime.date.today().strftime("%d %m %Y")
        # weekday assign mon. = 0 -> sun. = 6, I switch to sun. = 0 -> saturday = 6
        day_ref = (datetime.datetime.strptime(today_date, '%d %m %Y').weekday() + 1) % 7

        # if the day had passed, reset the current calories of the users and update week arrays
        # if hour == 0 and minute == 0:
        if hour > 0 and minute > 0:
            coll_ref = db.collection(u'UsersInfo').get()  # reference to the collection of users
            for doc in coll_ref:
                doc_dict = doc.to_dict()

                # handle different days
                if day_ref == 1:  # sunday ~00:00 -> reset date new week!
                    doc_dict['week_cal'] = ["0", "0", "0", "0", "0", "0", "0"]
                    doc_dict['week_water'] = ["0", "0", "0", "0", "0", "0", "0"]
                    doc_dict['week_sleep'] = ["00:00", "00:00", "00:00", "00:00", "00:00", "00:00", "00:00"]
                else:
                    doc_dict['week_cal'][day_ref] = doc_dict['current cal']
                    doc_dict['week_water'][day_ref] = doc_dict['current water']
                    doc_dict['week_sleep'][day_ref] = doc_dict['current sleep']

                # reset data new day :!
                doc_dict['current cal'] = "0"
                doc_dict['current water'] = "0"
                doc_dict['current sleep'] = "00:00"
                username = doc_dict['user name']
                doc_ref = db.collection(u'UsersInfo').document(username)
                doc_ref.set(doc_dict)


def main():
    open_sockets = []

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', 10000))
    server_socket.listen(10)

    cred = credentials.Certificate("json file goes here")
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
