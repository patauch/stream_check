"""
The idea of this project is to build app for checking the status of webcams used for other projects
Variants:
1) Telegram bot which will check status for all cams by button press
2) Little web service which will be held in docker container
3) console app which also can be handled in docker container
Questions:
1) How to check status of webcam without opening rtsp stream?
2) Is it really needed to develop such app

"""
import os
import time

import cv2
import threading
import json
from subprocess import call


listOfStatuses = {}

def get_rtsp():
    try:
        with open('rtsp.json', 'r') as file:
            listOfLinks = {}
            listOfPause = {}
            data = json.load(file)
            for key in data.keys():
                listOfLinks[key] = data[key]
                listOfPause[key] = 0
                listOfStatuses[key] = False

    except FileNotFoundError:
        print('No link file')
        return None
    return listOfLinks, listOfPause


def run(checkList, pauseList, checkKeys):
    lock = threading.Lock()
    while True:
        for key in checkKeys:
            if pauseList[key] == 0:
                lock.acquire()
                ret, frame = cv2.VideoCapture(checkList[key]).read()
                if ret:
                    listOfStatuses[key] = True
                else:
                    listOfStatuses[key] = False
                lock.release()
            else:
                pauseList[key] -= 1
            time.sleep(1)


def print_status(checkList):
    while True:
        lock = threading.Lock()
        lock.acquire()
        for key in listOfStatuses.keys():
            print(f'{checkList[key]} working: {listOfStatuses[key]}')
        lock.release()
        time.sleep(1)
        os.system('cls')


def main():
    checkList, pauseList = get_rtsp()
    checkKeys = checkList.keys()
    runThread = threading.Thread(target=run, args=[checkList, pauseList, checkKeys])
    printThread = threading.Thread(target=print_status, args=[checkList])
    runThread.start()
    printThread.start()


if __name__=="__main__":
    main()