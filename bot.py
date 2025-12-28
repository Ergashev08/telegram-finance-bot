import telebot
from telebot import types
import json
import os
from datetime import datetime

# Замените на ваш токен от BotFather
BOT_TOKEN = '8302450659:AAHgVJxjn9GUrY1ixNAQ_uoxy6ALjNP2bPo'

bot = telebot.TeleBot(BOT_TOKEN)

# Файл для хранения данных
DATA_FILE = 'finance_data.json'

# Загрузка данных из файла
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

# Сохранение данных в файл
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Инициализация пользователя
def init_user(user_id):
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str not in data:
        data[user_id_str] = {
            'balance': 0,
            'transactions': []
        }
        save_data(data)
    return data

# Главное меню с кнопками
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('💰 Баланс', '📊 Статистика')
    markup.row('➕ Доход', '➖ Расход')
    markup.row('📝 История', '🗑 Очистить')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    init_user(user_id)
    bot.send_message(
        message.chat.id,
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я помогу вам вести учет финансов.\n\n"
        "✅ Ваши данные сохраняются автоматически!",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda msg: msg.text == '💰 Баланс')
def show_balance(message):
    user_id = str(message.from_user.id)
    data = load_data()
    balance = data[user_id]['balance']
    
    emoji = '✅' if balance >= 0 else '❌'
    bot.send_message(
        message.chat.id,
        f"{emoji} Ваш текущий баланс:\n\n"
        f"💵 {balance:,.0f} сум"
    )

@bot.message_handler(func=lambda msg: msg.text == '➕ Доход')
def add_income(message):
    msg = bot.send_message(
        message.chat.id,
        "💵 Введите сумму дохода и категорию через запятую:\n\n"
        "Пример: 500000, зарплата"
    )
    bot.register_next_step_handler(msg, process_income)

def process_income(message):
    try:
        user_id = str(message.from_user.id)
        parts = message.text.split(',')
        amount = float(parts[0].strip())
        category = parts[1].strip() if len(parts) > 1 else 'Доход'
        
        data = load_data()
        data[user_id]['balance'] += amount
        data[user_id]['transactions'].append({
            'type': 'income',
            'amount': amount,
            'category': category,
            'date': datetime.now().strftime('%d.%m.%Y %H:%M')
        })
        save_data(data)
        
        bot.send_message(
            message.chat.id,
            f"✅ Доход добавлен и сохранён!\n\n"
            f"💰 Сумма: {amount:,.0f} сум\n"
            f"📁 Категория: {category}\n"
            f"💳 Новый баланс: {data[user_id]['balance']:,.0f} сум",
            reply_markup=main_menu()
        )
    except:
        bot.send_message(
            message.chat.id,
            "❌ Ошибка! Введите в формате: сумма, категория\n"
            "Пример: 500000, зарплата",
            reply_markup=main_menu()
        )

@bot.message_handler(func=lambda msg: msg.text == '➖ Расход')
def add_expense(message):
    msg = bot.send_message(
        message.chat.id,
        "💸 Введите сумму расхода и категорию через запятую:\n\n"
        "Пример: 50000, продукты"
    )
    bot.register_next_step_handler(msg, process_expense)

def process_expense(message):
    try:
        user_id = str(message.from_user.id)
        parts = message.text.split(',')
        amount = float(parts[0].strip())
        category = parts[1].strip() if len(parts) > 1 else 'Расход'
        
        data = load_data()
        data[user_id]['balance'] -= amount
        data[user_id]['transactions'].append({
            'type': 'expense',
            'amount': amount,
            'category': category,
            'date': datetime.now().strftime('%d.%m.%Y %H:%M')
        })
        save_data(data)
        
        bot.send_message(
            message.chat.id,
            f"✅ Расход добавлен и сохранён!\n\n"
            f"💸 Сумма: {amount:,.0f} сум\n"
            f"📁 Категория: {category}\n"
            f"💳 Новый баланс: {data[user_id]['balance']:,.0f} сум",
            reply_markup=main_menu()
        )
    except:
        bot.send_message(
            message.chat.id,
            "❌ Ошибка! Введите в формате: сумма, категория\n"
            "Пример: 50000, продукты",
            reply_markup=main_menu()
        )

@bot.message_handler(func=lambda msg: msg.text == '📊 Статистика')
def show_statistics(message):
    user_id = str(message.from_user.id)
    data = load_data()
    transactions = data[user_id]['transactions']
    
    if not transactions:
        bot.send_message(
            message.chat.id,
            "📊 Статистика пуста.\nДобавьте транзакции!"
        )
        return
    
    # Подсчёт по категориям
    income_categories = {}
    expense_categories = {}
    total_income = 0
    total_expense = 0
    
    for t in transactions:
        if t['type'] == 'income':
            total_income += t['amount']
            cat = t['category']
            income_categories[cat] = income_categories.get(cat, 0) + t['amount']
        else:
            total_expense += t['amount']
            cat = t['category']
            expense_categories[cat] = expense_categories.get(cat, 0) + t['amount']
    
    text = "📊 Статистика:\n\n"
    text += f"💰 Всего доходов: {total_income:,.0f} сум\n"
    text += f"💸 Всего расходов: {total_expense:,.0f} сум\n"
    text += f"💳 Баланс: {data[user_id]['balance']:,.0f} сум\n\n"
    
    if income_categories:
        text += "📈 Доходы по категориям:\n"
        for cat, amount in sorted(income_categories.items(), key=lambda x: -x[1]):
            text += f"  • {cat}: {amount:,.0f} сум\n"
        text += "\n"
    
    if expense_categories:
        text += "📉 Расходы по категориям:\n"
        for cat, amount in sorted(expense_categories.items(), key=lambda x: -x[1]):
            text += f"  • {cat}: {amount:,.0f} сум\n"
    
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda msg: msg.text == '📝 История')
def show_history(message):
    user_id = str(message.from_user.id)
    data = load_data()
    transactions = data[user_id]['transactions']
    
    if not transactions:
        bot.send_message(
            message.chat.id,
            "📝 История пуста"
        )
        return
    
    text = "📝 Последние 10 транзакций:\n\n"
    for t in reversed(transactions[-10:]):
        emoji = '💰' if t['type'] == 'income' else '💸'
        sign = '+' if t['type'] == 'income' else '-'
        text += f"{emoji} {sign}{t['amount']:,.0f} сум\n"
        text += f"   {t['category']} • {t['date']}\n\n"
    
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda msg: msg.text == '🗑 Очистить')
def confirm_clear(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('✅ Да, очистить', '❌ Отмена')
    bot.send_message(
        message.chat.id,
        "⚠️ Вы уверены?\nЭто удалит все ваши данные!",
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: msg.text == '✅ Да, очистить')
def clear_data(message):
    user_id = str(message.from_user.id)
    data = load_data()
    data[user_id] = {'balance': 0, 'transactions': []}
    save_data(data)
    
    bot.send_message(
        message.chat.id,
        "✅ Все данные очищены!",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda msg: msg.text == '❌ Отмена')
def cancel(message):
    bot.send_message(
        message.chat.id,
        "Отменено",
        reply_markup=main_menu()
    )

print("✅ Финансовый бот запущен с сохранением данных!")
print(f"📁 Данные сохраняются в: {os.path.abspath(DATA_FILE)}")
bot.infinity_polling()
