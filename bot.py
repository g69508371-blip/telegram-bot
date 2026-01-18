import logging
import os
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
    await update.message.reply_text('Send me a message link or /react <chat_id> <message_id> <emoji> to add reactions!')

async def react(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 3:
        await update.message.reply_text('Usage: /react <chat_id> <message_id> <emoji>')
        return
    
    chat_id = context.args[0]  # Can be str like '@channel' or int
    message_id = int(context.args[1])
    emoji = context.args[2]  # e.g., '👍'
    
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

async def auto_react(update: Update, context: CallbackContext) -> None:
    if update.message and update.message.chat.username == 'chatterbox_family':  # Replace with your channel username
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
