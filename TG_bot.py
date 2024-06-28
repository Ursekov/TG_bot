import telebot
from telebot import types
import psycopg2
import time
from dotenv import load_dotenv
import os
from my_functions import validate_date, children_list_request_by_id, \
                        children_parent_list_request, \
                        training_schedule_request, \
                        training_reg, event_schedule_request


load_dotenv()

# Данные для Telegram
token = os.getenv('MAIN_BOT_TOKEN')
# admin_id = os.getenv('ADMIN_ID')
admin_id = os.getenv('PROG_ID')
prog_id = os.getenv('PROG_ID')
bot = telebot.TeleBot(token)

# Данные для БД
dbname = os.getenv('DATABASE_NAME')
user_bd = os.getenv('DATABASE_USER')
password = os.getenv('DATABASE_PASSWORD')
host = "localhost"
port = "5432"


# Класс для регистрации пользователя
class NewUser:
    def __init__(self, name):
        self.name = name
        self.surname = None
        self.birth_date = None
        self.representative = None


user_dict = {}


# Функция для перезапуска бота
@bot.message_handler(commands=['restart'])
def restart_bot(message=None):
    if message:
        welcome(message)


# Приветствие
# Запрос '/reg'
@bot.message_handler(commands=['start'])
def welcome(message):
    try:
        answer = 'Здраствуйте, это бот ДФК Мегаполис, он предназначен для \
удобства получения различной информации в рамках нашего клуба. \
\nДля регистрации используйте команду /reg или посмотрите, \
что ещё я умею, использовав команду /help!'
        bot.send_message(message.from_user.id, answer)
    except Exception as e:
        bot.send_message(prog_id, f"Функция welcome: {e}")

##############################################################################


# Запрос '/reg'
@bot.message_handler(commands=['reg'])
def registration_question(message):
    try:
        markup = types.ReplyKeyboardMarkup(
            one_time_keyboard=True, resize_keyboard=True)
        markup.add('Да', 'Нет')
        text = 'Хотите зарегистрироваться?'
        msg = bot.send_message(message.from_user.id, text, reply_markup=markup)
        bot.register_next_step_handler(msg, registration_start)
    except Exception as e:
        bot.send_message(prog_id, f"Функция registration_question: {e}")


def registration_start(message):
    try:
        answer = message.text.capitalize()
        answer_yes = ['Да', 'Хотим', 'Хочу']
        if answer in answer_yes:
            text = 'Отлично! Как зовут ребенка?'
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, registration_name_step)
        elif answer == u'Нет':
            text = "Понял, если тебе интересно что ещё я умею, \
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
            text = "Таких команд я не знаю, давайте еще раз!"
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=markup)
            text = 'Хотите зарегистрироваться?'
            bot.send_message(message.from_user.id, text)
            bot.register_next_step_handler(msg, registration_start)
    except Exception as e:
        bot.send_message(prog_id, f"Функция registration_start: {e}")


def registration_name_step(message):
    try:
        answer = message.text.title()
        if answer == '/Restart':
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        # Инициализация класса
        user = NewUser(answer)
        user_dict[message.from_user.id] = user
        # Переход к следующему этапу
        text = 'Какая фамилия у ребенка?'
        msg = bot.send_message(message.from_user.id, text,
                               reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, registration_surname_step)
    except Exception as e:
        bot.send_message(prog_id, f"Функция registration_name_step: {e}")


def registration_surname_step(message):
    try:
        answer = message.text.title()
        if answer == u'/Restart':
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        # Добавление атрибута фамилия к экземпляру класса
        user = user_dict[message.from_user.id]
        user.surname = answer
        # Переход к следующему этапу
        text = 'Введите дату рождения ребенка в формате ДД.ММ.ГГГГ'
        msg = bot.send_message(message.from_user.id, text,
                               reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, registration_date_step)
    except Exception as e:
        bot.send_message(prog_id, f"Функция registration_surname_step: {e}")


def registration_date_step(message):
    try:
        answer = message.text
        if answer == u'/restart':  # Перезапуск всей системы
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        if validate_date(answer):  # Сохранение даты рождения
            # Добавление атрибута дата рождения к экземпляру класса
            user = user_dict[message.from_user.id]
            user.birth_date = answer
            # Переход к следующему этапу
            text = 'Введите Фамилию, Имя, Отчества представителя \
\nПример: Иванов Иван Иванович'
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, registration_parent_name)
        else:  # Повторный запрос даты рождения, в случае неверного формата
            text = "Некорректная дата. Пожалуйста, введите дату \
в формате ДД.ММ.ГГГГ"
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, registration_date_step)
    except Exception as e:
        bot.send_message(prog_id, f"Функция registration_date_step: {e}")


def registration_parent_name(message):
    try:
        answer = message.text.title()
        if answer == u'/Restart':  # Перезапуск всей системы
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        # Сохранение данных о представителе (родителе)
        # Добавление атрибута данные о представителе к экземпляру класса
        user = user_dict[message.from_user.id]
        user.representative = answer
        # Запрос о корректности введеных данных
        markup = types.ReplyKeyboardMarkup(
            one_time_keyboard=True, resize_keyboard=True)
        markup.add('Да', 'Нет', 'Отменить регистрацию')
        text = f"Ребенок: {user.name.title()} {user.surname.title()} \
{str(user.birth_date)}\nПредставитель: {user.representative.title()} \
\nВерно?"
        msg = bot.send_message(message.from_user.id, text, reply_markup=markup)
        bot.register_next_step_handler(msg, process_finish)
    except Exception as e:
        bot.send_message(prog_id, f"Функция registration_parent_name: {e}")


# Сценарии на ответ о сохранении
def process_finish(message):
    try:
        answer = message.text.capitalize()
        if answer == u'Да' or answer == u'Верно':
            save_client(message)
        elif answer == u'Нет':
            text = "Хорошо, давайте тогда начнем сначала. Как зовут ребенка?"
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, registration_name_step)
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
            bot.register_next_step_handler(msg, process_finish)
    except Exception as e:
        bot.send_message(prog_id, f"Функция process_finish: {e}")


# Сохранение данных
def save_client(message):
    user = user_dict[message.from_user.id]
    try:
        # Соединение с базой данных
        conn = psycopg2.connect(
            dbname=dbname,
            user=user_bd,
            password=password,
            host=host,
            port=port
        )

        # Создание курсора для выполнения запросов
        cursor = conn.cursor()
        try:
            # SQL-запрос для создания таблицы с проверкой ее существования
            create_table_query = """
            CREATE TABLE IF NOT EXISTS football_clients (
                id SERIAL PRIMARY KEY
                ,chat_id VARCHAR(100) NOT NULL
                ,child_name VARCHAR(100) NOT NULL
                ,child_surname VARCHAR(100) NOT NULL
                ,child_birth_date VARCHAR(20) NOT NULL
                ,parent_name VARCHAR(100) NOT NULL
            );
            """
            # Выполнение запроса
            cursor.execute(create_table_query)
            # Фиксирование изменений
            conn.commit()
            try:
                request = f"""INSERT INTO football_clients (chat_id
                                                            ,child_name
                                                            ,child_surname
                                                            ,child_birth_date
                                                            ,parent_name)
                VALUES ({str(message.from_user.id)}
                        ,'{user.name.replace(',', '，')}'
                        ,'{user.surname.replace(',', '，')}'
                        ,'{str(user.birth_date)}'
                        ,'{user.representative.replace(',', '，')}')"""
                # Выполнение запроса
                cursor.execute(request)
                # Фиксирование изменений
                conn.commit()
                markup = types.ReplyKeyboardMarkup(
                    one_time_keyboard=True, resize_keyboard=True)
                markup.add('Да', 'Нет')
                text = "Отлично! Вы зарегистрированы, с расписанием \
тренировок можете ознакомиться во вкладке расписание. \
\nХотите записаться на первую тренировку?"
                msg = bot.send_message(message.from_user.id, text,
                                       reply_markup=markup)
                bot.register_next_step_handler(msg, training_reg_question)
            except Exception as e:
                bot.send_message(prog_id, f"Функция save_client1: {e}")
        except Exception as e:
            bot.send_message(prog_id, f"Функция save_client2: {e}")
    except Exception as e:
        bot.send_message(prog_id, f"Функция save_client3: {e}")
    finally:
        # Закрываем курсор и соединение
        cursor.close()
        conn.close()


##############################################################################

# Запрос '/training'
@bot.message_handler(commands=['training'])
def training_reg_question(message):
    try:
        answer = message.text
        valid_choices = ['Да', 'Нет',
                         'Прервать запись.', 'Зарегистрировать ребенка.',
                         '/restart', '/training']
        if answer not in valid_choices:
            markup = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True)
            markup.add('Да')
            markup.add('Нет')
            bot.send_message(message.from_user.id,
                             'Неизвестная команда.',
                             reply_markup=types.ReplyKeyboardRemove())
            msg = bot.send_message(message.from_user.id,
                                   'Хотите записаться на первую тренировку?',
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, training_reg_question)
            return

        # Обработка запросов, полученных от функции registration_time
        if answer == u'Нет':
            text = "Хорошо. Для записи на тренировку воспользуйтесь командой \
/training."
            bot.send_message(message.from_user.id, text,
                             reply_markup=types.ReplyKeyboardRemove())
            return
        if answer == u'Прервать запись.':
            text = "Запись на тренировку прервана. Если захотите записаться \
на тренировку, используйте команду /training."
            bot.send_message(message.from_user.id, text,
                             reply_markup=types.ReplyKeyboardRemove())
            return
        elif answer == u'Зарегистрировать ребенка.':
            msg = bot.send_message(message.from_user.id, "Начало регистрации",
                                   reply_markup=types.ReplyKeyboardRemove())
            registration_question(message)
            return
        elif answer == u'/restart':
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        children = children_list_request_by_id(message.from_user.id)
        if children is None:
            markup = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True)
            markup.add('Зарегистрировать ребенка.', 'Прервать запись.')
            text = 'В данный момент нет зарегистрированных пользователей.'
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, registration_time)
        else:
            markup = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True)
            for child in children:
                parts = child.split(',')
                child = ','.join(parts[:3])
                markup.add(child)
            if len(children) > 2:
                markup.add('Всех')
            markup.add('Зарегистрировать ребенка.')
            markup.add('Прервать запись.')
            text = "Кого Вы хотите записать на тренировку?"
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, registration_time,
                                           children=children)
    except Exception as e:
        bot.send_message(prog_id, f"Функция training_reg_question: {e}")


def registration_time(message, children=None):
    try:
        global markup_trainer_time
        answer = message.text
        if answer == u'/restart':
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        if children is not None:
            valid_choices = [', '.join(child.split(', ')[:3])
                             for child in children[:-1]] \
                                + ['Всех', 'Зарегистрировать ребенка.',
                                   'Прервать запись.', 'Начать сначала']
        else:
            valid_choices = ['Всех', 'Зарегистрировать ребенка.',
                             'Прервать запись.', 'Начать сначала']
        if answer not in valid_choices:
            markup = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True)
            markup.add('Начать сначала')
            markup.add('Прервать запись.')
            markup.add('Зарегистрировать ребенка.')
            msg = bot.send_message(message.from_user.id,
                                   'Не помню такого человека.',
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, registration_time)
            return
        if answer == 'Начать сначала':
            msg = bot.send_message(message.from_user.id,
                                   'Начинаем сначала',
                                   reply_markup=types.ReplyKeyboardRemove())
            training_reg_question(message)
            return
        if answer == 'Зарегистрировать ребенка.':
            msg = bot.send_message(message.from_user.id, "Начало регистрации",
                                   reply_markup=types.ReplyKeyboardRemove())
            registration_question(message)
            return
        elif answer == u'Прервать запись.':
            text = "Запись на тренировку прервана. Если захотите записаться \
на тренировку, используйте команду /training."
            bot.send_message(message.from_user.id, text,
                             reply_markup=types.ReplyKeyboardRemove())
            return
        training_schedule = training_schedule_request()

        if training_schedule == "Расписание в данный момент отсутствует.":
            bot.send_message(message.from_user.id, training_schedule,
                             reply_markup=types.ReplyKeyboardRemove())
        else:
            schedule = training_schedule.split('\n')
            markup_trainer_time = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True)
            for date in schedule[:-1]:
                date_info = date.split(', ')
                date_info = f"{date_info[0]} {date_info[1]} {date_info[2]} \
{date_info[3]} {date_info[4]}\n"
                markup_trainer_time.add(date_info)
            markup_trainer_time.add('Прервать запись.')
            text = "На какое время Вы хотите записаться?"
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=markup_trainer_time)
            bot.register_next_step_handler(msg, registration_finish,
                                           who=answer)
    except Exception as e:
        bot.send_message(prog_id, f"Функция registration_time: {e}")


def registration_finish(message, who):
    try:
        global markup_trainer_time
        who = who
        choosed_time = message.text
        if choosed_time == u'/restart':
            bot.send_message(message.from_user.id, "Бот перезапускается...",
                             reply_markup=types.ReplyKeyboardRemove())
            restart_bot(message)
            return
        time_list = choosed_time.split(' ')
        train_schedule = training_schedule_request().split('\n')
        valid_choices = [' '.join(one_time.split(', ')) for one_time in
                         train_schedule[:-1]] + ['Всех',
                                                 'Зарегистрировать ребенка.',
                                                 'Прервать запись.']
        if choosed_time not in valid_choices:
            training_schedule = training_schedule_request()
            schedule = training_schedule.split('\n')
            markup_trainer_time = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True)
            for date in schedule[:-1]:
                date_info = date.split(', ')
                date_info = f"{date_info[0]} {date_info[1]} {date_info[2]} \
{date_info[3]} {date_info[4]}\n"
                markup_trainer_time.add(date_info)
            markup_trainer_time.add('Прервать запись.')
            text = "Такого времени нет"
            msg = bot.send_message(message.from_user.id, text,
                                   reply_markup=markup_trainer_time)
            bot.register_next_step_handler(msg, registration_finish, who)
            return
        if choosed_time == 'Прервать запись.':
            text = "Запись на тренировку прервана. Если захотите записаться \
на тренировку, используйте команду /training."
            bot.send_message(message.from_user.id, text,
                             reply_markup=types.ReplyKeyboardRemove())
            return
        if who == u'Всех':
            children = children_list_request_by_id(message.from_user.id)
            for child in children[:-1]:
                child = child.split(', ')
                text = f"На тренировку записался {child[0]} {child[1]}, \
{child[2]}\nПредставитель: {child[3]}\n{choosed_time}"
                training_reg(message.from_user.id, child[0], child[1],
                             child[2], child[3], time_list[1].strip('()'),
                             time_list[2])
                bot.send_message(admin_id, text,
                                 reply_markup=types.ReplyKeyboardRemove())
                registration_message = f"Отлично! {child[0]} {child[1]} \
зарегистрирован(а) на тренировку. \nДень: {time_list[0]} \
                        ({time_list[1].strip('()')}), время: {time_list[2]}!"
                bot.send_message(message.from_user.id, registration_message,
                                 reply_markup=types.ReplyKeyboardRemove())
        else:
            child = who.split(', ')
            parent = children_parent_list_request(message.from_user.id,
                                                  child[0], child[1])
            text = f"На тренировку записался {child[0]} {child[1]}, \
{child[2]}\nПредставитель: {parent[0][0]}\n{choosed_time}"
            training_reg(message.from_user.id, child[0], child[1], child[2],
                         parent[0][0], time_list[1].strip('()'), time_list[2])
            bot.send_message(admin_id, text,
                             reply_markup=types.ReplyKeyboardRemove())
            registration_message = f"Отлично! {child[0]} {child[1]} \
зарегистрирован(а) на тренировку. \nДень: {time_list[0]} \
({time_list[1].strip('()')}), время: {time_list[2]}!"
            bot.send_message(message.from_user.id, registration_message,
                             reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        bot.send_message(prog_id, f"Функция registration_finish: {e}")

##############################################################################


# Запрос '/help'
@bot.message_handler(commands=['help'])
def help(message):
    try:
        text = '''/reg - Регистрация
/training - Запись на тренировку
/training_schedule - Расписание тренировок
/event_schedule - Расписание событий
/payment - Реквизиты для оплаты
/address - Адрес секции
/video - Видео'''
        bot.send_message(message.from_user.id, text,
                         reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        bot.send_message(prog_id, f"Функция help: {e}")


@bot.message_handler(commands=['payment'])
def payment_details(message):
    try:
        text = 'Реквизиты для оплаты появятся позже!'
        bot.send_message(message.from_user.id, text,
                         reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        bot.send_message(prog_id, f"Функция payment_details: {e}")

##############################################################################


# Запрос '/training_schedule'
@bot.message_handler(commands=['training_schedule'])
def training_schedule(message):
    try:
        training_schedule = training_schedule_request()
        if training_schedule == "Расписание в данный момент отсутствует":
            bot.send_message(message.from_user.id, training_schedule,
                             reply_markup=types.ReplyKeyboardRemove())
        else:
            schedule = training_schedule.split('\n')
            for date in schedule[:-1]:
                date_info = date.split(', ')
                date_info = f"{date_info[0]} {date_info[1]} \
{date_info[2][:5]} {date_info[3]} {date_info[4]}\n"
                bot.send_message(message.from_user.id, date_info,
                                 reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        bot.send_message(prog_id, f"Функция training_schedule: {e}")


##############################################################################

# Запрос '/event_schedule'
@bot.message_handler(commands=['event_schedule'])
def event_schedule(message):
    try:
        event_schedule = event_schedule_request()
        if event_schedule == "Событий в данный момент нет.":
            bot.send_message(message.from_user.id, event_schedule,
                             reply_markup=types.ReplyKeyboardRemove())
        else:
            schedule = event_schedule.split('\n')
            for date in schedule[:-1]:
                date_info = date.split(', ')
                date_info = f"""Событие: {date_info[0]}
Место: {date_info[1]}
Дата: {date_info[2]} - {date_info[3]}\n"""
                bot.send_message(message.from_user.id, date_info,
                                 reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        bot.send_message(prog_id, f"Функция event_schedule: {e}")


##############################################################################

# Запрос '/address'
@bot.message_handler(commands=['address'])
def address(message):
    try:
        text = 'Тренировки проходят по адресу:'
        bot.send_message(message.from_user.id, text,
                         reply_markup=types.ReplyKeyboardRemove())
        text = 'г. Москва, ул. Садовническая, 40/42'
        bot.send_message(message.from_user.id, text,
                         reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        bot.send_message(prog_id, f"Функция address: {e}")


##############################################################################

# Запрос '/video'
@bot.message_handler(commands=['video'])
def video(message):
    try:
        text = 'Ждём обновление. Ссылки на видео появятся позже!'
        bot.send_message(message.from_user.id, text,
                         reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        bot.send_message(prog_id, f"Функция video: {e}")

##############################################################################


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


# Сохранение состояния запросов
bot.enable_save_next_step_handlers(delay=1)
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
