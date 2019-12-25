import telebot
import dialogs

class RecognitionService(object):
    def __init__(self, matchers, bot, user_id):
        self.providers = {
            'SRC_PRIVAT_BANK': 'pb',
            'SRC_ALFA_BANK': 'alfa'
        }
        self.selected_tags = []
        self.bot = bot
        self.user_id = user_id
        self.selected_bank = ''
        self.matchers = matchers
        self.counter = 0
        self.status = 'STARTED'
        self.current_record = {}
        self.select_bank()

    def next(self, message):
        if self.status == 'BANK_SELECTED':
            return self.bank_selected(message)
        elif self.status == 'CATEGORY_SELECTED':
            return self.category_selected(message)
        return -1

    def bank_selected(self, message):
        return self.bank_selected_replay(message.text)

    def bank_selected_replay(self, bank):
        self.selected_bank = bank
        self.current_record = self.matchers.get_unrecognized(bank, self.counter)
        if self.current_record == -1:
            return -1

        if self.current_record is None:
            self.bot.send_message(self.user_id, 'Усе гаразд, я знаю про всi витрати!')
            return 2

        self.bot.send_message(self.user_id, """
Обери основну категорiю для
```%s```
(%s разiв на суму %s)
    """ % (self.current_record['description'],
           self.current_record['count'],
           self.current_record['amount']), parse_mode='Markdown')
        categories = self.matchers.get_categories()
        if categories == -1:
            return -1

        keyboard = dialogs.create_one_time_keyboard([tag['tag'] for tag in categories])

        self.bot.send_message(self.user_id, 'Вкажи категорію',
                              parse_mode='Markdown', reply_markup=keyboard)
        self.status = 'CATEGORY_SELECTED'
        return 1

    def select_bank(self):
        keyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2)
        buttons = [telebot.types.KeyboardButton('SRC_PRIVAT_BANK'),
                   telebot.types.KeyboardButton('SRC_ALFA_BANK')]
        keyboard.add(*buttons)
        self.bot.send_message(self.user_id, 'Обери провайдера:',
                              parse_mode='Markdown', reply_markup=keyboard)

        self.status = 'BANK_SELECTED'
        return 1

    def category_selected(self, message):
        if message.text == '-' or message.text.lower() == 'це все':
            tags = self.matchers.add_matcher(self.selected_tags, self.providers[self.selected_bank], 'EQUAL', self.current_record['description'])
            if tags == -1:
                return -1
            remove_markup = telebot.types.ReplyKeyboardRemove(selective=False)
            self.bot.send_message(self.user_id, 'Записав!', reply_markup=remove_markup)
            self.counter += 1
            return self.bank_selected_replay(self.selected_bank)

        self.selected_tags.append(message.text.upper())
        self.bot.send_message(self.user_id, 'Готово!')

        tags = self.matchers.get_suggestions('')
        if tags == -1:
            return -1

        keyboard = dialogs.create_one_time_keyboard(['Це все'] + [tag for tag in tags])

        self.bot.send_message(self.user_id, """
Обери якийсь тег або напиши "-" щоб закiнчити з тегами
```%s```
(%s разiв на суму %s)
    """ % (self.current_record['description'],
           self.current_record['count'],
           self.current_record['amount']), parse_mode='Markdown', reply_markup=keyboard)

        self.status = 'CATEGORY_SELECTED'
        return 1
