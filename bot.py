import telebot
import os
import requests
import csv
import boto3
import json

from xlrd import open_workbook
from services.goals import Goals
from services.matchers import Matchers
from dialogs.unrecognized import RecognitionService

token = os.environ['TELEGRAM_TOKEN']

s3 = boto3.client(
    service_name='s3',
    aws_access_key_id=os.environ['OBJECT_STORAGE_KEY'],
    aws_secret_access_key=os.environ['OBJECT_STORAGE_SECRET'],
    endpoint_url=os.environ['OBJECT_STORAGE_ENDPOINT'])

rates_bucket = os.environ['RATES_BUCKET']
pb_input_bucket = os.environ['PB_INPUT_BUCKET']
pb_raw_bucket = os.environ['PB_RAW_BUCKET']
alfa_raw_bucket = os.environ['ALFA_RAW_BUCKET']
cs_raw_bucket = os.environ['CS_RAW_BUCKET']
kb_raw_bucket = os.environ['KB_RAW_BUCKET']

goals_base_url = os.environ['GOALS_BASE_URL']
matchers_base_url = os.environ['MATCHERS_BASE_URL']

bot = telebot.TeleBot(token)
remove_markup = telebot.types.ReplyKeyboardRemove(selective=False)
goals = Goals(goals_base_url)
matchers = Matchers("http://10.8.0.1:9999/matcher/")

dialog_state = {}


def handle_error(message, subject):
    if subject == -1:
        bot.send_message(message.chat.id, 'Щось поламалося((((((!')
        del dialog_state[message.from_user.id]

    return subject


def pb_xls_to_csv(file):
    wb = open_workbook(file)
    sh = wb.sheet_by_index(0)
    csv_key = file.replace('.xls', '.csv')
    with open(csv_key, 'w', newline="") as f:
        c = csv.writer(f)
        for i in range(1, sh.nrows):
            c.writerow([cell.value for cell in sh.row(i)])


def copy_to_bucket(file, bucket):
    s3.upload_file(Bucket=bucket, Key=file, Filename=file)


def handle_file(message):
    file_info = bot.get_file(message.document.file_id)
    file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(token, file_info.file_path))
    file_path = message.document.file_name
    open(file_path, 'wb').write(file.content)
    if message.document.mime_type == 'application/vnd.ms-excel':
        copy_to_bucket(file_path, pb_input_bucket)
        pb_xls_to_csv(file_path)
        copy_to_bucket(file_path.replace('.xls', '.csv'), pb_raw_bucket)
        os.unlink(file_path)
        os.unlink(file_path.replace('.xls', '.csv'))
    elif message.document.mime_type == 'text/csv':
        if message.document.file_name == 'rates.csv':
            copy_to_bucket(file_path, rates_bucket)
        elif message.document.file_name.startswith('cs '):
            copy_to_bucket(file_path, cs_raw_bucket)
        elif message.document.file_name.startswith('kb '):
            copy_to_bucket(file_path, kb_raw_bucket)
        elif message.document.file_name.startswith('alfa '):
            copy_to_bucket(file_path, alfa_raw_bucket)
        else:
            bot.send_message(message.chat.id, 'Нiчого не зрозумiв!\n%s' % message.text)


def await_category_input(message):
    bot.send_message(message.chat.id, 'Дякую! Який саме лiмiт?', reply_markup=remove_markup)
    dialog_state[message.from_user.id] = {
        'state': 'LIMIT_AWAITING_VALUE_INPUT',
        'category': message.text,
        'next': await_limit_value_input
    }


def await_limit_value_input(message):
    bot.send_message(message.chat.id, 'Чудово! Встановлюю лiмiт.')
    limit = goals.set_limit({'category': dialog_state[message.from_user.id]['category'],
                                 'limit': message.text,
                                 'family': 'zagoruiko'})
    del dialog_state[message.from_user.id]
    if handle_error(message, limit) == -1:
        return
    bot.send_message(message.chat.id, 'Поточнi лiмiти')
    limits = goals.get_limits('zagoruiko')
    if handle_error(message, limits) == -1:
        return

    maxlen=0
    for limit in limits:
        if len(limit['category']) > maxlen:
            maxlen = len(limit['category'])

    for limit in limits:
        if len(limit['category']) < maxlen:
            for i in range(0, maxlen - len(limit['category'])):
                limit['category'] += ' '

    limitstr = '```\n'
    for limit in limits:
        limitstr += "%s\t%s\n" % (limit['category'], limit['limit'])

    bot.send_message(message.chat.id, limitstr + '```', parse_mode='Markdown')


def handle_family(message):
    r = requests.post('%sevent/bot/family' % goals_base_url,
                      json.dumps({'chatId': message.chat.id,
                                  'userId': message.from_user.id,
                                  'userName': "%s %s" % (message.from_user.first_name,
                                                         message.from_user.last_name),
                                  'family': message.text}),
                      headers={"Content-type": "application/json"})

    if handle_error(message, (-1 if r.status_code != 200 else 1)) == -1:
        return

    response = r.json()
    if response['botStartState'] == 'REGISTERED':
        bot.send_message(message.chat.id, 'Шановний, ти тепер зiриганий!')
    elif response['botStartState'] == 'ALREADY_REGISTERED':
        bot.send_message(message.chat.id, 'Шановний, ти вже був зiриганий!')
    else:
        bot.send_message(message.chat.id, 'Нiчого не зрозумiв!\n%s' % message.text)
    del dialog_state[message.from_user.id]


@bot.message_handler(commands=['start'])
def start_message(message):
    if message.from_user.id != 334401978 and message.from_user.id != 359732226:
        bot.send_message(message.chat.id, 'Не готовий з вами спiвпрацювати!!\n')
        del dialog_state[message.from_user.id]
        return
    r = requests.post('%sevent/bot/start' % goals_base_url,
                      json.dumps({'chatId': message.chat.id,
                                  'userId': message.from_user.id,
                                  'userName': "%s %s" % (message.from_user.first_name,
                                                         message.from_user.last_name)}),
                      headers={"Content-type": "application/json"})

    if handle_error(message, (-1 if r.status_code != 200 else 1)) == -1:
        return

    response = r.json()
    if response['botStartState'] == 'FAMILY_REQUIRED':
        dialog_state[message.from_user.id] = {
            'state': response['botStartState'],
            'next': handle_family
        }
        bot.send_message(message.chat.id, 'Шановний, а тепер уважно напиши назву своєї родини саме так як його '
                                          'напишуть інщі мешканці твого домогосподарства!')
    elif response['botStartState'] == 'ALREADY_REGISTERED':
        bot.send_message(message.chat.id, 'Шановний, ти вже був зiриганий!')


@bot.message_handler(commands=['limits'])
def start_message(message):
    if message.from_user.id != 334401978 and message.from_user.id != 359732226:
        bot.send_message(message.chat.id, 'Не готовий з вами спiвпрацювати!!\n')
        del dialog_state[message.from_user.id]
        return
    bot.send_message(message.chat.id, 'Шановний, надсилаю запит на репорт!')

    bot.send_message(message.chat.id, 'Поточний стан')
    limits = goals.get_limit_report('zagoruiko')
    if handle_error(message, limits) == -1:
        return

    monthly_limit = goals.get_monthly_limit_status('zagoruiko')
    if handle_error(message, monthly_limit) == -1:
        return

    maxlen=0
    for limit in limits:
        if len(limit['category']) > maxlen:
            maxlen = len(limit['category'])

    for limit in limits:
        if len(limit['category']) < maxlen:
            for i in range(0, maxlen - len(limit['category'])):
                limit['category'] += ' '

    limitstr = '```\nКатегорiя\tЛiмiт/Витрати (%)\n'
    for limit in limits:
        limitstr += "%s\t%s/%s (%s%%)\n" \
                    % (limit['category'], limit['limit'], limit['amount'], limit['percent'])

    limitstr += "\nЗагальний лiмiт\t%s/%s (%s%%)\n" \
                % (monthly_limit['limit'], monthly_limit['amount'], monthly_limit['percent'])

    bot.send_message(message.chat.id, limitstr + '```', parse_mode='Markdown')


@bot.message_handler(commands=['report'])
def start_message(message):
    if message.from_user.id != 334401978 and message.from_user.id != 359732226:
        bot.send_message(message.chat.id, 'Не готовий з вами спiвпрацювати!!\n')
        del dialog_state[message.from_user.id]
        return
    bot.send_message(message.chat.id, 'Шановний, надсилаю запит на репорт!')
    r = requests.post('%sevent/bot/report' % goals_base_url,
                      json.dumps({'chatId': message.chat.id,
                                  'userId': message.from_user.id,
                                  'userName': "%s %s" % (message.from_user.first_name,
                                                         message.from_user.last_name)}),
                      headers={"Content-type": "application/json"})

    if handle_error(message, (-1 if r.status_code != 200 else 1)) == -1:
        return


@bot.message_handler(commands=['help'])
def help_message(message):
    if message.from_user.id != 334401978 and message.from_user.id != 359732226:
        bot.send_message(message.chat.id, 'Не готовий з вами спiвпрацювати!!\n')
        del dialog_state[message.from_user.id]
        return
    bot.send_message(message.chat.id, """
/help - Допомога або Перемога
/start - Розпочати реєстрацію
/report - Шалений репорт на поточний місяць
/limit - Створити новий або змінити існуючий ліміт на поточний місяць
/limits - Стан лімітів на поточний місяць
/define - Розпочати роботу з неразпзнаними транзакцiями
    """)


@bot.message_handler(commands=['limit'])
def set_limit_command(message):
    if message.from_user.id != 334401978 and message.from_user.id != 359732226:
        bot.send_message(message.chat.id, 'Не готовий з вами спiвпрацювати!!\n')
        del dialog_state[message.from_user.id]
        return
    categories = matchers.get_categories()
    if handle_error(message, categories) == -1:
        return

    keyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=3)

    buttons = []

    for tag in categories:
        buttons.append(telebot.types.KeyboardButton(tag['tag']))

    keyboard.add(*buttons)

    bot.send_message(message.chat.id, 'Шановний, бажаєш встановити ліміт? Тоді вкажи категорію!', reply_markup=keyboard)
    dialog_state[message.from_user.id] = {
        'state': 'LIMIT_AWAITING_CATEGORY_INPUT',
        'next': await_category_input
    }


@bot.message_handler(commands=['define'])
def start_define(message):
    if message.from_user.id != 334401978 and message.from_user.id != 359732226:
        bot.send_message(message.chat.id, 'Не готовий з вами спiвпрацювати!!\n')
        del dialog_state[message.from_user.id]
        return
    service = RecognitionService(matchers, bot, message.from_user.id)
    dialog_state[message.from_user.id] = {
        'state': 'DEFINE',
        'service': service,
        'next': service.next
    }


@bot.message_handler(content_types=['document'])
def file_message(message):
    if message.from_user.id != 334401978 and message.from_user.id != 359732226:
        bot.send_message(message.chat.id, 'Не готовий з вами спiвпрацювати!!\n')
        del dialog_state[message.from_user.id]
        return
    bot.send_message(message.chat.id, 'Завантажую файл!')
    handle_file(message)
    print(message)


@bot.message_handler(content_types=['text'])
def text_message(message):
    if message.from_user.id != 334401978 and message.from_user.id != 359732226:
        bot.send_message(message.chat.id, 'Не готовий з вами спiвпрацювати!!\n')
        del dialog_state[message.from_user.id]
        return
    if message.from_user.id in dialog_state:
        result = dialog_state[message.from_user.id]['next'](message)
        if result == 2:
            dialog_state[message.from_user.id]
        elif result == -1:
            handle_error(message, result)

    else:
        bot.send_message(message.chat.id, 'Нiчого не зрозумiв!\n%s' % message.text)
    print(message)


bot.polling()
