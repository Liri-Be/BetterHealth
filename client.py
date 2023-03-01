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

# global vars
CLIENT_SOC = socket.socket()  # the current client socket
# data of the user
USERNAME = ""
CURRENT_CAL = ""
IDEAL_CAL = ""
CURRENT_WATER = ""
IDEAL_WATER = ""
CURRENT_SLEEP = ""
IDEAL_SLEEP = ""
HEIGHT = ""
WEIGHT = ""
AGE = ""
SEX = ""
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


# start screen classes
class StartScreen(Screen):
    global CLIENT_SOC

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


class LogInScreen(Screen):
    global CLIENT_SOC
    username = ObjectProperty(None)
    password = ObjectProperty(None)

    def __init__(self, **kwargs):
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
        global USERNAME
        username = self.username.text
        password = self.password.text

        if " " in username or username == "" or " " in password or password == "":  # error state
            send_to_server(CLIENT_SOC, ("error" + " " + username + " " + password))
            self.error_lbl.text = recv_from_server(CLIENT_SOC)
            return

        # hash the password :P crypto wow!
        hashed_pwd = sha256(password.encode()).hexdigest()

        send_to_server(CLIENT_SOC, ("log" + " " + username + " " + hashed_pwd))  # modify the server we are logging in
        data_from_server = recv_from_server(CLIENT_SOC)  # get answer whether we logged in or not

        if "Successfully" in data_from_server:
            print(":)")
            USERNAME = username
            # update the server that we need the calories, water cups and sleep hours of user
            update_calories(CLIENT_SOC)
            update_water(CLIENT_SOC)
            update_sleep(CLIENT_SOC)
            self.manager.current = 'main'

        else:
            print(":(")
            self.error_lbl.text = data_from_server  # "Username has not found."


class SignUpScreen(Screen):
    global CLIENT_SOC
    username = ObjectProperty(None)
    password = ObjectProperty(None)

    def __init__(self, **kwargs):
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
        global USERNAME
        username = self.username.text
        password = self.password.text

        if " " in username or username == "" or " " in password or password == "":  # error state
            send_to_server(CLIENT_SOC, ("error" + " " + username + " " + password))
            self.error_lbl.text = recv_from_server(CLIENT_SOC)
            return

        # hash the password :P crypto wow!
        hashed_pwd = sha256(password.encode()).hexdigest()

        send_to_server(CLIENT_SOC, ("sign" + " " + username + " " + hashed_pwd))  # modify the server we are signing up
        data_from_server = recv_from_server(CLIENT_SOC)

        if "Good" in data_from_server:
            print(":)")
            USERNAME = username
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

    def set_cursor(self, pos, dt):
        self.cursor = pos


# main screen classes
class MainScreen(Screen):
    global USERNAME, CLIENT_SOC

    username = StringProperty(USERNAME)

    def update_username(self):
        self.username = USERNAME

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
        update_profile(CLIENT_SOC)
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


class ProfileScreen(Screen):
    global AGE, HEIGHT, WEIGHT, SEX, USERNAME

    def __init__(self, **kwargs):
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
        self.username_lbl.text = "Username: " + USERNAME
        self.age_lbl.text = "Age: " + AGE
        self.height_lbl.text = "Height: " + HEIGHT + " (cm)"
        self.weight_lbl.text = "Weight: " + WEIGHT + " (kg)"
        self.sex_lbl.text = "Sex: " + SEX
        return

    def pressed_main(self):
        """
        when pressing the main button it moves to the main screen
        :return: None
        """
        self.manager.current = 'main'


class UpdateInfoScreen(Screen):
    global CLIENT_SOC

    # vars for user's data
    user_age = ObjectProperty(None)
    user_height = ObjectProperty(None)
    user_weight = ObjectProperty(None)
    user_sex = ObjectProperty(None)

    def __init__(self, **kwargs):
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
                self.error_lbl.text = ""

                # update the server that we need the calories, water cups and sleep hours
                update_calories(CLIENT_SOC)
                update_water(CLIENT_SOC)
                update_sleep(CLIENT_SOC)
                self.manager.current = 'main'

            else:
                print(":(")
                self.error_lbl.text = "error accord"


class WeeklyReportScreen(Screen):
    global CLIENT_SOC, IDEAL_CAL, IDEAL_WATER, IDEAL_SLEEP
    # vars for the report
    avg_cal = StringProperty(None)
    avg_water = StringProperty(None)
    avg_sleep = StringProperty(None)
    week_cal = ListProperty(None)
    week_water = ListProperty(None)
    week_sleep = ListProperty(None)

    def __init__(self, **kw):
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
        global IDEAL_CAL, IDEAL_WATER, IDEAL_SLEEP
        (avg, cal, water, sleep) = get_statistics(CLIENT_SOC)  # get the data from server
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
                                     ("Ideal", IDEAL_CAL, IDEAL_WATER, IDEAL_SLEEP)
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
    global CLIENT_SOC, USERNAME, CURRENT_CAL, IDEAL_CAL

    def __init__(self, **kwargs):
        super(CalScreen, self).__init__(**kwargs)
        self.curr_lbl = self.ids['current_cal']
        self.ideal_lbl = self.ids['ideal_cal']

    def update_calories(self):
        """
        shows the currant and ideal calories of the user
        :return: None
        """
        self.curr_lbl.text = CURRENT_CAL
        self.ideal_lbl.text = IDEAL_CAL
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
        global CLIENT_SOC, USERNAME
        user_amount = self.user_amount.text

        send_to_server(CLIENT_SOC, ("food" + " " + USERNAME))  # let the server know we're entering food

        if user_amount == "" or not user_amount.isnumeric():  # error state
            send_to_server(CLIENT_SOC, ("error" + " " + USERNAME))
            self.error_lbl.text = recv_from_server(CLIENT_SOC)
            return

        # good input
        user_data = self.choice + " " + user_amount
        send_to_server(CLIENT_SOC, user_data)
        data = recv_from_server(CLIENT_SOC)

        if "Finished" in data:
            print(":)")

            # clear data from text input
            self.user_amount.text = ""
            self.error_lbl.text = ""

            # update the server that we need the calories
            update_calories(CLIENT_SOC)
            self.manager.current = 'cal'

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
        global CLIENT_SOC
        user_amount = self.user_amount.text

        send_to_server(CLIENT_SOC, ("sport" + " " + USERNAME))  # let the server know we're entering sport

        if user_amount == "" or not user_amount.isnumeric():  # error state
            send_to_server(CLIENT_SOC, ("error" + " " + USERNAME))
            self.error_lbl.text = recv_from_server(CLIENT_SOC)
            return

        # good input
        user_data = self.choice + " " + user_amount
        send_to_server(CLIENT_SOC, user_data)
        data = recv_from_server(CLIENT_SOC)

        if "Finished" in data:
            print(":)")

            # clear data from text input
            self.user_amount.text = ""
            self.error_lbl.text = ""

            # update the server that we need the calories
            update_calories(CLIENT_SOC)
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
    global CLIENT_SOC, USERNAME, CURRENT_WATER, IDEAL_WATER

    def __init__(self, **kwargs):
        super(WaterScreen, self).__init__(**kwargs)
        self.curr_lbl = self.ids['current_water']
        self.ideal_lbl = self.ids['ideal_water']

    def update_water(self):
        """
        shows the currant and ideal water cups of the user
        :return: None
        """
        self.curr_lbl.text = CURRENT_WATER
        self.ideal_lbl.text = IDEAL_WATER
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
        when pressing the submit button it sends data to the server,
        and moves to main water screen if succeeded, else shows appropriate msg
        :return: None
        """
        global CLIENT_SOC
        user_amount = self.user_amount.text

        send_to_server(CLIENT_SOC, ("cups" + " " + USERNAME))  # let the server know we're entering cups

        if user_amount == "" or not user_amount.isnumeric():  # error state
            send_to_server(CLIENT_SOC, ("error" + " " + USERNAME))
            data_from_server = recv_from_server(CLIENT_SOC)
            self.error_lbl.text = data_from_server
            return

        # good input
        send_to_server(CLIENT_SOC, user_amount)
        data = recv_from_server(CLIENT_SOC)
        if "Finished" in data:
            print(":)")

            # clear data from text input
            self.user_amount.text = ""
            self.error_lbl.text = ""

            # update the server that we need the water cups
            update_water(CLIENT_SOC)
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
    global CLIENT_SOC, USERNAME, CURRENT_SLEEP, IDEAL_SLEEP

    def __init__(self, **kwargs):
        super(SleepScreen, self).__init__(**kwargs)
        self.curr_lbl = self.ids['current_sleep']
        self.ideal_lbl = self.ids['ideal_sleep']

    def update_sleep(self):
        """
        shows the currant and ideal sleep hours of the user
        :return: None
        """
        self.curr_lbl.text = CURRENT_SLEEP
        self.ideal_lbl.text = IDEAL_SLEEP
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
    user_start = ObjectProperty(None)
    user_finish = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(AddHoursScreen, self).__init__(**kwargs)
        self.error_lbl = self.ids['error_msg']

    def pressed_submit(self):
        """
        when pressing the submit button it sends data to the server,
        and moves to main sleep screen if succeeded, else shows appropriate msg
        :return: None
        """
        global CLIENT_SOC
        user_start = self.user_start.text
        user_finish = self.user_finish.text

        send_to_server(CLIENT_SOC, ("hours" + " " + USERNAME))  # let the server know we're entering hours

        # error state
        if user_start == "" or user_finish == "":
            send_to_server(CLIENT_SOC, ("error" + " " + USERNAME))
            data_from_server = recv_from_server(CLIENT_SOC)
            self.error_lbl.text = data_from_server
            return

        if ":" not in user_start or ":" not in user_finish:
            send_to_server(CLIENT_SOC, ("error" + " " + USERNAME))
            data_from_server = recv_from_server(CLIENT_SOC)
            self.error_lbl.text = data_from_server
            return

        # good input
        send_to_server(CLIENT_SOC, (user_start + " " + user_finish))
        data = recv_from_server(CLIENT_SOC)

        if "Finished" in data:
            print(":)")

            # clear data from text input
            self.user_start.text = ""
            self.user_finish.text = ""
            self.error_lbl.text = ""

            # update the server that we need the calories
            update_sleep(CLIENT_SOC)
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
    def build(self):
        """
        Build the different screens in the app
        :return: sm, screen manager
        """
        sm = ScreenManager()  # the screen manager of the app
        self.icon = 'heart-health.png'
        # start screen
        sm.add_widget(StartScreen(name='start'))
        sm.add_widget(LogInScreen(name='log in'))
        sm.add_widget(SignUpScreen(name='sign up'))
        sm.add_widget(StartInstructions(name='start instru'))
        # main screen
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(ProfileScreen(name='profile'))
        sm.add_widget(UpdateInfoScreen(name='update info'))
        sm.add_widget(WeeklyReportScreen(name='report'))
        sm.add_widget(MainInstructions(name='main instru'))
        # cal screen
        sm.add_widget(CalScreen(name='cal'))
        sm.add_widget(AddFoodScreen(name='food'))
        sm.add_widget(AddSportScreen(name='sport'))
        sm.add_widget(CalInstructionsOne(name='cal instru one'))
        sm.add_widget(CalInstructionsTwo(name='cal instru two'))
        # water screen
        sm.add_widget(WaterScreen(name='water'))
        sm.add_widget(AddCupsScreen(name='cups'))
        sm.add_widget(WaterInstructions(name='water instru'))
        # sleep screen
        sm.add_widget(SleepScreen(name='sleep'))
        sm.add_widget(AddHoursScreen(name='hours'))
        sm.add_widget(SleepInstructions(name='sleep instru'))
        return sm


# functions to handle connections to server that aren't related to a specific screen
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


def update_profile(client_socket):
    """
    update the info global variables with data from the server
    :param client_socket: the client socket
    :return: None
    """
    global CLIENT_SOC, AGE, HEIGHT, WEIGHT, SEX
    if CLIENT_SOC == client_socket:
        CLIENT_SOC.send(b"profile" + b" " + USERNAME.encode())
        data = CLIENT_SOC.recv(1024).decode().split(" ")
        AGE = data[0]
        HEIGHT = data[1]
        WEIGHT = data[2]
        if data[3] == "f":
            SEX = "female"
        else:
            SEX = "male"
        return


def get_statistics(client_socket):
    """
    get from the user avg and daily amounts of cal, water cups and sleep hours
    :param client_socket: the client socket
    :return: dict of avg and daily amounts of cal, water cups and sleep hours
    """
    global CLIENT_SOC
    if CLIENT_SOC == client_socket:
        CLIENT_SOC.send(b"report" + b" " + USERNAME.encode())
        tot_data = []  # CLIENT_SOC.recv(1024).decode().split(",")
        for _ in range(4):
            tot_data.append(CLIENT_SOC.recv(1024).decode())
            CLIENT_SOC.send("good".encode())
        avg = tot_data[0]
        cal = tot_data[1]
        water = tot_data[2]
        sleep = tot_data[3]
        return avg, cal, water, sleep


def main():
    global CLIENT_SOC  # global var to save the client socket

    # connect to server
    client_socket = socket.socket()
    client_socket.connect(('10.0.0.18', 10000))  # connect to server in port 10000
    CLIENT_SOC = client_socket

    # start the application
    BetterHealthApp().run()


if __name__ == '__main__':
    main()
