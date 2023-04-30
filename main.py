import asyncio
import sqlite3
from datetime import date
import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
from tok_en import TOKEN


PROXY_URL = "http://proxy.server:3128"
DB_PATH_USER = 'user_db.db'
DB_PATH_QUESTIONS = 'questions1.db'
API_TOKEN = TOKEN
loop = asyncio.get_event_loop()

bot = Bot(token=TOKEN, loop=loop, proxy=PROXY_URL)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class User(StatesGroup):
    menu = State()
    play = State()
    answer = State()
    end_ans = State()
    wast_ans = State()
    question = State()
    end_question = State()
    new_admin = State()
    kick_admin = State()


def get_today_int():
    t = date.today()
    return t.day + t.month * 100 + t.year * 10000


def add_user_to_db(cursor, message: types.Message):
    t = get_today_int()
    cursor.execute(f"INSERT INTO users VALUES(?,?,?,?,?,?,?,?)",
                   (message.from_user.id, message.from_user.first_name, 0, 0, 0, 0, t, 0)).fetchone()


def update_right_ans(cursor, message: types.Message):
    dbToday = cursor.execute(f'SELECT today FROM users WHERE user_id={message.from_user.id}').fetchone()[0]
    t = get_today_int()
    if (dbToday != t):
        cursor.execute(f"UPDATE users SET right_today = 0 WHERE user_id = {message.from_user.id}")
        cursor.execute(f"UPDATE users SET today = {t} WHERE user_id = {message.from_user.id}")


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await User.menu.set()
    db = sqlite3.connect(DB_PATH_USER)
    cdb = db.cursor()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item0 = types.KeyboardButton('/start')
    item1 = types.KeyboardButton('/stats')
    item2 = types.KeyboardButton('/help')
    item3 = types.KeyboardButton('/participate')
    item4 = types.KeyboardButton('/bestofthebest')
    item5 = types.KeyboardButton('/thebest')
    admin = cdb.execute(f"SELECT admin FROM users WHERE user_id = '{message.from_user.id}'").fetchone()
    if admin != (0,):
        item6 = types.KeyboardButton('/newquestion')
        item7 = types.KeyboardButton('/newadmin')
        item8 = types.KeyboardButton('/kickadmin')
        markup.add(item0, item1, item2, item3, item4, item5, item6, item7, item8)
    else:
        markup.add(item0, item1, item2, item3, item4, item5)
    cdb.execute(f"SELECT user_id FROM users WHERE user_id = '{message.from_user.id}'")
    if cdb.fetchone() is None:
        add_user_to_db(cdb, message)
        db.commit()
    db.close()
    await message.answer(f"Здравствуйте, {message.from_user.first_name}!",
                         reply_markup=markup)


@dp.message_handler(state='*', commands=['help'])
@dp.message_handler(lambda message: message.text.lower() == 'help', state='*')
async def help_handler(message: types.Message):
    await bot.send_message(message.from_user.id, f'Добро пожаловать, {message.from_user.first_name}!\n'
                                                 'Кнопки, используемые в викторине:\n/start для выхода на главное '
                                                 'меню или начала игры;\n/participate для участия в игре;\n/stats для'
                                                 'просмотра личной статистики;\n/bestofthebest для просмотра списка'
                                                 'лучших игроков;\n/thebest для просмотра списка лучших игроков дня.\n'
                                                 'Правила игры:\n'
                                                 '1) Каждая игра представляет собой онлайн-викторину продолжительностью'
                                                 'в один день. В любое время можно приступить к ответу на вопросы.\n'
                                                 '2) Ответить каждый на вопрос викторины можно в течение 30 секунд,'
                                                 'право на ошибку отсутствует. Отсутствие ответа трактуется так же, как'
                                                 'и неверный ответ.\n3) В игре не предусмотрены подсказки.\n'
                                                 '4) Вы можете увидеть личную статистику и статистику пяти лучших '
                                                 'пользователей в любой момент времени.\n'
                                                 '5) В онлайн-викторине важную роль играет грамотность: ответы,'
                                                 'введённые неграмотно, не могут являться правильными. Буквы "е"'
                                                 'и "ё" считаются различными (не следует использовать букву "ё", '
                                                 'пробелы и знаки препинания не игнорируются программой, заглавные'
                                                 'и строчные буквы не являются различными. Все кавычки являются '
                                                 'двойными, все тире - длинными.\n'
                                                 '6) В конце ответа необходимо поставить точку, иначе ответ'
                                                 'не будет правильным.\n'
                                                 '7) Порядковый номер правителя необходимо записать латинскими '
                                                 'буквами (не цифрами).\n'
                                                 '8) Добавить новые вопросы в базу данных может только администратор. '
                                                 'Если Вы отказываетесь ввести новый вопрос или новый ответ, введите '
                                                 '"/start"\n'
                           )


@dp.message_handler(state='*', commands=['stats'])
@dp.message_handler(lambda message: message.text.lower() == 'stats', state='*')
async def stats_handler(message: types.Message):
    db = sqlite3.connect(DB_PATH_USER)
    cdb = db.cursor()
    cdb.execute(f"SELECT user_id FROM users WHERE user_id = '{message.from_user.id}'")
    if cdb.fetchone() is None:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton('/start')
        markup.add(item1)
        add_user_to_db(cdb, message)
        db.commit()
        db.close()
        await message.answer('Вы занесены в базу данных!Нажмите /stats ещё раз(так как вы сначала не нажали start)')
    else:
        result = cdb.execute(f"""SELECT all_ans, right_ans, wrong_ans FROM users
                            WHERE user_id = '{message.from_user.id}'""").fetchall()
        for elem in result:
            if elem[0] == 0:
                await bot.send_message(message.from_user.id, md.text(md.text(md.bold('Личная статистика📊:')),
                                                                     md.text(' '),
                                                                     md.text('Заданий выполнено: ', md.bold(elem[0])),
                                                                     md.text('Верных ответов: ', md.bold(elem[1]),
                                                                             ' (0%)'),
                                                                     md.text(f'Неверных ответов: ', md.bold(elem[2]),
                                                                             ' (0%)'),
                                                                     sep='\n'), parse_mode=ParseMode.MARKDOWN)
            else:
                await bot.send_message(message.from_user.id, md.text(md.text(md.bold('Личная статистика📊:')),
                                                                     md.text(' '),
                                                                     md.text('Заданий выполнено: ',
                                                                             md.bold(elem[0])),
                                                                     md.text('Верных ответов: ',
                                                                             md.bold(elem[1]),
                                                                             f' ({round((elem[1] / elem[0] * 100), 1)}%)'),
                                                                     md.text(f'Неверных ответов: ', md.bold(elem[2]),
                                                                             f' ({round((elem[2] / elem[0] * 100), 1)}%)'),
                                                                     sep='\n'), parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(state='*', commands=['participate'])
@dp.message_handler(lambda message: message.text.lower() == '/participate', state=User.menu)
async def process_predmet(message: types.Message, state: FSMContext):
    con = sqlite3.connect(DB_PATH_QUESTIONS)
    async with state.proxy() as data:
        data['predmet'] = message.text
        await User.answer.set()
        cur = con.cursor()
        result = cur.execute("""SELECT task, answer FROM ""
                WHERE id IN (SELECT id FROM "" ORDER BY RANDOM() LIMIT 1)""").fetchall()
        for elem in result:
            print(f'{message.from_user.first_name}, {message.from_user.last_name}, {message.from_user.username}: '
                  f'{elem[1]}')
            data['answer'] = elem[1]
            await bot.send_message(message.from_user.id, elem[0])
            await bot.send_message(message.from_user.id, 'Ваш ответ:', reply_markup=types.ReplyKeyboardRemove())
            global t
            t = loop.call_later(60, lambda: asyncio.ensure_future(waitThenPrintNoAnswer(message)))
        con.close()


async def waitThenPrintNoAnswer(message: types.Message):
    await bot.send_message(message.from_user.id, 'Вы не успели ответить на вопрос')
    db = sqlite3.connect(DB_PATH_USER)
    cdb = db.cursor()
    cdb.execute(f"UPDATE users SET all_ans = all_ans + 1 WHERE user_id = {message.from_user.id}")
    cdb.execute(f"UPDATE users SET wrong_ans = wrong_ans + 1 WHERE user_id = {message.from_user.id}")
    db.commit()
    db.close()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Попробовать еще")
    item2 = types.KeyboardButton("Отказаться")
    item3 = types.KeyboardButton('/stats')
    item4 = types.KeyboardButton('/help')
    markup.add(item1, item2)
    markup.add(item3, item4)
    await User.end_ans.set()
    await bot.send_message(message.from_user.id, 'Хотите попробовать еще?', reply_markup=markup)


@dp.message_handler(state=User.answer)
async def first_answer(message: types.Message, state: FSMContext):
    answer = message.text
    t.cancel()
    data = await state.get_data()
    if answer.lower() == data['answer'].lower():
        db = sqlite3.connect(DB_PATH_USER)
        cdb = db.cursor()
        update_right_ans(cdb, message)
        cdb.execute(f"UPDATE users SET all_ans = all_ans + 1 WHERE user_id = {message.from_user.id}")
        cdb.execute(f"UPDATE users SET right_ans = right_ans + 1 WHERE user_id = {message.from_user.id}")
        cdb.execute(f"UPDATE users SET right_today = right_today + 1 WHERE user_id = {message.from_user.id}")
        db.commit()
        db.close()
        await bot.send_message(message.from_user.id, 'Это правильный ответ!🎉')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Попробовать еще")
        item2 = types.KeyboardButton("Отказаться")
        item3 = types.KeyboardButton('/stats')
        item4 = types.KeyboardButton('/help')
        markup.add(item1, item2)
        markup.add(item3, item4)
        await User.end_ans.set()
        await bot.send_message(message.from_user.id, 'Хотите попробовать еще?', reply_markup=markup)
    elif ''.join(answer.lower().split()) == '/start':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item = types.KeyboardButton("/start")
        item1 = types.KeyboardButton('/stats')
        item2 = types.KeyboardButton('/help')
        markup.add(item, item1, item2)
        await state.reset_state(with_data=False)
        await bot.send_message(message.from_user.id, 'Начнем с начала!', reply_markup=markup)
    else:
        db = sqlite3.connect(DB_PATH_USER)
        cdb = db.cursor()
        update_right_ans(cdb, message)
        cdb.execute(f"UPDATE users SET all_ans = all_ans + 1 WHERE user_id = {message.from_user.id}")
        cdb.execute(f"UPDATE users SET wrong_ans = wrong_ans + 1 WHERE user_id = {message.from_user.id}")
        db.commit()
        db.close()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Попробовать еще")
        item2 = types.KeyboardButton("Отказаться")
        item3 = types.KeyboardButton('/stats')
        item4 = types.KeyboardButton('/help')
        markup.add(item1, item2)
        markup.add(item3, item4)
        await User.end_ans.set()
        await bot.send_message(message.from_user.id, 'К сожалению, это неправильный ответ.', reply_markup=markup)
        await bot.send_message(message.from_user.id, f'Правильный ответ: {data["answer"]}',
                               parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(state=User.end_ans)
async def process_end_ans(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        com = message.text
        if com.lower() == 'попробовать еще':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item = types.KeyboardButton(f"{data['predmet']}")
            item1 = types.KeyboardButton('/stats')
            item2 = types.KeyboardButton('/help')
            markup.add(item)
            markup.add(item1, item2)
            await User.play.set()
            await bot.send_message(message.from_user.id, 'Следующий вопрос', reply_markup=markup)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item = types.KeyboardButton("/start")
            item1 = types.KeyboardButton('/stats')
            item2 = types.KeyboardButton('/help')
            markup.add(item, item1, item2)
            await state.reset_state(with_data=False)
            await bot.send_message(message.from_user.id, 'До скорых встреч!👋', reply_markup=markup)


def str_percent(name, right, total):
    if total == 0:
        return f'{name}: 0 (0%)'
    return f'{name}: {right} ({round((right) * 100 / total, 2)}%)\n'


def str_name(name, right):
    return f'{name}: {right}\n'


@dp.message_handler(state='*', commands=['bestofthebest'])
@dp.message_handler(lambda message: message.text.lower() == 'bestofthebest', state='*')
async def best_handler(message: types.Message):
    db = sqlite3.connect(DB_PATH_USER)
    cdb = db.cursor()
    result = cdb.execute(f"SELECT user_name, right_ans, all_ans FROM users ORDER BY -right_ans LIMIT 5;").fetchall()
    data = []
    for elem in result:
        data.append(str_percent(elem[0], elem[1], elem[2]))
    await bot.send_message(message.from_user.id, md.text(md.text(md.bold('Лучшие игроки всех времён📊:')),
                                                    md.text(''.join(data)), sep='\n'), parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(state='*', commands=['thebest'])
@dp.message_handler(lambda message: message.text.lower() == 'thebest', state='*')
async def best_handler(message: types.Message):
    db = sqlite3.connect(DB_PATH_USER)
    cdb = db.cursor()
    result = cdb.execute(f"SELECT user_name, right_today, all_ans FROM users ORDER BY -right_today LIMIT 5;").fetchall()
    data = []
    for elem in result:
        data.append(str_name(elem[0], elem[1]))
    await bot.send_message(message.from_user.id, md.text(md.text(md.bold('Лучшие игроки дня📊:')),
                                                    md.text(''.join(data)), sep='\n'), parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(state='*', commands=['newquestion'])
@dp.message_handler(lambda message: message.text.lower() == 'newquestion', state='*')
async def question_handler(message: types.Message, state: FSMContext):
    db = sqlite3.connect(DB_PATH_USER)
    cdb = db.cursor()
    admin = cdb.execute(f"SELECT admin FROM users WHERE user_id = '{message.from_user.id}'").fetchone()
    if admin != (1,) and admin != (2,):
        await bot.send_message(message.from_user.id, 'Функция невозможна. Вы не являетесь администратором.')
    else:
        await User.question.set()
        await bot.send_message(message.from_user.id, 'Вы можете добавить вопрос в базу данных. Введите Ваш вопрос:',
                               reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=User.question)
async def question_handler(message: types.Message, state: FSMContext):
    try:
        global quest
        quest = message.text
        if quest == '/start':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item = types.KeyboardButton("/start")
            item1 = types.KeyboardButton('/help')
            markup.add(item, item1)
            await state.reset_state(with_data=False)
            await bot.send_message(message.from_user.id, 'Перенаправляем в главное меню', reply_markup=markup)
        else:
            await User.end_question.set()
            await bot.send_message(message.from_user.id, 'Теперь введите ответ:')
    except Exception:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item = types.KeyboardButton("/start")
        item1 = types.KeyboardButton('/help')
        markup.add(item, item1)
        await state.reset_state(with_data=False)
        await bot.send_message(message.from_user.id, 'Произошла ошибка. Или такой вопрос уже есть в таблице, или Вы '
                                                     'некорректно добавили новый запрос.', reply_markup=markup)


@dp.message_handler(state=User.end_question)
async def question_handler(message: types.Message, state: FSMContext):
    try:
        ans1 = message.text
        if ans1 == '/start':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item = types.KeyboardButton("/start")
            item1 = types.KeyboardButton('/help')
            markup.add(item, item1)
            await state.reset_state(with_data=False)
            await bot.send_message(message.from_user.id, 'Перенаправляем в главное меню', reply_markup=markup)
        else:
            db = sqlite3.connect(DB_PATH_QUESTIONS)
            cdb = db.cursor()
            cdb.execute(f"INSERT INTO '' (task, answer) VALUES ('{quest}', '{ans1}')")
            db.commit()
            db.close()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item = types.KeyboardButton("/start")
            item1 = types.KeyboardButton('/help')
            markup.add(item, item1)
            await state.reset_state(with_data=False)
            await bot.send_message(message.from_user.id, 'Вы добавили новый вопрос в таблицу.', reply_markup=markup)
    except Exception:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item = types.KeyboardButton("/start")
        item1 = types.KeyboardButton('/help')
        markup.add(item, item1)
        await state.reset_state(with_data=False)
        await bot.send_message(message.from_user.id, 'Произошла ошибка. Или такой вопрос уже есть в таблице, или Вы '
                                                     'некорректно добавили новый запрос.', reply_markup=markup)


@dp.message_handler(state='*', commands=['newadmin'])
@dp.message_handler(lambda message: message.text.lower() == 'newadmin', state='*')
async def admin_handler(message: types.Message, state: FSMContext):
    db = sqlite3.connect(DB_PATH_USER)
    cdb = db.cursor()
    admin = cdb.execute(f"SELECT admin FROM users WHERE user_id = '{message.from_user.id}'").fetchone()
    if admin != (1,) and admin != (2,):
        await bot.send_message(message.from_user.id, 'Функция невозможна. Вы не являетесь администратором.')
    else:
        await User.new_admin.set()
        await bot.send_message(message.from_user.id, 'Введите id человека, которого Вы хотите сделать администратором.',
                               reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=User.new_admin)
async def admin_handler(message: types.Message, state: FSMContext):
    number = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item = types.KeyboardButton("/start")
    item1 = types.KeyboardButton('/help')
    markup.add(item, item1)
    if number == '/start':
        await state.reset_state(with_data=False)
        await bot.send_message(message.from_user.id, 'Перенаправляем в главное меню', reply_markup=markup)
    else:
        db = sqlite3.connect(DB_PATH_USER)
        cdb = db.cursor()
        admin = cdb.execute(f"SELECT admin FROM users WHERE user_id = '{number}'").fetchone()
        if admin is not None:
            if admin != (0,) and str(message.from_user.id) == number:
                await state.reset_state(with_data=False)
                await bot.send_message(message.from_user.id, 'Вы и так являетесь администратором.', reply_markup=markup)
            elif admin != (0,):
                await state.reset_state(with_data=False)
                await bot.send_message(message.from_user.id, 'Этот человек уже является администратором.',
                                       reply_markup=markup)
            elif number == str(message.from_user.id) and admin == (0,):
                await state.reset_state(with_data=False)
                await bot.send_message(message.from_user.id, 'Вы не можете сделать себя администратором.',
                                       reply_markup=markup)
            else:
                cdb.execute(f"UPDATE users SET admin = 1 WHERE user_id = {number}")
                db.commit()
                db.close()
                await state.reset_state(with_data=False)
                await bot.send_message(message.from_user.id, 'Вы сделали данного человека администратором.',
                                                   reply_markup=markup)
        else:
            await state.reset_state(with_data=False)
            await bot.send_message(message.from_user.id, 'Произошла ошибка. Скорее всего, человека с таким id нет.',
                                   reply_markup=markup)


@dp.message_handler(state='*', commands=['kickadmin'])
@dp.message_handler(lambda message: message.text.lower() == 'kickadmin', state='*')
async def admin_handler(message: types.Message, state: FSMContext):
    db = sqlite3.connect(DB_PATH_USER)
    cdb = db.cursor()
    admin = cdb.execute(f"SELECT admin FROM users WHERE user_id = '{message.from_user.id}'").fetchone()
    if admin != (1,) and admin != (2,):
        await bot.send_message(message.from_user.id, 'Функция невозможна. Вы не являетесь администратором.')
    else:
        await User.kick_admin.set()
        await bot.send_message(message.from_user.id, 'Введите id человека, которого Вы хотите лишить статуса '
                                                     'администратора.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=User.kick_admin)
async def admin_handler(message: types.Message, state: FSMContext):
    number = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item = types.KeyboardButton("/start")
    item1 = types.KeyboardButton('/help')
    markup.add(item, item1)
    if number == '/start':
        await state.reset_state(with_data=False)
        await bot.send_message(message.from_user.id, 'Перенаправляем в главное меню', reply_markup=markup)
    else:
        db = sqlite3.connect(DB_PATH_USER)
        cdb = db.cursor()
        admin = cdb.execute(f"SELECT admin FROM users WHERE user_id = '{number}'").fetchone()
        if admin is not None:
            if number == str(message.from_user.id) and admin != (0,):
                await state.reset_state(with_data=False)
                await bot.send_message(message.from_user.id, 'Вы не можете лишить себя статуса администратора.',
                                       reply_markup=markup)
            elif number == str(message.from_user.id) and admin == (0,):
                await state.reset_state(with_data=False)
                await bot.send_message(message.from_user.id, 'Вы не являетесь администратором.',
                                       reply_markup=markup)
            elif admin == (0,):
                await state.reset_state(with_data=False)
                await bot.send_message(message.from_user.id, 'Этот человек не является администратором.', reply_markup=markup)
            elif admin == (2,):
                await state.reset_state(with_data=False)
                await bot.send_message(message.from_user.id, 'Вы не можете лишить этого человека статуса '
                                                             'администратора.', reply_markup=markup)
            else:
                cdb.execute(f"UPDATE users SET admin = 0 WHERE user_id = {number}")
                db.commit()
                db.close()
                await state.reset_state(with_data=False)
                await bot.send_message(message.from_user.id, 'Вы лишили данного человека статуса администратора.',
                                                   reply_markup=markup)
        else:
            await state.reset_state(with_data=False)
            await bot.send_message(message.from_user.id, 'Произошла ошибка. Скорее всего, человека с таким id нет.',
                                   reply_markup=markup)

if __name__ == '__main__':
    executor.start_polling(dp, loop=loop, skip_updates=True)
