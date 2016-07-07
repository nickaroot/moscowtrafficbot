# -*- coding: utf-8 -*-
from pymongo import MongoClient
import telepot
#from os.path import abspath, expanduser
import time
import re
from datetime import datetime
from datetime import timedelta
from urllib.request import urlopen
import json
import random

bot = telepot.Bot('222087284:AAGE6LHoKAr1tEIRvtiIqIni7WEo8lAHUio')

#filepath = abspath('moscowtrafficbot_last_update_id.txt')

client = MongoClient('localhost', 27017)

dbTelegram = client.telegram

collTrafficBot = dbTelegram.trafficBot

def lastUpdate(key, mode):
    if mode == 0:
        db_lastUpdateDict = collTrafficBot.find_one({"last_update":{"$exists": "true"}})
        if db_lastUpdateDict != None:
            return db_lastUpdateDict["last_update"]
    elif mode == 1:
        db_lastUpdateDict = collTrafficBot.find_one({"last_update":{"$exists": "true"}})
        if db_lastUpdateDict != None:
            collTrafficBot.replace_one({"last_update":{"$exists": "true"}}, {"last_update": int(key)})
        else:
            collTrafficBot.insert_one({"last_update": int(key)})

#last_f = open(filepath)
#last_update = last_f.read()
#last_f.close()
l_upd = lastUpdate(0, 0)

def parseTraffic(regionId):

    #print("parseTraffic()")

    url = "http://jgo.maps.yandex.net/trf/stat.js"
    response = urlopen(url).read()
    jsonUnformatted = response[36::][0:-2:1]
    r = r"(['\"])?([a-zA-Z_]+)(['\"])?:"
    p = re.compile(r)
    jsonFormatted = (p.sub(r'"\2": ', jsonUnformatted.decode("utf-8")))
    data = json.loads(jsonFormatted)
    timestamp = data['timestamp']
    regions = data['regions']
    for region in regions:
        if region['regionId'] == regionId:
            return (region['level'], region['localTime'])

def cmdHelp(chat_id):
    text = "Пример включения напоминаний: \nПробки ниже 6 баллов с 17:00 до 22:00\nПробки выше 4 баллов с 15:00 до 23:59\nПробки равны 8 баллам с 13:00\nМои напоминания - /notifies"
    try:
        bot.sendMessage(chat_id, text)
    except:
        print(sys.exc_info()[0])

def cmdStart(chat_id):
    db_chat = collTrafficBot.find_one({"chat_id": chat_id})
    if db_chat == None:
        collTrafficBot.insert_one({"chat_id": chat_id, "notifies": []})
        cmdHelp(chat_id)

def cmdNotifies(chat_id):
    db_chat = collTrafficBot.find_one({"chat_id": chat_id})
    if db_chat != None:
        if db_chat['notifies'] != None and db_chat['notifies'] != []:
            notifies = "Напоминания:\n"
            modes = {"lower": "ниже", "higher": "выше", "equal": "равны"}
            levels = {"lower": "баллов", "higher": "баллов", "equal": "баллам"}
            i = 0
            for db_notify in db_chat['notifies']:
                i += 1
                str_i = str(i)
                notifies += (str_i+" Пробки "+modes[db_notify['mode']]+" "+db_notify['level']+" "+levels[db_notify['mode']]+" с "+db_notify['startTime']+" до "+db_notify['finalTime']+"\n")
            notifies += "\nЧтобы удалить все используйте /removeAll\nЧтобы удалить одно напоминание используйте /remove номер_напоминания, например:\n/remove 1"
            try:
                bot.sendMessage(chat_id, notifies)
            except:
                print(sys.exc_info()[0])
        else:
            text = "Напоминания о пробках не заданы"
            try:
                bot.sendMessage(chat_id, text)
            except:
                print(sys.exc_info()[0])
    else:
        text = "Напоминания о пробках не заданы"
        try:
            bot.sendMessage(chat_id, text)
        except:
            print(sys.exc_info()[0])

def cmdRemove(chat_id, notify_id):
    db_chat = collTrafficBot.find_one({"chat_id": chat_id})
    if db_chat != None:
        if db_chat['notifies'] != None and db_chat['notifies'] != []:
            notifies = []
            i = 0
            for db_notify in db_chat['notifies']:
                i += 1
                if i != notify_id:
                    notifies.append(db_notify)
            collTrafficBot.replace_one({"chat_id": chat_id}, {"chat_id": chat_id, "notifies": notifies})
            if notify_id <= i:
                try:
                    bot.sendMessage(chat_id, "Напоминание удалено")
                except:
                    print(sys.exc_info()[0])
            else:
                try:
                    bot.sendMessage(chat_id, "Такого напоминания нет")
                except:
                    print(sys.exc_info()[0])
        else:
            text = "Напоминания о пробках не заданы"
            try:
                bot.sendMessage(chat_id, text)
            except:
                print(sys.exc_info()[0])
    else:
        text = "Напоминания о пробках не заданы"
        try:
            bot.sendMessage(chat_id, text)
        except:
            print(sys.exc_info()[0])

def cmdRemoveAll(chat_id):
    db_chat = collTrafficBot.find_one({"chat_id": chat_id})
    if db_chat != None and db_chat != []:
        if db_chat['notifies'] != None and db_chat['notifies'] != []:
            notifies = []
            collTrafficBot.replace_one({"chat_id": chat_id}, {"chat_id": chat_id, "notifies": notifies})
            try:
                bot.sendMessage(chat_id, "Все напоминания удалены")
            except:
                print(sys.exc_info()[0])
        else:
            text = "Напоминания о пробках не заданы"
            try:
                bot.sendMessage(chat_id, text)
            except:
                print(sys.exc_info()[0])

def insertChat(chat_id, mode, level, startTime, finalTime):
    startTimeFormatted = datetime.strptime(startTime, "%H:%M")
    finalTimeFormatted = datetime.strptime(finalTime, "%H:%M")

    if startTimeFormatted == finalTimeFormatted:
        try:
            bot.sendMessage(chat_id, "Начальное и конечное время не могут быть одинаковыми")
        except:
            print(sys.exc_info()[0])
    else:
        notifies = [{"mode": mode, "level": level, "startTime": startTime, "finalTime": finalTime,"last": "0"}]
        query = {"chat_id": chat_id, "notifies": notifies}
        collTrafficBot.insert_one(query)
        answers = ["Ок, я сообщу)", "Это его мама, я ему передам", "Отличный выбор, сэр!", "Ок. Почему ботам не платят зарплату :(", "Шутки не будет, но задание принято", "Скажу, так и быть, машина ведь не недвижимостью", "Ок"]
        answer = answers[random.randint(0,6)]
        try:
            bot.sendMessage(chat_id, answer)
        except:
            print(sys.exc_info()[0])

def updateChatNotifies(chat_id, mode, level, startTime, finalTime, db_chat):
    startTimeFormatted = datetime.strptime(startTime, "%H:%M")
    finalTimeFormatted = datetime.strptime(finalTime, "%H:%M")

    if startTimeFormatted == finalTimeFormatted:
        try:
            bot.sendMessage(chat_id, "Начальное и конечное время не могут быть одинаковы")
        except:
            print(sys.exc_info()[0])
    else:
        if finalTime == "0" or finalTime == "00:00":
            finalTime = "23:59"
        notifies = []
        notify = {"mode": mode, "level": level, "startTime": startTime, "finalTime": finalTime, "last": "0"}
        for db_notify in db_chat['notifies']:
            if notify != db_notify:
                notifies.append(db_notify)
        notifies.append(notify)
        collTrafficBot.replace_one({"chat_id": chat_id}, {"chat_id": chat_id, "notifies": notifies})
        answers = ["Ок, я сообщу и это)", "Требую трудоустройсво по ТК РФ! (Шучу, я прослежу и напишу ;)", "Принято!", "И снова ты пришел ко мне, сын мой. Я помогу тебе!", "Ок"]
        answer = answers[random.randint(0,4)]
        try:
            bot.sendMessage(chat_id, answer)
        except:
            print(sys.exc_info()[0])

def getUpdates(u_id, counter, initLevel, initLocalTime):

    #print("getUpdates()")

    response = bot.getUpdates(u_id)

    for item in response:
        update_id = int(item['update_id'])
        u_id = update_id+1
        message = item['message']
        text = str(message['text'])
        chat = message['chat']
        chat_id = chat['id']
        time = str(datetime.now())
        print("%s by %i on %s" % (text, chat_id, time))
        if text == "/help":
            cmdHelp(chat_id)
        elif text == "/start":
            cmdStart(chat_id)
        elif text == "/notifies":
            cmdNotifies(chat_id)
        elif text == "/removeAll":
            try:
                cmdRemoveAll(chat_id)
            except:
                print(sys.exc_info()[0])
        elif text == "/remove":
            try:
                bot.sendMessage(chat_id, "Укажите номер напоминания для удаления")
            except:
                print(sys.exc_info()[0])
        elif text[0:7] == "/remove" and text != "/remove":
            try:
                notify_id = int(re.search(r'\d+', text).group())
                cmdRemove(chat_id, notify_id)
            except:
                print(sys.exc_info()[0])
        elif text[0:6] == "пробки" or text[0:6] == "Пробки" or text[0:6] == "ПРОБКИ":
            mode = ""
            offset = 0
            if text[7:11] == "ниже" or text[7:11] == "Ниже" or text[7:11] == "НИЖЕ":
                mode = "lower"

            elif text[7:11] == "выше" or text[7:11] == "Выше" or text[7:11] == "ВЫШЕ":
                mode = "higher"

            elif text[7:12] == "равны" or text[7:12] == "Равны" or text[7:12] == "РАВНЫ":
                mode = "equal"
                offset += 1

            if text[12+offset:14+offset] == "10":
                offset += 1
                level = "10"

            else:
                level = text[12+offset:13+offset]

            if text[21+offset:22+offset] == "с" or text[21+offset:22+offset] == "С" or text[21+offset:22+offset] == "c" or text[21+offset:22+offset] == "C":
                startTime = text[23+offset:28+offset]

                if text[29+offset:31+offset] == "до" or text[29+offset:31+offset] == "До" or text[29+offset:31+offset] == "ДО":
                    finalTime = text[32+offset:37+offset]
                    print("start: %s, stop: %s, level: %s, mode: %s" % (startTime, finalTime, level, mode))
                    db_chat = collTrafficBot.find_one({"chat_id": chat_id})
                    if db_chat == None:
                        insertChat(chat_id, mode, level, startTime, finalTime)
                    else:
                        if db_chat['notifies'] != None:
                            updateChatNotifies(chat_id, mode, level, startTime, finalTime, db_chat)

                else:
                    finalTime = "23:59"
                    db_chat = collTrafficBot.find_one({"chat_id": chat_id})
                    if db_chat == None:
                        insertChat(chat_id, mode, level, startTime, finalTime)
                    else:
                        if db_chat['notifies'] != None:
                            updateChatNotifies(chat_id, mode, level, startTime, finalTime, db_chat)
    
    #last_f = open(filepath, "w")
    #last_f.write(str(u_id))
    #last_f.close()
    lastUpdate(u_id, 1)

    #global last_update
    #last_update = u_id
    global l_upd
    l_upd = u_id

    if counter % 60 == 0:
        level, localTime = parseTraffic('213')
    try:
        notify(level, localTime)
    except:
        notify(initLevel, initLocalTime)

def checkDate(chat_id, mode, last, level, db_level, localTime, nowDate, startDate, finalDate, startTime, finalTime):
    if nowDate >= startDate and nowDate <= finalDate:
        if last != datetime.date(nowDate).strftime('%Y-%m-%d'):
            if mode == "lower":
                if level < db_level:
                    notify = {"mode": mode, "level": db_level, "startTime": startTime, "finalTime": finalTime, "last": datetime.date(nowDate).strftime('%Y-%m-%d')}
                    try:
                        bot.sendMessage(chat_id, "Внимание!\nПробки "+level+" баллов\n("+localTime+")")
                    except:
                        print(sys.exc_info()[0])
                else:
                    notify = {"mode": mode, "level": db_level, "startTime": startTime, "finalTime": finalTime, "last": last}
            elif mode == "higher":
                if level > db_level:
                    notify = {"mode": mode, "level": db_level, "startTime": startTime, "finalTime": finalTime, "last": datetime.date(nowDate).strftime('%Y-%m-%d')}
                    try:
                        bot.sendMessage(chat_id, "Внимание!\nПробки "+level+" баллов\n("+localTime+")")
                    except:
                        print(sys.exc_info()[0])
                else:
                    notify = {"mode": mode, "level": db_level, "startTime": startTime, "finalTime": finalTime, "last": last}
            elif mode == "equal":
                if level == db_level:
                    notify = {"mode": mode, "level": db_level, "startTime": startTime, "finalTime": finalTime, "last": datetime.date(nowDate).strftime('%Y-%m-%d')}
                    try:
                        bot.sendMessage(chat_id, "Внимание!\nПробки "+level+" баллов\n("+localTime+")")
                    except:
                        print(sys.exc_info()[0])
                else:
                    notify = {"mode": mode, "level": db_level, "startTime": startTime, "finalTime": finalTime, "last": last}
        else:
            notify = {"mode": mode, "level": db_level, "startTime": startTime, "finalTime": finalTime, "last": last}
    else:
        notify = {"mode": mode, "level": db_level, "startTime": startTime, "finalTime": finalTime, "last": last}
    return notify
    print("Notify: %s" % notify)
def notify(level, localTime):
    items = collTrafficBot.find({})
    for item in items:
        chat_id = item['chat_id']
        db_notifies = item['notifies']
        notifies = []
        for notify in db_notifies:
            if notify != None:
                db_level = notify['level']
                mode = notify['mode']
                last = notify['last']
                nowDate = datetime.now()
                startDate = datetime.combine(datetime.date(nowDate), datetime.time(datetime.strptime(notify['startTime'], "%H:%M")))
                finalDate = datetime.combine(datetime.date(nowDate), datetime.time(datetime.strptime(notify['finalTime'], "%H:%M")))
                if startDate > finalDate:
                    tommorowDate = nowDate + timedelta(days=1)
                    yesterdayDate = nowDate - timedelta(days=1)
                    if datetime.date(nowDate) < datetime.date(finalDate):
                        finalDate = datetime.combine(datetime.date(tommorowDate), datetime.time(finalDate))
                    else:
                        startDate = datetime.combine(datetime.date(yesterdayDate), datetime.time(startDate))
                    new_notify = checkDate(chat_id, mode, last, level, db_level, localTime, nowDate, startDate, finalDate, notify['startTime'], notify['finalTime'])
                    notifies.append(new_notify)
                elif startDate < finalDate:
                    new_notify = checkDate(chat_id, mode, last, level, db_level, localTime, nowDate, startDate, finalDate, notify['startTime'], notify['finalTime'])
                    notifies.append(new_notify)
        collTrafficBot.replace_one({"chat_id": chat_id}, {"chat_id": chat_id, "notifies": notifies})

counter = 0
initLevel, initLocalTime = parseTraffic('213')

while True:
    try:
        getUpdates(l_upd, counter, initLevel, initLocalTime)
        if counter == 60:
            counter = 1
        else:
            counter += 1
    except:
        time.sleep(1)
    time.sleep(1)
