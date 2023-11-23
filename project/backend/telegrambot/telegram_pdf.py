import asyncio
from aiogram import Bot, types

async def send_message_to_user(bot, user_chat_id):
    message_to_user = 'Привет, это сообщение отправлено тебе из Python через бота!'
    await bot.send_message(chat_id=user_chat_id, text=message_to_user)

async def scheduled(wait_for, bot, user_chat_id):
    while True:
        await send_message_to_user(bot, user_chat_id)
        await asyncio.sleep(wait_for)

if __name__ == '__main__':
    bot_token = '6803088063:AAFAPtBq7NVjh8z-N9-wBi6V-oSXid0yFWM'
    bot = Bot(token=bot_token)

    user_chat_id = '968388749'

    loop = asyncio.get_event_loop()
    loop.create_task(scheduled(10, bot, user_chat_id))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()