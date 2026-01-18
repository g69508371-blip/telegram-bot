import logging
import os
from urllib.parse import urlparse
from telegram import Update, ReactionTypeEmoji, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Get environment variables
BOT_TOKENS = os.environ['BOT_TOKENS'].split(',')
MAIN_TOKEN = BOT_TOKENS[0]
DOMAIN = os.environ['DOMAIN']  # e.g., 'yourapp.onrender.com'
PORT = int(os.environ.get('PORT', 8443))  # Render sets PORT

# Pre-create Bot instances for each token
bots = [Bot(token) for token in BOT_TOKENS]

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

def main() -> None:
    application = Application.builder().token(MAIN_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('react', react))
    application.add_handler(MessageHandler(filters.ALL, auto_react))  # React to all new messages in monitored chats
    
    # Run as webhook
    application.run_webhook(
        listen='0.0.0.0',
        port=PORT,
        url_path=MAIN_TOKEN,
        webhook_url=f'https://{DOMAIN}/{MAIN_TOKEN}'
    )

if __name__ == '__main__':
    main()
