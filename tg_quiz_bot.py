import logging
import json
import enum
from functools import partial

from environs import Env
import redis
from telegram.ext import (CommandHandler, Filters,
                          MessageHandler, ConversationHandler, Updater)

from telegram_tools.keyboards import main_keyboard
from questions_module import collect_questions, get_random_question

@enum.unique
class States(enum.Enum):
    CHOOSING = 1


def get_database_connection():
    global database
    if database is None:
        database = redis.Redis(
            host=env('REDiS_HOST'),
            port=env('REDIS_PORT'),
            password=env('REDIS_PASSWORD'),
            decode_responses=True,
        )
    return database


def error(update, context):
    logger.warning(f'Bot caused error {context.error}')


def start(update, context):
    chat_id = update.message.chat_id

    context.bot.send_message(
        chat_id=chat_id,
        text='Добро пожаловать в QuizBot!',
        reply_markup=main_keyboard()
    )

    return CHOOSING


def handle_new_question_request(update, context, questions):
    chat_id = update.message.chat_id
    db = get_database_connection()

    question, answer = get_random_question(questions)
    context.bot.send_message(
        chat_id=chat_id,
        text=question,
        reply_markup=main_keyboard()
    )

    db.set(
        chat_id,
        json.dumps({
            'question': question,
            'answer': answer
        })
    )

    return CHOOSING


def handle_solution_attempt(update, context):
    chat_id = update.message.chat_id
    message_text = update.message.text
    db = get_database_connection()


    question_to_user = json.loads(db.get(chat_id))
    if question_to_user:
        answer = question_to_user.get('answer').lower()
        if answer in message_text.lower():
            context.bot.send_message(
                chat_id=chat_id,
                text='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».',
                reply_markup=main_keyboard()
            )
            db.getdel(chat_id)

        else:
            context.bot.send_message(
                chat_id=chat_id,
                text='Неправильно… Попробуешь ещё раз?',
                reply_markup=main_keyboard()
            )
    return CHOOSING


def handle_surrender(update, context):
    chat_id = update.message.chat_id
    db = get_database_connection()

    answer = json.loads(db.get(chat_id)).get('answer')

    context.bot.send_message(
        chat_id=chat_id,
        text=f'Правильный ответ:\n{answer}'
    )
    handle_chosen_question_request(update, context)


if __name__ == '__main__':
    env = Env()
    env.read_env()

    tg_token = env('TG_TOKEN')

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    files_dir = env('QUESTIONS_DIR')
    quiz_questions = collect_questions(files_dir)
    handle_chosen_question_request = partial(handle_new_question_request, questions=quiz_questions)

    database = None
    database = get_database_connection()


    CHOOSING = States.CHOOSING
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOOSING: [
                MessageHandler(Filters.regex('Новый вопрос'),
                             handle_chosen_question_request
                             ),
                MessageHandler(Filters.regex('Сдаться'),
                               handle_surrender
                               ),
                MessageHandler(Filters.text,
                               handle_solution_attempt,
                               ),
            ],
        },

        fallbacks=[]
    )

    updater = Updater(tg_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()
