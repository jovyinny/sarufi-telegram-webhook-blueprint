import os
import uvicorn
from sarufi import Sarufi
from dataclasses import dataclass

from telegram import (
    Update,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application,
    CallbackContext,
    ContextTypes,
    ExtBot
)
from fastapi import (
   FastAPI,
   Request,
   BackgroundTasks,
   Response,
   status)

from dotenv import load_dotenv

from utils import (
   send_response,
   simulate_typing,
  get_clicked_button_text)

from logger import logger


app = FastAPI()

load_dotenv()

# Check if all required environment variables are set

assert os.getenv("TELEGRAM_BOT_TOKEN") , "TELEGRAM_BOT_TOKEN not set"
assert os.getenv("SARUFI_API_KEY"), "SARUFI_API_KEY not set"
assert os.getenv("SARUFI_BOT_ID"), "SARUFI_BOT_ID not set"
assert os.getenv("START_MESSAGE"), "START_MESSAGE not set"

# Set up Sarufi and get bot's name
sarufi = Sarufi(api_key=os.getenv("SARUFI_API_KEY"))
bot_name=sarufi.get_bot(os.getenv("SARUFI_BOT_ID")).name
PORT = os.getenv("PORT", 8000)

@dataclass
class WebhookUpdate:
    """Simple dataclass to wrap a custom update type"""
    user_id: int
    payload: str

class CustomContext(CallbackContext[ExtBot, dict, dict, dict]):
    """
    Custom CallbackContext class that makes `user_data` available for updates of type
    `WebhookUpdate`.
    """
    @classmethod
    def from_update(
        cls,
        update: object,
        application: "Application",
    ) -> "CustomContext":
        if isinstance(update, WebhookUpdate):
            return cls(application=application, user_id=update.user_id)
        return super().from_update(update, application)


async def respond(message, chat_id,message_type="text")->dict:
  """
  Responds to the user's message.
  """
  response = sarufi.chat(os.getenv("SARUFI_BOT_ID"), chat_id, message,channel="whatsapp",message_type= message_type)
  response = response.get("actions")
  return response


async def reply_with_typing(update: Update, context: CustomContext, message)->None:

  await simulate_typing(update, context)
  await send_response(update,context,message)


async def echo(update: Update, context: CallbackContext)->None:
  """
  Handles messages sent to the bot.
  """
  chat_id = update.message.chat.id
  response = await respond(update.message.text, chat_id)
  await reply_with_typing(update, context, response)

async def button_click(update: Update, context: CallbackContext)->None:
  query = update.callback_query
  buttons=query.message.reply_markup.inline_keyboard
  message=query.data
  button_text = get_clicked_button_text(buttons,message)
  context.user_data["selection"] = button_text
  chat_id=update.effective_chat.id

  await context.bot.send_message(chat_id=chat_id, 
                                  text=button_text, 
                                  reply_markup=ReplyKeyboardRemove(), 
                                  reply_to_message_id=query.message.message_id
                                  )

  response = await respond(message=message,
                            chat_id=chat_id, 
                            message_type="interactive"
                            )
  
  await reply_with_typing(update, context, response)


# COMMAND HANDLERS
async def start(update: Update, context: CustomContext)->None:
  """
  Starts the bot.
  """
  try:

    first_name = update.message.chat.first_name
    await reply_with_typing(
        update,
        context,
        os.getenv("START_MESSAGE","Welcome to {bot_name}").format(user_name=first_name,bot_name=bot_name),
    )
  except Exception as error:
    logger.error(f"Error: {error} starting the bot")
    await reply_with_typing(update, context, "Welcome to the bot")


async def help(update: Update, context: CallbackContext)->None:
  """
  Shows the help message.
  """
  await reply_with_typing(update, context, "Help message")



# Set up application    
context_types = ContextTypes(context=CustomContext)
application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).updater(None).context_types(context_types).build()

@app.get("/")
async def webhook(request: Request):
    return Response(content="Webhook--Ok",status_code=status.HTTP_200_OK)


@app.post("/")
async def webhook_handler(request: Request,tasks: BackgroundTasks):
    update_data = await request.json()
    update = Update.de_json(data=update_data, bot=application.bot)
    
    if update.message and update.message.text:
        # Check for specific commands and call the appropriate command handlers otherwise repond to text
        if update.message.text.startswith('/start'):
            await start(update, CustomContext.from_update(update, application))
        elif update.message.text.startswith('/help'):
            await help(update, CustomContext.from_update(update, application))
        else:
            tasks.add_task(echo,update, CustomContext.from_update(update, application))
    elif update.callback_query:
        await button_click(update, CustomContext.from_update(update, application))

    return Response(content="OK",status_code=status.HTTP_200_OK)


if __name__ == "__main__":
    uvicorn.run("main:app",port=PORT)