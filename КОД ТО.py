import os
import shutil
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# Указываем токен бота
API_TOKEN = '7400618778:AAEXmaa3QTATXG30U93dnEdT34NFL5m_T60'  # Замените на свой токен

# Создаем бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Создаем клавиатуру с кнопками
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("Фото БС снаружи"))
keyboard.add(KeyboardButton("Фото БС внутри помещения"))
keyboard.add(KeyboardButton("Фото АМС"))
keyboard.add(KeyboardButton("Сформировать папку"))  # Кнопка для завершения сессии
keyboard.add(KeyboardButton("Начать"))  # Кнопка для начала новой работы

# Папки для фотографий
BASE_DIR = "photos"

# Словарь для хранения данных
user_data = {}


def ensure_dir_exists(dir_path):
    """Создает папку, если она не существует"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


# Начало диалога с пользователем
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        # Запрос номера базовой станции
        await message.answer("Пожалуйста, введите номер базовой станции.")
        user_data[user_id] = {"base_station_number": None, "current_category": None}
    else:
        await message.answer("Вы уже начали работу. Выберите категорию для отправки фото:", reply_markup=keyboard)


# Обработка номера базовой станции
@dp.message_handler(lambda message: message.text.isdigit())
async def handle_base_station_number(message: types.Message):
    user_id = message.from_user.id
    base_number = message.text

    if user_id in user_data:
        user_data[user_id]["base_station_number"] = base_number

        # Формируем корневую папку и подкатегории
        root_dir = os.path.join(BASE_DIR, f"ТО_{base_number}")
        ensure_dir_exists(root_dir)

        categories = [
            "Фото БС снаружи",
            "Фото БС внутри помещения",
            "Фото АМС"
        ]
        for category in categories:
            ensure_dir_exists(os.path.join(root_dir, category))

        await message.answer(
            f"Номер базовой станции установлен: {base_number}. Теперь отправляйте фото в соответствующие категории:",
            reply_markup=keyboard
        )


# Обработка выбора категории для отправки фото
@dp.message_handler(lambda message: message.text in ["Фото БС снаружи", "Фото БС внутри помещения", "Фото АМС"])
async def select_category(message: types.Message):
    user_id = message.from_user.id
    category = message.text
    if user_id in user_data and user_data[user_id]["base_station_number"]:
        user_data[user_id]["current_category"] = category
        await message.answer(f"Вы выбрали: {category}. Теперь отправьте фото.")
    else:
        await message.answer("Сначала укажите номер базовой станции.")


# Обработка полученных фотографий
@dp.message_handler(content_types=['photo'])
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    category = user_data.get(user_id, {}).get("current_category")
    base_number = user_data.get(user_id, {}).get("base_station_number")

    if category and base_number:
        photo_id = message.photo[-1].file_id
        photo_file = await bot.get_file(photo_id)

        # Загружаем файл
        photo_path = f"{photo_id}.jpg"
        await bot.download_file(photo_file.file_path, photo_path)

        # Определяем папку для сохранения
        root_dir = os.path.join(BASE_DIR, f"ТО_{base_number}")
        category_name = category
        save_dir = os.path.join(root_dir, category_name)

        # Путь для перемещения фотографии
        dest_path = os.path.join(save_dir, photo_path)

        # Создаем папку для категории, если она не существует
        ensure_dir_exists(save_dir)

        # Перемещаем файл в нужную папку
        shutil.move(photo_path, dest_path)

        # Путь к локальной сети (например, smb или другой доступный путь)
        network_path = r'C:\Users\17vas\OneDrive\Desktop\АВАВА'
        final_network_path = os.path.join(network_path, f'ТО_{base_number}', category_name)

        try:
            # Копируем файл в локальную сеть
            ensure_dir_exists(final_network_path)
            shutil.copy(dest_path, final_network_path)
            await message.answer(
                f"Фото сохранено и отправлено в локальную сеть: {category} с номером базовой станции: {base_number}")
        except Exception as e:
            await message.answer(f"Произошла ошибка при отправке в сеть: {e}")

        # Очищаем текущую категорию и предоставляем выбор
        user_data[user_id]["current_category"] = None
        await message.answer("Фотография сохранена. Выберите другую категорию или завершите работу:",
                             reply_markup=keyboard)
    else:
        await message.answer("Пожалуйста, выберите категорию и отправьте фото.")


# Обработка нажатия на кнопку "Сформировать папку" (для завершения сессии)
@dp.message_handler(lambda message: message.text == "Сформировать папку")
async def end_session(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
    await message.answer("Сессия завершена. Вы можете начать новую работу или выйти.", reply_markup=keyboard)


# Обработка нажатия на кнопку "Начать"
@dp.message_handler(lambda message: message.text == "Начать")
async def restart(message: types.Message):
    user_id = message.from_user.id
    # Очистка данных пользователя
    if user_id in user_data:
        del user_data[user_id]
    # Запрос номера базовой станции
    await start(message)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
