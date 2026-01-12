import os

from flask import Flask, request, jsonify
import logging
import random

from data import db_session
from data.users import User

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

cities = {
    'москва': ['1540737/a62ee36775e27c6799da', '965417/06bdc2c6149e23ecd2a5'],
    'нью-йорк': ['997614/a18b39cfa414e165c455', '937455/2456bd2d018147db94a7'],
    'париж': ["213044/7290461a8c1ca2861261", '1540737/b378c4a14b72d76d49f3'],
    'дубай': ["1540737/71a6c3811fb318b2e5ae", "1030494/3a58216b39a3f11a4516"],
    'абу-даби': ["1030494/2ca0f9f8e2e336276324", "1030494/4b1404258e35b139e64a"],
    'стамбул': ["1030494/6b6ba1e574a721fead9e", "1540737/124718cf1b91f2e8cc38"],
    'бангкок': ["937455/6d90c00e0ce72349544f", "1030494/f430a08b0b39bd498e3e"],
    'доха': ["1540737/6cc63754c73e42a78c39", "213044/e58cb3d8c6a02ce64623"],
    'шарджа': ["213044/b15afb83aef8a0716108", "1540737/565614949d1f371902fd"],
    'тель-авив': ["213044/0a7bdbf4e31d7deb2025", "213044/239cc7b2a312276ae5ba"],
    'анталья': ["1540737/ac7e6b2c724f78019feb", "213044/4bcf0fccc6ffc0a7792f"],
    'дели': ["997614/86f63317023803224d98", "1030494/9e97350cd02fbb693691"],
    'каир': ["213044/aaf994fbdc78d05706fd", "1540737/2e8e8b525d5ca7e2b681"],
    'иерусалим': ["1540737/033a4f5183db9c3d5874", "1540737/00370b56d20c393ba492"],
    'пхукет': ["213044/dfc86ff219ad0184d804", "213044/4df42c10217a4bc832e7"],
    'паттайя': ["213044/fcaea52bfb1cf86e6db5", "1030494/10964c0a9181b8002c77"],
    'хургада': ["937455/ac4280dec0d2d978ad78", "937455/6f7161dd8bd30b6849c1"],
    'маскат': ["1030494/22306619c32e4c471d9c", "965417/ce6c78d90ffb51eba0e9"],
    'бали': ["1540737/187c98b52e4211e2b551", "1540737/7c25bbd6288d6de716eb"],
    'осака': ["997614/278d60ef5f5d473e05d3", "937455/738d415dd726623c76a9"],
    'сингапур': ["213044/955558c2546d7073e8e7", "1540737/f73f8c9c76e3873ae1d9"],
    'барселона': ["213044/a06700d430836bda8785", "997614/8eb13016b0a5567d11ba"],
    'пальма-де-мальорка': ["937455/c2d893080ad3a33e8851", "1030494/c284ce7de986bf3bb3b6"],
    'милан': ["997614/8a8c9d1bb3247f51f19a", "965417/7d279fed7f6446c25078"],
    'гонконг': ["213044/af071a0e13eb197c8d90", "213044/dda27ed2d593c074ff79"],
    'мекка': ["965417/080467612ba3a3fc730f", '997614/ac87c0a635fca7638af1'],
    'лондон': ["213044/73bff893d3a374d4df3e", "997614/7f7444d8a55c3af4f526"],
    'куала-лумпур': ["1030494/37de018776eaf3dbe5db", "1030494/a0bd6875d7f92711344a"],
    'токио': ["1540737/3ddeaccce89f45ce4f4e", "1540737/c598285752cf0b62496b"],
    'сеул': ["213044/6d8dbfbc88e846d2f575", "1540737/4eb4c1664ee12b356bd8"],
    'макао ': ["213044/c59f501c2bcf8b6905fb", "997614/aca40e321fe3224ab325"]
}

sessionStorage = {}
db_session.global_init("db/blogs.db")

db_sess = db_session.create_session()

user_name = ''


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return jsonify(response)


def handle_dialog(res, req):
    global user_name
    user_id = req['session']['user_id']
    if req['session']['new']:
        db_sess.query(User).filter(User.id >= 1).delete()
        db_sess.commit()
        res['response']['text'] = 'Привет! Назови своё имя!'
        sessionStorage[user_id] = {
            'first_name': None,  # здесь будет храниться имя
            'game_started': False  # здесь информация о том, что пользователь начал игру. По умолчанию False
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            user_name = first_name
            user = User()
            user.name = first_name
            user.score = 0
            db_sess.add(user)
            db_sess.commit()
            # создаём пустой массив, в который будем записывать города, которые пользователь уже отгадал
            sessionStorage[user_id]['guessed_cities'] = []
            # как видно из предыдущего навыка, сюда мы попали, потому что пользователь написал своем имя.
            # Предлагаем ему сыграть и два варианта ответа "Да" и "Нет".
            res['response']['text'] = f'Приятно познакомиться, {first_name.title()}. Я Алиса. Отгадаешь город по фото?'
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                }
            ]
    else:
        # У нас уже есть имя, и теперь мы ожидаем ответ на предложение сыграть.
        # В sessionStorage[user_id]['game_started'] хранится True или False в зависимости от того,
        # начал пользователь игру или нет.
        if not sessionStorage[user_id]['game_started']:
            # игра не начата, значит мы ожидаем ответ на предложение сыграть.
            if 'да' in req['request']['nlu']['tokens']:
                # если пользователь согласен, то проверяем не отгадал ли он уже все города.
                # По схеме можно увидеть, что здесь окажутся и пользователи, которые уже отгадывали города
                if len(sessionStorage[user_id]['guessed_cities']) == 30:
                    # если все три города отгаданы, то заканчиваем игру

                    res['response']['text'] = 'Ты отгадал все города!'
                    res['end_session'] = True
                else:
                    # если есть неотгаданные города, то продолжаем игру
                    sessionStorage[user_id]['game_started'] = True
                    # номер попытки, чтобы показывать фото по порядку
                    sessionStorage[user_id]['attempt'] = 1
                    # функция, которая выбирает город для игры и показывает фото
                    play_game(res, req)
            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Ну и ладно!'
                sessionStorage[user_id]['game_started'] = False
            else:
                res['response']['text'] = 'Не поняла. Да или нет?'
        else:
            play_game(res, req)


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']
    if attempt == 1:
        # если попытка первая, то случайным образом выбираем город для гадания
        city = random.choice(list(cities))
        # выбираем его до тех пор пока не выбираем город, которого нет в sessionStorage[user_id]['guessed_cities']
        while city in sessionStorage[user_id]['guessed_cities']:
            city = random.choice(list(cities))
        h = open('correct answer.txt', 'w', encoding='utf-8')
        h.write(city)
        h.close()
        # записываем город в информацию о пользователе
        sessionStorage[user_id]['city'] = city
        # добавляем в ответ картинку
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Что это за город?'
        res['response']['card']['image_id'] = cities[city][attempt - 1]
        res['response']['text'] = 'Тогда сыграем!'
    else:
        # сюда попадаем, если попытка отгадать не первая
        city = sessionStorage[user_id]['city']
        print(city)
        # проверяем есть ли правильный ответ в сообщение
        if req['request']['original_utterance'].lower() == city:
            # если да, то добавляем город к sessionStorage[user_id]['guessed_cities'] и
            # отправляем пользователя на второй круг. Обратите внимание на этот шаг на схеме.
            user = db_sess.query(User).filter(User.name == user_name).first()
            user.score += 1
            user_score = user.score
            db_sess.commit()
            res['response']['text'] = f'Правильно! Сыграем ещё?(вы угадали: {user_score}/30)'
            sessionStorage[user_id]['guessed_cities'].append(city)
            sessionStorage[user_id]['game_started'] = False
            return
        else:
            # если нет
            if attempt == 3:
                # если попытка третья, то значит, что все картинки мы показали.
                # В этом случае говорим ответ пользователю,
                # добавляем город к sessionStorage[user_id]['guessed_cities'] и отправляем его на второй круг.
                # Обратите внимание на этот шаг на схеме.
                res['response']['text'] = f'Вы пытались. Это {city.title()}. Сыграем ещё?'
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['guessed_cities'].append(city)
                return
            else:
                # иначе показываем следующую картинку
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = 'Неправильно. Вот тебе дополнительное фото'
                res['response']['card']['image_id'] = cities[city][attempt - 1]
                res['response']['text'] = 'А вот и не угадал!'
    # увеличиваем номер попытки доля следующего шага
    sessionStorage[user_id]['attempt'] += 1


def get_city(req):
    # перебираем именованные сущности
    for entity in req['request']['nlu']['entities']:
        # если тип YANDEX.GEO, то пытаемся получить город(city), если нет, то возвращаем None
        if entity['type'] == 'YANDEX.GEO':
            # возвращаем None, если не нашли сущности с типом YANDEX.GEO
            return entity['value'].get('city', None)


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name', то возвращаем её значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()
