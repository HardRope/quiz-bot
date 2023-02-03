from telegram import ReplyKeyboardMarkup

def main_keyboard():
    keyboard_buttons = [
        ['Новый вопрос', 'Сдаться'],
        ['Мой счёт']
    ]
    return ReplyKeyboardMarkup(keyboard_buttons)
