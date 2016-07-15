# -*- coding: utf-8 -*-
from pymongo import MongoClient
import telepot
import time
import re
from datetime import datetime, timedelta
from urllib.request import urlopen
import json
import random
import string

bot = telepot.Bot('222087284:AAGE6LHoKAr1tEIRvtiIqIni7WEo8lAHUio')

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

l_upd = lastUpdate(0, 0)

def parseTraffic(regionId):
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

def noCmd(chat_id, size):
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    textMain = ''.join(random.choice(chars) for _ in range(size))
    textAdd = '(Примерно так я вижу это, я понимаю только описанные команды)'
    text = textMain+'\n'+textAdd
    bot.sendMessage(chat_id, text)

def cmdHelp(chat_id):
    text = "Пример включения напоминаний: \n/set ниже 6 баллов c 17:00 до 22:00\n/set выше 4 баллов с 15:00\n/set равны 8 баллам после 13:00\nМои напоминания - /notifies"
    try:
        bot.sendMessage(chat_id, text)
    except Exception as t:
        print(t)

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
            levels = {"lower": ["баллов", "балла", "баллов", "баллов", "баллов", "баллов", "баллов", "баллов", "баллов", "баллов", "баллов"], "higher": ["баллов", "балла", "баллов", "баллов", "баллов", "баллов", "баллов", "баллов", "баллов", "баллов", "баллов"], "equal": ["баллам", "баллу", "баллам", "баллам", "баллам", "баллам", "баллам", "баллам", "баллам", "баллам", "баллам"]}
            i = 0
            for db_notify in db_chat['notifies']:
                i += 1
                str_i = str(i)
                notifies += (str_i+" Пробки "+modes[db_notify['mode']]+" "+str(db_notify['level'])+" "+levels[db_notify['mode']][int(db_notify['level'])]+" с "+db_notify['startTime']+" до "+db_notify['finalTime']+"\n")
            notifies += "\nЧтобы удалить все используйте /removeAll\nЧтобы удалить одно напоминание используйте /remove номер_напоминания, например:\n/remove 1"
            try:
                bot.sendMessage(chat_id, notifies)
            except Exception as t:
                print(t)
        else:
            text = "Напоминания о пробках не заданы"
            try:
                bot.sendMessage(chat_id, text)
            except Exception as t:
                print(t)
    else:
        text = "Напоминания о пробках не заданы"
        try:
            bot.sendMessage(chat_id, text)
        except Exception as t:
            print(t)

def cmdRemove(chat_id, text):
    notify_ids = [int(s) for s in text.split() if s.isdigit()]
    if len(notify_ids) > 0:
        notify_id = int(notify_ids[0])
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
                    except Exception as t:
                        print(t)
                else:
                    try:
                        bot.sendMessage(chat_id, "Такого напоминания нет")
                    except Exception as t:
                        print(t)
            else:
                text = "Напоминания о пробках не заданы"
                try:
                    bot.sendMessage(chat_id, text)
                except Exception as t:
                    print(t)
        else:
            text = "Напоминания о пробках не заданы"
            try:
                bot.sendMessage(chat_id, text)
            except Exception as t:
                print(t)
    else:
        try:
            bot.sendMessage(chat_id, "Неверный формат, нет номера напоминания\n Верно, например, так: /remove 4")
        except Exception as t:
                print(t)

def cmdRemoveAll(chat_id):
    db_chat = collTrafficBot.find_one({"chat_id": chat_id})
    if db_chat != None and db_chat != []:
        if db_chat['notifies'] != None and db_chat['notifies'] != []:
            notifies = []
            collTrafficBot.replace_one({"chat_id": chat_id}, {"chat_id": chat_id, "notifies": notifies})
            try:
                bot.sendMessage(chat_id, "Все напоминания удалены")
            except Exception as t:
                print(t)
        else:
            text = "Напоминания о пробках не заданы"
            try:
                bot.sendMessage(chat_id, text)
            except Exception as t:
                print(t)

def cmdSet(chat_id, text):
    sText = text.replace("/set", "")
    mode, tMode = validateMode(sText)
    if mode == None:
        te = "Некорректное условие, проверьте\nВерно, например, так:\n/set ниже 6 баллов после 17:00"
        try:
            bot.sendMessage(chat_id, te)
        except Exception as t:
            print(t)
    else:
        mText = sText.replace(tMode, "")
        startTime, finalTime = validateTime(mText)
        if startTime == None:
            te = "Некорректный формат времени, проверьте\nВерно, например, так: 23:53"
            try:
                bot.sendMessage(chat_id, te)
            except Exception as t:
                print(t)
        else:
            stText = mText.replace(startTime, "")
            if finalTime == None:
                finalTime = "23:59"
                ftText = stText
            else:
                ftText = stText.replace(finalTime, "")

            levels = [int(s) for s in ftText if s.isdigit()]
            print(levels)

            if len(levels) > 0:
                level = int(levels[0])
                if level > 10 or level < 0:
                    try:
                        te = "Некорректный уровень пробок, проверьте\n Баллы могут быть целым числом от 0 до 10"
                        bot.sendMessage(chat_id, te)
                    except Exception as t:
                        print(t)
                else:
                    print("start: %s, stop: %s, level: %s, mode: %s" % (startTime, finalTime, level, mode))
            
                    db_chat = collTrafficBot.find_one({"chat_id": chat_id})
                    if db_chat == None:
                        insertChat(chat_id, mode, level, startTime, finalTime)
                    else:
                        if db_chat['notifies'] != None:
                            updateChatNotifies(chat_id, mode, level, startTime, finalTime, db_chat)

def insertChat(chat_id, mode, level, startTime, finalTime):
    startTimeFormatted = datetime.strptime(startTime, "%H:%M")
    finalTimeFormatted = datetime.strptime(finalTime, "%H:%M")

    if startTimeFormatted == finalTimeFormatted:
        try:
            bot.sendMessage(chat_id, "Начальное и конечное время не могут быть одинаковыми")
        except Exception as t:
            print(t)
    else:
        notifies = [{"mode": mode, "level": level, "startTime": startTime, "finalTime": finalTime,"last": "0"}]
        query = {"chat_id": chat_id, "notifies": notifies}
        collTrafficBot.insert_one(query)
        answers = ["Ок, я сообщу)", "Это его мама, я передам", "Отличный выбор, сэр!", "Ок. Почему ботам не платят зарплату :(", "Шутки не будет, но задание принято", "Скажу, так и быть, жалко машину", "Ок"]
        answer = answers[random.randint(0,6)]
        try:
            bot.sendMessage(chat_id, answer)
        except Exception as t:
            print(t)

def updateChatNotifies(chat_id, mode, level, startTime, finalTime, db_chat):
    startTimeFormatted = datetime.strptime(startTime, "%H:%M")
    finalTimeFormatted = datetime.strptime(finalTime, "%H:%M")

    if startTimeFormatted == finalTimeFormatted:
        try:
            bot.sendMessage(chat_id, "Начальное и конечное время не могут быть одинаковы")
        except Exception as t:
            print(t)
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
        except Exception as t:
            print(t)

def validateTime(text):
    q = r'(([01]\d|2[0-3]):([0-5]\d)|24:00)'
    r = re.compile(q)
    m = r.findall(text)
    if m == []:
        return (None, None)
    elif len(m) == 1:
        return (m[0][0], None)
    else:
        return (m[0][0], m[1][0])

def validateMode(text):
    lq = r'([Нн][Ии][Жж][Ее])'
    hq = r'([Вв][Ыы][Шш][Ее])'
    eq = r'([Рр][Аа][Вв][Нн][Оо])'
    lr = re.compile(lq)
    hr = re.compile(hq)
    er = re.compile(eq)
    m = lr.findall(text)
    if len(m) > 0:
        return ("lower", m[0])
    else:
        m = hr.findall(text)
        if len(m) > 0:
            return ("higher", m[0])
        else:
            m = er.findall(text)
            if len(m) > 0:
                return ("equal", m[0])
            else:
                return (None, None)

def parseCommand(text):
    qStart = r'([/][Ss][Tt][Aa][Rr][Tt])'
    qSet = r'([/][Ss][Ee][Tt])'
    qRemove = r'([/][Rr][Ee][Mm][Oo][Vv][Ee])'
    qRemoveAll = r'([/][Rr][Ee][Mm][Oo][Vv][Ee][Aa][Ll][Ll])'
    qNotifies = r'([/][Nn][Oo][Tt][Ii][Ff][Ii][Ee][Ss])'
    qHelp = r'([/][Hh][Ee][Ll][Pp])'
    rStart = re.compile(qStart)
    rSet = re.compile(qSet)
    rRemove = re.compile(qRemove)
    rRemoveAll = re.compile(qRemoveAll)
    rNotifies = re.compile(qNotifies)
    rHelp = re.compile(qHelp)
    m = rStart.findall(text)
    if len(m) > 0:
        return ("start", m[0])
    else:
        m = rSet.findall(text)
        if len(m) > 0:
            return ("set", m[0])
        else:
            m = rRemoveAll.findall(text)
            if len(m) > 0:
                return ("removeAll", m[0])
            else:
                m = rRemove.findall(text)
                if len(m) > 0:
                    return ("remove", m[0])
                else:
                    m = rNotifies.findall(text)
                    if len(m) > 0:
                        return ("notifies", m[0])
                    else:
                        m = rHelp.findall(text)
                        if len(m) > 0:
                            return ("help", m[0])
                        else:
                            return (None, None)

def getUpdates(u_id, counter):

    response = bot.getUpdates(u_id)
    for item in response:
        update_id = int(item['update_id'])
        u_id = update_id+1
        message = item['message']
        try:
            text = str(message['text'])
            chat = message['chat']
            chat_id = chat['id']
            time = str(datetime.now())

            print("%s by %i on %s" % (text, chat_id, time))

            cmd, tCmd = parseCommand(text)

            if tCmd != None:
                cText = text.replace(tCmd, "")
            else:
                cText = text

            if cmd == "start":
                cmdStart(chat_id)
            elif cmd == "set":
                cmdSet(chat_id, cText)
            elif cmd == "remove":
                cmdRemove(chat_id, cText)
            elif cmd == "removeAll":
                cmdRemoveAll(chat_id)
            elif cmd == "notifies":
                cmdNotifies(chat_id)
            elif cmd == "help":
                cmdHelp(chat_id)
            else:
                noCmd(chat_id, len(text))
        except KeyError:
            print("key error")

    lastUpdate(u_id, 1)

    global l_upd
    l_upd = u_id

    global level
    global localTime

    if counter % 60 == 0:
        try:
            level, localTime = parseTraffic('213')
        except Exception as t:
            print(t)
    notify(level, localTime)
def checkDate(chat_id, mode, last, level, db_level, localTime, nowDate, startDate, finalDate, startTime, finalTime):
    levels = ["баллов", "балл", "балла", "балла", "балла", "баллов", "баллов", "баллов", "баллов", "баллов", "баллов"]
    if nowDate >= startDate and nowDate <= finalDate:
        if last != datetime.date(nowDate).strftime('%Y-%m-%d'):
            sLevel = levels[int(level)]
            if mode == "lower":
                if int(level) < int(db_level):
                    notify = {"mode": mode, "level": db_level, "startTime": startTime, "finalTime": finalTime, "last": datetime.date(nowDate).strftime('%Y-%m-%d')}
                    try:
                        bot.sendMessage(chat_id, "Внимание!\nПробки "+level+" "+sLevel+"\n("+localTime+")")
                    except Exception as t:
                        print(t)
                else:
                    notify = {"mode": mode, "level": db_level, "startTime": startTime, "finalTime": finalTime, "last": last}
            elif mode == "higher":
                if int(level) > int(db_level):
                    notify = {"mode": mode, "level": db_level, "startTime": startTime, "finalTime": finalTime, "last": datetime.date(nowDate).strftime('%Y-%m-%d')}
                    try:
                        bot.sendMessage(chat_id, "Внимание!\nПробки "+level+" "+sLevel+"\n("+localTime+")")
                    except Exception as t:
                        print(t)
                else:
                    notify = {"mode": mode, "level": db_level, "startTime": startTime, "finalTime": finalTime, "last": last}
            elif mode == "equal":
                if int(level) == int(db_level):
                    notify = {"mode": mode, "level": db_level, "startTime": startTime, "finalTime": finalTime, "last": datetime.date(nowDate).strftime('%Y-%m-%d')}
                    try:
                        msg = "Внимание!\nПробки "+level+" "+sLevel+"\n("+localTime+")"
                        bot.sendMessage(chat_id, msg)
                        print("Отправлено в %i: %s" % (chat_id, msg))
                    except Exception as t:
                        print(t)
                else:
                    notify = {"mode": mode, "level": db_level, "startTime": startTime, "finalTime": finalTime, "last": last}
        else:
            notify = {"mode": mode, "level": db_level, "startTime": startTime, "finalTime": finalTime, "last": last}
    else:
        notify = {"mode": mode, "level": db_level, "startTime": startTime, "finalTime": finalTime, "last": last}
    return notify
    print("Notify: %s" % notify)

def notify(level, localTime):
    items = collTrafficBot.find({"notifies": {"$exists": "true"}})
    for item in items:
        if item['chat_id'] != None:
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
global level
global localTime
level, localTime = parseTraffic('213')

while True:
    try:
        getUpdates(l_upd, counter)
        if counter == 60:
            counter = 1
        else:
            counter += 1
    except Exception as t:
        print(t)
    time.sleep(1)
