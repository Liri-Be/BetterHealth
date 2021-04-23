from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, ListProperty
import socket

CLIENT_SOC = ""
SM = ScreenManager()
USERNAME = ""
CURRENT_CAL = ""
IDEAL_CAL = ""
CURRENT_WATER = ""
IDEAL_WATER = ""
CURRENT_SLEEP = ""
IDEAL_SLEEP = ""
CHOICE = ""
FOOD_VALUES = ["Apple", "Bagel", "Banana", "Beans", "Beef", "Blackberries", "Bread white", "Bread wholemeal",
               "Broccoli", "Butter", "Cabbage", "Cauliflower", "Celery", "Chicken", "Chocolate", "Cornflakes",
               "Cottage cheese", "Cream cheese", "Cucumber", "Dates", "Egg", "Grapes", "Honey", "Ice cream", " Jam",
               "Kiwi", "Lettuce", "Liver", "Margarine", "Melon", "Milk", "Muesli", "Mushrooms", "Noodles", "Oil",
               "Olives", "Onion", " Orange", "Pasta", "Peach", "Pear", "Peas", "Pepper yellow", "Pineapple", "Popcorn",
               "Potatoes", "Rice", "Salmon", "Sardines", "Spaghetti", "Steak", "Strawberries", "Syrup", "Toffee",
               "Tomato", "Tomato cherry", "Tuna", "White cheese", "White sugar", "Yogurt"]
SPORT_VALUES = ["Basketball", "Bowling", "Cycling", "Dancing", "Gardening", "Golf", "Hiking", "Jogging", "Skating",
                "Skiing", "Swimming", "Tennis", "Waling", "Weight Training"]


# start screen classes
class StartScreen(Screen):
    global CLIENT_SOC

    @staticmethod
    def pressed_log_in():
        """
        when pressing the login button it sends to the server request to login and move to login screen
        :return: None
        """
        connect_to_server()
        SM.current = 'log in'

    @staticmethod
    def pressed_sign_up():
        """
        when pressing the signup button it sends to the server request to signup and move to signup screen
        :return: None
        """
        connect_to_server()
        SM.current = 'sign up'

    @staticmethod
    def pressed_instru():
        """
        when pressing the instructions button it show the instructions of logging and signing to the app
        :return: None
        """
        SM.current = 'start instru'

    @staticmethod
    def pressed_exit():
        """
        when pressing the exit button it sends data to the server and modify it that we are leaving the app
        and close the screen
        :return: None
        """
        connect_to_server()
        send_to_server(CLIENT_SOC, ("off" + " " + "."))
        data = recv_from_server(CLIENT_SOC)
        if "Goodbye" in data:  # exit
            BetterHealthApp.get_running_app().stop()
            Window.close()


class LogInScreen(Screen):
    global CLIENT_SOC, SM
    username = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(LogInScreen, self).__init__(**kwargs)
        self.error_lbl = self.ids['error_msg']

    def pressed(self):
        """
        when pressing the login button it sends data to the server - log in if succeed
        :return: None
        """
        global USERNAME
        username = self.username.text
        send_to_server(CLIENT_SOC, ("log" + " " + username))
        data_from_server = recv_from_server(CLIENT_SOC)
        if "Successfully" in data_from_server:
            print(":)")
            USERNAME = username

            # update the server that we need the calories
            update_calories(CLIENT_SOC)
            update_water(CLIENT_SOC)
            update_sleep(CLIENT_SOC)
            SM.current = 'main'
        else:
            print(":(")
            self.error_lbl.text = "Username has not found."


class SignUpScreen(Screen):
    global CLIENT_SOC, SM
    username = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SignUpScreen, self).__init__(**kwargs)
        self.error_lbl = self.ids['error_msg']

    def pressed(self):
        """
        when pressing the signup button it sends data to the server - sign up if succeed
        :return: None
        """
        global USERNAME
        username = self.username.text
        if " " in username:  # error state
            send_to_server(CLIENT_SOC, ("error" + " " + username))
            self.error_lbl.text = recv_from_server(CLIENT_SOC)
        else:
            send_to_server(CLIENT_SOC, ("sign" + " " + username))
            data_from_server = recv_from_server(CLIENT_SOC)
            if "Good" in data_from_server:
                print(":)")
                USERNAME = username
                SM.current = 'update info'
            else:
                print(":(")
                self.error_lbl.text = "Username is taken."


class StartInstructions(Screen):
    global SM

    @staticmethod
    def pressed():
        """
        when pressing the back button it returns to the start screen
        :return: None
        """
        SM.current = 'start'


# main screen classes
class MainScreen(Screen):
    global SM

    @staticmethod
    def pressed_cal():
        """
        when pressing the cal button it goes to the cal screen
        :return: None
        """
        SM.current = 'cal'

    @staticmethod
    def pressed_water():
        """
        when pressing the water button it goes to the water screen
        :return: None
        """
        SM.current = 'water'

    @staticmethod
    def pressed_sleep():
        """
        when pressing the sleep button it goes to the sleep screen
        :return: None
        """
        SM.current = 'sleep'

    @staticmethod
    def pressed_instru():
        """
        when pressing the instru button it goes to the instru screen
        :return: None
        """
        SM.current = 'main instru'

    @staticmethod
    def pressed_update():
        """
        when pressing the update info button it goes to the update info screen
        :return: None
        """
        SM.current = 'update info'

    @staticmethod
    def pressed_exit():
        """
        when pressing the exit button it sends data to the server and modify it that we are leaving the app
        and close the screen
        :return: None
        """
        connect_to_server()
        send_to_server(CLIENT_SOC, ("off" + " " + "."))
        data = recv_from_server(CLIENT_SOC)
        if "Goodbye" in data:  # exit
            BetterHealthApp.get_running_app().stop()
            Window.close()


class UpdateInfoScreen(Screen):
    global CLIENT_SOC, SM
    user_age = ObjectProperty(None)
    user_height = ObjectProperty(None)
    user_weight = ObjectProperty(None)
    user_sex = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(UpdateInfoScreen, self).__init__(**kwargs)
        self.error_lbl = self.ids['error_msg']

    def pressed(self):
        """
        when pressing the submit button it sends data to the server - move to main cal screen if succeed
        :return: None
        """
        user_age = self.user_age.text
        user_height = self.user_height.text
        user_weight = self.user_weight.text
        user_sex = self.user_sex.text

        # error state
        if not (user_height.isnumeric() and user_weight.isnumeric() and user_age.isnumeric()):
            send_to_server(CLIENT_SOC, ("error" + " " + USERNAME))
            self.error_lbl.text = recv_from_server(CLIENT_SOC)

        elif not (user_sex == "f" or user_sex == "m"):
            send_to_server(CLIENT_SOC, ("error" + " " + USERNAME))
            self.error_lbl.text = recv_from_server(CLIENT_SOC)

        elif user_age == "" or user_height == "" or user_weight == "" or user_sex == "":
            send_to_server(CLIENT_SOC, ("error" + " " + USERNAME))
            self.error_lbl.text = recv_from_server(CLIENT_SOC)

        # good input
        else:
            send_to_server(CLIENT_SOC, ("update" + " " + USERNAME))
            user_data = user_height + " " + user_weight + " " + user_age + " " + user_sex
            send_to_server(CLIENT_SOC, user_data)

            data_from_server = recv_from_server(CLIENT_SOC)
            if "Successfully" in data_from_server:
                print(":)")

                # clear data from text input
                self.user_age.text = ""
                self.user_height.text = ""
                self.user_weight.text = ""
                self.user_sex.text = ""

                # update the server that we need the calories
                update_calories(CLIENT_SOC)
                update_water(CLIENT_SOC)
                update_sleep(CLIENT_SOC)
                SM.current = 'main'

            else:
                print(":(")
                self.error_lbl.text = "error accord"


class MainInstructions(Screen):
    global SM

    @staticmethod
    def pressed():
        """
        when pressing the back button it returns to the main screen
        :return: None
        """
        SM.current = 'main'


# cal screen classes
class CalScreen(Screen):
    global CLIENT_SOC, SM, USERNAME, CURRENT_CAL, IDEAL_CAL

    def __init__(self, **kwargs):
        super(CalScreen, self).__init__(**kwargs)
        self.curr_lbl = self.ids['current_cal']
        self.ideal_lbl = self.ids['ideal_cal']

    def update_calories(self):
        self.curr_lbl.text = CURRENT_CAL
        self.ideal_lbl.text = IDEAL_CAL
        return

    @staticmethod
    def pressed_main():
        """
        when pressing the main button it moves to the update info screen
        :return: None
        """
        SM.current = 'main'

    @staticmethod
    def pressed_add_food():
        """
        when pressing the add food button it moves to the add food screen
        :return: None
        """
        SM.current = 'food'

    @staticmethod
    def pressed_add_sport():
        """
        when pressing the add sport button it moves to the add sport screen
        :return: None
        """
        SM.current = 'sport'

    @staticmethod
    def pressed_instru():
        """
        when pressing the instructions button it shows the instructions of how to use the different actions that
        a user can take in the app, add sport or food and see current and ideal calories
        :return: None
        """
        SM.current = 'cal instru one'

    @staticmethod
    def pressed_exit():
        """
        when pressing the exit button it sends data to the server and modify it that we are leaving the app
        and close the screen
        :return: None
        """
        send_to_server(CLIENT_SOC, ("off" + " " + "."))
        data = recv_from_server(CLIENT_SOC)
        if "Goodbye" in data:  # exit
            BetterHealthApp.get_running_app().stop()
            Window.close()


class AddFoodScreen(Screen):
    global FOOD_VALUES
    user_amount = ObjectProperty(None)
    arr_food = ListProperty(FOOD_VALUES)

    def __init__(self, **kwargs):
        super(AddFoodScreen, self).__init__(**kwargs)
        self.error_lbl = self.ids['error_msg']

    def pressed_spinner(self, choice):
        """
        when pressing the spinner it save the choice the user made
        :return: None
        """
        global CHOICE
        self.error_lbl.text = str(choice)
        if " " in choice:  # fix spaces
            CHOICE = choice.split(" ")[0] + "_" + choice.split(" ")[1]
        else:
            CHOICE = choice

    def pressed_submit(self):
        """
        when pressing the submit button it sends data to the server - move to main cal screen if succeed
        :return: None
        """
        global CHOICE, CLIENT_SOC
        user_amount = self.user_amount.text

        send_to_server(CLIENT_SOC, ("food" + " " + USERNAME))  # let the server know we entering food

        if user_amount == "" or not user_amount.isnumeric():  # error state
            send_to_server(CLIENT_SOC, ("error" + " " + USERNAME))
            self.error_lbl.text = recv_from_server(CLIENT_SOC)

        else:  # good input
            user_data = CHOICE + " " + user_amount
            send_to_server(CLIENT_SOC, user_data)
            data = recv_from_server(CLIENT_SOC)
            if "Finished" in data:
                print(":)")

                # clear data from text input
                self.user_amount.text = ""

                # update the server that we need the calories
                update_calories(CLIENT_SOC)
                SM.current = 'cal'
            else:
                print(":(")
                self.error_lbl.text = "error accord"


class AddSportScreen(Screen):
    global SPORT_VALUES
    user_amount = ObjectProperty(None)
    arr_sport = ListProperty(SPORT_VALUES)

    def __init__(self, **kwargs):
        super(AddSportScreen, self).__init__(**kwargs)
        self.error_lbl = self.ids['error_msg']

    def pressed_spinner(self, choice):
        """
        when pressing the spinner it save the choice the user made
        :return: None
        """
        global CHOICE
        self.error_lbl.text = str(choice)
        CHOICE = choice

    def pressed_submit(self):
        """
        when pressing the submit button it sends data to the server - move to main cal screen if succeed
        :return: None
        """
        global CHOICE, CLIENT_SOC
        user_amount = self.user_amount.text

        send_to_server(CLIENT_SOC, ("sport" + " " + USERNAME))  # let the server know we entering food

        if user_amount == "" or not user_amount.isnumeric():  # error state
            send_to_server(CLIENT_SOC, ("error" + " " + USERNAME))
            self.error_lbl.text = recv_from_server(CLIENT_SOC)

        else:  # good input
            user_data = CHOICE + " " + user_amount
            send_to_server(CLIENT_SOC, user_data)
            data = recv_from_server(CLIENT_SOC)
            if "Finished" in data:
                print(":)")

                # clear data from text input
                self.user_amount.text = ""
                self.error_lbl.text = ""

                # update the server that we need the calories
                update_calories(CLIENT_SOC)
                SM.current = 'cal'
            else:
                print(":(")
                self.error_lbl.text = "error accord"


class CalInstructionsOne(Screen):
    global SM

    @staticmethod
    def pressed_next():
        """
        when pressing the next button it goes to the next instru screen
        :return: None
        """
        SM.current = 'cal instru two'

    @staticmethod
    def pressed_back():
        """
        when pressing the back button it returns to the cal screen
        :return: None
        """
        SM.current = 'cal'


class CalInstructionsTwo(Screen):
    global SM

    @staticmethod
    def pressed_previous():
        """
        when pressing the previous button it returns to the first instru screen
        :return: None
        """
        SM.current = 'cal instru one'

    @staticmethod
    def pressed_back():
        """
        when pressing the back button it returns to the cal screen
        :return: None
        """
        SM.current = 'cal'


# water screen classes
class WaterScreen(Screen):
    global CLIENT_SOC, SM, USERNAME, CURRENT_WATER, IDEAL_WATER

    def __init__(self, **kwargs):
        super(WaterScreen, self).__init__(**kwargs)
        self.curr_lbl = self.ids['current_water']
        self.ideal_lbl = self.ids['ideal_water']

    def update_water(self):
        self.curr_lbl.text = CURRENT_WATER
        self.ideal_lbl.text = IDEAL_WATER
        return

    @staticmethod
    def pressed_main():
        """
        when pressing the main button it moves to the update info screen
        :return: None
        """
        SM.current = 'main'

    @staticmethod
    def pressed_add_cups():
        """
        when pressing the add cups button it moves to the add cups screen
        :return: None
        """
        SM.current = 'cups'

    @staticmethod
    def pressed_instru():
        """
        when pressing the instructions button it shows the instructions of how to use the different actions that
        a user can take in the app, add cups of water and see current and ideal calories
        :return: None
        """
        SM.current = 'water instru'

    @staticmethod
    def pressed_exit():
        """
        when pressing the exit button it sends data to the server and modify it that we are leaving the app
        and close the screen
        :return: None
        """
        send_to_server(CLIENT_SOC, ("off" + " " + "."))
        data = recv_from_server(CLIENT_SOC)
        if "Goodbye" in data:  # exit
            BetterHealthApp.get_running_app().stop()
            Window.close()


class AddCupsScreen(Screen):
    user_amount = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(AddCupsScreen, self).__init__(**kwargs)
        self.error_lbl = self.ids['error_msg']

    def pressed_submit(self):
        """
        when pressing the submit button it sends data to the server - move to main water screen if succeed
        :return: None
        """
        global CLIENT_SOC
        user_amount = self.user_amount.text

        send_to_server(CLIENT_SOC, ("cups" + " " + USERNAME))  # let the server know we entering food

        if user_amount == "" or not user_amount.isnumeric():  # error state
            send_to_server(CLIENT_SOC, ("error" + " " + USERNAME))
            data_from_server = recv_from_server(CLIENT_SOC)
            self.error_lbl.text = data_from_server

        else:  # good input
            send_to_server(CLIENT_SOC, user_amount)
            data = recv_from_server(CLIENT_SOC)
            if "Finished" in data:
                print(":)")

                # clear data from text input
                self.user_amount.text = ""

                # update the server that we need the calories
                update_water(CLIENT_SOC)
                SM.current = 'water'
            else:
                print(":(")
                self.error_lbl.text = "error accord"


class WaterInstructions(Screen):
    global SM

    @staticmethod
    def pressed_back():
        """
        when pressing the back button it returns to the water screen
        :return: None
        """
        SM.current = 'water'


# sleep screen classes
class SleepScreen(Screen):
    global CLIENT_SOC, SM, USERNAME, CURRENT_SLEEP, IDEAL_SLEEP

    def __init__(self, **kwargs):
        super(SleepScreen, self).__init__(**kwargs)
        self.curr_lbl = self.ids['current_sleep']
        self.ideal_lbl = self.ids['ideal_sleep']

    def update_sleep(self):
        self.curr_lbl.text = CURRENT_SLEEP
        self.ideal_lbl.text = IDEAL_SLEEP
        return

    @staticmethod
    def pressed_main():
        """
        when pressing the main button it moves to the update info screen
        :return: None
        """
        SM.current = 'main'

    @staticmethod
    def pressed_add_hours():
        """
        when pressing the add cups button it moves to the add cups screen
        :return: None
        """
        SM.current = 'hours'

    @staticmethod
    def pressed_instru():
        """
        when pressing the instructions button it shows the instructions of how to use the different actions that
        a user can take in the app, add cups of water and see current and ideal calories
        :return: None
        """
        SM.current = 'sleep instru'

    @staticmethod
    def pressed_exit():
        """
        when pressing the exit button it sends data to the server and modify it that we are leaving the app
        and close the screen
        :return: None
        """
        send_to_server(CLIENT_SOC, ("off" + " " + "."))
        data = recv_from_server(CLIENT_SOC)
        if "Goodbye" in data:  # exit
            BetterHealthApp.get_running_app().stop()
            Window.close()


class AddHoursScreen(Screen):
    user_amount = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(AddHoursScreen, self).__init__(**kwargs)
        self.error_lbl = self.ids['error_msg']

    def pressed_submit(self):
        """
        when pressing the submit button it sends data to the server - move to main water screen if succeed
        :return: None
        """
        global CLIENT_SOC
        user_amount = self.user_amount.text

        send_to_server(CLIENT_SOC, ("hours" + " " + USERNAME))  # let the server know we entering food

        if user_amount == "" or not user_amount.isnumeric():  # error state
            send_to_server(CLIENT_SOC, ("error" + " " + USERNAME))
            data_from_server = recv_from_server(CLIENT_SOC)
            self.error_lbl.text = data_from_server

        else:  # good input
            send_to_server(CLIENT_SOC, user_amount)
            data = recv_from_server(CLIENT_SOC)
            if "Finished" in data:
                print(":)")

                # clear data from text input
                self.user_amount.text = ""

                # update the server that we need the calories
                update_sleep(CLIENT_SOC)
                SM.current = 'sleep'
            else:
                print(":(")
                self.error_lbl.text = "error accord"


class SleepInstructions(Screen):
    global SM

    @staticmethod
    def pressed_back():
        """
        when pressing the back button it returns to the water screen
        :return: None
        """
        SM.current = 'sleep'


# the app
class BetterHealthApp(App):
    global SM

    def build(self):
        # start screen
        SM.add_widget(StartScreen(name='start'))
        SM.add_widget(LogInScreen(name='log in'))
        SM.add_widget(SignUpScreen(name='sign up'))
        SM.add_widget(StartInstructions(name='start instru'))
        # main screen
        SM.add_widget(MainScreen(name='main'))
        SM.add_widget(UpdateInfoScreen(name='update info'))
        SM.add_widget(MainInstructions(name='main instru'))
        # cal screen
        SM.add_widget(CalScreen(name='cal'))
        SM.add_widget(AddFoodScreen(name='food'))
        SM.add_widget(AddSportScreen(name='sport'))
        SM.add_widget(CalInstructionsOne(name='cal instru one'))
        SM.add_widget(CalInstructionsTwo(name='cal instru two'))
        # water screen
        SM.add_widget(WaterScreen(name='water'))
        SM.add_widget(AddCupsScreen(name='cups'))
        SM.add_widget(WaterInstructions(name='water instru'))
        # sleep screen
        SM.add_widget(SleepScreen(name='sleep'))
        SM.add_widget(AddHoursScreen(name='hours'))
        SM.add_widget(SleepInstructions(name='sleep instru'))
        return SM


# functions to handle connections to server that aren't related to specific screen
def connect_to_server():
    # handle the connection to the server
    global CLIENT_SOC  # global var to save the client socket
    client_socket = socket.socket()
    client_socket.connect(('10.0.0.23', 10000))  # connect to server in port 10000
    CLIENT_SOC = client_socket


def send_to_server(client_socket, data):
    """
    send data to the server
    :param client_socket: the client socket
    :param data: the data to send in string
    :return: None
    """
    global CLIENT_SOC
    if CLIENT_SOC == client_socket:
        CLIENT_SOC.send(data.encode())


def recv_from_server(client_socket):
    """
    receive data from the server
    :param client_socket: the client socket
    :return: the data - string
    """
    global CLIENT_SOC
    if CLIENT_SOC == client_socket:
        return CLIENT_SOC.recv(1024).decode()


def update_calories(client_socket):
    """
    update the current and ideal calories global variables with data from the server
    :param client_socket: the client socket
    :return: None
    """
    global CLIENT_SOC, CURRENT_CAL, IDEAL_CAL
    if CLIENT_SOC == client_socket:
        CLIENT_SOC.send(b"cal" + b" " + USERNAME.encode())
        data = CLIENT_SOC.recv(1024).decode().split(" ")
        CURRENT_CAL = data[0]
        IDEAL_CAL = data[1]
        return


def update_water(client_socket):
    """
    update the current and ideal water global variables with data from the server
    :param client_socket: the client socket
    :return: None
    """
    global CLIENT_SOC, CURRENT_WATER, IDEAL_WATER
    if CLIENT_SOC == client_socket:
        CLIENT_SOC.send(b"water" + b" " + USERNAME.encode())
        data = CLIENT_SOC.recv(1024).decode().split(" ")
        CURRENT_WATER = data[0]
        IDEAL_WATER = data[1]
        return


def update_sleep(client_socket):
    """
    update the current and ideal sleep global variables with data from the server
    :param client_socket: the client socket
    :return: None
    """
    global CLIENT_SOC, CURRENT_SLEEP, IDEAL_SLEEP
    if CLIENT_SOC == client_socket:
        CLIENT_SOC.send(b"sleep" + b" " + USERNAME.encode())
        data = CLIENT_SOC.recv(1024).decode().split(" ")
        CURRENT_SLEEP = data[0]
        IDEAL_SLEEP = data[1]
        return


def main():
    # start the application
    BetterHealthApp().run()


if __name__ == '__main__':
    main()
