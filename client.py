from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, ListProperty
import socket

CLIENT_SOC = ""
SM = ScreenManager()
USERNAME = ""
CURRENT = ""
IDEAL = ""
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
        global USERNAME, CURRENT, IDEAL
        username = self.username.text
        send_to_server(CLIENT_SOC, ("log" + " " + username))
        data_from_server = recv_from_server(CLIENT_SOC)
        if "Successfully" in data_from_server:
            print(":)")
            USERNAME = username

            # update the server that we need the calories
            update_calories(CLIENT_SOC)
            SM.current = 'main'
        else:
            print(":(")
            self.error_lbl.text = "Username is not found."


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
        when pressing the submit button it sends data to the server - move to main screen if succeed
        :return: None
        """
        user_age = self.user_age.text
        user_height = self.user_height.text
        user_weight = self.user_weight.text
        user_sex = self.user_sex.text

        # error state
        if not (user_height.isnumeric() or user_weight.isnumeric() or user_age.isnumeric()):
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
                SM.current = 'main'

            else:
                print(":(")
                self.error_lbl.text = "error accord"


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
        CHOICE = choice

    def pressed_submit(self):
        """
        when pressing the submit button it sends data to the server - move to main screen if succeed
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
                SM.current = 'main'
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
        when pressing the submit button it sends data to the server - move to main screen if succeed
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
                SM.current = 'main'
            else:
                print(":(")
                self.error_lbl.text = "error accord"


class MainScreen(Screen):
    global CLIENT_SOC, SM, USERNAME, CURRENT, IDEAL

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.curr_lbl = self.ids['current']
        self.ideal_lbl = self.ids['ideal']

    def update_calories(self):
        self.curr_lbl.text = CURRENT
        self.ideal_lbl.text = IDEAL
        return

    @staticmethod
    def pressed_update():
        """
        when pressing the update button it sends data to the server and modify it that we are updating the info
        and move to the update info screen
        :return: None
        """
        SM.current = 'update info'

    @staticmethod
    def pressed_add_food():
        """
        when pressing the add food button it sends data to the server and modify it that we are adding food
        and move to the add food screen
        :return: None
        """
        SM.current = 'food'

    @staticmethod
    def pressed_add_sport():
        """
        when pressing the add sport button it sends data to the server and modify it that we are adding sport
        and move to the add sport screen
        :return: None
        """
        SM.current = 'sport'

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


class BetterHealthApp(App):
    global SM

    def build(self):
        SM.add_widget(StartScreen(name='start'))
        SM.add_widget(LogInScreen(name='log in'))
        SM.add_widget(SignUpScreen(name='sign up'))
        SM.add_widget(UpdateInfoScreen(name='update info'))
        SM.add_widget(MainScreen(name='main'))
        SM.add_widget(AddFoodScreen(name='food'))
        SM.add_widget(AddSportScreen(name='sport'))
        return SM


def connect_to_server():
    # handle the connection to the server
    global CLIENT_SOC  # global var to save the client socket
    client_socket = socket.socket()
    client_socket.connect(('10.0.0.32', 10000))  # connect to server in port 10000
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
    global CLIENT_SOC, CURRENT, IDEAL
    if CLIENT_SOC == client_socket:
        CLIENT_SOC.send(b"main" + b" " + USERNAME.encode())
        data = CLIENT_SOC.recv(1024).decode().split(" ")
        CURRENT = data[0]
        IDEAL = data[1]
        return


def main():
    # start the application
    BetterHealthApp().run()


if __name__ == '__main__':
    main()
