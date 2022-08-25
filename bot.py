import logging
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from service import main, Result
import schedule
import configparser

BOT_TOKEN = '5435062174:AAFk05hUbCX018oTsFn4pNegP1QUaDvePyw'
# logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class BotState(StatesGroup):
    api_key = State()
    client_id = State()
    sima_token = State()


@dp.message_handler(commands=['start'], state='*')
async def send_welcome(message: types.Message):
    await bot.send_message(message.from_user.id, 'Введите ключ API от озона')
    await BotState.next()


@dp.message_handler(state=BotState.api_key)
async def get_apikey(message: types.Message, state: FSMContext):
    if len(message.text) != 36:
        await bot.send_message(message.from_user.id, 'Неверно введен ключ! Введите еще раз')
        return
    else:
        async with state.proxy() as data:
            data['API_KEY'] = message.text
        await bot.send_message(message.from_user.id, 'Введите Client ID')
        await BotState.next()


@dp.message_handler(state=BotState.client_id)
async def get_clientid(message: types.Message, state: FSMContext):
    if len(message.text) != 6:
        await bot.send_message(message.from_user.id, 'Неверно введен Client-ID ! Введите еще раз')
        return
    else:
        async with state.proxy() as data:
            data['CLIENT_ID'] = str(message.text)
        await bot.send_message(message.from_user.id, 'Введите SIMA LAND JWT')
        await BotState.next()


@dp.message_handler(state=BotState.sima_token)
async def get_sima_token(message: types.Message, state: FSMContext):
    if 'Bearer' not in message.text:
        await bot.send_message(message.from_user.id, 'Неверно введен токен ! Копируйте вместе с Bearer')
        return
    else:
        async with state.proxy() as data:
            data['SIMA_LAND_TOKEN'] = str(message.text)
        await bot.send_message(message.from_user.id, 'Начинаю работу...')
        config = configparser.ConfigParser()
        config.read('conf.ini')  # -> "/path/name/"
        config['APP']['sima_land_token'] = data['SIMA_LAND_TOKEN']  # update
        config['APP']['api_key'] = data['API_KEY']  # create
        config['APP']['client_id'] = data['CLIENT_ID']  # create

        with open('conf.ini', 'w') as configfile:  # save
            config.write(configfile)

        main()
        await bot.send_message(message.from_user.id, f"Товаров в продаже: {Result.items_selling}, Товары которых нет на Сима-Ленде: {Result.items_waiting}")

        schedule.every(10).hours.do(main)
        while True:
            schedule.run_pending()
        await state.finish()


# todo здесь сделать остановку работы бота
@dp.message_handler(state='*', commands='stop')
async def stop_state(message: types.Message, state: FSMContext):
    cur_state = await state.get_state()
    if not cur_state:
        return
    await state.finish()
    await bot.send_message(message.from_user.id, 'Вышел из состояния')


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(send_welcome, commands='start')
    dp.register_message_handler(get_apikey)
    dp.register_message_handler(get_clientid)
    dp.register_message_handler(get_sima_token)
    dp.register_message_handler(stop_state)


register_handlers(dp)

executor.start_polling(dp, skip_updates=True)
