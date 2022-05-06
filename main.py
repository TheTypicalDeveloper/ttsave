import os
import re
import traceback
import time
import requests
import configparser
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
from aiogram.utils.helper import Helper, HelperMode, ListItem
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import BoundFilter
import db
import keyboards as kb

config = configparser.ConfigParser()
config.read("settings.ini")
TOKEN = config["tgbot"]["token"]
admin_id = int(config["tgbot"]["admin_id"])

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class Info(StatesGroup):
    adminka = State()
    rassilka = State()

if not os.path.exists('audio'):
	os.makedirs('audio')

def get_download_links(video_url):
    r = requests.get(f'https://api.douyin.wtf/api?url={video_url}').json()
    if r["status"] == "success":
        video_url = r["nwm_video_url"]
        video_r = requests.get(video_url).content
        audio_url = r["video_music_url"]
        audio_r = requests.get(audio_url).content
        return video_r, audio_r
    return None, None

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
	if db.get_users_exist(message.chat.id) == False:
		db.add_user_to_db(message.chat.id)
		if message.chat.id == admin_id:
			await bot.send_message(chat_id=message.chat.id, text='📼 Привет, я помогу тебе скачать видео с TikTok. \n/help - инструкция как скачать видео', reply_markup = kb.admin_start())
		else:
			await bot.send_message(chat_id=message.chat.id, text='📼 Привет, я помогу тебе скачать видео с TikTok. \n/help - инструкция как скачать видео', reply_markup=types.ReplyKeyboardRemove())
	else:
		if message.chat.id == admin_id:
			await bot.send_message(chat_id=message.chat.id, text='📼 Привет, я помогу тебе скачать видео с TikTok. \n/help - инструкция как скачать видео', reply_markup = kb.admin_start())
		else:
			await bot.send_message(chat_id=message.chat.id, text='📼 Привет, я помогу тебе скачать видео с TikTok. \n/help - инструкция как скачать видео', reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
	await bot.send_message(chat_id=message.chat.id, text='Скопируй ссылку на видео TikTok и отправь её мне:')

@dp.message_handler(text="Админка")
async def create_post(message: types.Message):
	if db.get_users_exist(message.chat.id) == True:
		if message.chat.id == admin_id:
			await bot.send_message(chat_id=message.chat.id, text='Вот ваше админ меню.', reply_markup = kb.admin_menu())
			await Info.adminka.set()

@dp.message_handler(state=Info.adminka, content_types=types.ContentTypes.TEXT)
async def adminka(message: types.Message, state: FSMContext):
    if message.text.lower() == 'назад':
        await bot.send_message(chat_id=message.chat.id, text='Ты вернулся в главное меню.', reply_markup=kb.admin_start())
        await state.finish()
    elif message.text.lower() == 'рассылка':
        await bot.send_message(chat_id=message.chat.id, text='Введи текст для рассылки.', reply_markup=kb.back_2())
        await state.finish()
        await Info.rassilka.set()
    elif message.text.lower() == 'статистика':
        all_users = db.get_all_users()
        await bot.send_message(chat_id=message.chat.id, text=f'Пользователей в боте: {len(all_users)}', reply_markup = kb.admin_menu())

@dp.message_handler(state=Info.rassilka, content_types=types.ContentTypes.TEXT)
async def rassilka2(message: types.Message, state: FSMContext):
	if message.text.lower() == 'отмена':
		await bot.send_message(chat_id=message.chat.id, text='Ты вернулся в админ меню.', reply_markup=kb.admin_menu())
		await state.finish()
	else:
		text = message.text
		start_time = time.time()
		users = db.get_all_users()
		for user in users:
			try:
				await bot.send_message(chat_id=user[0], text=text)
				time.sleep(0.1)
			except:
				pass
		end_time = time.time()
		await bot.send_message(message.from_user.id, f"✔️ Рассылка успешно завершена за {round(end_time-start_time, 1)} сек. \n 》 Все пользователи получили ваше сообщение. 《", reply_markup=kb.admin_menu())
		await state.finish()

@dp.message_handler(content_types=['text'])
async def text(message: types.Message):
    if message.text.startswith(('https://www.tiktok.com','http://www.tiktok.com', 'https://vm.tiktok.com', 'http://vm.tiktok.com')):
        await bot.send_message(chat_id=message.chat.id, text='Ожидайте...')
        video_url = message.text
        await bot.send_message(chat_id=message.chat.id, text='Получаю информацию о видео...')
        video_r, audio_r = get_download_links(video_url)
        if video_r != None:
            await bot.send_video(
                chat_id=message.chat.id,
                video=video_r,
                caption='Вот твое видео:'
                )
            await bot.send_message(chat_id=message.chat.id, text='Скачиваю музыку из видео...')
            await bot.send_audio(
                chat_id=message.chat.id,
                audio=audio_r,
                title=f'result_{message.from_user.id}.mp3',
                caption='Вот музыка видео:'
                )
        else:
            await bot.send_message(chat_id=message.chat.id, text='Ошибка при скачивании, неверная ссылка, видео было удалено или я его не нашел.')
    else:
        await bot.send_message(chat_id=message.chat.id, text='Я тебя не понял, отправь мне ссылку на видео TikTok.')
if __name__ == "__main__":
	db.check_db()
	# Запускаем бота
	executor.start_polling(dp, skip_updates=True)
