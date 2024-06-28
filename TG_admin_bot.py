import telebot
from telebot import types
import psycopg2
import time
import os
import sys
from dotenv import load_dotenv
from my_functions import validate_date, validate_time, \
    children_list_request_by_name


load_dotenv()

# Данные для Telegram
token = os.getenv('ADMIN_BOT_TOKEN')
bot = telebot.TeleBot(token)
prog_id = os.getenv('PROG_ID')

# Данные для БД
dbname = os.getenv('DATABASE_NAME')
user = os.getenv('DATABASE_USER')
password = os.getenv('DATABASE_PASSWORD')
host = "localhost"
port = "5432"


# класс для регистрации нового занятия
class Schedule:
    def __init__(self, date):
        self.time = None
        self.trainer = None
        self.date = date


# Класс для регистрации клиента с абонементом
class TrainingSubcription:
    def __init__(self, name):
        self.name = name
        self.surname = None
        self.date_start = None
        self.date_end = None


# Класс для регистрации события
class Event:
    def __init__(self, date_start):
        self.name = None
        self.place = None
        self.date_start = date_start
        self.date_end = None


training_dict = {}

training_subsc = {}

event_dict = {}


# Функция для перезапуска бота
@bot.message_handler(commands=['restart'])
def restart_bot(message=None):
    if message:
        time.sleep(2)
        welcome(message)
    os.execv(sys.executable, ['python'] + sys.argv)


# Приветствие
# Запрос '/start'
@bot.message_handler(commands=['start'])
def welcome(message):
    try:
        hello = 'Здраствуйте, это бот для администрирования ДФК Мегаполис'
        bot.send_message(message.from_user.id, hello)
    except Exception as e:
        bot.send_message(prog_id, f"Функция process_start: {e}")

#############################################################################


# Процесс добавления новой тренировки
# Запрос '/schedule_add'
@bot.message_handler(commands=['schedule_add'])
def schedule(message):
    try:
        markup = types.ReplyKeyboardMarkup(
            one_time_keyboard=True, resize_keyboard=True)
        markup.add('Да', 'Нет')
        text = 'Хотите добавить новую тренировку?'
        msg = bot.send_message(message.from_user.id, text,
                               reply_markup=markup)
        bot.register_next_step_handler(msg, schedule_start)
    except Exception as e:
        bot.send_message(prog_id, f"Функция schedule: {e}")


def schedule_start(message):
    try:
        answer = message.text
        if answer == u'Да':
            text = 'Отлично! Введите дату тренировки в формате ДД.ММ.ГГГГ:'
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, schedule_date)
        elif answer == u'Нет':
            text = "Понял тебя, если тебе интересно что еще я умею, \
то используй команду /help"
            bot.send_message(message.from_user.id, text,
                             reply_markup=types.ReplyKeyboardRemove())
            return
        elif answer == u'/restart':
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        else:
            bot.send_message(message.from_user.id, "Таких команд я не \
знаю, давайте еще раз!!", reply_markup=types.ReplyKeyboardRemove())
            schedule(message)
    except Exception as e:
        bot.send_message(prog_id, f"Функция schedule_start: {e}")


# Регистрация даты
def schedule_date(message):
    try:
        answer = message.text
        if answer == u'/restart':  # Перезапуск всей системы
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return

        if validate_date(answer):
            training_schedule_class = Schedule(answer)
            training_dict[message.from_user.id] = training_schedule_class
            text = '''Введите фамилию, имя, отчества тренера
Пример: Иванов Иван Иванович'''
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, schedule_trainer)
        else:
            text = """Некорректная дата.
Пожалуйста, введите дату в формате ДД.ММ.ГГГГ:"""
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, schedule_date)
    except Exception as e:
        bot.send_message(prog_id, f"Функция schedule_date: {e}")


# Регистрация тренера
def schedule_trainer(message):
    try:
        answer = message.text.title()
        if answer == u'/Restart':  # Перезапуск всей системы
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        # сохранение данных о тренере
        training_schedule_class = training_dict[message.from_user.id]
        training_schedule_class.trainer = answer
        # запрос информации о времени
        text = 'Введите время тренировки в формате ЧЧ:ММ'
        msg = bot.send_message(message.from_user.id, text,
                               reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, schedule_time)
    except Exception as e:
        bot.send_message(prog_id, f"Функция schedule_trainer: {e}")


# Регистрация времени
def schedule_time(message):
    try:
        answer = message.text
        if answer == u'/restart':  # Перезапуск всей системы
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return

        if validate_time(answer):  # сохранение времени
            training_schedule_class = training_dict[message.from_user.id]
            training_schedule_class.time = answer
            # уточнение введеных данных
            markup = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True)
            markup.add('Да', 'Нет', 'Отменить регистрацию')
            text = f"День: {training_schedule_class.date}, \
время: {training_schedule_class.time} \
\nТренер: {training_schedule_class.trainer.title()}\nВерно?"
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, schedule_finish)
        else:
            text = """Некорректное время.
Пожалуйста, введите время в формате ЧЧ:ММ"""
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, schedule_time)
    except Exception as e:
        bot.send_message(prog_id, f"Функция schedule_time: {e}")


def schedule_finish(message):
    try:
        answer = message.text
        if answer == u'Да' or answer == u'Верно':
            save_training(message)
        elif answer == u'Нет':
            markup = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True)
            markup.add('Да', 'Нет')
            text = """Хорошо, давайте тогда начнем сначала.
Хотите добавить новую тренировку?"""
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, schedule_start)
        elif answer == u'Отменить регистрацию':
            bot.send_message(message.from_user.id, "Регистрация отменена.")
            return
        elif answer == u'/restart':  # Перезапуск всей системы
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        else:
            markup = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True)
            markup.add('Да', 'Нет', 'Отменить регистрацию')
            text = "Таких команд я не знаю, давайте еще раз!"
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, schedule_finish)
    except Exception as e:
        bot.send_message(prog_id, f"Функция process_finish: {e}")


# Сохранение данных
def save_training(message):
    training_schedule_class = training_dict[message.from_user.id]
    try:
        # Соединение с базой данных
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

        # Создание курсора для выполнения запросов
        cursor = conn.cursor()
        try:
            # SQL-запрос для создания таблицы с проверкой ее существования
            create_table_query = """
            SET datestyle = 'ISO, DMY';

            CREATE TABLE IF NOT EXISTS training_schedule (
                id SERIAL primary key
                ,time TIME NOT NULL
                ,trainer VARCHAR(100) NOT NULL
                ,date DATE not NULL
            );
            """

            # Выполнение запроса
            cursor.execute(create_table_query)

            # Фиксирование изменений
            conn.commit()

            try:
                insert_query = """
                    INSERT INTO training_schedule (time, trainer, date)
                    VALUES (%s, %s, %s)
                """

                # Данные для вставки
                data_to_insert = (training_schedule_class.time,
                                  training_schedule_class.trainer.replace(',', '，'),
                                  training_schedule_class.date)

                # Выполнение вставки данных
                cursor.execute(insert_query, data_to_insert)

                # Фиксирование изменений
                conn.commit()

                text = "Отлично! Тренировка добавлена в расписание"
                bot.send_message(message.from_user.id, text)
            except Exception as e:
                bot.send_message(prog_id, f"Функция save_training1: {e}")
        except Exception as e:
            bot.send_message(prog_id, f"Функция save_training2: {e}")
    except Exception as e:
        bot.send_message(prog_id, f"Функция save_training3: {e}")
    finally:
        # Закрываем курсор и соединение
        cursor.close()
        conn.close()

#############################################################################


# Добавление пользователя с абонементом
# Запрос '/user_subscription'
@bot.message_handler(commands=['user_subscription'])
def training_sub(message):
    try:
        markup = types.ReplyKeyboardMarkup(
            one_time_keyboard=True, resize_keyboard=True)
        markup.add('Да', 'Нет')
        text = 'Хотите добавить пользователя, который купил абонемент?'
        msg = bot.send_message(message.from_user.id, text,
                               reply_markup=markup)
        bot.register_next_step_handler(msg, training_sub_start)
    except Exception as e:
        bot.send_message(prog_id, f"Функция training_sub: {e}")


def training_sub_start(message):
    try:
        answer = message.text
        if answer == u'Да':
            text = 'Отлично! Введите имя ребенка.'
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, training_sub_name)
        elif answer == u'Нет':
            text = "Понял тебя, если тебе интересно что еще я умею, \
то используй команду /help"
            bot.send_message(message.from_user.id, text,
                             reply_markup=types.ReplyKeyboardRemove())
            return
        elif answer == u'/restart':
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        else:
            markup = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True)
            markup.add('Да', 'Нет')
            msg = bot.send_message(message.from_user.id,
                                   "Таких команд я не знаю, давайте еще раз!!",
                                   reply_markup=markup)
            training_sub(message)
            return
    except Exception as e:
        bot.send_message(prog_id, f"Функция training_sub_start: {e}")


def training_sub_name(message):
    try:
        answer = message.text.strip(' ').title()
        if answer == u'/Restart':  # Перезапуск всей системы
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return

        training_subs_class = TrainingSubcription(answer)
        training_subsc[message.from_user.id] = training_subs_class
        text = 'Введите фамилию ребенка.'
        msg = bot.send_message(message.from_user.id, text,
                               reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, training_sub_surname)
    except Exception as e:
        bot.send_message(prog_id, f"Функция training_sub_name: {e}")


def training_sub_surname(message):
    try:
        answer = message.text.strip(' ').title()
        if answer == u'/Restart':  # Перезапуск всей системы
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return

        training_subs_class = training_subsc[message.from_user.id]
        training_subs_class.surname = answer
        text = 'Выберите ребенка из списка'
        training_subs_class.name, training_subs_class.surname
        children = children_list_request_by_name(training_subs_class.name,
                                                 training_subs_class.surname)
        if children[0] == 'Нет данных о детях.':
            text = 'В данный момент нет таких зарегистрированных \
пользователей.'
            bot.send_message(message.from_user.id, text,
                             reply_markup=types.ReplyKeyboardRemove())
            training_sub(message)
        else:
            markup = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True)
            for child in children:
                parts = child.split(',')
                child = ','.join(parts)
                markup.add(child)
            markup.add('Прервать запись.')
            text = "Кто оплатил абонемент?"
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, training_sub_child,
                                           children=children)
    except Exception as e:
        bot.send_message(prog_id, f"Функция training_sub_surname: {e}")


def training_sub_child(message, children):
    try:
        child = message.text
        if child == u'/restart':  # Перезапуск всей системы
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        valid_choices = [', '.join(child.split(', '))
                         for child in children[:-1]] + ['Прервать запись.']
        if child not in valid_choices:
            markup = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True)
            for child in children:
                parts = child.split(',')
                child = ','.join(parts)
                markup.add(child)
            markup.add('Прервать запись.')
            text = """Не помню такого человека. Давай еще раз!
Кто оплатил абонемент?"""
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, training_sub_child,
                                           children=children)
            return
        if child == u'Прервать запись.':
            bot.send_message(message.from_user.id, "Запись прервана.",
                             reply_markup=types.ReplyKeyboardRemove())
            return
        text = 'Укажите дату начала абонемента в формате ДД.ММ.ГГГГ'
        msg = bot.send_message(message.from_user.id, text,
                               reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, training_sub_start_date,
                                       child=child)
    except Exception as e:
        bot.send_message(prog_id, f"Функция training_sub_start_date: {e}")


def training_sub_start_date(message, child):
    try:
        child = child
        start_date = message.text
        if start_date == u'/restart':  # Перезапуск всей системы
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        if validate_date(start_date):
            training_subs_class = training_subsc[message.from_user.id]
            training_subs_class.date_start = start_date
            text = 'Укажите дату окончания абонемента в формате ДД.ММ.ГГГГ'
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, training_sub_finish,
                                           child=child, start_date=start_date)
        else:
            text = """Некорректная дата.
Пожалуйста, введите дату в формате ДД.ММ.ГГГГ:"""
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, training_sub_start_date,
                                           child=child)
    except Exception as e:
        bot.send_message(prog_id, f"Функция training_sub_start_date: {e}")


def training_sub_finish(message, child, start_date):
    try:
        child = child
        start_date = start_date
        end_date = message.text
        if end_date == u'/restart':  # Перезапуск всей системы
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        if validate_date(end_date):  # Сохранение даты рождения
            training_subs_class = training_subsc[message.from_user.id]
            training_subs_class.date_end = end_date
            save_subscription(message, child=child, start_date=start_date,
                              end_date=end_date)
        else:
            text = """Некорректная дата.
Пожалуйста, введите дату в формате ДД.ММ.ГГГГ:"""
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, training_sub_finish,
                                           child=child, start_date=start_date)
    except Exception as e:
        bot.send_message(prog_id, f"Функция training_sub_finish: {e}")


def save_subscription(message, child, start_date, end_date):
    try:
        # Соединение с базой данных
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

        # Создание курсора для выполнения запросов
        cursor = conn.cursor()
        try:
            # SQL-запрос для создания таблицы с проверкой ее существования
            create_table_query = """
            SET datestyle = 'ISO, DMY';

            CREATE TABLE IF NOT EXISTS training_subscription (
                    id SERIAL primary key
                    ,chat_id VARCHAR(100) NOT NULL
                    ,child_name VARCHAR(100) NOT NULL
                    ,child_surname VARCHAR(100) NOT NULL
                    ,child_birth_date VARCHAR(20) NOT NULL
                    ,parent_name VARCHAR(100) NOT NULL
                    ,date_start DATE NOT NULL
                    ,date_end DATE NOT NULL
                );
            """

            # Выполнение запроса
            cursor.execute(create_table_query)

            # Фиксирование изменений
            conn.commit()

            try:
                insert_query = """
                    INSERT INTO training_subscription (chat_id, child_name, \
child_surname, child_birth_date, parent_name, date_start, date_end)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                child = child.split(', ')
                # Данные для вставки
                data_to_insert = (child[1], child[2], child[3], child[4],
                                  child[5], start_date, end_date)

                # Выполнение вставки данных
                cursor.execute(insert_query, data_to_insert)

                # Фиксирование изменений
                conn.commit()

                markup = types.ReplyKeyboardMarkup(
                    one_time_keyboard=True, resize_keyboard=True)
                markup.add('Да', 'Нет')
                text = "Отлично! Пользователь, который купил абонемент, \
добавлен"
                bot.send_message(message.from_user.id, text,
                                 reply_markup=types.ReplyKeyboardRemove())
            except Exception as e:
                bot.send_message(prog_id, f"Функция save_subscription1: {e}")
        except Exception as e:
            bot.send_message(prog_id, f"Функция save_subscription2: {e}")
    except Exception as e:
        bot.send_message(prog_id, f"Функция save_subscription3: {e}")
    finally:
        # Закрываем курсор и соединение
        cursor.close()
        conn.close()


#############################################################################

# Добавление нового события
# Запрос '/event_add'
@bot.message_handler(commands=['event_add'])
def event(message):
    try:
        markup = types.ReplyKeyboardMarkup(
            one_time_keyboard=True, resize_keyboard=True)
        markup.add('Да', 'Нет')
        text = 'Хотите добавить новое событие?'
        msg = bot.send_message(message.from_user.id, text,
                               reply_markup=markup)
        bot.register_next_step_handler(msg, event_start)
    except Exception as e:
        bot.send_message(prog_id, f"Функция event: {e}")


def event_start(message):
    try:
        answer = message.text
        if answer == u'Да':
            text = 'Укажите дату начала турнира в формате ДД.ММ.ГГГГ'
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, event_date_start)
        elif answer == u'Нет':
            text = "Понял тебя, если тебе интересно что еще я умею, \
то используй команду /help"
            bot.send_message(message.from_user.id, text,
                             reply_markup=types.ReplyKeyboardRemove())
            return
        elif answer == u'/restart':
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        else:
            bot.send_message(message.from_user.id, "Таких команд я не \
знаю, давайте еще раз!!", reply_markup=types.ReplyKeyboardRemove())
            event(message)
    except Exception as e:
        bot.send_message(prog_id, f"Функция event_start: {e}")


def event_date_start(message):
    try:
        date_start = message.text
        if date_start == u'/restart':  # Перезапуск всей системы
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        if validate_date(date_start):
            event_schedule_class = Event(date_start)
            event_dict[message.from_user.id] = event_schedule_class
            text = 'Укажите дату окончания турнира в формате ДД.ММ.ГГГГ'
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, event_date_end)
        else:
            text = "Некорректная дата. Пожалуйста, введите дату \
в формате ДД.ММ.ГГГГ:"
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, event_date_start)
    except Exception as e:
        bot.send_message(prog_id, f"Функция event_date_start: {e}")


def event_date_end(message):
    try:
        date_end = message.text
        if date_end == u'/restart':  # Перезапуск всей системы
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        if validate_date(date_end):  # Сохранение даты рождения
            event_schedule_class = event_dict[message.from_user.id]
            event_schedule_class.date_end = date_end
            text = 'Введите название события.'
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, event_name)
        else:
            text = "Некорректная дата. Пожалуйста, введите дату \
в формате ДД.ММ.ГГГГ:"
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, event_date_end)
    except Exception as e:
        bot.send_message(prog_id, f"Функция event_date_end: {e}")


def event_name(message):
    try:
        answer = message.text.capitalize()
        if answer == u'/restart':  # Перезапуск всей системы
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        # сохранение данных о названии событии
        event_schedule_class = event_dict[message.from_user.id]
        event_schedule_class.name = answer
        text = 'Введите место проведения события.'
        msg = bot.send_message(message.from_user.id, text,
                               reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, event_place)
    except Exception as e:
        bot.send_message(prog_id, f"Функция event_name: {e}")


# Регистрация места
def event_place(message):
    try:
        answer = message.text
        if answer == u'/restart':  # Перезапуск всей системы
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        # сохранение данных о месте проведения события
        event_schedule_class = event_dict[message.from_user.id]
        event_schedule_class.place = answer
        # уточнение введеных данных
        markup = types.ReplyKeyboardMarkup(
            one_time_keyboard=True, resize_keyboard=True)
        markup.add('Да', 'Нет', 'Отменить регистрацию')
        text = f"Событие: {event_schedule_class.name}, \nМесто: \
{event_schedule_class.place} \nДата: {event_schedule_class.date_start} - \
{event_schedule_class.date_end}\nВерно?"
        msg = bot.send_message(message.from_user.id, text,
                               reply_markup=markup)
        bot.register_next_step_handler(msg, event_finish)
    except Exception as e:
        bot.send_message(prog_id, f"Функция event_place: {e}")


def event_finish(message):
    try:
        answer = message.text
        if answer == u'Да' or answer == u'Верно':
            save_event(message)
        elif answer == u'Нет':
            markup = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True)
            markup.add('Да', 'Нет')
            text = """Хорошо, давайте тогда начнем сначала.
Хотите добавить новое событие?"""
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, event_start)
        elif answer == u'Отменить регистрацию':
            bot.send_message(message.from_user.id, "Регистрация отменена.")
            return
        elif answer == u'/restart':  # Перезапуск всей системы
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        else:
            markup = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True)
            markup.add('Да', 'Нет', 'Отменить регистрацию')
            text = "Таких команд я не знаю, давайте еще раз!"
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, event_finish)
    except Exception as e:
        bot.send_message(prog_id, f"Функция event_finish: {e}")


# Сохранение данных
def save_event(message):
    event_schedule_class = event_dict[message.from_user.id]
    try:
        # Соединение с базой данных
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

        # Создание курсора для выполнения запросов
        cursor = conn.cursor()
        try:
            # SQL-запрос для создания таблицы с проверкой ее существования
            create_table_query = """
            SET datestyle = 'ISO, DMY';

            CREATE TABLE IF NOT EXISTS event_schedule(
                id SERIAL PRIMARY KEY
                ,event_name VARCHAR(300) NOT NULL
                ,event_place VARCHAR(300) NOT NULL
                ,event_date_start DATE NOT NULL
                ,event_date_end DATE NOT NULL
            );
            """

            # Выполнение запроса
            cursor.execute(create_table_query)

            # Фиксирование изменений
            conn.commit()

            try:
                insert_query = """
                    INSERT INTO event_schedule (event_name, event_place, \
event_date_start, event_date_end)
                    VALUES (%s, %s, %s, %s)
                """


                # Данные для вставки
                data_to_insert = (event_schedule_class.name.replace(',', '，'),
                                  event_schedule_class.place.replace(',', '，'),
                                  event_schedule_class.date_start,
                                  event_schedule_class.date_end)
                print(data_to_insert)
                # Выполнение вставки данных
                cursor.execute(insert_query, data_to_insert)

                # Фиксирование изменений
                conn.commit()

                text = "Отлично! Событие добавлено в расписание"
                bot.send_message(message.from_user.id, text)
            except Exception as e:
                bot.send_message(prog_id, f"Функция save_event1: {e}")
        except Exception as e:
            bot.send_message(prog_id, f"Функция save_event2: {e}")
    except Exception as e:
        bot.send_message(prog_id, f"Функция save_event3: {e}")
    finally:
        # Закрываем курсор и соединение
        cursor.close()
        conn.close()

#############################################################################


# Получение списком всех зарегистрированных пользователей
# Запрос '/all_clients'
@bot.message_handler(commands=['all_clients'])
def show_clients(message):
    try:
        # Соединение с базой данных
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

        # Создание курсора для выполнения запросов
        cursor = conn.cursor()
        try:
            select_all_clients = "SELECT * FROM football_clients"

            cursor.execute(select_all_clients)

            rows = cursor.fetchall()

            # Формируем сообщение с результатами
            if rows:
                result_message = ""
                for row in rows:
                    id, chat_id, child_name, child_surname, \
                        child_birth_date, parent_name = row
                    result_message += f"{id}, {chat_id}, {child_name}, \
{child_surname}, {child_birth_date}, {parent_name}\n"
            else:
                result_message = "Нет данных о детях."

            children = result_message.split('\n')
            if children[0] == 'Нет данных о детях.':
                text = 'В данный момент нет зарегистрированных \
пользователей.'
                bot.send_message(message.from_user.id, text,
                                 reply_markup=types.ReplyKeyboardRemove())
            else:
                for child in children[:-1]:
                    parts = child.split(',')
                    child = ','.join(parts)
                    child = child.split(', ')
                    text = f'Имя: {child[2]} \nФамилия: {child[3]}\
\nДата рождения: {child[4]} \nПредставитель: {child[5]}'
                    bot.send_message(message.from_user.id, text,
                                     reply_markup=types.ReplyKeyboardRemove())
        except Exception as e:
            bot.send_message(prog_id, f"Функция show_clients1: {e}")
    except Exception as e:
        bot.send_message(prog_id, f"Функция show_clients2: {e}")
    finally:
        # Закрываем курсор и соединение
        cursor.close()
        conn.close()

#############################################################################


# Запрос '/help'
@bot.message_handler(commands=['help'])
def help(message):
    pass
    try:
        text = '''/schedule_add - Добавить занятие в расписание
/user_subscription - Добавить пользователя с абонементом
/event_add - Добавить событие
/all_clients - Просмотр всех клиентов
/restart - Перезагрузка бота'''
        bot.send_message(message.from_user.id, text,
                         reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        bot.send_message(prog_id, f"Функция help: {e}")

#############################################################################


# Все остальные текстовые запросы
@bot.message_handler(content_types=['text'])
def handle_all_messages(message):
    try:
        text = "Неизвестная команда. Выберите команду из пункта меню или \
используйте команду /help"
        bot.send_message(message.from_user.id, text,
                         reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        bot.send_message(prog_id, f"Функция handle_all_messages: {e}")


# Enable saving next step handlers
bot.enable_save_next_step_handlers(delay=1)
# Load previously saved next step handlers
bot.load_next_step_handlers()

# Запуск
# bot.polling(none_stop=True, interval=0)

# Бесконечный запуск
def start_bot():
    while True:
        try:
            bot.send_message(prog_id, f"Футбольный бот запущен")
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            bot.send_message(prog_id,
                             f"Ошибка в запуске футбольного бота: {e}")
            time.sleep(1)

if __name__ == '__main__':
    start_bot()
