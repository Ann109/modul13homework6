from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
import asyncio

# Инициализация бота и диспетчера
bot = Bot(token='7488434207:AAGaZzGU__wkyE5u3k8S7GWTIVzxvjo-T5k')
storage = MemoryStorage()
router = Router()
dp = Dispatcher(storage=storage)
dp.include_router(router)

button_calories = InlineKeyboardButton(text='Рассчитать норму калорий', callback_data='calories')
button_formula = InlineKeyboardButton(text='Формулы расчёта', callback_data='formula')
inline_kb = InlineKeyboardMarkup(inline_keyboard=[[button_calories], [button_formula]], resize_keyboard=True)


class UserState(StatesGroup):
    age = State()
    growth = State()  # роста
    weight = State()  # веса


def is_valid_number(value):
    return value.isdigit() and int(value) > 0


# Ответ на нажатие кнопки 'Рассчитать'
@router.callback_query(F.data == 'main_menu')
async def set_age(call: CallbackQuery): # FSMContext хранит данные о текущем состоянии пользователя и позволяет изменять их
    await call.message.answer('Выбери опцию:', reply_markup=inline_kb)


# Функция для отображения формул расчёта
@router.callback_query(F.data == 'formula')
async def get_formula(call: CallbackQuery):
    formula_text = ('10*вес(кг)+6,25*рост(см)-5*возраст(г)-161')
    await call.message.answer(formula_text)


@router.callback_query(F.data == 'calories')
async def set_gender(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите свой возраст:")
    await state.set_state(UserState.age)


# Хендлер для обработки возраста
@router.message(UserState.age)
async def set_growth(message: types.Message, state: FSMContext):
    if is_valid_number(message.text):
        await state.update_data(age=int(message.text))  # обновляет данные состояния, сохраняя возраст пользователя
        await message.answer("Введите свой рост (в см):")
        await state.set_state(UserState.growth)  # устанавливаем состояние growth, где бот ожидает ввода роста
    else:
        await message.answer("Возраст должен быть положительным числом. Пожалуйста, введите корректное значение.")


# Хендлер для обработки роста
@router.message(UserState.growth)
async def set_weight(message: types.Message, state: FSMContext):
    if is_valid_number(message.text):
        await state.update_data(growth=int(message.text))  # обновляет данные состояния, сохраняя рост пользователя
        await message.answer("Введите свой вес (в кг):")
        await state.set_state(UserState.weight)  # устанавливаем состояние weight, где бот ожидает ввода вес
    else:
        await message.answer("Рост должен быть положительным числом. Пожалуйста, введите корректное значение.")


# Хендлер для обработки веса и вычисления нормы калорий
@router.message(UserState.weight)
async def send_calories(message: types.Message, state: FSMContext):
    if is_valid_number(message.text):
        await state.update_data(weight=int(message.text))  # обновляет данные состояния, сохраняя вес пользователя
        data = await state.get_data()
        age = data['age']
        growth = data['growth']
        weight = data['weight']
        # Формула Миффлина - Сан Жеора для мужчин
        calories = 10 * weight + 6.25 * growth - 5 * age + 5
        await message.answer(f"Ваша норма калорий: {calories:.2f} ккал в день.")
        await state.clear()  # Завершение машины состояний
    else:
        await message.answer("Вес должен быть положительным числом. Пожалуйста, введите корректное значение.")


# Команда start
@dp.message(Command("start"))
async def start_form(message: Message):
    await message.answer("Привет! Я бот, помогающий твоему здоровью. Если хочешь узнать свою суточную норму "
                         "калорий, то нажми 'Рассчитать'.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Рассчитать', callback_data='main_menu')]]))


# Хендлер для перенаправления всех остальных сообщений на start
@router.message(~F.text.lower('Рассчитать') and ~F.state(UserState.age) and ~F.state(UserState.growth)
                and ~F.state(UserState.weight))
async def redirect_to_start(message: types.Message):
    await start_form(message)  # Перенаправляем сообщение на хендлер команды /start


# Основная функция запуска бота
async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())