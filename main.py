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


DB_PATH_USER = 'db/user_db.db'
DB_PATH_EGE = 'db/questions1.db'

API_TOKEN = TOKEN

loop = asyncio.get_event_loop()
bot = Bot(token=TOKEN, loop=loop)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class User(StatesGroup):
    examen = State()
    predmet = State()
    answer = State()
    end_ans = State()
    wast_ans = State()


def get_today_int():
    t = date.today()
    return t.day + t.month * 100 + t.year * 10000


def add_user_to_db(cursor, message: types.Message):
    t = get_today_int()
    cursor.execute(f"INSERT INTO users VALUES(?,?,?,?,?,?,?)", (message.from_user.id, message.from_user.first_name, 0, 0, 0, 0, t)).fetchone()


def update_right_ans(cursor, message: types.Message):
    dbToday = cursor.execute(f'SELECT today FROM users WHERE user_id={message.from_user.id}').fetchone()[0]
    t = get_today_int()
    if(dbToday != t):
        cursor.execute(f"UPDATE users SET right_today = 0 WHERE user_id = {message.from_user.id}")
        cursor.execute(f"UPDATE users SET today = {t} WHERE user_id = {message.from_user.id}")


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await User.examen.set()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item0 = types.KeyboardButton('/start')
    item1 = types.KeyboardButton('/stats')
    item2 = types.KeyboardButton('/help')
    item3 = types.KeyboardButton('/participate')
    item4 = types.KeyboardButton('/bestofthebest')
    item5 = types.KeyboardButton('/thebest')
    markup.add(item0, item1, item2, item3, item4, item5)
    db = sqlite3.connect(DB_PATH_USER)
    cdb = db.cursor()
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
                                                 'и строчные буквы не являются различными.\n'
                                                 '6) В конце ответа необходимо поставить точку, иначе ответ'
                                                 'не будет правильным.\n'
                                                 '7) Порядковый номер правителя необходимо записать латинскими '
                                                 'буквами (не цифрами).\n'
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
@dp.message_handler(lambda message: message.text.lower() == '/participate', state=User.examen)
async def process_predmet(message: types.Message, state: FSMContext):
    con = sqlite3.connect(DB_PATH_EGE)
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
            await User.predmet.set()
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
        return f'{name}: 0(0%)'
    return f'{name}: {right} ({round((right) * 100 / total, 2)}%)\n'


def str_name(name, right):
    return f'{name}: {right}\n'


@dp.message_handler(state='*', commands=['bestofthebest'])
@dp.message_handler(lambda message: message.text.lower() == 'bestofthebest', state='*')
async def best_handler(message: types.Message):
    db = sqlite3.connect(DB_PATH_USER)
    cdb = db.cursor()
    result = cdb.execute(f"SELECT user_name, right_ans, all_ans FROM users ORDER BY -right_ans LIMIT 5;").fetchall()
    for elem in result:
        await bot.send_message(message.from_user.id, md.text(md.text(md.bold('Лучшие игроки всех времён📊:')),
                                                             md.text(str_percent(elem[0], elem[1], elem[2])),
                                                             sep='\n'), parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(state='*', commands=['thebest'])
@dp.message_handler(lambda message: message.text.lower() == 'thebest', state='*')
async def best_handler(message: types.Message):
    db = sqlite3.connect(DB_PATH_USER)
    cdb = db.cursor()
    result = cdb.execute(f"SELECT user_name, right_today, all_ans FROM users ORDER BY -right_today LIMIT 5;").fetchall()
    for elem in result:
        await bot.send_message(message.from_user.id, md.text(md.text(md.bold('Лучшие игроки дня📊:')),
                                                             md.text(str_name(elem[0], elem[1])),
                                                             sep='\n'), parse_mode=ParseMode.MARKDOWN)


if __name__ == '__main__':
    executor.start_polling(dp, loop=loop, skip_updates=True)