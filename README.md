# BetterHealth
An app that track you calories in each day - using socket connection and Kivy GUI - written in python.

## Server part
The server handles all the actions on the app - calculating the calories for a day, how many eaten and how many burned in sport activites. It also handles all the connections to the database - get info about member on the app, food or sport, upadate info about members and add new members to the app. At 12am the server make sure that the calories that gained in the current day will reset.

## Client part
The client part hadles the app - GUI. It handles all the input the app get from the user and sends appropriate data to server to enable the appropriate activity of the app.

## betterhealth.kv
Creates the visual app - screens, buttons, labels and etc.

#### *The code is in master branch*
