import datetime
import psycopg2
import telebot
from dotenv import load_dotenv
import os


load_dotenv()

# Данные для Telegram
token = os.getenv('MAIN_BOT_TOKEN')
prog_id = os.getenv('PROG_ID')
bot = telebot.TeleBot(token)

# Данные для БД
dbname = os.getenv('DATABASE_NAME')
user = os.getenv('DATABASE_USER')
password = os.getenv('DATABASE_PASSWORD')
host = "localhost"
port = "5432"


def validate_date(date_text):
    try:
        datetime.datetime.strptime(date_text, '%d.%m.%Y')
        return True
    except ValueError:
        return False


# Проверка времени
def validate_time(time_text):
    try:
        datetime.datetime.strptime(time_text, '%H:%M')
        return True
    except ValueError:
        return False


def children_parent_list_request(chat_id, child_name, child_surname):
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
        # SQL-запрос для получения данных о представителях
        select_table_query = f"""
        SELECT parent_name
        FROM football_clients
        WHERE chat_id = '{chat_id}' and child_name = '{child_name}' \
and child_surname = '{child_surname}'
        """

        cursor.execute(select_table_query)

        # Получение результата
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return rows
    except Exception as e:
        bot.send_message(prog_id, f"Функция children_parent_list_request: {e}")


def children_list_request_by_id(chat_id):
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
        # SQL-запрос для получения данных о клиентах
        select_table_query = f"""
        SELECT child_name, child_surname, child_birth_date, parent_name
        FROM football_clients
        WHERE chat_id = '{chat_id}'
        """
        cursor.execute(select_table_query)
        # Получение результата
        rows = cursor.fetchall()

        # Формируем сообщение с результатами
        if rows:
            result_message = ""
            for row in rows:
                child_name, child_surname, child_birth_date, parent_name = row
                result_message += f"{child_name}, {child_surname}, \
{child_birth_date}, {parent_name}\n"

        # Закрываем курсор и соединение
        cursor.close()
        conn.close()

        return result_message.split('\n')
    except Exception as e:
        bot.send_message(prog_id, f"Функция children_list_request_by_id: {e}")


def children_list_request_by_name(child_name, child_surname):
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
        # SQL-запрос для получения данных о клиентах
        select_table_query = f"""
        SELECT id, chat_id, child_name, child_surname, \
child_birth_date, parent_name
        FROM football_clients
        WHERE child_name = '{child_name.replace(',', '，')}' AND child_surname = '{child_surname.replace(',', '，')}'
        """

        cursor.execute(select_table_query)

        # Получение результата
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

        # Закрываем курсор и соединение
        cursor.close()
        conn.close()

        return result_message.split('\n')
    except Exception as e:
        bot.send_message(prog_id, f"Функция children_list_request_by_name: {e}")


# Получение данных о тренировках
def training_schedule_request():
    try:
        # Соединение с базой данных
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

        cursor = conn.cursor()

        select_schedule_query = f"""
        SELECT date, time, trainer
        FROM training_schedule
        WHERE date >= '{datetime.date.today()}'
        ORDER BY date, time ASC
        """

        cursor.execute(select_schedule_query)

        # Получение результата
        rows = cursor.fetchall()

        days = ["Понедельник", "Вторник", "Среда", "Четверг",
                "Пятница", "Суббота", "Воскресенье"]
        if rows:
            result_message = ""
            for row in rows:
                date, time, trainer = row
                day_of_week = date.weekday()
                day_name = days[day_of_week]
                result_message += f"{day_name.title()}, ({date}), \
{str(time)[:5]}, тренер:, {trainer.title()}\n"
        else:
            result_message = "Расписание в данный момент отсутствует."

        # Закрываем курсор и соединение
        cursor.close()
        conn.close()

        return result_message
    except Exception as e:
        bot.send_message(prog_id, f"Функция training_schedule_request: {e}")


def training_reg(chat_id, child_name, child_surname,
                 child_birth_date, parent_name, date, time):
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

        # SQL-запрос для создания таблицы с проверкой ее существования
        create_table_query = """
            SET datestyle = 'ISO, DMY';

            CREATE TABLE IF NOT EXISTS clients_training (
                id SERIAL PRIMARY KEY
                ,chat_id VARCHAR(100) NOT NULL
                ,child_name VARCHAR(100) NOT NULL
                ,child_surname VARCHAR(100) NOT NULL
                ,child_birth_date VARCHAR(20) NOT NULL
                ,parent_name VARCHAR(100) NOT NULL
                ,date DATE NOT NULL
                ,time VARCHAR(20) NOT NULL
            );
            """
        cursor.execute(create_table_query)

        insert_query = """
            INSERT INTO clients_training (chat_id, child_name, \
child_surname, child_birth_date, parent_name, date, time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        # Данные для вставки
        data_to_insert = (chat_id, child_name, child_surname,
                          child_birth_date, parent_name, date, time)

        # Выполнение вставки данных
        cursor.execute(insert_query, data_to_insert)

        conn.commit()

        cursor.close()
        conn.close()
    except Exception as e:
        bot.send_message(prog_id, f"Функция training_reg: {e}")


# Получение данных о тренировках
def event_schedule_request():
    try:
        # Соединение с базой данных
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

        cursor = conn.cursor()

        select_schedule_query = f"""
        SELECT event_name, event_place, event_date_start, event_date_end
        FROM event_schedule
        WHERE event_date_end >= '{datetime.date.today()}'
        ORDER BY event_date_end ASC
        """

        cursor.execute(select_schedule_query)

        # Получение результата
        rows = cursor.fetchall()

        if rows:
            result_message = ""
            for row in rows:
                name, place, date_start, date_end = row
                result_message += f"{name.title()}, {place.capitalize()}, \
{date_start}, {date_end}\n"
        else:
            result_message = "Событий в данный момент нет."

        # Закрываем курсор и соединение
        cursor.close()
        conn.close()

        return result_message
    except Exception as e:
        bot.send_message(prog_id, f"Функция event_schedule_request: {e}")
