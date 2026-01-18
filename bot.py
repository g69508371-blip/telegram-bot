import logging
import os
from urllib.parse import urlparse
from telegram import Update, ReactionTypeEmoji, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from pyrogram import Client
from pyrogram.enums import ChatPrivileges
import asyncio

# Get environment variables
BOT_TOKENS = os.environ['BOT_TOKENS'].split(',')
MAIN_TOKEN = BOT_TOKENS[0]
DOMAIN = os.environ['DOMAIN']  # e.g., 'yourapp.onrender.com'
PORT = int(os.environ.get('PORT', 8443))  # Render sets PORT
API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']
PHONE_NUMBER = os.environ['PHONE_NUMBER']

# Pre-create Bot instances for each token
bots = [Bot(token) for token in BOT_TOKENS]

# Pre-fetch reaction bot usernames (including main if desired; skip bots[0] if not)
async def fetch_usernames():
    usernames = []
    for bot in bots:
        try:
            me = await bot.get_me()
            usernames.append(me.username)
        except Exception as e:
            logging.error(f"Error fetching username: {e}")
    return usernames

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Send /react <message_link> <emoji> to add reactions! Example: /react https://t.me/chatterbox_family/123 👍')

async def react(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 2:
        await update.message.reply_text('Usage: /react <message_link> <emoji>')
        return
   
    link = context.args[0]
    emoji = context.args[1]  # e.g., '👍'
   
    try:
        # Parse the link (e.g., https://t.me/username/123)
        parsed_url = urlparse(link)
        if parsed_url.scheme != 'https' or parsed_url.netloc != 't.me':
            raise ValueError("Invalid Telegram link.")
       
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) != 2:
            raise ValueError("Link should be in format https://t.me/username/message_id")
       
        username = path_parts[0]
        message_id = int(path_parts[1])
        chat_id = f'@{username}'  # Format as '@username' for API
       
        success_count = 0
        for bot in bots:
            try:
                await bot.set_message_reaction(
                    chat_id=chat_id,
                    message_id=message_id,
                    reaction=[ReactionTypeEmoji(emoji=emoji)]
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Error with bot: {e}")
       
        await update.message.reply_text(f'Added {success_count} reactions with {emoji}!')
    except ValueError as ve:
        await update.message.reply_text(f'Error: {ve}')
    except Exception as e:
        await update.message.reply_text(f'Failed to add reactions: {str(e)}')
        logger.error(f"Error: {e}")

async def auto_react(update: Update, context: CallbackContext) -> None:
    if update.message and update.message.chat.username == 'chatterbox_family':  # Your channel
        message_id = update.message.message_id
        chat_id = update.message.chat_id
        emoji = '❤'  # Default emoji; customize
       
        success_count = 0
        for bot in bots:
            try:
                await bot.set_message_reaction(
                    chat_id=chat_id,
                    message_id=message_id,
                    reaction=[ReactionTypeEmoji(emoji=emoji)]
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Error: {e}")
       
        logger.info(f'Auto-added {success_count} reactions to message {message_id}')

async def add_channel(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 1:
        await update.message.reply_text('Usage: /add <channel_username>')
        return
   
    channel_username = context.args[0]
   
    try:
        async with Client("userbot_session", api_id=API_ID, api_hash=API_HASH, phone_number=PHONE_NUMBER) as app:
            channel = await app.get_chat(channel_username)
           
            for bot_username in reaction_bot_usernames:
                try:
                    bot_user = await app.get_users(bot_username)
                    await app.promote_chat_member(
                        chat_id=channel.id,
                        user_id=bot_user.id,
                        privileges=ChatPrivileges(
                            can_change_info=False,
                            can_post_messages=True,
                            can_edit_messages=True,
                            can_delete_messages=False,
                            can_restrict_members=False,
                            can_invite_users=False,
                            can_pin_messages=False,
                            can_promote_members=False,
                            can_manage_video_chats=False,
                            is_anonymous=False,
                            can_manage_chat=True
                        )
                    )
                    logger.info(f"Added {bot_username} as admin to {channel_username}")
                except Exception as e:
                    logger.error(f"Error adding {bot_username}: {e}")
           
            await update.message.reply_text(f'Added all reaction bots to @{channel_username}!')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')
        logger.error(f"Error: {e}")

async def main_async():
    global reaction_bot_usernames
    reaction_bot_usernames = await fetch_usernames()
    application = Application.builder().token(MAIN_TOKEN).build()
   
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('react', react))
    application.add_handler(CommandHandler('add', add_channel))
    application.add_handler(MessageHandler(filters.ALL, auto_react))  # React to all new messages in monitored chats
   
    # Run as webhook
    await application.run_webhook(
        listen='0.0.0.0',
        port=PORT,
        url_path=MAIN_TOKEN,
        webhook_url=f'https://{DOMAIN}/{MAIN_TOKEN}'
    )

if __name__ == '__main__':
    asyncio.run(main_async())
