from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import json
import os

TOKEN = '8277370661:AAFNUaOrfptzNZcXHfTG-8AdgLYdDGeXFh4'
channel = '@work3dpc_help'
orders_file = 'orders.json'
if not os.path.exists(orders_file):
    with open(orders_file, 'w') as f:
        json.dump({}, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("3D печать", callback_data='category_3d')],
        [InlineKeyboardButton("Услуги ПК", callback_data='category_pc')]
    ]
    await update.message.reply_text('Выбери категорию для заказа:', reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith('category_'):
        category = data.split('_')[1].upper()
        context.user_data['category'] = category
        keyboard = [
            [InlineKeyboardButton("Москва", callback_data='city_Москва')],
            [InlineKeyboardButton("Санкт-Петербург", callback_data='city_Санкт-Петербург')],
            [InlineKeyboardButton("Крым", callback_data='city_Крым')],
            [InlineKeyboardButton("Другой", callback_data='city_Другой')]
        ]
        await query.edit_message_text('Выбери город:', reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith('city_'):
        city = data.split('_')[1]
        context.user_data['city'] = city
        await query.edit_message_text('Напиши описание услуги:')
        context.user_data['state'] = 'description'
    elif data.startswith('take_'):
        order_id = data.split('_')[1]
        with open(orders_file, 'r') as f:
            orders = json.load(f)
        if order_id in orders and orders[order_id]['status'] == 'open':
            orders[order_id]['status'] = 'accepted'
            orders[order_id]['maker'] = query.from_user.id
            with open(orders_file, 'w') as f:
                json.dump(orders, f)
            await query.edit_message_text('Заказ взят. Обсуди детали с заказчиком.')
            await context.bot.send_message(
                orders[order_id]['user_id'],
                f'Твой заказ #{order_id} взял @{query.from_user.username}. Пиши ему.'
            )
        else:
            await query.edit_message_text('Заказ уже взят или закрыт.')

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'state' in context.user_data:
        state = context.user_data['state']
        if state == 'description':
            context.user_data['description'] = update.message.text
            await update.message.reply_text('Укажи примерную стоимость (в рублях):')
            context.user_data['state'] = 'cost'
        elif state == 'cost':
            try:
                cost = int(update.message.text)
            except:
                cost = 0  # Default if not number
            context.user_data['cost'] = cost
            with open(orders_file, 'r') as f:
                orders = json.load(f)
            order_id = str(len(orders) + 1)
            order = {
                'category': context.user_data['category'],
                'city': context.user_data.get('city', 'Не указан'),
                'description': context.user_data['description'],
                'cost': cost,
                'user_id': update.message.chat_id,
                'status': 'open'
            }
            orders[order_id] = order
            with open(orders_file, 'w') as f:
                json.dump(orders, f)
            keyboard = [[InlineKeyboardButton("Взять заказ", callback_data=f'take_{order_id}')]]
            await context.bot.send_message(
                channel,
                f'Новый заказ #{order_id}\nКатегория: {order["category"]}\nГород: {order["city"]}\nОписание: {order["description"]}\nПримерная стоимость: {order["cost"]} руб.',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await update.message.reply_text(f'Заказ #{order_id} создан и опубликован.')
            context.user_data.clear()

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler('start', start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
app.run_polling()
