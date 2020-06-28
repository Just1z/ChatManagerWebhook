# -*- coding: utf-8 -*-
import base64 # Нужно для photo_upload
import requests
from flask import Flask, request, json
from hashlib import md5 # Нужно для первого запроса

settings = {'token': '...', # Токен от API Чат-Менеджера
            'id': 1, # ID вашей страницы ВК
            'access_token': '...'} # Токен от API VK, который вы должны получить самостоятельно по ссылке https://vk.cc/96T6nM

chats = {'AAA': 111, 'BBB': 222} # Список ваших чатов. Ключ - UID, значение - id чата на вашей странице.

token = settings["access_token"]

app = Flask(__name__)
# Получаем Callback запрос
@app.route('/', methods=['POST'])
def processing():
    try:
        data = json.loads(request.data) # Декодируем Callback запрос
        if data["type"] == 'confirm': # Первый запрос
            confirm_str = str(str(settings["id"]) + settings["token"]).encode('utf-8') # Берём строку 
            confirmation_token = md5(confirm_str) # Превращаем строку в MD5 хэш
            return str(confirmation_token.hexdigest()) # Возвращаем MD5 хэш



        else:
            chat = chats[data["data"]['chat']] # Берём сразу ID чата


            if data["type"] == 'invite' or data["type"] == 'ban_expired': # Если использована команда !invite или прошёл срок бана
                user = data["data"]['user'] # ID пользователя, которого нужно пригласить или у которого прошёл бан
                code = f'var chat = {chat};var user = {user};' + 'if (API.friends.areFriends({"user_ids": user})[0].friend_status == 3){return API.messages.addChatUser({"chat_id": chat, "user_id": user});}'
                requests.post('https://api.vk.com/method/execute', params={"code": code, "access_token": token, "v": 5.103})



            if data["type"] == 'delete_for_all':
                ids = ','.join(str(x) for x in data["data"]['conversation_message_ids']) # Список ID сообщений которые надо удалить
                # Получаем ID сообщений у себя
                messages = requests.post("https://api.vk.com/method/messages.getByConversationMessageId", params={"peer_id": 2000000000 + chat, "conversation_message_ids": ids, "access_token": token, "v": 5.103}).json()['response']
                msgids = '' # Создаём переменную
                for i in range(messages["count"]): # В цикле к строке прибавляется новый ID, в конце получается строка с ID, разделёнными запятыми
                    msgids = msgids + str(messages["items"][i]["id"]) + ',' # Когда цикл завершится, будет строка с ID сообщений, разделёнными запятыми
                requests.post("https://api.vk.com/method/messages.delete", params={"delete_for_all": 1, "message_ids": msgids[0:-1], "access_token": token, "v": 5.103}) # Удаляем сообщения



            if data["type"] == 'message_pin':
                msg = data['data']['conversation_message_id'] # ID сообщения в беседе
                code = f'var peer_id = {chat} + 2000000000;var msg = "{msg}";' + 'var msgid = API.messages.getByConversationMessageId({"peer_id":peer_id,"conversation_message_ids":msg}).items@.id;return API.messages.pin({"peer_id":peer_id, "message_id":msgid});'
                requests.post('https://api.vk.com/method/execute', params={"code": code, "access_token": token, "v": 5.103})



            if data["type"] == 'photo_update':
                photo = data['data']['photo'] # Закодированное в base64 изображение беседы
                upload_url = requests.get("https://api.vk.com/method/photos.getChatUploadServer", params={"chat_id": chat, "access_token": token, "v": 5.103}).json()['response']['upload_url'] # Получаем URL сервера для загрузки фото
                print(upload_url)
                with open("photo.png", "wb") as file:
                    file.write(base64.b64decode(photo)) # Декодируем base64 и создаём саму картинку
                    file.close()
                image = open("photo.png", "rb")
                f = requests.get(upload_url, files={'file': ('photo.png', open("photo.png", 'rb'))}).json()['response'] # Загружаём её на сервер и берём строку для ответа в setChatPhoto
                requests.post(f"https://api.vk.com/method/messages.setChatPhoto", params={"file": f, "access_token": token, "v": 5.103})
                image.close()

            return 'ok'
    except:
        return '0'