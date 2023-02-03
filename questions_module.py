import random
import glob


def parse_file(file_path):
    with open(file_path, 'r', encoding='KOI8-R') as quiz_file:
        quiz_collection = quiz_file.read()
        questions_collection = quiz_collection.split('\n\nВопрос ')[1:]

        questions_blocks = [question.split('\n\n') for question in questions_collection]

        file_questions = []
        for block in questions_blocks:
            question = block[0].split('\n', maxsplit=1)[1]
            answer_long = block[1].split('\n', maxsplit=1)[1]
            answer_short = answer_long.split('.', maxsplit=1)[0]
            file_questions.append({'question': question, 'answer': answer_short})

    return file_questions


def collect_questions(files_dir):
    files_paths = glob.glob(f'{files_dir}/*.txt')
    questions = []
    for path in files_paths:
        file_questions = parse_file(path)
        questions.extend(file_questions)

    return questions


def get_random_question(collection):
    question_count = len(collection)
    random_question_index = random.randint(0, question_count + 1)
    print(collection[random_question_index])
    return collection[random_question_index].get('question'), collection[random_question_index].get('answer')
