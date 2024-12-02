from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
# from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, PhotoSize)

from aiogram.types import (KeyboardButton, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove, BotCommand)

from aiogram.types import Message, FSInputFile

from filter import IsDatetime, IsFIO, Is_login_and_passsword
# from aiogram.fsm.storage.redis import RedisStorage, Redis

from aiogram.utils.keyboard import ReplyKeyboardBuilder

from config import BOT_TOKEN, login, password

import asyncio
from PIL import Image

from mc_api_utils import autorization, get_my_pages, load_photo, get_biography
from models import image2video, image2discript


# Инициализируем Redis
# redis = Redis(host='localhost', port=6378)

# Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
storage = MemoryStorage()
# storage = RedisStorage(redis=redis)
# Создаем объекты бота и диспетчера
bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=storage)

# Создаем асинхронную функцию
async def set_main_menu(bot: Bot):

    # Создаем список с командами и их описанием для кнопки menu
    main_menu_commands = [
        BotCommand(command='/help',
                   description='Справка по работе бота'),
        BotCommand(command='/start',
                   description='Начало работы'),
        BotCommand(command='/support',
                   description='Поддержка'),
        BotCommand(command='/contacts',
                   description='Другие способы связи'),
    ]

    await bot.set_my_commands(main_menu_commands)


# Регистрируем асинхронную функцию в диспетчере,
# которая будет выполняться на старте бота,
dp.startup.register(set_main_menu)
# Создаем "базу данных" пользователей
user_dict: dict[int, dict[str, str | int | bool]] = {}

# Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMFillForm(StatesGroup):
    # Создаем экземпляры класса State, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодейтсвия с пользователем
    autorization = State()        # Состояние ожидания авторизации
    choice_page = State()      # Выбор страницы для редактирования
    fill_name = State()        # Состояние ожидания ввода имени
    birth_date = State()       # Состояние ожидания даты рождения
    death_date = State()       # Состояние ожидания даты смерти
    short_epitaph = State()    # Состояние ожидания краткой эпитафии
    upload_photo = State()     # Состояние ожидания загрузки фото
    generation = State()   # Состояние ожидания выбора получать ли новости
    fill_correct_data = State()# Проверка введенных данных на коректность


 # Создаем объекты инлайн-кнопок
yes_change_button = InlineKeyboardButton(
    text='Да',
    callback_data='yes'
)
no_change_button = InlineKeyboardButton(
    text='Нет, спасибо',
    callback_data='no')
# Добавляем кнопки в клавиатуру в один ряд
keyboard: list[list[InlineKeyboardButton]] = [
    [yes_change_button, no_change_button]
]
# Создаем объект инлайн-клавиатуры
markup_yes_no = InlineKeyboardMarkup(inline_keyboard=keyboard)

# # Этот хэндлер будет срабатывать на команду "/start"
# # и отправлять в чат клавиатуру
# @dp.message(CommandStart())
# async def process_start_command(message: Message):
#     await message.answer(
#         text='Вот такая получается клавиатура',
#         reply_markup=kb_builder.as_markup(resize_keyboard=True)
#     )

button_1 = KeyboardButton(text='Авторизироваться')
button_2 = KeyboardButton(text='По умолчанию')

# Создаем объект клавиатуры, добавляя в него кнопки
keyboard_autorization = ReplyKeyboardMarkup(
    keyboard=[[button_1, button_2]],
    resize_keyboard=True
)

# Этот хэндлер будет срабатывать на команду /start вне состояний
# и предлагать перейти к заполнению анкеты, отправив команду /fillform
@dp.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await message.answer(
        text=f'Этот бот позволяет заполнить анкету на портале <a href="https://memorycode.ru/">Код памяти</a> \n' #[Код памяти](https://www.google.com/)
             'Для заполения анкеты - '
             'авторизируйтесь', disable_web_page_preview=True, parse_mode="HTML", reply_markup=keyboard_autorization
    )

# Этот хэндлер будет срабатывать на команду "/cancel" в любых состояниях,
# кроме состояния по умолчанию, и отключать машину состояний
@dp.message(Command(commands='cancel'), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext):
    await message.answer(
        text='Вы удалили данные о себе из бота\n\n',
             reply_markup=keyboard_autorization
    )
    # Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()


@dp.message(F.text=='Авторизироваться')
async def process_autorization(message: Message, state: FSMContext):
    await message.answer(text='Введите ваш логин и пароль через пробел:',
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(FSMFillForm.autorization)

@dp.message(StateFilter(FSMFillForm.autorization), Is_login_and_passsword())
async def process_autorizate(message: Message, state: FSMContext):
    login, password = message.text.split()
    code, data = autorization(login, password)
    if code==200:
        await message.answer(text='Спасибо!\n Авторизация прошла успешно! Теперь можете выбрать страницу для редактирования')
        await state.update_data(autorization_tag=data)
        await state.update_data(login=login)
        await state.update_data(password=password)
        await state.set_state(FSMFillForm.choice_page)
    else:
        await state.set_state(FSMFillForm.autorization)
        await message.answer(text=data)
        await message.answer(text='Пожалуйста повторите ввод почты и пароля или перейдите в начальное состояние отправив /cancel ')


# Этот хэндлер будет срабатывать, если во время ввода логина и пароля
# будет введено что-то некорректное
@dp.message(StateFilter(FSMFillForm.autorization))
async def warning_not_name(message: Message):
    await message.answer(
        text='То, что вы отправили имеет неверный формат \n'
             'Пример: qwertt@mail.com 123456 \n'
             'Если вы хотите прервать заполнение анкеты - '
             'отправьте команду /cancel'
    )

@dp.message(F.text=='По умолчанию')
async def process_cucumber_answer(message: Message, state: FSMContext):
    code, data = autorization(login, password)
    if code==200:
        await message.answer(text='Авторизация прошла успешно! Теперь можете выбрать страницу для редактирования', reply_markup=ReplyKeyboardRemove())
        await state.update_data(autorization_tag=data)
        await state.update_data(login=login)
        await state.update_data(password=password)
        
        autorization_tag = data
        code, data = get_my_pages(autorization_tag)
        if code==200:
            # # Инициализируем билдер
            kb_builder = ReplyKeyboardBuilder()

            # Создаем список с кнопками
            buttons: list[KeyboardButton] = [
                KeyboardButton(text=f'Стр. {i + 1}') for i in range(len(data))
            ]

            # Распаковываем список с кнопками в билдер, указываем, что
            # в одном ряду должно быть 4 кнопки
            kb_builder.row(*buttons, width=3)
            await message.answer(text=f'Вам доступно {len(data)} страниц для редактирования. Выберите одну',
                reply_markup=kb_builder.as_markup())
            await state.set_state(FSMFillForm.choice_page)
        else:
            await message.answer(text=data)
            await message.answer(text=f'Получить страницы доступные для Вас не удалось. Перезайдите или создайте их! Введите логин и пароль через пробел')
            await state.set_state(FSMFillForm.autorization)

    else:
        await state.set_state(FSMFillForm.autorization)
        await message.answer(text=data)
        await message.answer(text='Зайти по умолчанию не удалось поэтому введите свой логин и пароль через пробел: ',
            reply_markup=ReplyKeyboardRemove())
        await state.set_state(FSMFillForm.autorization)
                


# Этот хэндлер будет срабатывать на команду /fillform
# и переводить бота в состояние ожидания ввода имени
@dp.message(StateFilter(FSMFillForm.choice_page), F.text.startswith('Стр'))
async def process_choice_pages(message: Message, state: FSMContext):
    sdata = await state.get_data()
    code, data = get_my_pages(sdata['autorization_tag'])
    if code==200:
        # pages = sdata['pages']
        try: 
            page = int(message.text.split()[1])
            if page in list(range(1, len(data)+1)):
                await state.update_data(page=data[page-1])
                await message.answer(text=f"Вы выбрали {page} страницу!", reply_markup=ReplyKeyboardRemove())
                # Создаем объекты инлайн-кнопок
                code_biog, data_biog = get_biography(data[page-1]["link"], sdata['autorization_tag'])
                if code_biog!=200 or len(data_biog)==0:
                    await message.answer(text=f"На странице {page} не удалось загрузить биографию!", reply_markup=ReplyKeyboardRemove())
                else:
                    await state.update_data(biography=data_biog)
                    images_num = 0
                    for i in data_biog:
                        try:
                            images_num+=len(data_biog[i]['images'])
                        except Exception as ex:
                            pass
                    await message.answer(text=f"На странице {page} в биографии доступно абзацев: {len(data_biog)} и {images_num} изображений!", reply_markup=ReplyKeyboardRemove())
                await message.answer(
                text=f'Текущее ФИО на странице: {data[page-1]["name"]} \n Хотите его изменить?',
                reply_markup=markup_yes_no)

                await state.set_state(FSMFillForm.fill_name)
            else:
                await message.answer(text=f"Страницы {page} не существует. Повторите выбор страницы")
        except:
            await message.answer(text=f"Страницы {page} не существует")
    else:
        await message.answer(text=f"Страницы {page} не существует")

    

# Этот хэндлер будет срабатывать, если во время ввода имени
# будет введено что-то некорректное
@dp.message(StateFilter(FSMFillForm.choice_page))
async def warning_choice_pages(message: Message):
    await message.answer(
        text='То, что вы отправили не похоже на страницу\n\n'
             'Пожалуйста, отправьте страницу\n\n'
    )

#-------------------------------------------------------------------------------------------------------------
# Этот хэндлер будет срабатывать, если введено корректное имя
# и переводить в состояние ожидания ввода возраста
@dp.callback_query(StateFilter(FSMFillForm.fill_name), F.data.in_(['yes', 'no']))
async def process_name_choice(callback: CallbackQuery, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "name"
    sdata = await state.get_data()
    page = sdata['page']
    if callback.data == 'yes':
        await callback.message.answer(text='Введите новые ФИО...')
    else:
        await state.update_data(name=page["name"])
        await callback.message.answer(text='ФИО оставлены')
        await callback.message.answer(text=f'Текущая дата рождения: {page["birthday_at"]} \n Хотите ее изменить?',
            reply_markup=markup_yes_no)
        await state.set_state(FSMFillForm.birth_date)


# Этот хэндлер будет срабатывать, если введено корректное имя
# и переводить в состояние ожидания ввода возраста
@dp.message(StateFilter(FSMFillForm.fill_name), IsFIO())
async def process_name_sent(message: Message, state: FSMContext):
    sdata = await state.get_data()
    page = sdata['page']
    # Cохраняем введенное имя в хранилище по ключу "name"
    await state.update_data(name=message.text)
    await message.answer(text=f'Текущая дата рождения: {page["birthday_at"]} \n Хотите ее изменить?',
            reply_markup=markup_yes_no)
    await state.set_state(FSMFillForm.birth_date)


# Этот хэндлер будет срабатывать, если во время ввода имени
# будет введено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_name))
async def warning_not_name(message: Message):
    await message.answer(
        text='То, что вы отправили не похоже ФИО\n\n'
             'Пожалуйста, введите правильное ФИО\n\n'
             'Если вы хотите прервать заполнение анкеты - '
             'отправьте команду /cancel'
    )
#-------------------------------------------------------------------------------------------------------------

#-------------------------------------------------------------------------------------------------------------
# Этот хэндлер будет срабатывать, если введено корректное имя
# и переводить в состояние ожидания ввода возраста
@dp.callback_query(StateFilter(FSMFillForm.birth_date), F.data.in_(['yes', 'no']))
async def process_birth_choice(callback: CallbackQuery, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "name"
    sdata = await state.get_data()
    page = sdata['page']
    if callback.data == 'yes':
        await callback.message.answer(text='Введите новую дату рождения...')
        await state.set_state(FSMFillForm.birth_date)
    else:
        await state.update_data(birth=page["birthday_at"])
        await callback.message.answer(text='Дата рождения оставлена')
        await callback.message.answer(text=f'Текущая дата смерти: {page["died_at"]} \n Хотите ее изменить?',
            reply_markup=markup_yes_no)
        await state.set_state(FSMFillForm.death_date)

# Этот хэндлер будет срабатывать, если введен корректный возраст
# и переводить в состояние выбора пола
@dp.message(StateFilter(FSMFillForm.birth_date),
            IsDatetime())
async def process_birth(message: Message, state: FSMContext):
    sdata = await state.get_data()
    page = sdata['page']
    # Cохраняем возраст в хранилище по ключу "age"
    await state.update_data(birth=message.text)
    # Устанавливаем состояние ожидания выбора даты смерти
    await message.answer(
        text=f'Текущая дата смерти: {page["died_at"]} \n Хотите ее изменить?',
            reply_markup=markup_yes_no)
    # Устанавливаем состояние ожидания выбора даты смерти
    await state.set_state(FSMFillForm.death_date)


# Этот хэндлер будет срабатывать, если во время ввода возраста
# будет введено что-то некорректное
@dp.message(StateFilter(FSMFillForm.birth_date))
async def warning_birth(message: Message):
    await message.answer(
        text='Дата должна быть строкой день.месяц.год (пр. 11.11.1980)\n\n'
             'Попробуйте еще раз\n\nЕсли вы хотите прервать '
             'заполнение анкеты - отправьте команду /cancel'
    )
#-------------------------------------------------------------------------------------------------------------

#-------------------------------------------------------------------------------------------------------------
@dp.callback_query(StateFilter(FSMFillForm.death_date), F.data.in_(['yes', 'no']))
async def process_death_choice(callback: CallbackQuery, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "name"
    sdata = await state.get_data()
    page = sdata['page']
    if callback.data == 'yes':
        await callback.message.answer(text='Напишите краткую эпитафию про данного человека \n\n'
        'Расскажите о его жизни, достижениях и т.д.')
        await state.set_state(FSMFillForm.death_date)
    else:
        await state.update_data(death=page["died_at"])
        await callback.message.answer(text='Дата смерти оставлена')
        await callback.message.answer(text=f'Текущая краткая эпитафия: {page["epitaph"]} \n Хотите ее изменить?',
            reply_markup=markup_yes_no)
        await state.set_state(FSMFillForm.short_epitaph)

@dp.message(StateFilter(FSMFillForm.death_date),
            IsDatetime(['?', '-']))
async def process_death(message: Message, state: FSMContext):
    # Cохраняем возраст в хранилище по ключу "age"
    sdata = await state.get_data()
    page = sdata['page']

    await state.update_data(death=message.text)
    
    # Отправляем пользователю сообщение
    await message.answer(text=f'Текущая краткая эпитафия: {page["epitaph"]} \n Хотите ее изменить?',
            reply_markup=markup_yes_no)

    # Устанавливаем состояние ожидания выбора даты смерти
    await state.set_state(FSMFillForm.short_epitaph)

# Этот хэндлер будет срабатывать, если во время выбора даты смерти
# будет введено/отправлено что-то некорректное
@dp.message(StateFilter(FSMFillForm.death_date))
async def warning_death(message: Message):
    await message.answer(
       text='Дата смерти должна быть строкой день.месяц.год (пр. 11.11.2024) и быть больше даты рождения\n\n'
             'Попробуйте еще раз\n\nЕсли вы хотите прервать '
             'заполнение анкеты - отправьте команду /cancel'
    )

#------------------------------------------------------------------------------------------------------------
@dp.callback_query(StateFilter(FSMFillForm.short_epitaph), F.data.in_(['yes', 'no']))
async def process_death_choice(callback: CallbackQuery, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "name"
    sdata = await state.get_data()
    page = sdata['page']
    if callback.data == 'yes':
        await callback.message.answer(text='Напишите краткую эпитафию про данного человека \n\n'
        'Расскажите о его жизни, достижениях и т.д.')
        await state.set_state(FSMFillForm.short_epitaph)
    else:
        await state.update_data(epitaph=page["epitaph"])
        await callback.message.answer(text='Дата рождения оставлена')
        if page['main_image'] != None:
            await callback.message.answer_photo(photo=page['main_image'],  caption=f'Текущее изображение такое \n Хотите его изменить?',
                reply_markup=markup_yes_no)
        else:
            await callback.message.answer(text='В данный момент на странице нет изображения. Загрузите его сейчас!')
        await state.set_state(FSMFillForm.upload_photo)

@dp.message(StateFilter(FSMFillForm.short_epitaph), F.text!='')
async def process_epitaph(message: Message, state: FSMContext):
    # Cохраняем возраст в хранилище по ключу "age"
    await state.update_data(epitaph=message.text)
    sdata = await state.get_data()
    page = sdata['page']
    # Отправляем пользователю сообщение
    await message.answer(
        text='Спасибо!')
    if page['main_image'] != None:
        await message.answer_photo(photo=page['main_image'],  caption=f'Текущее изображение такое \n Хотите его изменить?',
                reply_markup=markup_yes_no)
    else:
        await message.answer(text='В данный момент на странице нет изображения. Загрузите его сейчас!')
    # Устанавливаем состояние ожидания выбора даты смерти
    await state.set_state(FSMFillForm.upload_photo)

# Этот хэндлер будет срабатывать, если во время выбора даты смерти
# будет введено/отправлено что-то некорректное
@dp.message(StateFilter(FSMFillForm.short_epitaph))
async def warning_epitaph(message: Message):
    await message.answer(
       text='Напишите краткую эпитафию про данного человека текстом\n\n'
             'Попробуйте еще раз\n\nЕсли вы хотите прервать '
             'заполнение анкеты - отправьте команду /cancel'
    )

# ------------------------------------------------------------------------------------------------
@dp.callback_query(StateFilter(FSMFillForm.upload_photo), F.data.in_(['yes', 'no']))
async def process_death_choice(callback: CallbackQuery, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "name"
    sdata = await state.get_data()
    page = sdata['page']
    if callback.data == 'yes':
        await callback.message.answer(text='Загрузите фотографию данного человека \n\n'
        'Желательно, чтобы на фотографии он был один')
        await state.set_state(FSMFillForm.upload_photo)
    else:
        await state.update_data(photo_id=page["main_image"])
        await callback.message.answer(text='Изображение оставлено')
            # Создаем объекты инлайн-кнопок
        yes_news_button = InlineKeyboardButton(
            text='Одному',
            callback_data='one'
        )
        no_news_button = InlineKeyboardButton(
            text='Нескольким',
            callback_data='many')
        # Добавляем кнопки в клавиатуру в один ряд
        keyboard: list[list[InlineKeyboardButton]] = [
            [yes_news_button, no_news_button]
        ]
        # Создаем объект инлайн-клавиатуры
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        # Редактируем предыдущее сообщение с кнопками, отправляя
        # новый текст и новую клавиатуру
        await callback.message.answer(
            text='Спасибо!\n\nСтраница сохранена, хотите сгенерировать видео по одному изображению или по нескольким?',
            reply_markup=markup
        )
        await state.set_state(FSMFillForm.generation)
# Этот хэндлер будет срабатывать, если отправлено фото
# и переводить в состояние выбора образования

@dp.message(StateFilter(FSMFillForm.upload_photo),
            F.photo[-1].as_('largest_photo'))
async def process_photo_sent(message: Message,
                             state: FSMContext,
                             largest_photo: PhotoSize):
    # Cохраняем данные фото (file_unique_id и file_id) в хранилище
    # по ключам "photo_unique_id" и "photo_id"
    await state.update_data(
        photo_unique_id=largest_photo.file_unique_id,
        photo_id=largest_photo.file_id
    )
    yes_news_button = InlineKeyboardButton(
            text='Одному',
            callback_data='one'
    )
    no_news_button = InlineKeyboardButton(
        text='Нескольким',
        callback_data='many')
    # Добавляем кнопки в клавиатуру в один ряд
    keyboard: list[list[InlineKeyboardButton]] = [
        [yes_news_button, no_news_button]
    ]
    # Создаем объект инлайн-клавиатуры
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(
        text='Спасибо!\nСтраница сохранена, хотите сгенерировать видео по одному изображению или по нескольким?', reply_markup=markup
    )
    # Устанавливаем состояние ожидания выбора образования
    await state.set_state(FSMFillForm.generation)


# Этот хэндлер будет срабатывать, если во время отправки фото
# будет введено/отправлено что-то некорректное
@dp.message(StateFilter(FSMFillForm.upload_photo))
async def warning_not_photo(message: Message):
    await message.answer(
        text='Пожалуйста, на этом шаге отправьте '
             'фотографию\n\nЕсли вы хотите прервать '
             'заполнение анкеты - отправьте команду /cancel'
    )


# Этот хэндлер будет срабатывать на выбор получать или
# не получать новости и выводить из машины состояний
@dp.callback_query(StateFilter(FSMFillForm.generation),
                   F.data.in_(['one', 'many']))
async def process_wish_news_press(callback: CallbackQuery, state: FSMContext):
    # Cохраняем данные о получении новостей по ключу "wish_news"
    await state.update_data(one=callback.data == 'one')
    # Добавляем в "базу данных" анкету пользователя
    # по ключу id пользователя

    # # Завершаем машину состояний
        # Создаем объекты инлайн-кнопок
    yes_news_button = InlineKeyboardButton(
        text='Да',
        callback_data='yes_true'
    )
    no_news_button = InlineKeyboardButton(
        text='Нет',
        callback_data='no_false')
    # Добавляем кнопки в клавиатуру в один ряд
    keyboard: list[list[InlineKeyboardButton]] = [
        [yes_news_button, no_news_button]
    ]
    # Создаем объект инлайн-клавиатуры
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    # Редактируем предыдущее сообщение с кнопками, отправляя
    # новый текст и новую клавиатуру


    data = await state.get_data()
    await callback.message.answer_photo(
            photo=data['photo_id'],
            caption=f'ФИО: {data["name"]}\n'
                    f'Дата рождения: {data["birth"]}\n'
                    f'Дата смерти: {data["death"]}\n'
                    f'Эпитафия: {data["epitaph"]}\n'
                    f'Сгенерировать видео: {"по одному" if data["one"]==True else "по нескольким"} изображениям')
    await callback.message.answer(
        text='Спасибо! Проверьте данные выше.\n'
             'Все ли указано верно?\n\n',
        reply_markup=markup
    )
    await state.set_state(FSMFillForm.fill_correct_data)


# Этот хэндлер будет срабатывать, если во время согласия на получение
# новостей будет введено/отправлено что-то некорректное
@dp.message(StateFilter(FSMFillForm.generation))
async def warning_not_wish_news(message: Message):
    await message.answer(
        text='Пожалуйста, воспользуйтесь кнопками!\n\n'
             'Если вы хотите прервать заполнение анкеты - '
             'отправьте команду /cancel'
    )


# Этот хэндлер будет срабатывать на выбор получать или
# не получать новости и выводить из машины состояний
@dp.callback_query(StateFilter(FSMFillForm.fill_correct_data),
                   F.data.in_(['yes_true', 'no_false']))
async def process_wish_news_press(callback: CallbackQuery, state: FSMContext):
    # Cохраняем данные о получении новостей по ключу "wish_news"
    # по ключу id пользователя
    if callback.data == 'yes_true':
        user_dict[callback.message.from_user.id] = await state.get_data()
        # Завершаем машину состояний
        if user_dict[callback.message.from_user.id]['one']==True:

            await callback.message.edit_text(
                text='Спасибо! Ваши данные сохранены!\n\n'
                    'Генерация началась'
            )
            if 'htt' in user_dict[callback.message.from_user.id]['photo_id']:
                code, content_img = load_photo(user_dict[callback.message.from_user.id]['photo_id'])
                if code==200:
                    await callback.message.edit_text(
                text='Изображение загружено! Генерация началась!')
                else:
                    await callback.message.edit_text(
                    text='Изображение не загружено, произошла ошибка')
            
            else:
 
                file_info_content = await bot.get_file(user_dict[callback.message.from_user.id]['photo_id'])
                content_img = await bot.download_file(file_info_content.file_path)
                content_img = Image.open(content_img)
            #a good short script that is well suited for creating an animation of this picture?
            prompt = image2discript(content_img, prompt="Please write short who and what does it do of this picture? ") #what is shown in the picture 
            print(prompt)
            video_name = image2video(content_img, prompt, callback.message.chat.id)
            # f = await bot.download_file(video_name)
            video_file = FSInputFile(path=video_name)
            await bot.send_animation(callback.message.chat.id, video_file, caption='Ваше видео!')
            await asyncio.sleep(2)
            # img = open(video_name, 'rb')
            # await bot.send_video(callback.message.chat.id, img, None, 'Text')
            # img.close()
            await callback.message.answer(
                text='Спасибо за ожидание! Вот ваше видео!\n\n'
            )
        else:
            await callback.message.edit_text(
                text='Спасибо! Генерация по нескольким видео еще не реализована!\n\n'
            )
            yes_news_button = InlineKeyboardButton(
            text='Одному',
            callback_data='one'
            )
            no_news_button = InlineKeyboardButton(
                text='Нескольким',
                callback_data='many')
            # Добавляем кнопки в клавиатуру в один ряд
            keyboard: list[list[InlineKeyboardButton]] = [
                [yes_news_button, no_news_button]
            ]
            # Создаем объект инлайн-клавиатуры
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            # Редактируем предыдущее сообщение с кнопками, отправляя
            # новый текст и новую клавиатуру
            await callback.message.answer(
                text='Выберите по одному изображению пожалуйста?',
                reply_markup=markup
            )
            await state.set_state(FSMFillForm.generation)


        # Отправляем в чат сообщение о выходе из машины состояний
    else:
        await state.clear()
        # Отправляем в чат сообщение о выходе из машины состояний
        await callback.message.edit_text(
            text='Плохо! Ваши данные удалены!\n\n'
                'Попробуйте заново'
        )


# Этот хэндлер будет срабатывать, если во время согласия на получение
# новостей будет введено/отправлено что-то некорректное
@dp.message(StateFilter(FSMFillForm.fill_correct_data))
async def warning_not_wish_news(message: Message):
    await message.answer(
        text='Пожалуйста, воспользуйтесь кнопками!\n\n'
             'Если вы хотите прервать заполнение анкеты - '
             'отправьте команду /cancel'
    )

# Этот хэндлер будет срабатывать на отправку команды /showdata
# и отправлять в чат данные анкеты, либо сообщение об отсутствии данных
@dp.message(Command(commands='showdata'), StateFilter(default_state))
async def process_showdata_command(message: Message):
    # Отправляем пользователю анкету, если она есть в "базе данных"
    if message.from_user.id in user_dict:
        await message.answer_photo(
            photo=user_dict[message.from_user.id]['photo_id'],
            caption=f'ФИО: {user_dict[message.from_user.id]["name"]}\n'
                    f'Дата рождения: {user_dict[message.from_user.id]["birth"]}\n'
                    f'Дата смерти: {user_dict[message.from_user.id]["death"]}\n'
                    f'Эпитафия: {user_dict[message.from_user.id]["epitaph"]}\n'
        )
    else:
        # Если анкеты пользователя в базе нет - предлагаем заполнить
        await message.answer(
            text='Вы еще не заполняли анкету. Чтобы приступить - '
            'отправьте команду /fillform'
        )


# Этот хэндлер будет срабатывать на любые сообщения в состоянии "по умолчанию",
# кроме тех, для которых есть отдельные хэндлеры
@dp.message(StateFilter(default_state))
async def send_echo(message: Message):
    await message.reply(text='Извините, такой команды нет')    


if __name__ == '__main__':
    dp.run_polling(bot)