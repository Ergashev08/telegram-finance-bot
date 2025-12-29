import telebot
from telebot import types
import json
import requests
from datetime import datetime
from flask import Flask
import threading
import os

# Замените на ваши данные
BOT_TOKEN = '8302450659:AAHgVJxjn9GUrY1ixNAQ_uoxy6ALjNP2bPo'
JSONBIN_API_KEY = '$2a$10$RBaqxBk9CB.MWUqTuaKL8OZVfOq3FWO1WOLb0sH2zXIvtjJLdP.ne'
JSONBIN_BIN_ID = '69524449d0ea881f4047077a'

bot = telebot.TeleBot(BOT_TOKEN)

# Загрузка данных из облака
def load_data():
    try:
        headers = {'X-Master-Key': JSONBIN_API_KEY}
        response = requests.get(
            f'https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}/latest',
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('record', {})
        print(f"Ошибка загрузки: {response.status_code}")
        return {}
    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")
        return {}

# Сохранение данных в облако
def save_data(data):
    try:
        headers = {
            'Content-Type': 'application/json',
            'X-Master-Key': JSONBIN_API_KEY
        }
        response = requests.put(
            f'https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}',
            json=data,
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            print("✅ Данные сохранены в облако")
            return True
        print(f"❌ Ошибка сохранения: {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return False

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
        "☁️ Ваши данные сохраняются в облаке!",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda msg: msg.text == '💰 Баланс')
def show_balance(message):
    user_id = str(message.from_user.id)
    data = load_data()
    balance = data.get(user_id, {}).get('balance', 0)
    
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
        
        processing_msg = bot.send_message(message.chat.id, "⏳ Сохраняю в облако...")
        
        data = load_data()
        if user_id not in data:
            data[user_id] = {'balance': 0, 'transactions': []}
        
        data[user_id]['balance'] += amount
        data[user_id]['transactions'].append({
            'type': 'income',
            'amount': amount,
            'category': category,
            'date': datetime.now().strftime('%d.%m.%Y %H:%M')
        })
        
        if save_data(data):
            bot.delete_message(message.chat.id, processing_msg.message_id)
            bot.send_message(
                message.chat.id,
                f"✅ Доход добавлен и сохранён в облако!\n\n"
                f"💰 Сумма: {amount:,.0f} сум\n"
                f"📁 Категория: {category}\n"
                f"💳 Новый баланс: {data[user_id]['balance']:,.0f} сум",
                reply_markup=main_menu()
            )
        else:
            bot.send_message(message.chat.id, "❌ Ошибка сохранения в облако", reply_markup=main_menu())
    except:
        bot.send_message(
            message.chat.id,
            "❌ Ошибка! Введите в формате: сумма, категория\nПример: 500000, зарплата",
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
        
        processing_msg = bot.send_message(message.chat.id, "⏳ Сохраняю в облако...")
        
        data = load_data()
        if user_id not in data:
            data[user_id] = {'balance': 0, 'transactions': []}
        
        data[user_id]['balance'] -= amount
        data[user_id]['transactions'].append({
            'type': 'expense',
            'amount': amount,
            'category': category,
            'date': datetime.now().strftime('%d.%m.%Y %H:%M')
        })
        
        if save_data(data):
            bot.delete_message(message.chat.id, processing_msg.message_id)
            bot.send_message(
                message.chat.id,
                f"✅ Расход добавлен и сохранён в облако!\n\n"
                f"💸 Сумма: {amount:,.0f} сум\n"
                f"📁 Категория: {category}\n"
                f"💳 Новый баланс: {data[user_id]['balance']:,.0f} сум",
                reply_markup=main_menu()
            )
        else:
            bot.send_message(message.chat.id, "❌ Ошибка сохранения в облако", reply_markup=main_menu())
    except:
        bot.send_message(
            message.chat.id,
            "❌ Ошибка! Введите в формате: сумма, категория\nПример: 50000, продукты",
            reply_markup=main_menu()
        )

@bot.message_handler(func=lambda msg: msg.text == '📊 Статистика')
def show_statistics(message):
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data or not data[user_id]['transactions']:
        bot.send_message(message.chat.id, "📊 Статистика пуста.\nДобавьте транзакции!")
        return
    
    transactions = data[user_id]['transactions']
    income_categories = {}
    expense_categories = {}
    total_income = 0
    total_expense = 0
    income_count = 0
    expense_count = 0
    
    for t in transactions:
        if t['type'] == 'income':
            total_income += t['amount']
            income_count += 1
            cat = t['category']
            income_categories[cat] = income_categories.get(cat, 0) + t['amount']
        else:
            total_expense += t['amount']
            expense_count += 1
            cat = t['category']
            expense_categories[cat] = expense_categories.get(cat, 0) + t['amount']
    
    balance = data[user_id]['balance']
    
    text = "📊 ФИНАНСОВАЯ СТАТИСТИКА\n"
    text += "=" * 30 + "\n\n"
    text += f"💰 Всего доходов: {total_income:,.0f} сум\n"
    text += f"   Количество: {income_count} операций\n"
    if income_count > 0:
        text += f"   Средний доход: {total_income/income_count:,.0f} сум\n"
    text += "\n"
    text += f"💸 Всего расходов: {total_expense:,.0f} сум\n"
    text += f"   Количество: {expense_count} операций\n"
    if expense_count > 0:
        text += f"   Средний расход: {total_expense/expense_count:,.0f} сум\n"
    text += "\n"
    text += f"💳 Текущий баланс: {balance:,.0f} сум\n"
    if total_income > 0:
        expense_percent = (total_expense / total_income) * 100
        text += f"📈 Расходы составляют {expense_percent:.1f}% от доходов\n"
    text += "\n" + "=" * 30 + "\n\n"
    
    if income_categories:
        text += "📈 ДОХОДЫ ПО КАТЕГОРИЯМ:\n\n"
        sorted_income = sorted(income_categories.items(), key=lambda x: -x[1])
        for i, (cat, amount) in enumerate(sorted_income, 1):
            percent = (amount / total_income) * 100
            text += f"{i}. {cat}\n   💵 {amount:,.0f} сум ({percent:.1f}%)\n\n"
    
    if expense_categories:
        text += "📉 РАСХОДЫ ПО КАТЕГОРИЯМ:\n\n"
        sorted_expense = sorted(expense_categories.items(), key=lambda x: -x[1])
        for i, (cat, amount) in enumerate(sorted_expense, 1):
            percent = (amount / total_expense) * 100
            text += f"{i}. {cat}\n   💸 {amount:,.0f} сум ({percent:.1f}%)\n\n"
    
    if len(expense_categories) > 0:
        text += "🔝 ТОП-3 РАСХОДОВ:\n"
        top_3 = sorted(expense_categories.items(), key=lambda x: -x[1])[:3]
        for i, (cat, amount) in enumerate(top_3, 1):
            text += f"   {i}. {cat}: {amount:,.0f} сум\n"
    
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda msg: msg.text == '📝 История')
def show_history(message):
    user_id = str(message.from_user.id)
    data = load_data()
    
    if user_id not in data or not data[user_id]['transactions']:
        bot.send_message(message.chat.id, "📝 История пуста")
        return
    
    transactions = data[user_id]['transactions']
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
        "⚠️ Вы уверены?\nЭто удалит все ваши данные из облака!",
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: msg.text == '✅ Да, очистить')
def clear_data(message):
    user_id = str(message.from_user.id)
    data = load_data()
    data[user_id] = {'balance': 0, 'transactions': []}
    save_data(data)
    bot.send_message(message.chat.id, "✅ Все данные очищены!", reply_markup=main_menu())

@bot.message_handler(func=lambda msg: msg.text == '❌ Отмена')
def cancel(message):
    bot.send_message(message.chat.id, "Отменено", reply_markup=main_menu())

# Flask веб-сервер для Render
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Telegram Finance Bot is running!"

@app.route('/status')
def status():
    return {"status": "online", "bot": "finance-bot"}

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def run_bot():
    print("☁️ Финансовый бот запущен!")
    print(f"🔑 API Key: {JSONBIN_API_KEY[:20] if len(JSONBIN_API_KEY) > 20 else '***'}...")
    print(f"📦 Bin ID: {JSONBIN_BIN_ID}")
    bot.infinity_polling()

if __name__ == '__main__':
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Запускаем бота
    run_bot()
