"""
The idea of this project is to build app for checking the status of webcams used for other projects
Variants:
1) Telegram bot which will check status for all cams by button press
2) Little web service which will be held in docker container
3) console app which also can be handled in docker container
Questions:
1) How to check status of webcam without opening rtsp stream?
2) Is it really needed to develop such app
a
"""
import os
import time

import cv2
import threading
import json
from threading import Event, Lock

STATUS_LOCK = Lock()
STATUSES = {}
STOP_THREADS = Event()


def get_stream_status(url):
    """
    function captures first frame of rtsp stream and return result of capturing
    :param url: RTSP stream link
    :return: result of capture
    """
    stream = cv2.VideoCapture(url)
    ret, frame = stream.read()
    stream.release()
    return ret


def get_rtsp():
    """
    function parse json file and create dictionary files for each camera available
    :return: dictionaries with links and timeouts to check
    """
    global STATUSES
    try:
        with open('rtsp.json', 'r') as file:
            list_of_links = {}
            list_of_pause = {}
            data = json.load(file)
            for key in data.keys():
                list_of_links[key] = data[key]
                list_of_pause[key] = 0
                STATUSES[key] = False
    except FileNotFoundError:
        print('No link file')
        return None
    return list_of_links, list_of_pause


def run(check_list, pause_list, check_keys):
    """
    main function to check existing rtsp streams
    :param check_list: list of links
    :param pause_list: list of timeouts
    :param check_keys: list of rtsp stream names
    :return:
    """
    while True:
        global STOP_THREADS
        global STATUS_LOCK
        global STATUSES
        for key in check_keys:
            if STOP_THREADS.is_set():
                return
            if pause_list[key] == 0:
                ret = get_stream_status(check_list[key])
                if ret:
                    STATUSES[key] = True
                else:
                    STATUSES[key] = False
                pause_list[key] = 30
            else:
                pause_list[key] -= 1
                time.sleep(1)
            time.sleep(1)
        """print(f'|{f"refreshed {times_refreshed+1} times":{filler}^{string_len}}|')
        for key in check_keys:
                print(f'|{f"{key} working: {STATUSES[key]}":^{string_len}}|')
        print(f"|{filler*string_len}|")"""
        time.sleep(2)
        
        


def print_status():
    """
    function to print status for rtsp links
    :return:
    """
    times_refreshed = 0
    filler = '-'
    string_len = 45
    while True:    
        global STOP_THREADS
        global STATUS_LOCK
        global STATUSES
        os.system('clear')
        print(f'|{f"refreshed {times_refreshed+1} times":{filler}^{string_len}}|')
        for key in STATUSES.keys():
            if STOP_THREADS.is_set():
                return
            print(f'|{f"{key} working: {STATUSES[key]}":^{string_len}}|')
        print(f"|{filler*string_len}|")
        times_refreshed+=1
        time.sleep(4)


def get_input():
    while True:
        global STOP_THREADS
        a = input()
        # keyboard.read_key() == 'c' or
        if a == 'c':
            STOP_THREADS.set()
            return


def main():
    check_list, pause_list = get_rtsp()
    check_keys = check_list.keys()
    run_thread = threading.Thread(target=run, args=[check_list, pause_list, check_keys])
    catch_input_thread = threading.Thread(target=get_input)
    print_thread = threading.Thread(target=print_status)
    run_thread.start()
    catch_input_thread.start()
    print_thread.start()
    """runThread.join()
        keybThread.join()
        printThread.join()"""


if __name__ == "__main__":
    main()
