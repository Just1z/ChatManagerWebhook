# -*- coding: utf-8 -*-
import base64
from hashlib import md5
import requests
from flask import Flask, request, json

SETTINGS = {'token': '...', # Токен от API Чат-Менеджера
            'id': 1, # ID вашей страницы ВК
            'access_token': '...'} # Токен от API VK нужно получить здесь: https://vk.cc/96T6nM

# Список ваших чатов. Ключ - UID, значение - id чата на вашей странице.
CHATS = {'AAA': 111, 'BBB': 222}
TOKEN = SETTINGS["access_token"]

app = Flask(__name__)
@app.route('/', methods=['POST'])
def processing():
    try:
        data = json.loads(request.data) # Декодируем Callback запрос
        if data["type"] == 'confirm': # Первый запрос
            confirm_str = str(str(SETTINGS["id"]) + SETTINGS["token"]).encode('utf-8')
            confirmation_token = md5(confirm_str) # Превращаем строку в MD5 хэш
            return str(confirmation_token.hexdigest()) # Возвращаем MD5 хэш
        else:
            chat = CHATS[data["data"]['chat']] # Берём сразу ID чата

            if data["type"] == 'invite' or data["type"] == 'ban_expired':
                user = data["data"]['user'] # ID пользователя, которого нужно пригласить в чат
                code = f'var chat = {chat};var user = {user};' + 'if (API.friends.areFriends({"user_ids": user})[0].friend_status == 3){return API.messages.addChatUser({"chat_id": chat, "user_id": user});}'
                requests.post(
                    'https://api.vk.ru/method/execute',
                    params={"code": code,
                            "access_token": TOKEN, 
                            "v": 5.103},
                    timeout=60)

            if data["type"] == 'delete_for_all':
                # Список ID сообщений которые надо удалить
                ids = ','.join(str(x) for x in data["data"]['conversation_message_ids'])
                # Получаем ID сообщений у себя
                messages = requests.post(
                    "https://api.vk.ru/method/messages.getByConversationMessageId",
                    params={"peer_id": 2000000000 + chat,
                            "conversation_message_ids": ids,
                            "access_token": TOKEN,
                            "v": 5.103},
                    timeout=60).json()['response']
                msgids = ",".join(i["id"] for i in messages["items"])
                requests.post(
                    "https://api.vk.ru/method/messages.delete",
                    params={"delete_for_all": 1,
                            "message_ids": msgids,
                            "access_token": TOKEN,
                            "v": 5.103},
                    timeout=60) # Удаляем сообщения

            if data["type"] == 'message_pin':
                msg = data['data']['conversation_message_id'] # ID сообщения в беседе
                code = f'var peer_id = {chat} + 2000000000;var msg = "{msg}";' + 'var msgid = API.messages.getByConversationMessageId({"peer_id":peer_id,"conversation_message_ids":msg}).items@.id;return API.messages.pin({"peer_id":peer_id, "message_id":msgid});'
                requests.post(
                    'https://api.vk.ru/method/execute',
                    params={"code": code,
                            "access_token": TOKEN,
                            "v": 5.103},
                    timeout=60)

            if data["type"] == 'photo_update':
                photo = data['data']['photo'] # Закодированное в base64 изображение беседы
                # Получаем URL сервера для загрузки фото
                upload_url = requests.get(
                    "https://api.vk.ru/method/photos.getChatUploadServer",
                    params={"chat_id": chat,
                            "access_token": TOKEN,
                            "v": 5.103},
                    timeout=60).json()['response']['upload_url']
                with open("photo.png", "wb") as file:
                    file.write(base64.b64decode(photo)) # Декодируем base64 и создаём саму картинку
                    file.close()
                image = open("photo.png", "rb")
                # Загружаём её на сервер и берём строку для ответа в setChatPhoto
                f = requests.get(
                    upload_url,
                    files={
                        'file': ('photo.png', open("photo.png", 'rb'))
                        },
                    timeout=60).json()['response']
                requests.post(
                    "https://api.vk.ru/method/messages.setChatPhoto",
                    params={"file": f,
                            "access_token": TOKEN,
                            "v": 5.103},
                    timeout=60)
                image.close()
            return 'ok'
    except:
        return '0'

