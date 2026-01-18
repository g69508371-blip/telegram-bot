import logging
from telegram import Update, ReactionTypeEmoji
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# List of your bot tokens (replace with yours)
BOT_TOKENS = [
    'YOUR_FIRST_BOT_TOKEN_HERE',
    'YOUR_SECOND_BOT_TOKEN_HERE',
    # Add more for more reactions
]

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Send me a message link or /react <chat_id> <message_id> <emoji> to add reactions!')

async def react(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 3:
        await update.message.reply_text('Usage: /react <chat_id> <message_id> <emoji>')
        return
    
    chat_id = context.args[0]
    message_id = int(context.args[1])
    emoji = context.args[2]  # e.g., '👍'
    
    success_count = 0
    for token in BOT_TOKENS:
        try:
            # Create a temporary app for each token to avoid conflicts
            temp_app = Application.builder().token(token).build()
            async with temp_app:
                await temp_app.bot.set_message_reaction(
                    chat_id=chat_id,
                    message_id=message_id,
                    reaction=[ReactionTypeEmoji(emoji=emoji)]
                )
            success_count += 1
        except Exception as e:
            logger.error(f"Error with token {token}: {e}")
    
    await update.message.reply_text(f'Added {success_count} reactions with {emoji}!')

def main() -> None:
    # Use your main bot token here (can be one from the pool)
    application = Application.builder().token(BOT_TOKENS[0]).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('react', react))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()