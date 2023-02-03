import json
from functools import partial
from environs import Env
import redis

import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from vk_tools.keyboards import main_keyboard
from questions_module import collect_questions, get_random_quiz_question


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


def welcome(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        message='Добро пожаловать в QuizBot! Докажи, что ты - самый умный :)',
        keyboard=main_keyboard(),
        random_id=get_random_id()
    )


def send_question(event, vk_api, questions):
    db = get_database_connection()

    question_with_answer = get_random_quiz_question(questions)
    question = question_with_answer.get('question')
    answer = question_with_answer.get('answer')

    vk_api.messages.send(
        user_id=event.user_id,
        message=question,
        keyboard=main_keyboard(),
        random_id=get_random_id()
    )

    db.set(
        event.user_id,
        json.dumps({
            'question': question,
            'answer': answer
        })
    )


def check_answer(event, vk_api):
    db = get_database_connection()

    question_to_user = json.loads(db.get(event.user_id))
    if question_to_user:
        answer = question_to_user.get('answer').lower()
        if answer in event.text.lower():
            vk_api.messages.send(
                user_id=event.user_id,
                message='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».',
                keyboard=main_keyboard(),
                random_id=get_random_id()
            )
            db.getdel(event.user_id)

        else:
            vk_api.messages.send(
                user_id=event.user_id,
                message='Неправильно… Попробуешь ещё раз?',
                keyboard=main_keyboard(),
                random_id=get_random_id()
            )


def user_surrend(event, vk_api):
    db = get_database_connection()

    answer = json.loads(db.get(event.user_id)).get('answer')

    vk_api.messages.send(
        user_id=event.user_id,
        message=f'Правильный ответ:\n{answer}',
        keyboard=main_keyboard(),
        random_id=get_random_id()
    )
    send_chosen_question(event, vk_api)


if __name__ == "__main__":
    env = Env()
    env.read_env()

    files_dir = env('QUESTIONS_DIR')
    quiz_questions = collect_questions(files_dir)
    send_chosen_question = partial(send_question, questions=quiz_questions)

    database = None
    database = get_database_connection()

    vk_access_token = env('VK_ACCESS_TOKEN')
    vk_session = vk.VkApi(token=vk_access_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():

        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == 'Новый вопрос':
                send_chosen_question(event, vk_api)
            elif event.text == 'Сдаться':
                user_surrend(event, vk_api)
            elif event.text:
                try:
                    check_answer(event, vk_api)
                except:
                    welcome(event, vk_api)
