from aiogram import Bot, types, md
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from tmdbv3api import TMDb, Movie
import os
from collections import defaultdict
import typing as tp


TOKEN = os.environ['BOT_TOKEN']

WEBHOOK_HOST = 'https://shrouded-gorge-03991.herokuapp.com'
WEBHOOK_PATH = '/webhook/'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.environ.get('PORT')


bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


tmdb = TMDb()
tmdb.api_key = os.environ['TMDB_API_KEY']
tmdb.debug = False


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message) -> None:
    await message.reply("Привет!\nЯ MovieBot!\nВведите название фильма и я расскажу вам о нем!")


NUM_MOVIES = 5
MOVIES_DICT: tp.DefaultDict[str, tp.Any] = defaultdict(str)
MAX_TITLE_LEN = 25


@dp.message_handler()
async def find_movie(message: types.Message) -> None:
    query = message.text
    tmdb.language = 'ru'
    movie_engine_ru = Movie()
    movie_list_ru = movie_engine_ru.search(query)[:NUM_MOVIES]

    tmdb.language = 'en'
    movie_engine_en = Movie()
    movie_list_en = movie_engine_en.search(query)[:NUM_MOVIES]

    global MOVIES_DICT
    if len(movie_list_ru) > 0:
        captions_kb = types.InlineKeyboardMarkup(row_width=1)
        for i, movie in enumerate(movie_list_ru):
            title = movie.title
            if len(title) > MAX_TITLE_LEN:
                title = title[:MAX_TITLE_LEN] + "..."
            if hasattr(movie, 'release_date'):
                year = movie.release_date.split('-')[0]
                caption = f"{title} ({year})"
            else:
                caption = title
            if not movie.overview and movie_list_en[i].overview:
                movie.overview = movie_list_en[i].overview
            MOVIES_DICT[caption] = movie

            captions_kb.add(types.InlineKeyboardButton(caption, callback_data=caption))

        await message.reply("Какой именно фильм вас интересует?", reply_markup=captions_kb)
    else:
        await message.reply("Увы, данный фильм не найден в базе. Попробуйте уточнить название.")


@dp.callback_query_handler()
async def process_callback(callback_query: types.CallbackQuery) -> None:
    caption = callback_query.data
    global MOVIES_DICT
    movie = MOVIES_DICT[caption]
    watch_url = f"https://www.themoviedb.org/movie/{movie.id}/watch?language=ru"
    description = md.text(f"{md.bold(caption)}\n\n{movie.overview}\n\nГде посмотреть:\n{watch_url}")
    if movie.poster_path:
        poster_url = f"https://image.tmdb.org/t/p/original{movie.poster_path}"
        await bot.send_photo(callback_query.message.chat.id, poster_url, description, types.ParseMode.MARKDOWN)
    else:
        await bot.send_message(callback_query.message.chat.id, description, types.ParseMode.MARKDOWN)


if __name__ == '__main__':
    executor.start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH,
                           host=WEBAPP_HOST, port=WEBAPP_PORT)
