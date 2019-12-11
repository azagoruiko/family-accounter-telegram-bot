import telebot
import os
import requests
import csv
import boto3
import json

from xlrd import open_workbook

token = os.environ['TELEGRAM_TOKEN']

s3 = boto3.client(
    service_name='s3',
    aws_access_key_id=os.environ['OBJECT_STORAGE_KEY'],
    aws_secret_access_key=os.environ['OBJECT_STORAGE_SECRET'],
    endpoint_url=os.environ['OBJECT_STORAGE_ENDPOINT'])

bot = telebot.TeleBot(token)

rates_bucket = os.environ['RATES_BUCKET']
pb_input_bucket = os.environ['PB_INPUT_BUCKET']
pb_raw_bucket = os.environ['PB_RAW_BUCKET']
alfa_raw_bucket = os.environ['ALFA_RAW_BUCKET']

goals_base_url = os.environ['GOALS_BASE_URL']

dialog_state = {}


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
        else:
            copy_to_bucket(file_path, alfa_raw_bucket)


def handle_family(message):
    r = requests.post('%sevent/bot/family' % goals_base_url,
                      json.dumps({'chatId': message.chat.id,
                                  'userId': message.from_user.id,
                                  'userName': "%s %s" % (message.from_user.first_name,
                                                         message.from_user.last_name),
                                  'family': message.text}),
                      headers={"Content-type": "application/json"})

    if r.status_code != 200:
        bot.send_message(message.chat.id, 'Щось поламалося((((((!')

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
    r = requests.post('%sevent/bot/start' % goals_base_url,
                      json.dumps({'chatId': message.chat.id,
                                  'userId': message.from_user.id,
                                  'userName': "%s %s" % (message.from_user.first_name,
                                                            message.from_user.last_name)}),
                      headers={"Content-type": "application/json"})

    if r.status_code != 200:
        bot.send_message(message.chat.id, 'Щось поламалося((((((!')

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


@bot.message_handler(commands=['report'])
def start_message(message):
    bot.send_message(message.chat.id, 'Шановний, надсилаю запит на репорт!')
    r = requests.post('%sevent/bot/report' % goals_base_url,
                      json.dumps({'chatId': message.chat.id,
                                  'userId': message.from_user.id,
                                  'userName': "%s %s" % (message.from_user.first_name,
                                                         message.from_user.last_name)}),
                      headers={"Content-type": "application/json"})

    if r.status_code != 200:
        bot.send_message(message.chat.id, 'Щось поламалося((((((!')


@bot.message_handler(content_types=['document'])
def file_message(message):
    bot.send_message(message.chat.id, 'Завантажую файл!')
    handle_file(message)
    print(message)


@bot.message_handler(content_types=['text'])
def text_message(message):
    if message.from_user.id in dialog_state:
        dialog_state[message.from_user.id]['next'](message)
    else:
        bot.send_message(message.chat.id, 'Нiчого не зрозумiв!\n%s' % message.text)
    print(message)


bot.polling()
