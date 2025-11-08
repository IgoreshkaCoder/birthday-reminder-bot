from dotenv import load_dotenv
from datetime import datetime
from aiogram import *
import sqlite3
import random
import os

# загружает пременное окружение из .env
load_dotenv()

tkn = os.getenv('tkn')
bt = Bot(token=tkn)
dp = Dispatcher(bt)

key_date = {}

# тело 
# DataBase
def create_db():
    with sqlite3.connect('nap.db') as conn:
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS users(
                    num_reg INTEGER PRIMARY KEY AUTOINCREMENT, 
                    user_id INTEGER UNIQUE, 
                    name TEXT DEFAULT "_", 
                    b_date TEXT DEFAULT "_",
                    stats TEXT DEFAULT "f"
            )''')
        conn.commit()
# stus: 
# f: ничего не ожидаем
# n: ожидание имя, d: ожидание даты
create_db()

# ======= функции текста add =========
async def add_sms_n(message):
    await message.answer(
        text='<b>✅ Напиши мне имя человека: </b><u><i>Например свое</i></u> или имя друга/коллеги.'
        '\n<b>Отправь его следующим сообщением</b>',
        parse_mode='html',
        reply=message.message_id
    )

async def add_sms_d(message):
    await message.answer(
        text='<b>✅ Теперь напиши мне дату в формате: ДД.ММ.ГГГГ (например: 03.05.2009)</b>',
        parse_mode='html',
        reply=message.message_id
    )

async def add_sms_f(message):
    await message.answer(
        text='<b>❎ Если хочешь добавить имя или дату, то воспользуйся командой /add</b>',
        parse_mode='html',
        reply=message.message_id
    )

# ========= Функция проверки даты add =========
async def is_valid_date(date_str):
    try:
        # Эта строка сама проверит валидность даты
        datetime.strptime(date_str, "%d.%m.%Y")
        return True
    except ValueError:
        return False

#============== просмотр БД =============
@dp.message_handler(commands=['db'])
async def database(message: types.Message):
    if message.from_user.id == 1438689283:
        with sqlite3.connect('nap.db') as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users')
            users = cur.fetchall() # вернет все найденные записи

            info = ''
            for el in users:
                info += (f'Регистрация №{el[0]} - user_id: {el[1]}\n'
                f'|\n|\n')

            conn.commit()

        await bt.send_message(
            chat_id=message.chat.id,
            text=f"{info}"
        )

#============ start - начало работы ==============
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer_photo(
        photo=open(r'напоминалка.jpg', 'rb'),
        caption=f'''
<i><b>👋 Привет, {message.from_user.first_name}!</b>
✅ Я помогу тебе не забывать о днях рождениях.\n
⚙️ Вот мои команды:<blockquote>
/start - Основная информация о боте и его возможностях.
/add - Добавить новую дату.
/list - Показать все добавленные даты.
/nearest - Показать ближайшие 3 даты.</blockquote></i>
''',
        parse_mode='html',
        reply=message.message_id
    )

#=========== list - вывод всех дат =============
@dp.message_handler(commands=['list'])
async def list(message: types.Message):
    user_id = message.from_user.id
    info = '💌 Вот все добавленные дни рождения:\n\n'

    with sqlite3.connect('nap.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user_data = cur.fetchone()
        if user_data: # проверка на регистрацию
            names, dates = user_data[2], user_data[3]
            # разделяем
            name = names.split('_')
            date = dates.split('_')

            for i in range(len(name)): # повторяем цикл столько раз сколько есть имен
                if (len(name[i]) > 1) and (len(date[i]) > 1): # фильтруем пустые строки
                    smile = [
                        '✅','✴️','❇️','⚡','🔥','🌟','⭐','☀️','💥','❣️','❤️‍🔥','❤️','🩷',
                        '🧡','💛','💚','💙','🩵','💜','🤎','🖤','🩶','🤍','💋','💯','💢','💫','💟'
                    ] # 28 el
                    dgt = random.randint(0, 27)

                    info += f'№{i} - {name[i]}: {date[i]} {smile[dgt]}\n' # окончательно формируем текст

            await message.answer(
                text=f'<b>{info}</b>\n' + '<i>⚙️ Добавить новую дату - /add\n⚙️ Посмотреть ближайшие 3 дня рождения - /nearest</i>',
                parse_mode='html',
                reply=message.message_id
            )
        else: # если нет регистрации
            await message.answer(
                text=f'<b>🚫 У тебя еще нет сохраненных дат! ⚠️ Используй - /add</b>',
                parse_mode='html',
                reply=message.message_id
            )

        conn.commit()

#=========== nearest - показываем ближайшие 3 дня =============
@dp.message_handler(commands=['nearest'])
async def nearest(message: types.Message):
    user_id = message.from_user.id

    with sqlite3.connect('nap.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user_data = cur.fetchone()

        if user_data: # проверка на регистрацию
            names, dates = user_data[2], user_data[3]
            name_list = names.split('_')
            date_list = dates.split('_')

            # Собираем все валидные даты
            valid_dates = []
            today = datetime.now().date()
            current_year = today.year # актуальный год

            for i in range(len(name_list)): # повторяется столько раз сколько имен есть
                if len(name_list[i]) > 1 and len(date_list[i]) > 1 and date_list[i] != "_": # фильтрация
                    try:
                        # Парсим дату рождения
                        b_date = datetime.strptime(date_list[i], "%d.%m.%Y").date()

                        # Создаем дату дня рождения в текущем году
                        next_birthday = b_date.replace(year=current_year)

                        # Если день рождения в этом году уже прошел, берем следующий год
                        if next_birthday < today:
                            next_birthday = next_birthday.replace(year=current_year + 1)

                        # Считаем сколько дней осталось
                        days_until = (next_birthday - today).days

                        # Добавляем в список
                        valid_dates.append({
                            'name': name_list[i],
                            'date': date_list[i],
                            'next_date': next_birthday,
                            'days_left': days_until,
                            'age': next_birthday.year - b_date.year # реплейс возвращает год, месяц, день
                        })
                    except:
                        continue
                    
            if valid_dates:
                # Сортируем по количеству оставшихся дней
                valid_dates.sort(key=lambda x: x['days_left'])
                
                # Берем ближайшие даты (гипко)
                nearest_dates = valid_dates[:30] # подставлять выбранное пользователем значение
                
                # Формируем сообщение
                info = "<b>💌 Ближайшие дни рождения:</b>\n\n"
                for i, item in enumerate(nearest_dates, 1):
                    smile = [
                        '✅','✴️','❇️','⚡','🔥','🌟','⭐','☀️','💥','❣️','❤️‍🔥','❤️','🩷',
                        '🧡','💛','💚','💙','🩵','💜','🤎','🖤','🩶','🤍','💋','💯','💢','💫','💟'
                    ] # 28 el
                    dgt = random.randint(0, 27)

                    intdays = item['days_left'] # склонения для дня
                    kdays = intdays % 10
                    if intdays > 100:
                        mdays = intdays % 100
                    else:
                        mdays = 0

                    intage = item['age'] # склонения для возраста
                    kage = intage % 10
                    if intage > 100:
                        mage = intage % 100
                    else:
                        mage = 0

                    next_date_str = item['next_date'].strftime("%d.%m.%Y")
                    info += f"№{i} - <b>{item['name']} {smile[dgt]}</b>\n"
                    info += f"""    📅 {next_date_str} (через {item['days_left']} {
                        'дней' if 11 <= mdays <= 14 else 
                        'дней' if 11 <= intdays <= 14 else 
                        'день' if kdays == 1 else 
                        'дня' if kdays in [2, 3, 4] else 'дней'
                    })\n"""
                    info += f"""    🎂 Исполнится: {item['age']} {
                        'лет' if 11 <= mage <= 14 else 
                        'лет' if 11 <= intage <= 14 else 
                        'год' if kage == 1 else 
                        'года' if kage in [2, 3, 4] else 'лет'
                    }\n\n"""
                
                await message.answer(
                    text=info + '<i>⚙️ Добавить новую дату - /add\n⚙️ Посмотреть весь список дат - /list</i>',
                    parse_mode='html',
                    reply=message.message_id
                )
            else:
                await message.answer(
                    text='<b>🚫 Ошибка!\n⚠️ Нет валидных дат для отображения!</b>',
                    parse_mode='html',
                    reply=message.message_id
                )
                
        else: # если нет регистрации
            await message.answer(
                text='<b>🚫 У тебя еще нет сохраненных дат! ⚠️ Используй - /add</b>',
                parse_mode='html',
                reply=message.message_id
            )    
    
    conn.commit()

#=========== add - сохранение имя и даты =============
@dp.message_handler(commands=['add'])
async def add(message: types.Message):
    user_id = message.from_user.id

    with sqlite3.connect('nap.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) # получение всех данных
        user_data = cur.fetchone()

        # проверка на регистрацию
        if user_data: # если зарегистрирован
            stats = user_data[4] # получение статуса

            if stats == 'f':
                cur.execute('UPDATE users SET stats = "n" WHERE user_id = ?', (user_id,)) # обновляем статус
                await add_sms_n(message)
            elif stats == 'n':
                await add_sms_n(message)
            elif stats == 'd':
                await add_sms_d(message)

        else: # если нет регистрации
            cur.execute('INSERT INTO users(user_id) VALUES (?)', (user_id,)) # регистрация user_id
            cur.execute('UPDATE users SET stats = "n" WHERE user_id = ?', (user_id,)) # обновляем статус
            await add_sms_n(message)
        conn.commit()

@dp.message_handler(content_types=['text'])
async def add_text(message: types.Message): # фильтруем ненужные сообщения либо получаем ответ
    user_id = message.from_user.id
    text = str(message.text)
    correct = 0

    with sqlite3.connect('nap.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) # получение всех даных
        user_data = cur.fetchone()

        # проверка на регистрацию
        if user_data: # если зарегистрирован
            stats = user_data[4]
            num = len(text)

            if (stats == 'f'): # ничего не ожидаем
                if message.chat.type in ['private']:
                    await add_sms_f(message)

            elif (stats == 'n') and (num <= 16) and (num > 1): # получаем имя
                txt0up = text[0].upper() # первая буква - большая
                txtlow = text[1:].lower() # остальное маленькое
                name = txt0up + txtlow # делаем только первую букву большой

                if user_id not in key_date:
                    key_date[user_id] = {'name': '', 'date': ''}

                key_date[user_id]['name'] = name # обновление name для вывода

                cur.execute('UPDATE users SET name = name || ? || "_" WHERE user_id = ?', (name, user_id)) # добавляем _ для разделения
                cur.execute('UPDATE users SET stats = "d" WHERE user_id = ?', (user_id,))

                await add_sms_d(message)

            elif stats == 'd' and (num <= 16): # получаем дату
                today = datetime.now().date()

                # Проверяем что ключ существует
                if user_id not in key_date:
                    await message.answer("🚫 Ошибка! ⚠️ Сначала введите имя!")
                    return
                
                try: # проверки
                    # проверка №1
                    numpoint = text.count('.')
                    if numpoint == 2: 
                        correct += 1
                
                    # проверка №2
                    txt = text.split('.') # пытаемся получить чисто цифры
                    full = int(txt[0] + txt[1] + txt[2])
                    if type(full) == int: 
                        correct += 1
                    
                    # проверка №3
                    numtxt = len(text)
                    if numtxt == 10: 
                        correct += 1
                
                    # проверка №4
                    dd = int(txt[0]) # выбераем дни
                    if 1 <= dd <= 31:
                        correct +=1

                    # проверка №5
                    mm = int(txt[1]) # выбераем месяц
                    if 1 <= mm <= 12:
                        correct += 1

                    # проверка №6
                    gggg = int(txt[2]) # выбераем год
                    if (gggg > 1000) and (gggg <= today.year):
                        correct += 1
                except: # если какая либо ошибка
                    correct = 0

                if correct == 6: # если все правильно 
                    date = await is_valid_date(text)

                    if date == True:
                        key_date[user_id]['date'] = text
                        # Получаем актуальное имя из словаря
                        actual_name = key_date[user_id]['name']
                        actual_date = key_date[user_id]['date']

                        cur.execute('UPDATE users SET b_date = b_date || ? || "_" WHERE user_id = ?', (actual_date, user_id))
                        cur.execute('UPDATE users SET stats = "f" WHERE user_id = ?', (user_id,))

                        await message.answer(
                            text=f'<b><i>🎉 Успех! {message.from_user.first_name}, вы успешно добавили новую дату!\n</i></b>'
                            f"<i>👤 Имя: {actual_name}, 📅 дата: {actual_date}</i>\n\n"
                            '<b>⚙️ Посмотреть все сохраненные даты  - /list</b>',
                            parse_mode='html',
                            reply=message.message_id
                        )
                        if user_id in key_date:
                            del key_date[user_id]
                    else:
                        await message.answer(
                            text=f'<b><i>🚫 Введена несуществующая дата!\n⚠️ Попробуй еще раз!</i></b>',
                            parse_mode='html',
                            reply=message.message_id
                        )
                else:
                    await message.answer(
                        text='<b>🚫 Ошибка!\n⚠️ Напиши мне дату в формате: ДД.ММ.ГГГГ (например: 03.05.2009)</b>',
                        parse_mode='html',
                        reply=message.message_id
                    )

            elif num > 16:
                await message.answer(
                    text='<b>🚫 Ошибка! ⚠️ Слишком длинное сообщение!</b>',
                    parse_mode='html',
                    reply=message.message_id
                )
            else:
                await message.answer(
                    text='<b>🚫 Ошибка! ⚠️ Неправильный формат ввода!</b>',
                    parse_mode='html',
                    reply=message.message_id
                )

        else: # если нет регистрации
            if message.chat.type in ['private']:
                cur.execute('INSERT INTO users(user_id) VALUES (?)', (user_id,)) # регистрация user_id
                await add_sms_f(message)
        conn.commit()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)