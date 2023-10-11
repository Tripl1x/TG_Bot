import os
import telebot
from telebot import types
import sqlite3
import bcrypt
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
SQL_DIR = 'storage.sql'
user_id = 703835441

bot = telebot.TeleBot(TOKEN)

site = None
login = None


class MySQL:
    def __init__(self):
        self._connect = sqlite3.connect(SQL_DIR)
        self._cursor = self._connect.cursor()
        self._create = self._cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
        id int auto_increment PRIMARY KEY,
        site varchar(50),
        login varchar(20),
        password varchar(20)
        )
        """)
        self._close = self._connect.close()


@bot.message_handler(func=lambda message: message.chat.id != user_id)
def access(message):
    bot.send_message(message.chat.id, 'Доступ запрещен')


@bot.message_handler(commands=['start'])
def start(message):
    MySQL()
    bot.send_message(message.chat.id, 'Введите пароль')
    bot.register_next_step_handler(message, check_passwd)


def check_passwd(message):
    user_input = message.text.strip()
    passwd = os.getenv("PASSWORD")
    salt = os.getenv('SALT')
    encoded = user_input.encode()
    hashed = bcrypt.hashpw(encoded, salt.encode())
    decoded = str(hashed)
    if passwd == decoded:
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Добавить аккаунт', callback_data='add')
        btn2 = types.InlineKeyboardButton('Очистить', callback_data='clear')
        markup.row(btn1, btn2)
        btn3 = types.InlineKeyboardButton('Список аккаунтов', callback_data='accounts')
        markup.row(btn3)
        bot.reply_to(message, 'Доступ разрешен', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Доступ запрещен')


@bot.callback_query_handler(func=lambda callback: True)
def callback_accounts(callback):
    if callback.data == 'accounts':
        with sqlite3.connect(SQL_DIR) as connect:
            cursos = connect.cursor()
            cursos.execute('SELECT * FROM accounts')
            accounts = cursos.fetchall()
            result = ''
            for i in accounts:
                result += f'Сайт: {i[1]}, Логин: {i[2]}, Пароль: {i[3]}\n'
            bot.send_message(callback.message.chat.id, result)
    if callback.data == 'add':
        bot.send_message(callback.message.chat.id, 'для какого сайта добавить учетные данные?')
        bot.register_next_step_handler(callback.message, user_site)
    if callback.data == 'clear':
        bot.delete_message(callback.message.chat.id, callback.message.message_id - 1)



def user_site(message):
    global site
    site = message.text.strip()
    bot.send_message(message.chat.id, 'Введите логин')
    bot.register_next_step_handler(message, user_login)


def user_login(message):
    global login
    login = message.text.strip()
    bot.send_message(message.chat.id, 'Введите пароль')
    bot.register_next_step_handler(message, user_pass)


def user_pass(message):
    password = message.text.strip()
    with sqlite3.connect(SQL_DIR) as connect:
        cursor = connect.cursor()
        cursor.execute(
            "INSERT INTO accounts (site, login, password) VALUES ('%s', '%s', '%s')" % (site, login, password))
        connect.commit()


@bot.message_handler(func=lambda message: message.text in ['привет', 'hi'])
def _hi(message):
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name} {message.from_user.last_name}')


@bot.message_handler(func=lambda message: message.text == 'id')
def _id(message):
    bot.reply_to(message, f'ID: {message.from_user.id}')


bot.polling(none_stop=True)
