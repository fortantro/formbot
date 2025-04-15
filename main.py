import telebot
import random
import telebot
import random
import time
import requests
import os
from telebot import types
import threading
from flask import Flask, request, jsonify
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация Flask и бота
app = Flask(__name__)
token = os.getenv('BOT_TOKEN')
logger.info(f"Используемый токен: {token[:10]}...")  # Логируем часть токена для проверки
bot = telebot.TeleBot(token)
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
logger.info(f"WEBHOOK_URL: {WEBHOOK_URL}")

logger.info("Инициализация бота завершена")
logger.info(f"Зарегистрированные обработчики: {bot.message_handlers}")

# Глобальные переменные (без изменений)
ADMINS = [716559083]
roles = {}
players = {}
dead_players_messages = {}
game_started = False
chat_id = None
roles_assigned = {}
votes = {}
voting_active = False
playersplay = {}
message_ids = {}
role_descriptions = {
    'Каринка': "Вы - мафия 🕵️‍♂️. Ваша цель - устранить мирных жителей.",
    'Селях': "Вы - комиссар 🔫. Вы можете проверять игроков на принадлежность к мафии, но сделать это можно только убив игрока.",
    'Саша Доктор': "Вы доктор 🩺. Можете спасать игроков от убийства.",
    'Радчик': "Вы - маньяк 🔪. Вы убиваете одного игрока каждую ночь. Ваша цель - убить всех.",
    'Мирный житель': "Вы - мирный житель 🏡. Ваша задача - выявить мафию и линчевать её на дневном собрании.",
    'Дытман': "Вы - путана 💃. Вы можете блокировать ход ночью любому игроку.",
    'Марина Виктория': "Вы - самоубийца 💔. Ваша задача - умереть на дневном собрании.",
    'Матвей': "Вы - бомж 🧳. Вы можете ходить к другим игрокам и становиться свидетелем преступлений.",
    'Лилия Федоровна': "Вы - шизик 🤪. Ваш голос на дневном голосовании удваивается.",
    'Юлия Сергеевна': "Вы - волк 🐺. Изначально вы мирный житель, но как только мафия умрёт, вы займёте их место.",
    'Шпион': "Вы - шпион 🕶️. Работаете на мафию. Каждую ночь вы можете выбрать игрока и узнать его роль. Эта информация будет отправлена вам и мафии утром.",
    'Павлуша': "Вы - хакер 💾. Ваша цель - выжить до конца игры. Каждую ночь вы можете выбрать игрока и заблокировать его роль, чтобы он не смог использовать свою способность."
}

role_tips = {
    'Каринка': (
        "🔹 Старайтесь не выдавать себя днём\n"
        "🔹 Договоритесь со шпионом для координации\n"
        "🔹 Убивайте самых опасных для вас ролей (комиссара, доктора)"
    ),
    'Селях': (
        "🔹 Проверяйте подозрительных игроков\n"
        "🔹 Не раскрывайте свою роль без необходимости\n"
        "🔹 Доктор может вас защитить - попробуйте договориться"
    ),
    'Саша Доктор': (
        "🔹 Защищайте самых важных игроков (комиссара, себя)\n"
        "🔹 Меняйте тактику защиты, чтобы мафия не угадала\n"
        "🔹 Не раскрывайте, кого защитили"
    ),
    'Радчик': (
        "🔹 Убивайте игроков, которые могут вас вычислить\n"
        "🔹 Маскируйтесь под мирного жителя\n"
        "🔹 Помните - вы играете против всех, даже против мафии"
    ),
    'Мирный житель': (
        "🔹 Внимательно анализируйте поведение других\n"
        "🔹 Не доверяйте слепо обвинениям\n"
        "🔹 Ищите противоречия в словах игроков"
    ),
    'Дытман': (
        "🔹 Блокируйте самых активных игроков\n"
        "🔹 Меняйте цели, чтобы не было очевидно\n"
        "🔹 Можно блокировать одного и того же игрока несколько ночей подряд"
    ),
    'Марина Виктория': (
        "🔹 Старайтесь быть изгнанной днём\n"
        "🔹 Выбирайте для мести самых опасных игроков\n"
        "🔹 Можно имитировать поведение мафии, чтобы вас изгнали"
    ),
    'Матвей': (
        "🔹 Посещайте разных игроков для сбора информации\n"
        "🔹 Ваши показания могут быть решающими днём\n"
        "🔹 Не раскрывайте сразу, что вы узнали"
    ),
    'Лилия Федоровна': (
        "🔹 Ваш голос весит больше - используйте это\n"
        "🔹 Можете влиять на исход голосований\n"
        "🔹 Не афишируйте свою роль без необходимости"
    ),
    'Юлия Сергеевна': (
        "🔹 Ведите себя как мирный житель, пока мафия жива\n"
        "🔹 Готовьтесь заменить мафию, когда она будет уничтожена\n"
        "🔹 Анализируйте, кто может быть мафией"
    ),
    'Шпион': (
        "🔹 Делитесь информацией с мафией\n"
        "🔹 Проверяйте самых подозрительных игроков\n"
        "🔹 Маскируйтесь под мирного жителя"
    ),
    'Павлуша': (
        "🔹 Блокируйте самые опасные роли (мафию, комиссара, доктора)\n"
        "🔹 Старайтесь остаться незамеченным\n"
        "🔹 Ваша цель - выжить любой ценой"
    )
}
NIGHT_DURATION = 60
DAY_DURATION = 80
PERERIV_DURATION = 40

# Флаги для отслеживания состояния игры
is_night = False
mafia_choice = None
commissar_choice = None
maniac_choice = None
hobo_choice = None
doctor_choice = None
lover_choice = None
spy_choice = None
hacker_choice = None
voting_in_progress = False
reg_id = None
message_text = None
reg_message = None
keyboardd = None
join_buttonn = None

# Установка вебхука
def set_webhook():
    try:
        logger.info("Проверка токена бота")
        bot_info = bot.get_me()
        logger.info(f"Бот активен: @{bot_info.username}")
        logger.info("Удаление старого вебхука")
        bot.remove_webhook()
        time.sleep(1)
        if not WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL не установлен")
        logger.info(f"Установка вебхука: {WEBHOOK_URL}")
        success = bot.set_webhook(
            url=WEBHOOK_URL,
            max_connections=40,
            allowed_updates=["message", "callback_query"]
        )
        if success:
            logger.info(f"Вебхук успешно установлен: {WEBHOOK_URL}")
        else:
            logger.error("Не удалось установить вебхук")
        webhook_info = bot.get_webhook_info()
        logger.info(f"Статус вебхука: {webhook_info}")
    except Exception as e:
        logger.error(f"Ошибка при установке вебхука: {str(e)}")

# Остальная логика бота (без изменений)
def retry_on_connection_error(max_retries=5, delay=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.ConnectionError as e:
                    print(f"Ошибка соединения: {e}. Попытка {attempt + 1} из {max_retries}.")
                    time.sleep(delay)
                except Exception as e:
                    print(f"Произошла ошибка: {e}")
                    break
        return wrapper
    return decorator

@bot.message_handler(commands=['secretqward'])
def secret_admin_panel(message):
    if message.from_user.id not in ADMINS:
        bot.send_message(message.chat.id, "❌ Доступ запрещен!")
        return
    
    keyboard = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("👥 Показать игроков и роли", callback_data="admin_show")
    btn2 = types.InlineKeyboardButton("📊 Статистика игры", callback_data="admin_stats")
    keyboard.add(btn1, btn2)
    
    bot.send_message(message.chat.id, 
                    "🔐 <b>Минималистичная админ-панель</b>\n"
                    "Выберите действие:",
                    reply_markup=keyboard, 
                    parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data in ["admin_show", "admin_stats"])
def handle_admin_actions(call):
    if call.from_user.id not in ADMINS:
        bot.answer_callback_query(call.id, "❌ Доступ запрещен!")
        return
    
    if call.data == "admin_show":
        try:
            # Формируем список всех игроков
            players_info = "<b>👥 Список всех игроков:</b>\n\n"
            
            # Сначала живые игроки
            alive_players = []
            for player_id, player_name in players.items():
                if player_id in roles_assigned:  # Игрок жив
                    role = roles_assigned.get(player_id, "Роль не назначена")
                    alive_players.append(f"🟢 {player_name}: <b>{role}</b>")
            
            # Затем мертвые игроки (есть в playersplay, но нет в roles_assigned)
            dead_players = []
            for player_id, player_name in playersplay.items():
                if player_id not in roles_assigned and player_id in players:
                    dead_players.append(f"🔴 {player_name}: <i>убит</i>")
            
            # Собираем полное сообщение
            if alive_players:
                players_info += "<b>Живые:</b>\n" + "\n".join(alive_players) + "\n\n"
            if dead_players:
                players_info += "<b>Мертвые:</b>\n" + "\n".join(dead_players)
            
            if not alive_players and not dead_players:
                players_info = "❌ Нет данных об игроках"
            
            bot.send_message(call.from_user.id, players_info, parse_mode="HTML")
            bot.answer_callback_query(call.id, "Данные отправлены в ЛС!")
            
        except Exception as e:
            print(f"Ошибка в admin_show: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка при получении данных!")
    
    elif call.data == "admin_stats":
        try:
            # Считаем статистику
            total_players = len(playersplay)
            alive_count = len(roles_assigned)
            dead_count = total_players - alive_count
            
            mafia_alive = any(role == 'Каринка' for role in roles_assigned.values())
            commissar_alive = any(role == 'Селях' for role in roles_assigned.values())
            doctor_alive = any(role == 'Саша Доктор' for role in roles_assigned.values())
            
            stats = f"""
📊 <b>Статистика игры:</b>

👥 Игроков всего: {total_players}
🟢 Живых: {alive_count}
🔴 Мертвых: {dead_count}
🌃 Текущая фаза: {'Ночь' if is_night else 'День'}

<b>Ключевые роли:</b>
🕵️‍♂️ Мафия: {'жива' if mafia_alive else 'мертва'}
🔫 Комиссар: {'жив' if commissar_alive else 'мертв'}
🩺 Доктор: {'жив' if doctor_alive else 'мертв'}
"""
            bot.send_message(call.from_user.id, stats, parse_mode="HTML")
            bot.answer_callback_query(call.id, "Статистика отправлена!")
            
        except Exception as e:
            print(f"Ошибка в admin_stats: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка при получении статистики!")



def retry_on_connection_error(max_retries=5, delay=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.ConnectionError as e:
                    print(f"Ошибка соединения: {e}. Попытка {attempt + 1} из {max_retries}.")
                    time.sleep(delay)
                except Exception as e:
                    print(f"Произошла ошибка: {e}")
                    break
        return wrapper
    return decorator

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "<b>Привет✌️, это бот для игры в мафию!</b>\n<i>Напиши /join, чтобы присоединиться.</i>", parse_mode='html')

@bot.message_handler(commands=['mstart'])
def start_registration(message):
    global game_started, chat_id, reg_id, reg_message, registration_message, keyboardd, join_buttonn
    if game_started:
        bot.send_message(message.chat.id, "<b>❌ Игра уже началась!</b>", parse_mode='html')
        return
    
    chat_id = message.chat.id
    
    registration_message = "<b>📋 Регистрация на игру в мафию начата!</b>\n\n"
    
    if players:
        registration_message += "\n".join(players.values())
    else:
        registration_message += "<i>Пока нет зарегистрированных игроков.</i>"
    
    join_buttonn = types.InlineKeyboardButton(text="Присоединиться", url=f"https://t.me/{bot.get_me().username}?start=join", callback_data="join_game")
    keyboardd = types.InlineKeyboardMarkup().add(join_buttonn)
    
    reg_message = bot.send_message(chat_id, registration_message, reply_markup=keyboardd, parse_mode='html')
    reg_id = reg_message.message_id
    
    chat_id = message.chat.id

@bot.message_handler(commands=['join'])
def join_game(message):
    if game_started:
        bot.send_message(message.chat.id, "<b>❌ Игра уже идёт!</b>\n<i>Дождитесь её окончания.</i>", parse_mode='html')
        return
    if message.from_user.id in players:
        print(f"Игрок {message.from_user.username} пытается присоединиться.")
        bot.send_message(message.chat.id, "<b>❌ Вы уже в игре!</b>", parse_mode='html')
        return
    
    players[message.from_user.id] = message.from_user.first_name
    playersplay[message.from_user.id] = message.from_user.first_name
    print(f"Игрок {message.from_user.username} добавлен в игру.")
    bot.send_message(chat_id, f"<b>👤 {message.from_user.first_name}, вы присоединились к игре!</b>", parse_mode='html')
    update_registered_users_message()

@bot.message_handler(commands=['start_game'])
def start_game(message):
    global game_started, playersplay
    if game_started:
        bot.send_message(chat_id, "<b>❌ Игра уже началась!</b>", parse_mode='html')
        return
    
    if len(players) < 4:
        bot.send_message(chat_id, "<b>❌ Нужно минимум 4 игрока!</b>", parse_mode='html')
        return

    game_started = True
    print(playersplay)
    assign_roles()
    start_night()

@bot.message_handler(func=lambda message: True)
@retry_on_connection_error()
def handle_messages(message):
    global chat_id, dead_players_messages
    user_id = message.from_user.id
    print("Тут пока еще работает")
    if game_started:
        if is_night:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(message.from_user.id, "<b>🌙 Ночь!</b>\n<i>Вы не можете писать в чат во время ночи.</i>", parse_mode='html')
            except Exception as e:
                print(f"Ошибка при удалении сообщения: {e}")
        if user_id in playersplay and user_id not in players:
            print("здесь кстати тоже работает")
            if user_id not in dead_players_messages:
                print("вот тут нихуя не работает")
                dead_players_messages[user_id] = message.text
                bot.send_message(chat_id, f"<b>💀 Кто-то слышал, как {message.from_user.first_name} кричал:</b>\n<i>{message.text}</i>", parse_mode='html')
            else:
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                except Exception as e:
                    print(f"Ошибка при удалении сообщения: {e}")

@retry_on_connection_error()
def assign_roles():
    global roles_assigned
    roles_assigned = {}
    num_players = len(players)
    
    if num_players == 4:
        roles = ['Каринка', 'Саша Доктор', 'Селях'] + ['Мирный житель']
    if num_players == 5:
        roles = ['Каринка', 'Саша Доктор', 'Селях'] + ['Мирный житель'] + ['Дытман']
    elif num_players == 6:
        roles = ['Каринка', 'Саша Доктор', 'Селях'] + ['Мирный житель'] + ['Дытман'] + ['Радчик']
    elif num_players == 7:
        roles = ['Каринка', 'Саша Доктор', 'Селях'] + ['Мирный житель'] + ['Дытман'] + ['Радчик'] + ['Шпион']
    elif num_players == 8:
        roles = ['Каринка', 'Саша Доктор', 'Селях'] + ['Мирный житель'] + ['Дытман'] + ['Радчик'] + ['Шпион'] + ['Матвей']
    elif num_players == 9:
        roles = ['Каринка', 'Саша Доктор', 'Селях'] + ['Мирный житель'] + ['Дытман'] + ['Радчик'] + ['Шпион'] + ['Матвей'] + ['Лилия Федоровна']
    elif num_players == 10:
        roles = ['Каринка', 'Саша Доктор', 'Селях'] + ['Мирный житель'] + ['Дытман'] + ['Радчик'] + ['Шпион'] + ['Матвей'] + ['Лилия Федоровна'] + ['Юлия Сергеевна']
    elif num_players == 11:
        roles = ['Каринка', 'Саша Доктор', 'Селях'] + ['Мирный житель'] + ['Дытман'] + ['Радчик'] + ['Шпион'] + ['Матвей'] + ['Лилия Федоровна'] + ['Юлия Сергеевна'] + ['Марина Виктория']
    elif num_players == 12:
        roles = ['Каринка', 'Саша Доктор', 'Селях'] + ['Мирный житель'] + ['Дытман'] + ['Радчик'] + ['Шпион'] + ['Матвей'] + ['Лилия Федоровна'] + ['Юлия Сергеевна'] + ['Марина Виктория'] + ['Павлуша']
    elif num_players == 13:
        roles = ['Каринка', 'Саша Доктор', 'Селях'] + ['Мирный житель'] * 2 + ['Дытман'] + ['Радчик'] + ['Шпион'] + ['Матвей'] + ['Лилия Федоровна'] + ['Юлия Сергеевна'] + ['Марина Виктория'] + ['Павлуша'] 
    elif num_players == 14:
        roles = ['Каринка', 'Саша Доктор', 'Селях'] + ['Мирный житель'] * 3 + ['Дытман'] + ['Радчик'] + ['Шпион'] + ['Матвей'] + ['Лилия Федоровна'] + ['Юлия Сергеевна'] + ['Марина Виктория'] + ['Павлуша'] 
    elif num_players == 15:
        roles = ['Каринка', 'Саша Доктор', 'Селях'] + ['Мирный житель'] * 4 + ['Дытман'] + ['Радчик'] + ['Шпион'] + ['Матвей'] + ['Лилия Федоровна'] + ['Юлия Сергеевна'] + ['Марина Виктория'] + ['Павлуша']
    elif num_players == 16:
        roles = ['Каринка', 'Саша Доктор', 'Селях'] + ['Мирный житель'] * 5 + ['Дытман'] + ['Радчик'] + ['Шпион'] + ['Матвей'] + ['Лилия Федоровна'] + ['Юлия Сергеевна'] + ['Марина Виктория'] + ['Павлуша']  
    
    random.shuffle(roles)
    
    for player_id, role in zip(players.keys(), roles):
        roles_assigned[player_id] = role
        
        # Формируем сообщение без лишних переносов строк
        message = (
            f"<b>🎭 Ваша роль: {role}</b>\n"
            f"{role_descriptions[role]}\n\n"
            f"<b>💡 Советы по игре:</b>\n" + 
            ''.join(role_tips[role])  # Объединяем советы через \n
        )
            
        # Отправляем одним сообщением
        bot.send_message(player_id, message, parse_mode='HTML')

    mafia_id = None
    spy_id = None
    for player_id in players.keys():
        if roles_assigned[player_id] == 'Каринка':
            mafia_id = player_id
        elif roles_assigned[player_id] == 'Шпион':
            spy_id = player_id

    if mafia_id and spy_id:
        mafia_name = players[mafia_id]
        spy_name = players[spy_id]
        bot.send_message(mafia_id, f"<b>🕶️ Ваш шпион: {spy_name}</b>", parse_mode='html')
        bot.send_message(spy_id, f"<b>🕵️‍♂️ Ваша мафия: {mafia_name}</b>", parse_mode='html')

    bot.send_message(chat_id, "<b>🎲 Игра началась! Роли розданы, проверьте личные сообщения!</b>", parse_mode='html')

@retry_on_connection_error()
def start_night():
    global is_night, mafia_choice, doctor_choice, mafia_id, commissar_id, commissar_choice, doctor_id, killed_player_name, maniac_id, maniac_choice, lover_id, lover_choice, hobo_id, hobo_choice, spy_choice, spy_id, hacker_id, hacker_choice
    if not game_started:
        return
    is_night = True
    mafia_choice = None
    commissar_choice = None
    lover_choice = None
    doctor_choice = None
    maniac_choice = None
    hobo_choice = None
    spy_choice = None
    hacker_choice = None
    join_button = types.InlineKeyboardButton(text="Перейти к боту", url=f"https://t.me/{bot.get_me().username}")
    keyboard = types.InlineKeyboardMarkup().add(join_button)
    bot.send_message(chat_id, "<b>🌙 Ночь окутала город!</b>\n<i>Самые смелые и опасные вышли на улицы. Утром узнаем, кто выжил...</i>", reply_markup=keyboard, parse_mode="html")
    
    mafia_id = get_mafia_id()
    if mafia_id:
        create_mafia_keyboard(mafia_id)

    threading.Timer(NIGHT_DURATION, end_night).start()

    commissar_id = get_commissar_id()
    if commissar_id:
        create_commissar_keyboard(commissar_id)

    doctor_id = get_doctor_id()
    if doctor_id:
        create_doctor_keyboard(doctor_id)

    if len(playersplay) >= 5:
        lover_id = get_lover_id()
        if lover_id:
            create_lover_keyboard(lover_id)

    if len(playersplay) >= 6:
        maniac_id = get_maniac_id()
        if maniac_id:
            create_maniac_keyboard(maniac_id)

    if len(playersplay) >= 8:
        hobo_id = get_hobo_id()
        if hobo_id:
            create_hobo_keyboard(hobo_id)

    if len(playersplay) >= 7:
        spy_id = get_spy_id()
        if spy_id:
            create_spy_keyboard(spy_id)

    if len(playersplay) >= 12:
        hacker_id = get_hacker_id()
        if hacker_id:
            create_hacker_keyboard(hacker_id)

@retry_on_connection_error()
def create_mafia_keyboard(mafia_id):
    global vibor
    keyboard = types.InlineKeyboardMarkup()
    for player_id in players.keys():
        if player_id != mafia_id and roles_assigned[player_id] != 'Шпион':
            button = types.InlineKeyboardButton(text=players[player_id], callback_data=f'kill_{player_id}')
            keyboard.add(button)
    vibor = bot.send_message(mafia_id, "<b>🕵️‍♂️ Мафия, выберите жертву этой ночи:</b>", reply_markup=keyboard, parse_mode='html')
    return vibor.message_id

@retry_on_connection_error()
def create_commissar_keyboard(commissar_id):
    global viborkom
    keyboard = types.InlineKeyboardMarkup()
    for player_id in players.keys():
        if player_id != commissar_id:
            button = types.InlineKeyboardButton(text=players[player_id], callback_data=f'check_{player_id}')
            keyboard.add(button)
    viborkom = bot.send_message(commissar_id, "<b>🔫 Комиссар, выберите игрока для проверки:</b>", reply_markup=keyboard, parse_mode='html')
    return viborkom.message_id

@retry_on_connection_error()
def create_doctor_keyboard(doctor_id):
    global vibordok
    keyboard = types.InlineKeyboardMarkup()
    for player_id in players.keys():
        if player_id != doctor_id:
            button = types.InlineKeyboardButton(text=players[player_id], callback_data=f'heal_{player_id}')
            keyboard.add(button)
    vibordok = bot.send_message(doctor_id, "<b>🩺 Доктор, выберите, кого спасти этой ночью:</b>", reply_markup=keyboard, parse_mode='html')
    return vibordok.message_id

@retry_on_connection_error()
def create_maniac_keyboard(maniac_id):
    global vibormaniac
    keyboard = types.InlineKeyboardMarkup()
    for player_id in players.keys():
        if player_id != maniac_id:
            button = types.InlineKeyboardButton(text=players[player_id], callback_data=f'mankill_{player_id}')
            keyboard.add(button)
    vibormaniac = bot.send_message(maniac_id, "<b>🔪 Маньяк, выберите жертву этой ночи:</b>", reply_markup=keyboard, parse_mode='html')
    return vibormaniac.message_id

@retry_on_connection_error()
def create_lover_keyboard(lover_id):
    global viborlover
    keyboard = types.InlineKeyboardMarkup()
    for player_id in players.keys():
        if player_id != lover_id:
            button = types.InlineKeyboardButton(text=players[player_id], callback_data=f'lovercome_{player_id}')
            keyboard.add(button)
    viborlover = bot.send_message(lover_id, "<b>💃 Путана, выберите, к кому пойти этой ночью:</b>", reply_markup=keyboard, parse_mode='html')
    return viborlover.message_id

@retry_on_connection_error()
def create_hobo_keyboard(hobo_id):
    global viborhobo
    keyboard = types.InlineKeyboardMarkup()
    for player_id in players.keys():
        if player_id != hobo_id:
            button = types.InlineKeyboardButton(text=players[player_id], callback_data=f'hobocome_{player_id}')
            keyboard.add(button)
    viborhobo = bot.send_message(hobo_id, "<b>🧳 Бомж, выберите, к кому пойти этой ночью:</b>", reply_markup=keyboard, parse_mode='html')
    return viborhobo.message_id

@retry_on_connection_error()
def create_spy_keyboard(spy_id):
    global viborspy
    keyboard = types.InlineKeyboardMarkup()
    for player_id in players.keys():
        if player_id != spy_id and roles_assigned[player_id] != 'Каринка':
            button = types.InlineKeyboardButton(text=players[player_id], callback_data=f'spycheck_{player_id}')
            keyboard.add(button)
    viborspy = bot.send_message(spy_id, "<b>🕶️ Шпион, выберите игрока для проверки роли:</b>", reply_markup=keyboard, parse_mode='html')
    return viborspy.message_id

@retry_on_connection_error()
def create_hacker_keyboard(hacker_id):
    global viborhacker
    keyboard = types.InlineKeyboardMarkup()
    for player_id in players.keys():
        if player_id != hacker_id:
            button = types.InlineKeyboardButton(text=players[player_id], callback_data=f'hack_{player_id}')
            keyboard.add(button)
    viborhacker = bot.send_message(hacker_id, "<b>💾 Павлуша, выберите игрока, чтобы заблокировать его роль:</b>", reply_markup=keyboard, parse_mode='html')
    return viborhacker.message_id

@retry_on_connection_error()
def start_voting():
    global voting_active, votes, message_ids
    if not game_started:
        return
    voting_active = True
    votes.clear()
    print("Голосование началось")
    print("Начинаем голосование. Идентификаторы игроков:", players.keys())
    join_button = types.InlineKeyboardButton(text="Перейти к боту", url=f"https://t.me/{bot.get_me().username}")
    keyboard = types.InlineKeyboardMarkup().add(join_button)
    bot.send_message(chat_id, "<b>🗳️ Голосование началось!</b>\n<i>Проверьте личные сообщения и выберите, кого линчевать.</i>", reply_markup=keyboard, parse_mode='html')

    keyboard = types.InlineKeyboardMarkup()
    for player_id in players.keys():
        button = types.InlineKeyboardButton(text=players[player_id], callback_data=f'vote_{player_id}')
        keyboard.add(button)

    for player_id in players.keys():
        try:
            message = bot.send_message(player_id, "<b>🗳️ Голосование!</b>\n<i>Выберите игрока для изгнания:</i>", reply_markup=keyboard, parse_mode='html')
            message_ids[player_id] = message.message_id
            print(f"Сообщение отправлено игроку {player_id}")
        except Exception as e:
            print(f"Ошибка при отправке сообщения игроку {player_id}: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('vote_'))
def handle_vote(call):
    global votes, message_ids
    if voting_active:
        voted_player_id = int(call.data.split('_')[1])
        votes[call.from_user.id] = voted_player_id
        bot.delete_message(call.from_user.id, message_ids[call.from_user.id])
        bot.send_message(call.from_user.id, "<b>🗳️ Ваш голос учтён!</b>", parse_mode='html')
        
        # Оповещаем чат, что игрок проголосовал (без указания за кого)
        voter_name = players.get(call.from_user.id, "Неизвестный игрок")
        bot.send_message(chat_id, f"<b>🗳️ {voter_name} проголосовал(а)!</b>", parse_mode='html')

@retry_on_connection_error()
def end_voting():
    global voting_active
    voting_active = False

    # Удаляем сообщения для игроков, которые не проголосовали
    for player_id in players.keys():
        if player_id not in votes and player_id in message_ids:
            try:
                bot.delete_message(player_id, message_ids[player_id])
                print(f"Сообщение о голосовании удалено для игрока {player_id}")
            except Exception as e:
                print(f"Ошибка при удалении сообщения для игрока {player_id}: {e}")

    vote_count = {}
    for player_id, vote in votes.items():
        if get_user_role(player_id) == 'Лилия Федоровна':
            vote_count[vote] = vote_count.get(vote, 0) + 2
        else:
            vote_count[vote] = vote_count.get(vote, 0) + 1

    if vote_count:
        max_votes = max(vote_count.values())
        players_with_max_votes = [player_id for player_id, count in vote_count.items() if count == max_votes]

        if len(players_with_max_votes) > 1:
            bot.send_message(chat_id, "<b>🗳️ Голосование завершилось вничью!</b>\n<i>Никто не был изгнан.</i>", parse_mode='html')
        else:
            max_votes_player = players_with_max_votes[0]
            max_votes_player_role = get_user_role(max_votes_player)
            
            # Обработка особого случая для Марины Виктории
            if max_votes_player_role == 'Марина Виктория':
                bot.send_message(chat_id, 
                               f"<b>💔 {players[max_votes_player]} (Марина Виктория) была казнена!</b>\n"
                               "<i>Она может выбрать одного игрока, который умрёт вместе с ней...</i>", 
                               parse_mode='html')
                
                # Создаем клавиатуру для выбора жертвы мести
                keyboard = types.InlineKeyboardMarkup()
                for player_id, player_name in players.items():
                    if player_id != max_votes_player:  # Не может выбрать себя
                        keyboard.add(types.InlineKeyboardButton(
                            player_name, 
                            callback_data=f'revenge_{player_id}'))
                
                # Сохраняем ID казненной любовницы
                global revenge_victim
                revenge_victim = max_votes_player
                
                bot.send_message(max_votes_player, 
                               "<b>💔 Выберите игрока, который умрёт вместе с вами:</b>", parse_mode='html',
                               reply_markup=keyboard)
            else:
                # Обычный случай казни
                bot.send_message(chat_id, 
                               f"<b>🗳️ Игрок {players[max_votes_player]} был изгнан!</b>\n"
                               f"<i>Его роль: {max_votes_player_role}</i>", 
                               parse_mode='html')
                remove_player(max_votes_player)
    else:
        bot.send_message(chat_id, "<b>🗳️ Голосование завершилось без результатов.</b>\n<i>Никто не проголосовал.</i>", parse_mode='html')


@bot.callback_query_handler(func=lambda call: call.data.startswith('revenge_'))
def handle_revenge(call):
    global revenge_victim
    player_id_to_kill = int(call.data.split('_')[1])
    
    # Удаляем любовницу
    bot.send_message(chat_id, 
                   f"💔 {players[revenge_victim]} (Марина Виктория) забрала с собой {players[player_id_to_kill]}!",
                   parse_mode="HTML")
    
    # Удаляем обоих игроков
    remove_player(revenge_victim)
    remove_player(player_id_to_kill)
    
    # Удаляем сообщение с кнопками
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "Мщение совершено!")

def get_mafia_id():
    for player_id in players.keys():
        if roles_assigned[player_id] == 'Каринка':
            return player_id
    return None

def get_maniac_id():
    for player_id in players.keys():
        if roles_assigned[player_id] == 'Радчик':
            return player_id
    return None

def get_commissar_id():
    for player_id in players.keys():
        if roles_assigned[player_id] == "Селях":
            print(f"Found commissar ID: {player_id}")
            return player_id
    return None

def get_doctor_id():
    for player_id in players.keys():
        if roles_assigned[player_id] == "Саша Доктор":
            print(f"Found doctor ID: {player_id}")
            return player_id
    return None

def get_lover_id():
    for player_id in players.keys():
        if roles_assigned[player_id] == "Дытман":
            print(f"Found lover ID: {player_id}")
            return player_id
    return None

def get_hobo_id():
    for player_id in players.keys():
        if roles_assigned[player_id] == "Матвей":
            return player_id
    return None

def get_spy_id():
    for player_id in players.keys():
        if roles_assigned[player_id] == 'Шпион':
            return player_id
    return None

def get_hacker_id():
    for player_id in players.keys():
        if roles_assigned[player_id] == 'Павлуша':
            return player_id
    return None

def get_user_role(user_id):
    return roles_assigned.get(user_id)

def get_alive_players():
    alive_players = [username for player_id, username in players.items() if player_id in roles_assigned]
    return alive_players

def get_mafia_nick():
    for player_id in players:
        if get_user_role(player_id) == 'Каринка':
            return players[player_id]
    return None

def get_commissar_nick():
    for player_id in players:
        if get_user_role(player_id) == 'Селях':
            return players[player_id]
    return None

def get_maniac_nick():
    for player_id in players:
        if get_user_role(player_id) == 'Радчик':
            return players[player_id]
    return None

@retry_on_connection_error()
def update_registered_users_message():
    global players, message_text
    players_list = "\n".join(players.values())
    message_text = f"<b>📋 Зарегистрированные игроки:</b>\n\n{players_list}"
    bot.edit_message_text(chat_id=chat_id, message_id=reg_id, text="<b>📋 Регистрация на игру в мафию начата!</b>\n\n" + message_text, reply_markup=keyboardd, parse_mode='html')

@bot.callback_query_handler(func=lambda call: call.data == "join_game")
def handle_join_game(call):
    user_id = call.from_user.id
    username = call.from_user.username or "Неизвестный"
    
    players[user_id] = username
    bot.send_message(user_id, "<b>👤 Вы присоединились к игре!</b>\n<i>Введите /join для регистрации.</i>", parse_mode='html')

@bot.callback_query_handler(func=lambda call: True)
@retry_on_connection_error()
def handle_callback_query(call):
    global mafia_choice, commissar_id, commissar_choice, doctor_choice, killed_player_name, votes, message_ids, maniac_choice, vibormaniac, lover_choice, lover_id, hobo_choice, spy_choice, hacker_choice
    
    if is_night and call.from_user.id in players:
        user_role = get_user_role(call.from_user.id)
        
        if user_role == 'Каринка':
            mafia_choice = call.data.split('_')[1]
            if int(mafia_choice) in players:
                bot.delete_message(call.from_user.id, vibor.message_id)
                bot.send_message(mafia_id, "<b>🕵️‍♂️ Выбор сделан!</b>\n<i>Ожидайте начала дня.</i>", parse_mode='html')
            else:
                bot.send_message(call.from_user.id, "<b>❌ Ошибка!</b>\n<i>Выбранный игрок не найден.</i>", parse_mode='html')
                
        elif user_role == 'Селях':
            commissar_choice = call.data.split('_')[1]
            if int(commissar_choice) in players:
                bot.delete_message(call.from_user.id, viborkom.message_id)
                bot.send_message(commissar_id, "<b>🔫 Выбор сделан!</b>\n<i>Ожидайте начала дня.</i>", parse_mode='html')
            else:
                bot.send_message(call.from_user.id, "<b>❌ Ошибка!</b>\n<i>Выбранный игрок не найден.</i>", parse_mode='html')

        elif user_role == 'Саша Доктор':
            doctor_choice = call.data.split('_')[1]
            if int(doctor_choice) in players:
                bot.delete_message(call.from_user.id, vibordok.message_id)
                bot.send_message(call.from_user.id, "<b>🩺 Выбор сделан!</b>\n<i>Ожидайте начала дня.</i>", parse_mode='html')
            else:
                bot.send_message(call.from_user.id, "<b>❌ Ошибка!</b>\n<i>Выбранный игрок не найден.</i>", parse_mode='html')

        elif user_role == 'Дытман' and len(playersplay) >= 5:
            lover_choice = call.data.split('_')[1]
            if int(lover_choice) in players:
                bot.delete_message(call.from_user.id, viborlover.message_id)
                bot.send_message(call.from_user.id, "<b>💃 Выбор сделан!</b>\n<i>Ожидайте начала дня.</i>", parse_mode='html')
            else:
                bot.send_message(call.from_user.id, "<b>❌ Ошибка!</b>\n<i>Выбранный игрок не найден.</i>", parse_mode='html')

        elif user_role == 'Радчик' and len(playersplay) >= 6:
            maniac_choice = call.data.split('_')[1]
            if int(maniac_choice) in players:
                bot.delete_message(call.from_user.id, vibormaniac.message_id)
                bot.send_message(call.from_user.id, "<b>🔪 Выбор сделан!</b>\n<i>Ожидайте начала дня.</i>", parse_mode='html')
            else:
                bot.send_message(call.from_user.id, "<b>❌ Ошибка!</b>\n<i>Выбранный игрок не найден.</i>", parse_mode='html')

        elif user_role == 'Матвей' and len(playersplay) >= 8:
            hobo_choice = call.data.split('_')[1]
            if int(hobo_choice) in players:
                bot.delete_message(call.from_user.id, viborhobo.message_id)
                bot.send_message(call.from_user.id, "<b>🧳 Выбор сделан!</b>\n<i>Ожидайте начала дня.</i>", parse_mode='html')
            else:
                bot.send_message(call.from_user.id, "<b>❌ Ошибка!</b>\n<i>Выбранный игрок не найден.</i>", parse_mode='html')

        elif user_role == 'Шпион' and len(playersplay) >= 7:
            spy_choice = call.data.split('_')[1]
            if int(spy_choice) in players:
                bot.delete_message(call.from_user.id, viborspy.message_id)
                bot.send_message(call.from_user.id, "<b>🕶️ Выбор сделан!</b>\n<i>Ожидайте начала дня.</i>", parse_mode='html')
            else:
                bot.send_message(call.from_user.id, "<b>❌ Ошибка!</b>\n<i>Выбранный игрок не найден.</i>", parse_mode='html')

        elif user_role == 'Павлуша' and len(playersplay) >= 12:
            hacker_choice = call.data.split('_')[1]
            if int(hacker_choice) in players:
                bot.delete_message(call.from_user.id, viborhacker.message_id)
                bot.send_message(call.from_user.id, "<b>💾 Выбор сделан!</b>\n<i>Ожидайте начала дня.</i>", parse_mode='html')
            else:
                bot.send_message(call.from_user.id, "<b>❌ Ошибка!</b>\n<i>Выбранный игрок не найден.</i>", parse_mode='html')
        
    if voting_active and call.data.startswith('vote_'):
        voted_player_id = int(call.data.split('_')[1])
        votes[call.from_user.id] = voted_player_id
        bot.delete_message(call.from_user.id, message_ids[call.from_user.id])
        bot.send_message(call.from_user.id, "<b>🗳️ Ваш голос учтён!</b>", parse_mode='html')

@retry_on_connection_error()
def remove_player(player_id):
    if player_id in players:
        del players[player_id]
        del roles_assigned[player_id]

@retry_on_connection_error()
def check_game_status():
    alive_players = get_alive_players()
    mafia_alive = any(get_user_role(player_id) == 'Каринка' for player_id in players)

    
    if mafia_alive and len(alive_players) > 2:
        return
    else:
        if len(alive_players) == 1:
            bot.send_message(chat_id, "<b>🏆 Мирные жители победили!</b>\n<i>Мафия была уничтожена!</i>", parse_mode='html')
            reset_game()
        elif len(alive_players) == 2:
            if mafia_alive:
                bot.send_message(chat_id, "<b>🏆 Мафия победила!</b>\n<i>Остались только мафия и мирный житель.</i>", parse_mode='html')
            else:
                bot.send_message(chat_id, "<b>🏆 Мирные жители победили!</b>\n<i>Мафия была уничтожена!</i>", parse_mode='html')
            reset_game()
        elif not mafia_alive and len(alive_players) > 1: 
            bot.send_message(chat_id, "<b>🏆 Мирные жители победили!</b>\n<i>Мафия была уничтожена!</i>", parse_mode='html')
            reset_game()

@retry_on_connection_error()
def check_game_status_maniac():
    alive_players = get_alive_players()
    maniac_alive = any(get_user_role(player_id) == 'Радчик' for player_id in players)
    werewolf_alive = any(get_user_role(player_id) == 'Юлия Сергеевна' for player_id in players)

    if werewolf_alive:
        for player_id in players:
            if get_user_role(player_id) == 'Юлия Сергеевна':
                roles_assigned[player_id] = 'Каринка'
                bot.send_message(chat_id, f"<b>🐺 Оборотень стал частью мафии!</b>", parse_mode='html')
                break

    mafia_alive = any(get_user_role(player_id) == 'Каринка' for player_id in players)
    if mafia_alive or maniac_alive and len(alive_players) > 2:
        return
    else:
        if len(alive_players) == 1:

            bot.send_message(chat_id, "<b>🏆 Мирные жители победили!</b>\n<i>Все злодеи были уничтожены!</i>", parse_mode='html')
            reset_game()
        elif len(alive_players) == 2:
            if mafia_alive and not maniac_alive:
                bot.send_message(chat_id, "<b>🏆 Мафия победила!</b>\n<i>Остались только мафия и мирный житель.</i>", parse_mode='html')
            elif maniac_alive and mafia_alive:
                bot.send_message(chat_id, "<b>🏆 Маньяк победил!</b>\n<i>Остались только маньяк и его жертва.</i>", parse_mode='html')
            elif maniac_alive and not mafia_alive:
                bot.send_message(chat_id, "<b>🏆 Маньяк победил!</b>\n<i>Остались только маньяк и его жертва.</i>", parse_mode='html')
            else:
                bot.send_message(chat_id, "<b>🏆 Мирные жители победили!</b>\n<i>Все злодеи были уничтожены!</i>", parse_mode='html')
            reset_game()
        elif not mafia_alive and not maniac_alive and len(alive_players) > 1:
            bot.send_message(chat_id, "<b>🏆 Мирные жители победили!</b>\n<i>Все злодеи были уничтожены!</i>", parse_mode='html')
            reset_game()

@retry_on_connection_error()
def end_night():
    global is_night, mafia_choice, commissar_choice, doctor_choice, killed_player_name, alive_players, maniac_choice, mafia_id, commissar_id, lover_choice, hobo_choice, spy_choice, spy_id, hobo_id, lover_id, doctor_id, hacker_choice, hacker_id
    if not game_started:
        return
    is_night = False
    bot.send_message(chat_id, "<b>🌞 Ночь закончилась!</b>\n<i>Город просыпается, подсчитываем потери...</i>", parse_mode='html')

    # Удаляем сообщения с выбором для ролей, если выбор не был сделан
    if mafia_id and mafia_choice is None:
        try:
            bot.delete_message(mafia_id, vibor.message_id)
            print(f"Сообщение о выборе мафии удалено для игрока {mafia_id}")
        except Exception as e:
            print(f"Ошибка при удалении сообщения мафии: {e}")

    if commissar_id and commissar_choice is None:
        try:
            bot.delete_message(commissar_id, viborkom.message_id)
            print(f"Сообщение о выборе комиссара удалено для игрока {commissar_id}")
        except Exception as e:
            print(f"Ошибка при удалении сообщения комиссара: {e}")

    if doctor_id and doctor_choice is None:
        try:
            bot.delete_message(doctor_id, vibordok.message_id)
            print(f"Сообщение о выборе доктора удалено для игрока {doctor_id}")
        except Exception as e:
            print(f"Ошибка при удалении сообщения доктора: {e}")

    if len(playersplay) >= 5 and lover_id and lover_choice is None:
        try:
            bot.delete_message(lover_id, viborlover.message_id)
            print(f"Сообщение о выборе путаны удалено для игрока {lover_id}")
        except Exception as e:
            print(f"Ошибка при удалении сообщения путаны: {e}")

    if len(playersplay) >= 6 and maniac_id and maniac_choice is None:
        try:
            bot.delete_message(maniac_id, vibormaniac.message_id)
            print(f"Сообщение о выборе маньяка удалено для игрока {maniac_id}")
        except Exception as e:
            print(f"Ошибка при удалении сообщения маньяка: {e}")
    
    if len(playersplay) >= 8 and hobo_id and hobo_choice is None:
        try:
            bot.delete_message(hobo_id, viborhobo.message_id)
            print(f"Сообщение о выборе бомжа удалено для игрока {hobo_id}")
        except Exception as e:
            print(f"Ошибка при удалении сообщения бомжа: {e}")

    if len(playersplay) >= 7 and spy_id and spy_choice is None:
        try:
            bot.delete_message(spy_id, viborspy.message_id)
            print(f"Сообщение о выборе шпиона удалено для игрока {spy_id}")
        except Exception as e:
            print(f"Ошибка при удалении сообщения шпиона: {e}")

    if len(playersplay) >= 12 and hacker_id and hacker_choice is None:
        try:
            bot.delete_message(hacker_id, viborhacker.message_id)
            print(f"Сообщение о выборе хакера удалено для игрока {hacker_id}")
        except Exception as e:
            print(f"Ошибка при удалении сообщения хакера: {e}")

    # Проверяем, кого заблокировал хакер
    blocked_player_id = None
    if hacker_choice is not None and int(hacker_choice) in players:
        blocked_player_id = int(hacker_choice)

    start_day()

    # Применяем блокировку ролей
    if blocked_player_id:
        blocked_role = get_user_role(blocked_player_id)
        if blocked_role == 'Каринка':
            mafia_choice = None
        elif blocked_role == 'Селях':
            commissar_choice = None
        elif blocked_role == 'Саша Доктор':
            doctor_choice = None
        elif blocked_role == 'Дытман':
            lover_choice = None
        elif blocked_role == 'Радчик':
            maniac_choice = None
        elif blocked_role == 'Матвей':
            hobo_choice = None
        elif blocked_role == 'Шпион':
            spy_choice = None

    if mafia_choice is not None and int(mafia_choice) in players:
        killed_player_name = players[int(mafia_choice)]
        killed_player_role = get_user_role(int(mafia_choice))
        if doctor_choice is not None and doctor_choice == mafia_choice:
            bot.send_message(chat_id, f"<b>🩺 Доктор спас {killed_player_name} от мафии!</b>", parse_mode='html')
        elif len(playersplay) >= 5:
            if lover_choice == mafia_id:
                lover_id = get_lover_id()
                print("lover vibral mafia")
                bot.send_message(lover_id, f"<b>💃 Вы спасли кого-то от смерти!</b>", parse_mode='html')
            elif mafia_choice != doctor_choice and lover_choice != mafia_id:
                bot.send_message(int(mafia_choice), f"<b>💀 Вы были убиты ночью!</b>\n<i>Можете оставить последние слова:</i>", parse_mode='html')
                bot.send_message(chat_id, f"<b>🕵️‍♂️ Ночью был убит {killed_player_name}.</b>\n<i>Его роль: {killed_player_role}</i>", parse_mode='html')
                remove_player(int(mafia_choice))
        elif doctor_choice != mafia_choice and len(playersplay) < 5:
            bot.send_message(int(mafia_choice), f"<b>💀 Вы были убиты ночью!</b>\n<i>Можете оставить последние слова:</i>", parse_mode='html')
            bot.send_message(chat_id, f"<b>🕵️‍♂️ Ночью был убит {killed_player_name}.</b>\n<i>Его роль: {killed_player_role}</i>", parse_mode='html')
            remove_player(int(mafia_choice))

    if commissar_choice is not None and int(commissar_choice) in players:
        checked_player_name = players[int(commissar_choice)]
        checked_player_role = get_user_role(int(commissar_choice))
        if doctor_choice == commissar_choice:
            bot.send_message(chat_id, f"<b>🩺 Доктор спас {checked_player_name} от выстрела Селях!</b>", parse_mode='html')
        elif len(playersplay) >= 5:
            if lover_choice == commissar_id:
                lover_id = get_lover_id()
                print("lover vibral comisara")
                bot.send_message(lover_id, f"<b>💃 Вы спасли кого-то от смерти!</b>", parse_mode='html')
            elif doctor_choice != commissar_choice and lover_choice != commissar_id:
                bot.send_message(int(commissar_choice), f"<b>💀 Вы были убиты ночью!</b>\n<i>Можете оставить последние слова:</i>", parse_mode='html')
                bot.send_message(chat_id, f"<b>🔫 Селях проверила выстрелом {checked_player_name}.</b>\n<i>Его роль: {checked_player_role}</i>", parse_mode='html')
                remove_player(int(commissar_choice))
        elif doctor_choice != commissar_choice and len(playersplay) < 5:
            bot.send_message(int(commissar_choice), f"<b>💀 Вы были убиты ночью!</b>\n<i>Можете оставить последние слова:</i>", parse_mode='html')
            bot.send_message(chat_id, f"<b>🔫 Селях проверила выстрелом {checked_player_name}.</b>\n<i>Его роль: {checked_player_role}</i>", parse_mode='html')
            remove_player(int(commissar_choice))

    if doctor_choice is not None and int(doctor_choice) in players:
        if doctor_choice != mafia_choice and maniac_choice and commissar_choice:
            doctor_id = get_doctor_id()
            bot.send_message(doctor_id, f"<b>🩺 Ваши услуги не понадобились этой ночью.</b>", parse_mode='html')

    if len(playersplay) >= 6:
        if maniac_choice is not None and int(maniac_choice) in players:
            mkilled_player_name = players[int(maniac_choice)]
            mkilled_player_role = get_user_role(int(maniac_choice))
            if doctor_choice == maniac_choice:
                bot.send_message(chat_id, f"<b>🩺 Доктор спас {mkilled_player_name} от маньяка!</b>", parse_mode='html')
            elif len(playersplay) >= 5:
                if lover_choice == maniac_id:
                    lover_id = get_lover_id()
                    bot.send_message(lover_id, f"<b>💃 Вы спасли кого-то от мучительной смерти!</b>", parse_mode='html')
                elif doctor_choice != maniac_choice and lover_choice != maniac_id:
                    bot.send_message(int(maniac_choice), f"<b>💀 Вы были убиты ночью!</b>\n<i>Можете оставить последние слова:</i>", parse_mode='html')
                    bot.send_message(chat_id, f"<b>🔪 Ночью маньяк убил {mkilled_player_name}.</b>\n<i>Его роль: {mkilled_player_role}</i>", parse_mode='html')
                    remove_player(int(maniac_choice))

    if len(playersplay) >= 8:
        if hobo_choice is not None:
            hobo_id = get_hobo_id()
            if hobo_choice is not None and hobo_choice == mafia_choice:
                killer = get_mafia_nick()
                bot.send_message(hobo_id, f"<b>🧳 Ты видел {killer} на месте преступления!</b>", parse_mode='html')
            elif hobo_choice is not None and hobo_choice == commissar_choice:
                comkiller = get_commissar_nick()
                bot.send_message(hobo_id, f"<b>🧳 Ты видел {comkiller} на месте преступления!</b>", parse_mode='html')
            elif hobo_choice is not None and hobo_choice == maniac_choice:
                mankiller = get_maniac_nick()
                bot.send_message(hobo_id, f"<b>🧳 Ты видел {mankiller} на месте преступления!</b>", parse_mode='html')
            elif hobo_choice is not None:
                bot.send_message(hobo_id, f"<b>🧳 Ты ничего не увидел этой ночью.</b>", parse_mode='html')

    if len(playersplay) >= 7:
        if spy_choice is not None and int(spy_choice) in players:
            spy_id = get_spy_id()
            mafia_id = get_mafia_id()
            spy_checked_player_name = players[int(spy_choice)]
            spy_checked_player_role = get_user_role(int(spy_choice))
            if spy_id:
                bot.send_message(spy_id, f"<b>🕶️ Вы узнали, что {spy_checked_player_name} имеет роль: {spy_checked_player_role}</b>", parse_mode='html')
            if mafia_id:
                bot.send_message(mafia_id, f"<b>🕶️ Шпион сообщает: {spy_checked_player_name} имеет роль: {spy_checked_player_role}</b>", parse_mode='html')

    if len(playersplay) >= 6:
        check_game_status_maniac()
    elif len(playersplay) < 6:
        check_game_status()

    if game_started:
        alive_players = get_alive_players()
        bot.send_message(chat_id, f"<b>👥 Живые игроки:</b> {', '.join(alive_players)}", parse_mode='html')
        roles_set = set()
        for player_id in players:
            player_role = get_user_role(player_id)
            if player_role is not None:
                roles_set.add(player_role)
        roles_message = "<b>🎭 Среди них:</b>\n" + "\n".join([f"{role}" for role in roles_set])
        bot.send_message(chat_id, roles_message, parse_mode='html')

@retry_on_connection_error()
def reset_game():
    global game_started, players, roles_assigned, is_night, mafia_choice, commissar_choice, doctor_choice, maniac_choice, lover_choice, hobo_choice, spy_choice, hacker_choice
    game_started = False
    players.clear()
    roles_assigned.clear()
    is_night = False
    mafia_choice = None
    commissar_choice = None
    doctor_choice = None
    maniac_choice = None
    lover_choice = None
    hobo_choice = None
    spy_choice = None
    hacker_choice = None

@retry_on_connection_error()
def start_day():
    global is_night
    if not game_started:
        return
    is_night = False
    threading.Timer(DAY_DURATION, end_day).start()
    bot.send_message(chat_id, f"<b>🌞 День наступил!</b>\n<i>У вас есть {DAY_DURATION // 60} минут на обсуждение. Решайте, кто виновен! 🗳️</i>", parse_mode='html')
    threading.Timer(PERERIV_DURATION, start_voting).start()

@retry_on_connection_error()
def end_day():
    global is_night, mafia_choice, commissar_choice, doctor_choice, killed_player_name, playersplay
    if not game_started:
        return
    end_voting()
    print(playersplay)
    if len(playersplay) >= 6:
        check_game_status_maniac()
    elif len(playersplay) < 6:
        check_game_status()
    if game_started:
        start_night()

@bot.message_handler(commands=['test'])
def handle_test(message):
    logger.info(f"Вызван обработчик /test: user_id={message.from_user.id}, chat_id={message.chat.id}, text={message.text}")
    try:
        bot.reply_to(message, "✅ Тест пройден! Бот активен.")
        logger.info(f"Сообщение /test успешно отправлено в chat_id={message.chat.id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения /test: {str(e)}")

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        logger.info("Получен входящий запрос на вебхук")
        json_data = request.get_json()
        if not json_data:
            logger.error("Пустое тело запроса")
            return jsonify({"error": "Empty request"}), 400
        update = telebot.types.Update.de_json(json_data)
        if not update:
            logger.error("Не удалось декодировать Update")
            return jsonify({"error": "Invalid Update"}), 400
        logger.info(f"Обработка обновления: {json_data}")
        if update.message:
            logger.info(f"Сообщение: {update.message.text} от user_id={update.message.from_user.id}")
        elif update.callback_query:
            logger.info(f"Callback: {update.callback_query.data} от user_id={update.callback_query.from_user.id}")
        logger.info("Передача обновления в bot.process_new_updates")
        try:
            bot.process_new_updates([update])
            logger.info("Обновление успешно обработано")
        except Exception as e:
            logger.error(f"Ошибка в bot.process_new_updates: {str(e)}")
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Критическая ошибка в вебхуке: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def health_check():
    return 'Bot is running', 200

@app.route('/test_telegram')
def test_telegram():
    try:
        bot_info = bot.get_me()
        logger.info(f"Успешно получена информация о боте: @{bot_info.username}")
        bot.send_message(716559083, "Тестовое сообщение от бота")
        logger.info("Тестовое сообщение отправлено")
        return jsonify({"status": "ok", "bot": bot_info.username})
    except Exception as e:
        logger.error(f"Ошибка при тестировании Telegram: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/check_webhook')
def check_webhook_status():
    try:
        webhook_info = bot.get_webhook_info()
        return jsonify({
            'webhook_url': webhook_info.url,
            'pending_update_count': webhook_info.pending_update_count,
            'last_error_date': webhook_info.last_error_date,
            'last_error_message': webhook_info.last_error_message
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Запуск приложения
if __name__ == '__main__':
    set_webhook()  # Используем существующую функцию
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 10000)))