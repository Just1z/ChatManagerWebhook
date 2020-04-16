# -*- coding: utf-8 -*-
import vk_api # Библиотека для работы с VK API
import base64 # Нужно для photo_upload
import hashlib # Нужно для первого запроса
import urllib.request
import requests
from vk_api.longpoll import VkLongPoll, VkEventType
from flask import Flask, request, json
from hashlib import md5

settings = {'token': '...', # Токен от API Чат-Менеджера
            'id': 1, # ID вашей страницы ВК
            'access_token': '...'} # Токен от API VK, который вы должны получить самостоятельно по ссылке https://vk.com/away.php?to=https%3A%2F%2Fvk.cc%2F96T6nM

chats = {'AcDcaD': 127, 'CabDab': 144} # Слева - UID чатов у Чат-Менеджера, справа - ID чата у вас
# Поменяйте все данные на свои, т.к. это просто пример!

vk_session = vk_api.VkApi(token=settings["access_token"], api_version=5.100) 
vk = vk_session.get_api() # Вызываем VK API


app = Flask(__name__)

@app.route('/', methods=['POST'])
def processing():
    data = json.loads(request.data)


    if not data: # Если запрос пустой
        return "Пустой запрос!"


    if data["type"] == 'confirm': # Первый запрос
        confirm_str = str(str(settings["id"]) + settings["token"]).encode('utf-8') # Берём строку 
        confirmation_token = md5(confirm_str) # Превращаем строку в MD5 хэш
        return str(confirmation_token.hexdigest()) # Возвращаем MD5 хэш



    else:
        chat = chats[data["data"]['chat']] # Берём сразу ID чата



        if data["type"] == 'invite' or data["type"] == 'ban_expired': # Если использована команда !invite или прошёл срок бана
            user = data["data"]['user'] # ID пользователя, которого нужно пригласить или у которого прошёл бан
            # Если пользователь в друзьях вебхука и вы настроили ID чата в settings
            try:
                if chat in chats.values():
                    vk.execute(code='''var chat = %s;var user = %s;
if (API.friends.areFriends({"user_ids":user})[0].friend_status == 3){return API.messages.addChatUser({"chat_id": chat, "user_id": user});}''' % (chat, user))
                    return 'ok'
                else:
                    return '0'
            except:
                return '0'



        if data["type"] == 'delete_for_all':
            ids = ','.join(str(x) for x in data["data"]['conversation_message_ids']) # Список ID сообщений которые надо удалить
            try:
                if chat in chats.values():
                    # Получаем ID сообщений у себя
                    with urllib.request.urlopen("https://api.vk.com/method/messages.getByConversationMessageId?peer_id=%s&conversation_message_ids=%s&access_token=%s&v=5.100" % (2000000000 + int(chat), ids, settings["access_token"])) as url:
                        messages = json.loads(url.read().decode())['response']
                    msgids = '' # Создаём переменную
                    # В цикле к строке прибавляется новый ID, в конце получается строка с ID, разделёнными запятыми
                    for i in range(messages["count"]):
                        msgids = msgids + str(messages["items"][i]["id"]) + ',' # Когда цикл завершится, будет строка с ID сообщений, разделёнными запятыми
                    urllib.request.urlopen("https://api.vk.com/method/messages.delete?delete_for_all=1&message_ids=%s&access_token=%s&v=5.100" % (msgids[0:-1], settings["access_token"])) # Удаляем сообщения
                    return 'ok'
                else:
                    return '0'
            except:
                return '0'



        if data["type"] == 'message_pin':
            msg = data['data']['conversation_message_id'] # ID сообщения в беседе
            try:
                if chat in chats.values():
                    vk.execute(code='''var peer_id = %s + 2000000000;var msg = %s;
var msgid = API.messages.getByConversationMessageId({"peer_id":peer_id,"conversation_message_ids":msg}).items@.id;
return API.messages.pin({"peer_id":peer_id, "message_id":msgid});''' % (chat, msg))
                    return 'ok'
                else:
                    return '0'
            except:
                return '0'



        if data["type"] == 'photo_update':
            photo = data['data']['photo'] # Закодированное в base64 изображение беседы
            try:
                if chat in chats.values():
                    upload_url = vk.photos.getChatUploadServer(chat_id=chat)['upload_url'] # Получаем URL сервера для загрузки фото
                    with open("photo.png", "wb") as file:
                        file.write(base64.b64decode(photo)) # Декодируем base64 и создаём саму картинку
                        file.close() 
                    image = open("photo.png", "rb")
                    r = requests.post(upload_url, files={'file': ('photo.png', open("photo.png", 'rb'))}) # Загружаём её на сервер
                    with urllib.request.urlopen(upload_url) as server_url:
                        f = json.loads(r.text)['response'] # Получаем строку для ответа в setChatPhoto
                        vk.messages.setChatPhoto(file=f) # Изменяем изображение беседы
                        server_url.close()
                    image.close()
                    return 'ok'
                else:
                    return '0'
            except:
                return '0'





