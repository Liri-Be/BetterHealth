import hashlib

from cryptography.hazmat.primitives import hashes
from kivy.metrics import dp
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, ListProperty, StringProperty, BooleanProperty
from kivymd.uix.button import MDFillRoundFlatIconButton
from kivymd.uix.datatables import MDDataTable
import socket
from hashlib import sha256
from kivymd.uix.textfield import MDTextField
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dh, rsa, padding
from cryptography.hazmat.primitives.serialization import PublicFormat, Encoding, load_der_public_key

# the possible choices for user
FOOD_VALUES = ["Apple", "Bagel", "Banana", "Beans", "Beef", "Blackberries", "Bread white", "Bread wholemeal",
               "Broccoli", "Butter", "Cabbage", "Cauliflower", "Celery", "Chicken", "Chocolate", "Cornflakes",
               "Cottage cheese", "Cream cheese", "Cucumber", "Dates", "Egg", "Grapes", "Honey", "Ice cream", " Jam",
               "Kiwi", "Lettuce", "Liver", "Margarine", "Melon", "Milk", "Muesli", "Mushrooms", "Noodles", "Oil",
               "Olives", "Onion", " Orange", "Pasta", "Peach", "Pear", "Peas", "Pepper yellow", "Pineapple", "Popcorn",
               "Potatoes", "Rice", "Salmon", "Sardines", "Spaghetti", "Steak", "Strawberries", "Syrup", "Toffee",
               "Tomato", "Tomato cherry", "Tuna", "White cheese", "White sugar", "Yogurt"]
SPORT_VALUES = ["Basketball", "Bowling", "Cycling", "Dancing", "Gardening", "Golf", "Hiking", "Jogging", "Skating",
                "Skiing", "Swimming", "Tennis", "Walking", "Weight Training"]


class User:
    def __init__(self, c_soc, p, g, k):
        """
        constructor
        :param c_soc: client_socket
        :type c_soc: socket.socket
        :param p: prime of group - diffie hellman
        :param g: generator of group - diffie hellman
        :param k: key
        """
        # communication with the server
        self.client_socket = c_soc  # the current client socket
        self.key = k  # the shared key for communication with the server
        self.p = p
        self.g = g
        self.sk, self.pk = self.createKeysRSA()  # the RSA keys for communication with the server
        self.pk_server = self.switchKeysRSA()  # the public key of the server
        # data of the user
        self.username = ""
        self.current_cal = ""
        self.ideal_cal = ""
        self.current_water = ""
        self.ideal_water = ""
        self.current_sleep = ""
        self.ideal_sleep = ""
        self.height = ""
        self.weight = ""
        self.age = ""
        self.sex = ""

    # RSA encryption and decryption for data transfer between client and server
    @staticmethod
    def createKeysRSA():
        """
        create keys for asymmetric encryption
        :return: sk and pk
        """
        sk = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        pk = sk.public_key()
        return sk, pk

    def switchKeysRSA(self):
        """
        switch keys RSA
        :return: our sk and the pk of the server
        """
        # recv pk from server
        pk_server_len = int.from_bytes(self.client_socket.recv(2), "big")  # encode back to int from bytes
        pk_server_bytes = self.client_socket.recv(pk_server_len)
        print(b"client recv: " + pk_server_bytes)  # sanity check
        pk_server = load_der_public_key(pk_server_bytes, default_backend())  # decode back to dh object

        # send our pk to server
        pk_client_bytes = self.pk.public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)  # encode to bytes
        self.client_socket.send(
            len(pk_client_bytes).to_bytes(2, "big") + pk_client_bytes)  # send also the len in bytes (for the recv)
        print(b"client sent: " + pk_client_bytes)  # sanity check

        return pk_server

    def encryptRSA(self, msg):
        """
        encrypt msg with RSA
        :param msg: the msg to encrypt
        :return: the encrypted msg
        """
        return self.pk_server.encrypt(msg, padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))

    def decryptRSA(self, cipher):
        """
        decrypt msg with RSA
        :param cipher: the cipher to decrypt
        :return: the decrypted msg
        """
        return self.sk.decrypt(cipher, padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))

    # send and receive data from the server
    def send_to_server(self, data):
        """
        send data to the server
        :param data: the data to send in string
        :return: None
        """
        cipher = self.encryptRSA(data.encode())
        self.client_socket.send(cipher)

    def recv_from_server(self):
        """
        receive data from the server
        :return: the data - string
        """
        cipher = self.client_socket.recv(256)
        data = self.decryptRSA(cipher).decode()
        return data

    def update_calories(self):
        """
        update the current and ideal calories with data from the server
        :return: None
        """
        self.send_to_server("cal" + " " + self.username)
        data = self.recv_from_server().split(" ")
        self.current_cal = data[0]
        self.ideal_cal = data[1]

    def update_water(self):
        """
        update the current and ideal water with data from the server
        :return: None
        """
        self.send_to_server("water" + " " + self.username)
        data = self.recv_from_server().split(" ")
        self.current_water = data[0]
        self.ideal_water = data[1]

    def update_sleep(self):
        """
        update the current and ideal sleep with data from the server
        :return: None
        """
        self.send_to_server("sleep" + " " + self.username)
        data = self.recv_from_server().split(" ")
        self.current_sleep = data[0]
        self.ideal_sleep = data[1]

    def update_profile(self):
        """
        update the info with data from the server
        :return: None
        """
        self.send_to_server("profile" + " " + self.username)
        data = self.recv_from_server().split(" ")
        self.age = data[0]
        self.height = data[1]
        self.weight = data[2]
        if data[3] == "f":
            self.sex = "female"
        else:
            self.sex = "male"

    def get_statistics(self):
        """
        get from the user avg and daily amounts of cal, water cups and sleep hours
        :return: dict of avg and daily amounts of cal, water cups and sleep hours
        """
        self.send_to_server("report" + " " + self.username)
        whole_data = []
        for _ in range(4):
            whole_data.append(self.recv_from_server())
            self.send_to_server("good")
        avg = whole_data[0]
        cal = whole_data[1]
        water = whole_data[2]
        sleep = whole_data[3]
        return avg, cal, water, sleep


# start screen classes
class StartScreen(Screen):
    def __init__(self, user, **kw):
        """
        constructor
        :param user: the user that use the screen
        :type User
        """
        self.user = user  # the user that use the screen
        super().__init__(**kw)

    def pressed_log_in(self):
        """
        when pressing the login button it moves to log in screen
        :return: None
        """
        self.manager.current = 'log in'

    def pressed_sign_up(self):
        """
        when pressing the signup button it moves to signup screen
        :return: None
        """
        self.manager.current = 'sign up'

    def pressed_instru(self):
        """
        when pressing the instructions button it shows the instructions of logging and signing to the app
        :return: None
        """
        self.manager.current = 'start instru'

    def pressed_exit(self):
        """
        when pressing the exit button it sends data to the server and modify it that we are leaving the app
        and close the screen
        :return: None
        """
        self.user.send_to_server("off" + " " + ".")
        data = self.user.recv_from_server()
        if "Goodbye" in data:  # exit
            BetterHealthApp.get_running_app().stop()
            Window.close()


class LogInScreen(Screen):
    username = ObjectProperty(None)
    password = ObjectProperty(None)

    def __init__(self, user, **kwargs):
        """
        constructor
        :param user: the user that use the screen
        :type User
        """
        self.user = user  # the user that use the screen
        super(LogInScreen, self).__init__(**kwargs)
        self.username = self.ids['username']
        self.password = self.ids['password']
        self.error_lbl = self.ids['error_msg']

    def pressed(self):
        """
        when pressing the login button it modifies the server we are logging in
        and sends data (username) to the server - logs in if succeeded, else shows appropriate msg
        :return: None
        """
        username = self.username.text
        password = self.password.text

        if " " in username or username == "" or " " in password or password == "":  # error state
            self.user.send_to_server("error" + " " + username)
            self.error_lbl.text = self.user.recv_from_server()
            return

        # hash the password :P crypto wow!
        hashed_pwd = sha256(password.encode()).hexdigest()

        # modify the server we are logging in
        self.user.send_to_server("log" + " " + username)  # send the username
        self.user.send_to_server(hashed_pwd)  # send the hashed password
        data_from_server = self.user.recv_from_server()  # get answer whether we logged in or not

        if "Successfully" in data_from_server:
            print(":)")
            self.user.username = username
            # update the server that we need the calories, water cups and sleep hours of user
            self.user.update_calories()
            self.user.update_water()
            self.user.update_sleep()
            self.manager.current = 'main'

        else:
            print(":(")
            self.error_lbl.text = data_from_server  # "Username has not found. / Wrong password."


class SignUpScreen(Screen):
    username = ObjectProperty(None)
    password = ObjectProperty(None)

    def __init__(self, user, **kwargs):
        """
        constructor
        :param user: the user that use the screen
        :type User
        """
        self.user = user  # the user that use the screen
        super(SignUpScreen, self).__init__(**kwargs)
        self.username = self.ids['username']
        self.password = self.ids['password']
        self.error_lbl = self.ids['error_msg']

    def pressed(self):
        """
        when pressing the signup button it modifies the server we are signing up
        and sends data (username) to the server - moves to get user's date if succeeded, else shows appropriate msg
        :return: None
        """
        username = self.username.text
        password = self.password.text

        if " " in username or username == "" or " " in password or password == "":  # error state
            self.user.send_to_server("error" + " " + username + " " + password)
            self.error_lbl.text = self.user.recv_from_server()
            return

        # hash the password :P crypto wow!
        hashed_pwd = sha256(password.encode()).hexdigest()

        # modify the server we are signing up
        self.user.send_to_server("sign" + " " + username + " " + hashed_pwd)
        data_from_server = self.user.recv_from_server()

        if "Good" in data_from_server:
            print(":)")
            self.user.username = username
            self.manager.current = 'update info'  # move to the screen where we get user's data

        else:
            print(":(")
            self.error_lbl.text = "Username is taken."


class StartInstructions(Screen):
    def pressed(self):
        """
        when pressing the back button it returns to the start screen
        :return: None
        """
        self.manager.current = 'start'


# MDTextField but for passwords, better version (fletcher)!
class MDTextFieldPassword(MDTextField):
    password_mode = BooleanProperty(True)

    def on_touch_down(self, touch):
        """
        when we press the password bar, check if we pressed the eye icon and make the password visible or invisible
        according to the state it is right now
        :param touch: object of the place we pressed now
        :return: superclass
        """
        if self.collide_point(*touch.pos):
            if self.icon_left:
                # icon position based on the KV code for MDTextField - stackoverflow!
                up_bound_x = self.x + self._icon_left_label.texture_size[1] + dp(8)
                down_bound_x = self.x + dp(8)
                up_bound_y = self.center[1] + self._icon_left_label.texture_size[1] / 2
                down_bound_y = self.center[1] - self._icon_left_label.texture_size[1] / 2

                # check if pressed in the range of the icon
                if down_bound_x < touch.pos[0] < up_bound_x and down_bound_y < touch.pos[1] < up_bound_y:
                    # if pressed - switch between on and off :)
                    if self.password_mode:  # now on -> off (password visible)
                        self.icon_left = 'eye'
                        self.password_mode = False
                        self.password = self.password_mode
                    else:  # now off -> on (password invisible)
                        self.icon_left = 'eye-off'
                        self.password_mode = True
                        self.password = self.password_mode

        return super(MDTextFieldPassword, self).on_touch_down(touch)


# main screen classes
class MainScreen(Screen):
    username = StringProperty("")

    def __init__(self, user, **kw):
        """
        constructor
        :param user: the user that use the screen
        :type User
        """
        self.user = user  # the user that use the screen
        super().__init__(**kw)

    def update_username(self):
        self.username = self.user.username

    def pressed_cal(self):
        """
        when pressing the cal button it goes to the cal screen
        :return: None
        """
        self.manager.current = 'cal'

    def pressed_water(self):
        """
        when pressing the water button it goes to the water screen
        :return: None
        """
        self.manager.current = 'water'

    def pressed_sleep(self):
        """
        when pressing the sleep button it goes to the sleep screen
        :return: None
        """
        self.manager.current = 'sleep'

    def pressed_profile(self):
        """
        when pressing the see profile button it goes to the profile screen
        :return:
        """
        self.user.update_profile()
        self.manager.current = 'profile'

    def pressed_instru(self):
        """
        when pressing the instru button it goes to the instru screen
        :return: None
        """
        self.manager.current = 'main instru'

    def pressed_update(self):
        """
        when pressing the update info button it goes to the update info screen
        :return: None
        """
        self.manager.current = 'update info'

    def pressed_report(self):
        """
        when pressing the weekly report button it goes to the weekly report screen
        :return: None
        """
        self.manager.current = 'report'

    def pressed_exit(self):
        """
        when pressing the exit button it sends data to the server and modify it that we are leaving the app
        and close the screen
        :return: None
        """
        self.user.send_to_server("off" + " " + ".")
        data = self.user.recv_from_server()
        if "Goodbye" in data:  # exit
            BetterHealthApp.get_running_app().stop()
            Window.close()


class ProfileScreen(Screen):
    def __init__(self, user, **kwargs):
        """
        constructor
        :param user: the user that use the screen
        :type User
        """
        self.user = user  # the user that use the screen
        super(ProfileScreen, self).__init__(**kwargs)
        self.username_lbl = self.ids['username']
        self.age_lbl = self.ids['age']
        self.height_lbl = self.ids['height']
        self.weight_lbl = self.ids['weight']
        self.sex_lbl = self.ids['sex']

    def update_labels(self):
        """
        shows the currant info of the user
        :return: None
        """
        self.username_lbl.text = "Username: " + self.user.username
        self.age_lbl.text = "Age: " + self.user.age
        self.height_lbl.text = "Height: " + self.user.height + " (cm)"
        self.weight_lbl.text = "Weight: " + self.user.weight + " (kg)"
        self.sex_lbl.text = "Sex: " + self.user.sex
        return

    def pressed_main(self):
        """
        when pressing the main button it moves to the main screen
        :return: None
        """
        self.manager.current = 'main'


class UpdateInfoScreen(Screen):
    # vars for user's data
    user_age = ObjectProperty(None)
    user_height = ObjectProperty(None)
    user_weight = ObjectProperty(None)
    user_sex = ObjectProperty(None)

    def __init__(self, user, **kwargs):
        """
        constructor
        :param user: the user that use the screen
        :type User
        """
        self.user = user  # the user that use the screen
        super(UpdateInfoScreen, self).__init__(**kwargs)
        self.error_lbl = self.ids['error_msg']

    def pressed(self):
        """
        when pressing the submit button it sends data to the server,
        it moves to main cal screen if succeeded, else shows appropriate msg
        :return: None
        """
        user_age = self.user_age.text
        user_height = self.user_height.text
        user_weight = self.user_weight.text
        user_sex = self.user_sex.text

        # error state
        if not (user_height.isnumeric() and user_weight.isnumeric() and user_age.isnumeric()):
            self.user.send_to_server("error" + " " + self.user.username)
            self.error_lbl.text = self.user.recv_from_server()

        elif not (user_sex == "f" or user_sex == "m"):
            self.user.send_to_server("error" + " " + self.user.username)
            self.error_lbl.text = self.user.recv_from_server()

        elif user_age == "" or user_height == "" or user_weight == "" or user_sex == "":
            self.user.send_to_server("error" + " " + self.user.username)
            self.error_lbl.text = self.user.recv_from_server()

        # good input
        else:
            self.user.send_to_server("update" + " " + self.user.username)
            user_data = user_height + " " + user_weight + " " + user_age + " " + user_sex
            self.user.send_to_server(user_data)

            data_from_server = self.user.recv_from_server()
            if "Successfully" in data_from_server:
                print(":)")

                # clear data from text input
                self.user_age.text = ""
                self.user_height.text = ""
                self.user_weight.text = ""
                self.user_sex.text = ""
                self.error_lbl.text = ""

                # update the server that we need the calories, water cups and sleep hours
                self.user.update_calories()
                self.user.update_water()
                self.user.update_sleep()
                self.manager.current = 'main'

            else:
                print(":(")
                self.error_lbl.text = "error accord"


class WeeklyReportScreen(Screen):
    # vars for the report
    avg_cal = StringProperty(None)
    avg_water = StringProperty(None)
    avg_sleep = StringProperty(None)
    week_cal = ListProperty(None)
    week_water = ListProperty(None)
    week_sleep = ListProperty(None)

    def __init__(self, user, **kw):
        """
        constructor
        :param user: the user that use the screen
        :type User
        """
        self.user = user  # the user that use the screen
        super(WeeklyReportScreen, self).__init__(**kw)
        self.table = None
        self.button = None

    def on_leave(self, *args):
        self.remove_widget(self.table)
        self.remove_widget(self.button)

    def update_statistics(self):
        """
        update all the info from the current week - daily cal, water and sleep amounts, avg amounts and ideal amounts
        :return: None
        """
        (avg, cal, water, sleep) = self.user.get_statistics()  # get the data from server
        self.avg_cal = avg.split(" ")[0]
        self.avg_water = avg.split(" ")[1]
        self.avg_sleep = avg.split(" ")[2]
        self.week_cal = cal.split(" ")
        self.week_water = water.split(" ")
        self.week_sleep = sleep.split(" ")

        # make the table for the report
        self.table = MDDataTable(pos_hint={"center_x": 0.5, "center_y": 0.47},
                                 size_hint=(0.92, 0.74),
                                 rows_num=9,
                                 column_data=[
                                     ("Day", dp(9)),
                                     ("Calories", dp(13.25)),
                                     ("Water cups", dp(18)),
                                     ("Sleep hours", dp(18))
                                 ],
                                 row_data=[
                                     ("Sun.", self.week_cal[0], self.week_water[0], self.week_sleep[0]),
                                     ("Mon.", self.week_cal[1], self.week_water[1], self.week_sleep[1]),
                                     ("Tue.", self.week_cal[2], self.week_water[2], self.week_sleep[2]),
                                     ("Wed.", self.week_cal[3], self.week_water[3], self.week_sleep[3]),
                                     ("Thu.", self.week_cal[4], self.week_water[4], self.week_sleep[4]),
                                     ("Fri.", self.week_cal[5], self.week_water[5], self.week_sleep[5]),
                                     ("Sat.", self.week_cal[6], self.week_water[6], self.week_sleep[6]),
                                     ("Avg", self.avg_cal, self.avg_water, self.avg_sleep),
                                     ("Ideal", self.user.ideal_cal, self.user.ideal_water, self.user.ideal_sleep)
                                 ])

        # button to get back to main
        self.button = MDFillRoundFlatIconButton(text="Main",
                                                pos_hint={"center_x": 0.5, "center_y": 0.05},
                                                size_hint=(0.45, 0.075),
                                                icon="home",
                                                on_press=self.pressed_main
                                                )

        # add table and button to the screen
        self.add_widget(self.table)
        self.add_widget(self.button)
        return

    def pressed_main(self, arg):
        """
        when pressing the main button move to the main screen
        :param arg: argument that the button gives
        :return: None
        """
        print(arg)
        self.manager.current = 'main'
        return


class MainInstructions(Screen):
    def pressed(self):
        """
        when pressing the back button it returns to the main screen
        :return: None
        """
        self.manager.current = 'main'


# cal screen classes
class CalScreen(Screen):
    def __init__(self, user, **kwargs):
        """
        constructor
        :param user: the user that use the screen
        :type User
        """
        self.user = user  # the user that use the screen
        super(CalScreen, self).__init__(**kwargs)
        self.curr_lbl = self.ids['current_cal']
        self.ideal_lbl = self.ids['ideal_cal']

    def update_calories(self):
        """
        shows the currant and ideal calories of the user
        :return: None
        """
        self.curr_lbl.text = self.user.current_cal
        self.ideal_lbl.text = self.user.ideal_cal
        return

    def pressed_main(self):
        """
        when pressing the main button it moves to the main screen
        :return: None
        """
        self.manager.current = 'main'

    def pressed_add_food(self):
        """
        when pressing the add food button it moves to the add food screen
        :return: None
        """
        self.manager.current = 'food'

    def pressed_add_sport(self):
        """
        when pressing the add sport button it moves to the add sport screen
        :return: None
        """
        self.manager.current = 'sport'

    def pressed_instru(self):
        """
        when pressing the instructions button it shows the instructions of how to use the different actions that
        a user can take in the app, add sport or food and see current and ideal calories
        :return: None
        """
        self.manager.current = 'cal instru one'

    def pressed_exit(self):
        """
        when pressing the exit button it sends data to the server and modify it that we are leaving the app
        and close the screen
        :return: None
        """
        self.user.send_to_server("off" + " " + ".")
        data = self.user.recv_from_server()
        if "Goodbye" in data:  # exit
            BetterHealthApp.get_running_app().stop()
            Window.close()


class AddFoodScreen(Screen):
    global FOOD_VALUES
    user_amount = ObjectProperty(None)
    arr_food = ListProperty(FOOD_VALUES)

    def __init__(self, user, **kwargs):
        """
        constructor
        :param user: the user that use the screen
        :type User
        """
        self.user = user  # the user that use the screen
        super(AddFoodScreen, self).__init__(**kwargs)
        self.error_lbl = self.ids['error_msg']
        self.choice = ""

    def pressed_spinner(self, choice):
        """
        when pressing the spinner it saves the choice the user made
        :return: None
        """
        if " " in choice:  # fix spaces, server split data by spaces, and we don't want to lose information
            self.choice = choice.split(" ")[0] + "_" + choice.split(" ")[1]
        else:
            self.choice = choice

    def pressed_submit(self):
        """
        when pressing the submit button it sends data to the server,
        and moves to main cal screen if succeeded, else shows appropriate msg
        :return: None
        """
        user_amount = self.user_amount.text

        # let the server know we're entering food
        self.user.send_to_server("food" + " " + self.user.username)

        if user_amount == "" or not user_amount.isnumeric():  # error state
            self.user.send_to_server("error" + " " + self.user.username)
            self.error_lbl.text = self.user.recv_from_server()
            return

        # good input
        user_data = self.choice + " " + user_amount
        self.user.send_to_server(user_data)
        data = self.user.recv_from_server()

        if "Finished" in data:
            print(":)")

            # clear data from text input
            self.user_amount.text = ""
            self.error_lbl.text = ""

            # update the server that we need the calories
            self.user.update_calories()
            self.manager.current = 'cal'

        else:
            print(":(")
            self.error_lbl.text = "error accord"


class AddSportScreen(Screen):
    global SPORT_VALUES
    user_amount = ObjectProperty(None)
    arr_sport = ListProperty(SPORT_VALUES)

    def __init__(self, user, **kwargs):
        """
        constructor
        :param user: the user that use the screen
        :type User
        """
        self.user = user  # the user that use the screen
        super(AddSportScreen, self).__init__(**kwargs)
        self.error_lbl = self.ids['error_msg']
        self.choice = ""

    def pressed_spinner(self, choice):
        """
        when pressing the spinner it save the choice the user made
        :return: None
        """
        self.choice = choice

    def pressed_submit(self):
        """
        when pressing the submit button it sends data to the server,
        and moves to main cal screen if succeeded, else shows appropriate msg
        :return: None
        """
        user_amount = self.user_amount.text

        # let the server know we're entering sport
        self.user.send_to_server("sport" + " " + self.user.username)

        if user_amount == "" or not user_amount.isnumeric():  # error state
            self.user.send_to_server("error" + " " + self.user.username)
            self.error_lbl.text = self.user.recv_from_server()
            return

        # good input
        user_data = self.choice + " " + user_amount
        self.user.send_to_server(user_data)
        data = self.user.recv_from_server()

        if "Finished" in data:
            print(":)")

            # clear data from text input
            self.user_amount.text = ""
            self.error_lbl.text = ""

            # update the server that we need the calories
            self.user.update_calories()
            self.manager.current = 'cal'

        else:
            print(":(")
            self.error_lbl.text = "error accord"


class CalInstructionsOne(Screen):
    def pressed_next(self):
        """
        when pressing the next button it goes to the next instru screen
        :return: None
        """
        self.manager.current = 'cal instru two'

    def pressed_back(self):
        """
        when pressing the back button it returns to the cal screen
        :return: None
        """
        self.manager.current = 'cal'


class CalInstructionsTwo(Screen):
    def pressed_previous(self):
        """
        when pressing the previous button it returns to the first instru screen
        :return: None
        """
        self.manager.current = 'cal instru one'

    def pressed_back(self):
        """
        when pressing the back button it returns to the cal screen
        :return: None
        """
        self.manager.current = 'cal'


# water screen classes
class WaterScreen(Screen):
    def __init__(self, user, **kwargs):
        """
        constructor
        :param user: the user that use the screen
        :type User
        """
        self.user = user  # the user that use the screen
        super(WaterScreen, self).__init__(**kwargs)
        self.curr_lbl = self.ids['current_water']
        self.ideal_lbl = self.ids['ideal_water']

    def update_water(self):
        """
        shows the currant and ideal water cups of the user
        :return: None
        """
        self.curr_lbl.text = self.user.current_water
        self.ideal_lbl.text = self.user.ideal_water
        return

    def pressed_main(self):
        """
        when pressing the main button it moves to the main screen
        :return: None
        """
        self.manager.current = 'main'

    def pressed_add_cups(self):
        """
        when pressing the add cups button it moves to the add cups screen
        :return: None
        """
        self.manager.current = 'cups'

    def pressed_instru(self):
        """
        when pressing the instructions button it shows the instructions of how to use the different actions that
        a user can take in the app, add cups of water and see current and ideal water cups
        :return: None
        """
        self.manager.current = 'water instru'

    # @staticmethod
    def pressed_exit(self):
        """
        when pressing the exit button it sends data to the server and modify it that we are leaving the app
        and close the screen
        :return: None
        """
        self.user.send_to_server("off" + " " + ".")
        data = self.user.recv_from_server()
        if "Goodbye" in data:  # exit
            BetterHealthApp.get_running_app().stop()
            Window.close()


class AddCupsScreen(Screen):
    user_amount = ObjectProperty(None)

    def __init__(self, user, **kwargs):
        """
        constructor
        :param user: the user that use the screen
        :type User
        """
        self.user = user  # the user that use the screen
        super(AddCupsScreen, self).__init__(**kwargs)
        self.error_lbl = self.ids['error_msg']

    def pressed_submit(self):
        """
        when pressing the submit button it sends data to the server,
        and moves to main water screen if succeeded, else shows appropriate msg
        :return: None
        """
        user_amount = self.user_amount.text

        # let the server know we're entering cups
        self.user.send_to_server("cups" + " " + self.user.username)

        if user_amount == "" or not user_amount.isnumeric():  # error state
            self.user.send_to_server("error" + " " + self.user.username)
            data_from_server = self.user.recv_from_server()
            self.error_lbl.text = data_from_server
            return

        # good input
        self.user.send_to_server(user_amount)
        data = self.user.recv_from_server()
        if "Finished" in data:
            print(":)")

            # clear data from text input
            self.user_amount.text = ""
            self.error_lbl.text = ""

            # update the server that we need the water cups
            self.user.update_water()
            self.manager.current = 'water'
        else:
            print(":(")
            self.error_lbl.text = "error accord"


class WaterInstructions(Screen):
    def pressed_back(self):
        """
        when pressing the back button it returns to the water screen
        :return: None
        """
        self.manager.current = 'water'


# sleep screen classes
class SleepScreen(Screen):
    def __init__(self, user, **kwargs):
        """
        constructor
        :param user: the user that use the screen
        :type User
        """
        self.user = user  # the user that use the screen
        super(SleepScreen, self).__init__(**kwargs)
        self.curr_lbl = self.ids['current_sleep']
        self.ideal_lbl = self.ids['ideal_sleep']

    def update_sleep(self):
        """
        shows the currant and ideal sleep hours of the user
        :return: None
        """
        self.curr_lbl.text = self.user.current_sleep
        self.ideal_lbl.text = self.uesr.ideal_sleep
        return

    def pressed_main(self):
        """
        when pressing the main button it moves to the main screen
        :return: None
        """
        self.manager.current = 'main'

    def pressed_add_hours(self):
        """
        when pressing the add hours button it moves to the add hours screen
        :return: None
        """
        self.manager.current = 'hours'

    def pressed_instru(self):
        """
        when pressing the instructions button it shows the instructions of how to use the different actions that
        a user can take in the app, add hours of sleep and see current and ideal sleep hours
        :return: None
        """
        self.manager.current = 'sleep instru'

    # @staticmethod
    def pressed_exit(self):
        """
        when pressing the exit button it sends data to the server and modify it that we are leaving the app
        and close the screen
        :return: None
        """
        self.user.send_to_server("off" + " " + ".")
        data = self.user.recv_from_server()
        if "Goodbye" in data:  # exit
            BetterHealthApp.get_running_app().stop()
            Window.close()


class AddHoursScreen(Screen):
    user_start = ObjectProperty(None)
    user_finish = ObjectProperty(None)

    def __init__(self, user, **kwargs):
        """
        constructor
        :param user: the user that use the screen
        :type User
        """
        self.user = user  # the user that use the screen
        super(AddHoursScreen, self).__init__(**kwargs)
        self.error_lbl = self.ids['error_msg']

    def pressed_submit(self):
        """
        when pressing the submit button it sends data to the server,
        and moves to main sleep screen if succeeded, else shows appropriate msg
        :return: None
        """
        user_start = self.user_start.text
        user_finish = self.user_finish.text

        # let the server know we're entering hours
        self.user.send_to_server("hours" + " " + self.user.username)

        # error state
        if user_start == "" or user_finish == "":
            self.user.send_to_server("error" + " " + self.user.username)
            data_from_server = self.user.recv_from_server()
            self.error_lbl.text = data_from_server
            return

        if ":" not in user_start or ":" not in user_finish:
            self.user.send_to_server("error" + " " + self.user.username)
            data_from_server = self.user.recv_from_server()
            self.error_lbl.text = data_from_server
            return

        # good input
        self.user.send_to_server(user_start + " " + user_finish)
        data = self.user.recv_from_server()

        if "Finished" in data:
            print(":)")

            # clear data from text input
            self.user_start.text = ""
            self.user_finish.text = ""
            self.error_lbl.text = ""

            # update the server that we need the calories
            self.user.update_sleep()
            self.manager.current = 'sleep'
        else:
            print(":(")
            self.error_lbl.text = "Invalid."


class SleepInstructions(Screen):
    def pressed_back(self):
        """
        when pressing the back button it returns to the sleep screen
        :return: None
        """
        self.manager.current = 'sleep'


# the app
class BetterHealthApp(MDApp):
    def __init__(self, user, **kwargs):
        super().__init__(**kwargs)
        self.user = user

    def build(self):
        """
        Build the different screens in the app
        :return: sm, screen manager
        """
        sm = ScreenManager()  # the screen manager of the app
        self.icon = 'heart-health.png'
        # start screen
        sm.add_widget(StartScreen(self.user, name='start'))
        sm.add_widget(LogInScreen(self.user, name='log in'))
        sm.add_widget(SignUpScreen(self.user, name='sign up'))
        sm.add_widget(StartInstructions(name='start instru'))
        # main screen
        sm.add_widget(MainScreen(self.user, name='main'))
        sm.add_widget(ProfileScreen(self.user, name='profile'))
        sm.add_widget(UpdateInfoScreen(self.user, name='update info'))
        sm.add_widget(WeeklyReportScreen(self.user, name='report'))
        sm.add_widget(MainInstructions(name='main instru'))
        # cal screen
        sm.add_widget(CalScreen(self.user, name='cal'))
        sm.add_widget(AddFoodScreen(self.user, name='food'))
        sm.add_widget(AddSportScreen(self.user, name='sport'))
        sm.add_widget(CalInstructionsOne(name='cal instru one'))
        sm.add_widget(CalInstructionsTwo(name='cal instru two'))
        # water screen
        sm.add_widget(WaterScreen(self.user, name='water'))
        sm.add_widget(AddCupsScreen(self.user, name='cups'))
        sm.add_widget(WaterInstructions(name='water instru'))
        # sleep screen
        sm.add_widget(SleepScreen(self.user, name='sleep'))
        sm.add_widget(AddHoursScreen(self.user, name='hours'))
        sm.add_widget(SleepInstructions(name='sleep instru'))
        return sm


# some crypto :o
def switchKeysDH(c_soc):
    """
    switch keys diffie-hellman
    :param c_soc: the communication socket
    :type c_soc: socket.socket
    :return: p, g and the key
    """
    # parameters
    # get p from server
    len_p = int.from_bytes(c_soc.recv(2), "big")
    p = int.from_bytes(c_soc.recv(len_p), "big")
    c_soc.send(b"good")

    # get g from server
    len_g = int.from_bytes(c_soc.recv(2), "big")
    g = int.from_bytes(c_soc.recv(len_g), "big")
    c_soc.send(b"good")

    pn = dh.DHParameterNumbers(p, g)
    parameters = pn.parameters()

    # sk
    sk_client = parameters.generate_private_key()
    # pk = g^sk
    pk_client = sk_client.public_key()
    pk_client_bytes = pk_client.public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)  # encode to bytes

    # recv pk from server
    pk_server_len = int.from_bytes(c_soc.recv(2), "big")  # encode back to int from bytes
    pk_server_bytes = c_soc.recv(pk_server_len)
    print(b"client recv: " + pk_server_bytes)  # sanity check
    pk_server = load_der_public_key(pk_server_bytes, default_backend())  # decode back to dh object

    # send our pk to server
    c_soc.send(len(pk_client_bytes).to_bytes(2, "big") + pk_client_bytes)  # send also the len in bytes (for the recv)
    print(b"client sent: " + pk_client_bytes)

    # create the shared key
    shared_key = sk_client.exchange(pk_server)

    return p, g, hashlib.sha256(shared_key).hexdigest()


def main():
    # connect to server
    client_socket = socket.socket()
    client_socket.connect(('server ip goes here', 10000))  # connect to server in port 10000
    # (p, g, key) = switchKeysDH(client_socket)
    user = User(client_socket, 0, 0, 0)

    # start the application
    BetterHealthApp(user).run()


if __name__ == '__main__':
    main()
