from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
import socket

CLIENT_SOC = ""
SM = ScreenManager()
USERNAME = ""
CURRENT = ""
IDEAL = ""


class StartScreen(Screen):
    global CLIENT_SOC

    @staticmethod
    def pressed_log_in():
        """
        when pressing the login button it sends to the server request to login and move to login screen
        :return: None
        """
        SM.current = 'log in'

    @staticmethod
    def pressed_sign_up():
        """
        when pressing the signup button it sends to the server request to signup and move to signup screen
        :return: None
        """
        SM.current = 'sign up'


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
        send_to_server(CLIENT_SOC, ("sign" + " " + username))
        data_from_server = recv_from_server(CLIENT_SOC)
        if "Send" in data_from_server:
            print(":)")
            USERNAME = username
            SM.current = 'sign info'
        else:
            print(":(")
            self.error_lbl.text = "Username is taken."


class SignInfoScreen(Screen):
    global CLIENT_SOC, SM
    user_age = ObjectProperty(None)
    user_height = ObjectProperty(None)
    user_weight = ObjectProperty(None)
    user_sex = ObjectProperty(None)

    def pressed(self):
        user_age = self.user_age.text
        user_height = self.user_height.text
        user_weight = self.user_weight.text
        user_sex = self.user_sex.text

        user_data = user_height + " " + user_weight + " " + user_age + " " + user_sex
        send_to_server(CLIENT_SOC, user_data)

        data_from_server = recv_from_server(CLIENT_SOC)
        if "Successfully" in data_from_server:
            print(":)")

            # update the server that we need the calories
            update_calories(CLIENT_SOC)
            SM.current = 'main'
        else:
            print(":(")


class UpdateInfoScreen(Screen):
    global CLIENT_SOC, SM
    user_age = ObjectProperty(None)
    user_height = ObjectProperty(None)
    user_weight = ObjectProperty(None)
    user_sex = ObjectProperty(None)

    def pressed(self):
        user_age = self.user_age.text
        user_height = self.user_height.text
        user_weight = self.user_weight.text
        user_sex = self.user_sex.text

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
        send_to_server(CLIENT_SOC, ("update" + " " + USERNAME))
        SM.current = 'update info'


class BetterHealthApp(App):
    global SM

    def build(self):
        SM.add_widget(StartScreen(name='start'))
        SM.add_widget(LogInScreen(name='log in'))
        SM.add_widget(SignUpScreen(name='sign up'))
        SM.add_widget(SignInfoScreen(name='sign info'))
        SM.add_widget(UpdateInfoScreen(name='update info'))
        SM.add_widget(MainScreen(name='main'))
        return SM


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
    # handle the connection to the server
    global CLIENT_SOC  # global var to save the client socket
    client_socket = socket.socket()
    client_socket.connect(('192.168.56.1', 10000))  # connect to server in port 10000
    CLIENT_SOC = client_socket

    # start the application
    BetterHealthApp().run()


if __name__ == '__main__':
    main()
