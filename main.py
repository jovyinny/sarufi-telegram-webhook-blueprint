import os
import uvicorn
import asyncio
from dataclasses import dataclass

from sarufi import Sarufi
from starlette.routing import Route
from starlette.requests import Request
from starlette.applications import Starlette
from starlette.responses import Response
from telegram import (
    Update,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ExtBot,
    filters,
    MessageHandler,
    CallbackQueryHandler
)
from dotenv import load_dotenv

from utils import (
   send_response,
   simulate_typing,
  get_clicked_button_text)

load_dotenv()

# Set up Sarufi and get bot's name
sarufi = Sarufi(api_key=os.getenv("SARUFI_API_KEY"))
bot_name=sarufi.get_bot(os.getenv("SARUFI_BOT_ID")).name

PORT = 8000

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
  first_name = update.message.chat.first_name
  await reply_with_typing(
      update,
      context,
      os.getenv("START_MESSAGE").format(name=first_name,bot_name=bot_name),
  )


async def help(update: Update, context: CallbackContext)->None:
  """
  Shows the help message.
  """
  await reply_with_typing(update, context, "Help message")



# Set up application    
context_types = ContextTypes(context=CustomContext)
application = (
    Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).updater(None).context_types(context_types).build()
)



async def telegram(request: Request) -> Response:
    """Handle incoming Telegram updates by putting them into the `update_queue`"""
    await application.update_queue.put(
        Update.de_json(data=await request.json(), bot=application.bot)
    )
    return Response()

# 
app = Starlette(
        routes=[
            Route("/", telegram, methods=["POST"]),
        ]
    )

async def main() -> None:
    """Set up the application and a custom webserver."""
    
    # register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(MessageHandler(filters.TEXT, echo))
    application.add_handler(CallbackQueryHandler(button_click))
    
    # Set up webserver
    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=app,
            port=PORT,
            use_colors=False,
            host="127.0.0.1",
            reload=True
        )
    )

    # Run application and webserver together
    async with application:
        await application.start()
        await webserver.serve()
        await application.stop()


if __name__ == "__main__":
    asyncio.run(main())