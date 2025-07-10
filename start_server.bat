@echo off
title Starting Web Platform on Port 8080

:: Navigate to your project folder
cd /d C:\Users\tkrljan\Desktop\my-map-platform

:: Open the web browser to your page
start "" http://localhost:8080/index.html

:: Start the Python HTTP server on port 8080
python -m http.server 8080

:: Keep the window open after the server stops
pause