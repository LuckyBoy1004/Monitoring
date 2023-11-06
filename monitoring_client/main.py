import datetime  
import socket
import os
import struct
import sys
import cv2
import numpy as np  #pip install numpy
import cv2 as cv    #pip install opencv-python
import pyautogui    #pip install PyAutoGUI
import time
from os import walk
import shutil
import winreg
from pywinauto import Application
from dotenv import dotenv_values
from threading import Thread
import psutil
import win32event
import win32api
import tkinter as tk
from tkinter import messagebox
import requests
import json

def create_result_directory():
    global directory
    directory = "C:\\Users/Public/Result_Output/"
    if os.path.exists(directory):
        pass
    else:
        os.makedirs(directory)

mutex_name = "Monitoring_client"
def add_to_startup():
    global _log_file_path
    
    script_name = "Monitoring"
    client_log_file = 'Monitoring_Client.txt'
    create_result_directory()
    running_file = sys.argv[0]
    setting_conf_path = os.path.join(os.getenv("APPDATA"))
    global setting_file_path
    setting_file_path = setting_conf_path.replace('\\AppData\\Roaming','')
    _log_file_path = setting_file_path + '/' + client_log_file
    script_path = os.path.abspath(running_file)
    __conf_root = script_path.replace(running_file.replace('.\\',''),'')
    print(__conf_root)
    if os.path.exists(os.path.join(__conf_root, "setting.conf")):
        setting_path = os.path.abspath('setting.conf')
        if os.path.exists(os.path.join(setting_file_path, "setting.conf")):
        # Copy the setting file to the Startup folder
            os.remove(setting_file_path + '\\setting.conf')
            shutil.copy2(setting_path, setting_file_path)
        else:
            shutil.copy2(setting_path, setting_file_path)
        # setting_file_path = "."
    else:
        pass
    # Get the path to the Startup folder
    startup_folder = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    # Copy the script to the Startup folder
    if not os.path.exists(os.path.join(startup_folder, "main.exe")):
        # Copy the script to the Startup folder
        shutil.copy2(script_path, startup_folder)
        log_file = open(_log_file_path, mode='a', buffering=1)
        log_file.write("Set to run automatically upon restart. {}\n".format(time.strftime("%y:%m:%d %H:%M:%S", time.localtime())))
        log_file.close()  
    else:
        pass
    # Create a shortcut to the script
    shortcut_path = os.path.join(startup_folder, f"{script_name}.lnk")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
        winreg.SetValueEx(key, script_name, 0, winreg.REG_SZ, shortcut_path)
add_to_startup()


mutex = win32event.CreateMutex(None, 1, mutex_name)
if win32api.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    log_file = open(_log_file_path, mode='a', buffering=1)
    log_file.write("Another instance of the program is already running. {}\n".format(time.strftime("%y:%m:%d %H:%M:%S", time.localtime())))
    log_file.close()   
    sys.exit()
# win32event.ReleaseMutex(mutex)
def check_socket_connection():
    global server_port
    server_port = 56230
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(20)
        try:
            sock.connect((server_ip, server_port))
            # If the connection was successful, print a success message
            print(f"Successfully connected to {server_ip}")
            log_file = open(_log_file_path, mode='a', buffering=1)
            log_file.write(f"Successfully connected to {server_ip} \n".format(time.strftime("%y:%m:%d %H:%M:%S", time.localtime())))
            log_file.close()

            def test_connect():
                while True:
                    try:
                        data = sock.recv(1024)
                    except socket.error as err:
                        print('disconnected Socket, reconnecting...')
                        sock.close()
                        check_socket_connection()
                        break
            test_thread = Thread(target=test_connect)
            test_thread.start()            
            #record process
            record_process()
        except socket.timeout:
            print('Socket disconnected, reconnecting...')
            sock.close()
            check_socket_connection()            
        except socket.error as err:
            print('not connect Socket, reconnecting...')
            sock.close()
            check_socket_connection()
    except socket.error as e:
        # If an error occurred during the connection attempt, print the error message
        print(f"Failed to connect to {server_ip}:{server_port} - {e}")
        log_file = open(_log_file_path, mode='a', buffering=1)
        log_file.write(f"Failed to connect to {server_ip} \n".format(time.strftime("%y:%m:%d %H:%M:%S", time.localtime())))
        log_file.close()
        # Reconnect to the server
        sock.close()
        check_socket_connection()
def find_time():
    x = datetime.datetime.now()
    date_for_name = (x.strftime("%Y") + "-" + x.strftime("%m") + "-" + x.strftime("%d") + "-" + x.strftime("%H") + "-" +
                     x.strftime("%M") + "-" + x.strftime("%S"))
    # date_for_name = (x.strftime("%d") + "-" + x.strftime("%m") + "-" + x.strftime("%Y") + "-" + x.strftime("%H") + "-" +
    #                  x.strftime("%M") + "-" + x.strftime("%S"))
    return date_for_name

def into_server(cut_time):
    print("into_server")
    files1 = os.listdir(directory)
    for file in files1:
        created_file_time = file.split(' ')[1].split('.')[0]
        if current_recording(cut_time,created_file_time):
            imgfp = open(directory+file, 'rb')
            # imgdata = imgfp.read()
            # imgfp.close()
            # send(imgdata, find_time(), find_time(), file, user_name)
            url = "http://103.116.105.101/upload.php"

            payload = {}
            files=[
                ('sendfile',(directory+file,imgfp,'application/octet-stream'))
            ]
            headers = {
                'Content-Type': 'multipart/form-data'
            }

            response = requests.request("POST", url, data=payload, files=files)

            print(response.text)
            text = json.loads(response.text)

            log_file = open(_log_file_path, mode='a', buffering=1)
            log_file.write(response.text + "\n" + ' {}\n'.format(time.strftime("%y:%m:%d %H:%M:%S", time.localtime())))
            log_file.close()
            if text['message'] == "File Uploaded Successfully":
                print(text['message'])
                imgfp.close()
                os.remove( directory+file )
            if text['message'] == "Sorry, file already exists check upload folder":
                print(text['message'])
                imgfp.close()
                os.remove( directory+file )
            time.sleep(1)

def send(screen, currtime, idletime, filename, username):
    sock = socket.socket()
    sock.settimeout(60)
    try:
        print('server send success...')
        sock.connect((server_ip, server_port))
        sock.sendall(struct.pack('<QQ64s64sI', 111, 222, filename.encode('utf-8'), username.encode('utf-8'), len(screen)))
        sock.sendall(screen)
        sock.close()
        os.remove( directory+filename )
        log_file = open(_log_file_path, mode='a', buffering=1)
        log_file.write("send file success....\n"+ ' {}\n'.format(time.strftime("%y:%m:%d %H:%M:%S", time.localtime())))
        log_file.close()
        
    except:
        print('server connection faild.')
        # send(screen, currtime, idletime, filename, username)
        log_file = open(_log_file_path, mode='a', buffering=1)
        log_file.write("send file success failed...      Server connection failed\n")
        log_file.close()
 
def video_record():
    log_file = open(_log_file_path, mode='a', buffering=1)
    log_file.write("Started recording...\n")
    log_file.close()
    cut_time = 10
    create_time = datetime.datetime.now()
    screen_width, screen_height = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    output = cv2.VideoWriter(directory + user_name + " " + find_time() + ".mp4", fourcc, 20.0, (screen_width, screen_height))
    frame_count = 0
    while True:
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output.write(frame)
        frame_count += 1
        if frame_count % (20 * 60 * cut_time) == 0:
            output.release()
            thread = Thread(target=into_server, args=(cut_time,))
            thread.start()
            # into_server(cut_time)
            output = cv2.VideoWriter(directory + user_name + " " + find_time() + ".mp4", fourcc, 20.0, (screen_width, screen_height))
        # current_time = datetime.datetime.now()
        # difference_minutes = (current_time - create_time).total_seconds() / 60
        # if difference_minutes >= 2.1:
        #     break
    output.release()
    cv2.destroyAllWindows()

def current_recording(cut_time,created_file_time):
    _current_time = datetime.datetime.now()
    change_time_dt = datetime.datetime.strptime(created_file_time, "%Y-%m-%d-%H-%M-%S")
    diff = (_current_time - change_time_dt).total_seconds() / 60
    if diff < cut_time:
        return False
    return True

def start_monitoring():
    
    log_file = open(_log_file_path, mode='a',buffering=1)
    log_file.write("Started monitoring client."+ ' {}\n'.format(time.strftime("%y:%m:%d %H:%M:%S", time.localtime())))
    log_file.close()
    video_record()

def record_process():
    print('username', user_name)
    if user_name == '':
        # messagebox.showwarning("Incorrect USER_NAME", f"Please insert correct USER_NAME in setting.conf.")
        log_file = open(_log_file_path, mode='a',buffering=1)
        log_file.write("Incorrect USER_NAME          Please insert correct USER_NAME in setting.conf.")
        log_file.close()
    # checking_connection = check_socket_connection(server_ip)
    # if checking_connection == False:
    #     status = True
    else :
        try:
            start_monitoring()
        except Exception as e:
            log_file = open(_log_file_path, mode='a', buffering=1)
            log_file.write(str(e) + ' {}\n'.format(time.strftime("%y:%m:%d %H:%M:%S", time.localtime())))
            log_file.close()
            # win32event.ReleaseMutex(mutex)
    add_to_startup()

global server_ip,user_name
print(setting_file_path)
__file_path = setting_file_path + '\\setting.conf'
with open(__file_path, 'r') as file:
    for line in file:
        if line.startswith('SERVER_IP'):
            server_ip = line.split('=')[1].strip()
            print('serverIP:' + server_ip)
        elif line.startswith('USER_NAME'):
            user_name = line.split('=')[1].strip()
check_socket_connection()