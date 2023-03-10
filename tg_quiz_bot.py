import logging
import json
from functools import partial

import redis
from environs import Env
from telegram.ext import (CommandHandler, Filters,
                          MessageHandler, Updater)

from telegram_tools.keyboards import main_keyboard
from questions_module import collect_questions, get_random_quiz_question

logger = logging.getLogger(__name__)


def error(update, context):
    logger.warning(f'Bot caused error {context.error}')


def start(update, context):
    chat_id = update.message.chat_id

    context.bot.send_message(
        chat_id=chat_id,
        text='Добро пожаловать в QuizBot!',
        reply_markup=main_keyboard()
    )


def handle_new_question_request(update, context, questions, db):
    chat_id = update.message.chat_id

    question_with_answer = get_random_quiz_question(questions)
    question = question_with_answer.get('question')
    answer = question_with_answer.get('answer')

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


def handle_solution_attempt(update, context, db):
    chat_id = update.message.chat_id
    message_text = update.message.text

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


def handle_surrender(update, context, db):
    chat_id = update.message.chat_id

    answer = json.loads(db.get(chat_id)).get('answer')

    context.bot.send_message(
        chat_id=chat_id,
        text=f'Правильный ответ:\n{answer}'
    )
    handle_chosen_question_request(update, context)


if __name__ == '__main__':
    env = Env()
    env.read_env()

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    redis_host = env('REDiS_HOST')
    redis_port = env('REDIS_PORT')
    redis_password = env('REDIS_PASSWORD')
    db = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        decode_responses=True,
    )

    files_dir = env('QUESTIONS_DIR')
    quiz_questions = collect_questions(files_dir)
    handle_chosen_question_request = partial(handle_new_question_request, questions=quiz_questions, db=db)
    handle_surrender = partial(handle_surrender, db=db)
    handle_solution_attempt = partial(handle_solution_attempt, db=db)

    tg_token = env('TG_TOKEN')
    updater = Updater(tg_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.regex('Новый вопрос'), handle_chosen_question_request))
    dispatcher.add_handler(MessageHandler(Filters.regex('Сдаться'), handle_surrender))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_solution_attempt))

    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()
