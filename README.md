# BetterHealth

An app that track you calories, sleeping hours and drinking water in each day.  
Using socket connection and Kivy GUI. Written in python.

## Server part (server.py)
The server handles all the actions on the app - 
1. Calculating the recommended amount of calories, water cups and sleeping hours for a day.
2. Calculating how many calories eaten and how many burned in sport activites.
3. Calculating how many hours the user slept and how many water cups the user drank.
4. Handles all the connections to the database:
    - get info about member on the app
    - upadate info about members
    - add new members to the app
5. At 12am the server make sure that the calories that gained in the current day will reset.


## Client part (client.py)
The client part hadles the app - GUI.  
It handles all the input the app get from the user and sends appropriate data to server to enable the appropriate activity of the app.

## betterhealth.kv
Creates the visual app - screens, buttons, labels and etc.

## The rest of the files
The rest of the files are - 
1. png files that are in the app.
2. connection file to the database.

