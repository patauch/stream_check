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


def get_stream_status(URL):
    """
    function captures first frame of rtsp stream and return result of capturing
    :param URL: RTSP stream link
    :return: result of capture
    """
    stream = cv2.VideoCapture(URL)
    ret, frame = stream.read()
    stream.release()
    return ret


def get_rtsp():
    """
    function parse json file and create dictionary files for each camera available
    :return: dictionaries with links and timeouts to check
    """
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
    """
    main function to check existing rtsp streams
    :param checkList: list of links
    :param pauseList: list of timeouts
    :param checkKeys: list of rtsp stream names
    :return:
    """
    lock = threading.Lock()
    while True:
        for key in checkKeys:
            if pauseList[key] == 0:

                ret = get_stream_status(checkList[key])

                if ret:
                    listOfStatuses[key] = True
                else:
                    listOfStatuses[key] = False
                pauseList[key] = 30
            else:
                pauseList[key] -= 1
                time.sleep(1)
            time.sleep(1)


def print_status(checkList):
    """
    function to print status for rtsp links
    :param checkList: list of links
    :return:
    """
    while True:
        for key in listOfStatuses.keys():
            print(f'{key} working: {listOfStatuses[key]}')
        time.sleep(2)
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