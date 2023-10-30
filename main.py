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
from flask import Flask, render_template_string, request, redirect
import asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()
STATUSES = {}
STOP_THREADS = asyncio.Event()
TOKEN = os.getenv("TOKEN")
dp = Dispatcher()
bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
DATA_LOCK = Lock()
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        action = request.form.get("action")
        key = request.form.get("key")
        value = request.form.get("value")

        with DATA_LOCK:
            global STATUSES
            if action == "add":
                STATUSES[key] = get_stream_status(value)
            elif action == "delete" and key in STATUSES:
                del STATUSES[key]
        return redirect('/')
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        <title>IP-cam check</title>
        <style>
            body {
                display: flex;
                height: 100vh;
                justify-content: center;
                align-items: center;
            }
        </style>
    </head>
    <body>
        <div class="container text-center">
            <table class="table table-bordered table-striped">
                <thead>
                    <tr>
                        <th>Камера</th>
                        <th>Возможность подключения</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {% for key, value in data.items() %}
                        <tr>
                            <td>{{ key }}</td>
                            <td>{{ value }}</td>
                            <td>
                                <form method="post">
                                    <input type="hidden" name="action" value="delete">
                                    <input type="hidden" name="key" value="{{ key }}">
                                    <button type="submit" class="btn btn-danger">Delete</button>
                                </form>
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
            <form method="post" class="mt-3">
                <input type="hidden" name="action" value="add">
                <input type="text" name="key" placeholder="Key" required>
                <input type="text" name="value" placeholder="Value" required>
                <button type="submit" class="btn btn-primary">Add</button>
            </form>
            <button class="btn btn-secondary mt-3" onclick="location.reload()">Reload</button>
        </div>
    </body>
    </html>
    ''', data=STATUSES)

def get_stream_status(url):
    """
    function captures first frame of rtsp stream and return result of capturing
    :param url: RTSP stream link
    :return: result of capture
    """
    stream = cv2.VideoCapture(url)
    ret = stream.grab() 
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
        global STATUSES
        with DATA_LOCK:
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
        global STATUSES
        #os.system('clear')
        print(f'|{f"refreshed {times_refreshed+1} times":{filler}^{string_len}}|')
        for key in STATUSES.keys():
            if STOP_THREADS.is_set():
                return
            print(f'|{f"{key} working: {STATUSES[key]}":^{string_len}}|')
        print(f"|{filler*string_len}|")
        times_refreshed+=1
        time.sleep(60)


async def get_input():
    no_stop_event = True
    while no_stop_event:
        global STOP_THREADS
        no_stop_event = not STOP_THREADS.is_set()
        a = await asyncio.to_thread(input, "Enter 'c' to stop: " )
        # keyboard.read_key() == 'c' or
        if a == 'c':
            STOP_THREADS.set()
            print("finished get_input")
            return
        await asyncio.sleep(1)

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, your chat id is {message.chat.id}")

async def send_periodic_message() -> None:
    chat_id = os.getenv('CHAT_ID')
    tmp_statuses = None
    no_stop_event = True
    while no_stop_event:
        global STOP_THREADS
        no_stop_event = not STOP_THREADS.is_set()
        updated_statuses = {}
        global STATUSES
        if STOP_THREADS.is_set():
            print("finished send_periodic_message")
            return
        if tmp_statuses is None:
            tmp_statuses = STATUSES.copy()
        for a,b in zip(tmp_statuses, STATUSES):
            if tmp_statuses[a] != STATUSES[b]:
                updated_statuses[a] = STATUSES[b]
                tmp_statuses[a] = STATUSES[b]
        if len(updated_statuses)>0:
            message = "Upadated Cams \n"
            message += '\n'.join([f"{a}:{updated_statuses[a]}" for a in updated_statuses.keys()])
            await bot.send_message(chat_id, message)
        await asyncio.sleep(5)

async def update_variable(check_list, pause_list, check_keys) -> None:
    no_stop_event = True
    while no_stop_event:
        global STOP_THREADS
        no_stop_event = not STOP_THREADS.is_set()
        global STATUSES
        with DATA_LOCK:
            for key in check_keys:
                if STOP_THREADS.is_set():
                    print("finished update_variable")
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
                    await asyncio.sleep(1)
                await asyncio.sleep(1)


def run_flask():
    port = 5001
    app.run(host='0.0.0.0', port=5000)

def async_main():
    check_list, pause_list = get_rtsp()
    check_keys = check_list.keys()
    loop = asyncio.get_event_loop()
    update_task = loop.create_task(update_variable(check_list, pause_list, check_keys))
    message_task = loop.create_task(send_periodic_message())
    input_task = loop.create_task(get_input())
    tg_task = loop.create_task(dp.start_polling(bot))
    threading.Thread(target=run_flask).start()
    loop.run_until_complete(asyncio.gather(tg_task, update_task, message_task, input_task))
    #await (dp.start_polling(bot))
    

if __name__ == "__main__":
    #port = 5001
    async_main()
    #t = threading.Thread(target=main())
    #t.start()
    #app.run(host='0.0.0.0', port=5000)
    
