import telebot

def create_one_time_keyboard(items):
    keyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=3)

    buttons = []
    for item in items:
        buttons.append(telebot.types.KeyboardButton(item))

    keyboard.add(*buttons)
    return keyboard
