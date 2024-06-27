# 0 9 * * * /Users/artem_ursekov/Desktop/TG/tg_bot/bin/python /Users/artem_ursekov/Desktop/TG/TG_alarm_training.py


import telebot
from datetime import datetime
import psycopg2
import datetime
import random
import requests
from dotenv import load_dotenv
import os

load_dotenv()

# Данные для Telegram
token = os.getenv('MAIN_BOT_TOKEN')
prog_id = os.getenv('PROG_ID')
bot = telebot.TeleBot(token)

# Устанавливаем таймаут для всех запросов
requests.adapters.DEFAULT_RETRIES = 5  # Количество попыток
requests.adapters.TIMEOUT = 60  # Таймаут подключения в секундах

# Данные для БД
dbname = os.getenv('DATABASE_NAME')
user = os.getenv('DATABASE_USER')
password = os.getenv('DATABASE_PASSWORD')
host = "localhost"
port = "5432"


def training_today():
    # Соединение с базой данных
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

        cursor = conn.cursor()

        check_query = f"SELECT * FROM training_schedule \
WHERE date = '{datetime.date.today()}'"
        cursor.execute(check_query)
        training = cursor.fetchall()
        conn.commit()
        cursor.close()
        conn.close()
        return training
    except Exception as e:
        bot.send_message(prog_id, f"Функция training_today: {e}")


def training_message():
    try:
        trainings = training_today()
        today = datetime.date.today()
        if trainings:
            for training in trainings:
                # Соединение с базой данных
                conn = psycopg2.connect(
                    dbname=dbname,
                    user=user,
                    password=password,
                    host=host,
                    port=port
                    )

                time = str(training[1])[:5]
                cursor = conn.cursor()
                check_query = f"SELECT * FROM clients_training \
WHERE date = '{today}' AND time = '{time}'"
                cursor.execute(check_query)
                clients_one = cursor.fetchall()
                for client in clients_one:
                    train_time = client[7][:5]
                    responses = [
                        f'Приветствую, как настроение? \
Готов сегодня показать на что ты способен? Сегодня в {train_time} не забудь!',
                        f'Доброе утро! Тренер ждет тебя, Чемпион! \
Сегодня в {train_time}, будь готов!',
                        f'Тренировка сегодня в {train_time}, не забудь форму!',
                        f'Как себя чувствуешь? Сегодня отличный день для \
тренировки! Она состоится сегодня в {train_time}!',
                        f'Привет, {client[2]}, хочешь стать лучше? \
Сегодня в {train_time} у тебя будет шанс.']
                    invite = random.choice(responses)
                    bot.send_message(client[1], invite)

                check_query = f"SELECT * FROM training_subscription \
WHERE date_start <= '{today}' and date_end >= '{today}'"
                cursor.execute(check_query)
                clients_subscription = cursor.fetchall()

                for client in clients_subscription:
                    train_time = str(training[1])[:5]
                    responses = [
                        f'Приветствую, как настроение? \
Готов сегодня показать на что ты способен? Сегодня в {train_time}, не забудь!',
                        f'Доброе утро! Тренер ждет тебя, Чемпион! \
Сегодня в {train_time}, будь готов!',
                        f'Тренировка сегодня в {train_time}, не забудь форму!',
                        f'Как себя чувствуешь? Сегодня отличный день для \
тренировки! Она состоится сегодня в {train_time}!',
                        f'Привет, {client[2]}, хочешь стать лучше? \
Сегодня в {train_time} у тебя будет шанс.']
                    invite = random.choice(responses)
                    bot.send_message(client[1], invite)

            conn.commit()
            cursor.close()
            conn.close()
    except Exception as e:
        bot.send_message(prog_id, f"Функция training_message: {e}")


def main():
    training_message()


if __name__ == "__main__":
    main()
