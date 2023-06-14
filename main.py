import os
import time
import uvicorn
import logging
import asyncio
import telegram
import requests
# import functools
# import html
from http import HTTPStatus
from dataclasses import dataclass

from sarufi import Sarufi
from starlette.routing import Route
from starlette.requests import Request
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response
from telegram import (
    Update,
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ExtBot,
    filters,
    MessageHandler,
    TypeHandler,
    CallbackQueryHandler
)
from dotenv import load_dotenv


load_dotenv()

# Set up Sarufi and get bot's name
sarufi = Sarufi(api_key=os.environ["sarufi_api_key"])
bot_name=sarufi.get_bot(os.environ["sarufi_bot_id"]).name

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


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



def get_buttons(data:dict,type:str)->list:
  buttons=[]
  if type=="reply_button":
    
    for button in data.get("buttons"):
      button_title=button.get("reply").get("title")
      button_id=button.get("reply").get("id")
      button_data=[InlineKeyboardButton(button_title,callback_data=button_id)]
      buttons.append(button_data)
    return buttons
  
  else:
    
    for menu in data.get("sections")[0].get("rows"):
      menu_title=menu.get("title")
      menu_id=menu.get("id")
      menu_button=[InlineKeyboardButton(menu_title,callback_data=menu_id)]
      buttons.append(menu_button)
    return buttons


def get_clicked_button_text(buttons:tuple,button_callback_data:str)-> str:
  for button in buttons:
    if button[0].callback_data==button_callback_data:
      return button[0].text


async def send_medias(update: Update,context: CallbackContext,media:dict,type:str):
  chat_id=update.effective_chat.id
  
  for file in media:
    url=file.get("link")
    caption=file.get("caption")
    
    if type=="images":
      response = requests.get(url)
      await context.bot.send_photo(chat_id=chat_id, photo=response.content,caption=caption)

    elif type=="audios":
      response = requests.get(url)
      await context.bot.send_audi(chat_id=chat_id, audio=response.content,caption=caption)
    
    elif type=="videos":
      response = requests.get(url)
      await context.bot.send_video(chat_id=chat_id, video=response.content,caption=caption)
    

    elif type=="documents":
      response = requests.get(url)
      await context.bot.send_document(chat_id=chat_id, document=response.content,caption=caption)


    elif type=="stickers":
      response = requests.get(url)
      await context.bot.send_stickers(chat_id=chat_id, sticker=response.content,caption=caption)

    else:
      logging.error(f"Sorry unrecognized media {type}")


async def respond(message, chat_id,message_type="text")->dict:
  """
  Responds to the user's message.
  """
  response = sarufi.chat(os.environ["sarufi_bot_id"], chat_id, message,channel="whatsapp",message_type= message_type)
  response = response.get("actions")
  return response


async def simulate_typing(update: Update, context: CallbackContext)->None:
  await context.bot.send_chat_action(
      chat_id=update.effective_chat.id, action=telegram.constants.ChatAction.TYPING
  )
  time.sleep(0.01)


async def reply_with_typing(update: Update, context: CustomContext, message)->None:

  await simulate_typing(update, context)
  chat_id=update.effective_chat.id
  
  if isinstance(message,dict) or isinstance(message,list):

    for action in (message):
      if action.get("send_message") and not action["send_message"]==['']:
        message = action.get("send_message")

        if isinstance(message, list):
            message = "\n".join(message)
        await context.bot.send_message(chat_id=chat_id, text=message)
      
      elif action.get("send_reply_button"):
        reply_button = action.get("send_reply_button")
        message=reply_button.get("body").get("text")
        buttons= get_buttons(reply_button.get("action"),"reply_button")              
        markdown=InlineKeyboardMarkup(buttons)

        await context.bot.send_message(chat_id=chat_id, text=message,reply_markup=markdown)

      elif action.get("send_button"):
        buttons=action.get("send_button")
        message=buttons.get("body")
        menus= get_buttons(buttons.get("action"),"button")
        markdown=InlineKeyboardMarkup(menus)

        await context.bot.send_message(chat_id=chat_id, text=message,reply_markup=markdown)

      elif action.get("send_images"):
        images=action.get("send_images")
        await send_medias(update,context,images,"images")

      elif action.get("send_videos"):
        videos=action.get("send_videos")
        await send_medias(update,context,videos,"videos")

      elif action.get("send_audios"):
        audios=action.get("send_audios")
        await send_medias(update,context,audios,"audios")

      elif action.get("send_documents"):
        documents=action.get("send_documents")
        await send_medias(update,context,documents,"documents")

      elif action.get("send_stickers"):
        stickers=action.get("send_stickers")
        await send_medias(update,context,stickers,"stickers")

      else:
        logger.error("Unkown action")

  else:
    await context.bot.send_message(chat_id=chat_id, text=message)


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


# Comand handlers
async def start(bot_name:str,update: Update, context: CustomContext)->None:
  """
  Starts the bot.
  """

#   first_name = update.message.chat.first_name
#   await reply_with_typing(
#       update,
#       context,
#       os.environ["start_message"].format(name=first_name,bot_name=bot_name),
#   )


async def help(update: Update, context: CallbackContext)->None:
  """
  Shows the help message.
  """
  await reply_with_typing(update, context, "Help message")



async def webhook_update(update: WebhookUpdate, context: CustomContext) -> None:
    """Callback that handles the custom updates."""
    chat_member = await context.bot.get_chat_member(chat_id=update.user_id, user_id=update.user_id)
    payloads = context.user_data.setdefault("payloads", [])
    payloads.append(update.payload)
    combined_payloads = "</code>\n• <code>".join(payloads)
    text = (
        f"The user {chat_member.user.mention_html()} has sent a new payload. "
        f"So far they have sent the following payloads: \n\n• <code>{combined_payloads}</code>"
    )
    # text="sdasd"
    await context.bot.send_message(
        chat_id=update.user_id, text=text, parse_mode=ParseMode.HTML
    )


async def main() -> None:
    """Set up the application and a custom webserver."""
    url = "https://dc8c-102-64-70-79.ngrok-free.app"
    admin_chat_id = 123456
    port = 8000

    context_types = ContextTypes(context=CustomContext)
    
    # Here we set updater to None because we want our custom webhook server to handle the updates
    # and hence we don't need an Updater instance
    
    application = (
        Application.builder().token(os.getenv("token")).updater(None).context_types(context_types).build()
    )

    # save the values in `bot_data` such that we may easily access them in the callbacks
    application.bot_data["url"] = url

    # partial functions
    # partial_handler=functools.partial(start,bot_name)

    # register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(TypeHandler(type=WebhookUpdate, callback=webhook_update))
    application.add_handler(MessageHandler(filters.TEXT, echo))
    application.add_handler(CallbackQueryHandler(button_click))

    # Pass webhook settings to telegram
    await application.bot.set_webhook(url=f"{url}/telegram")
            
    # Set up webserver
    async def telegram(request: Request) -> Response:
        """Handle incoming Telegram updates by putting them into the `update_queue`"""
        await application.update_queue.put(
            Update.de_json(data=await request.json(), bot=application.bot)
        )
        return Response()

    async def custom_updates(request: Request) -> PlainTextResponse:
        """
        Handle incoming webhook updates by also putting them into the `update_queue` if
        the required parameters were passed correctly.
        """
        try:
            user_id = int(request.query_params["user_id"])
            payload = request.query_params["payload"]
        except KeyError:
            return PlainTextResponse(
                status_code=HTTPStatus.BAD_REQUEST,
                content="Please pass both `user_id` and `payload` as query parameters.",
            )
        except ValueError:
            return PlainTextResponse(
                status_code=HTTPStatus.BAD_REQUEST,
                content="The `user_id` must be a string!",
            )

        await application.update_queue.put(WebhookUpdate(user_id=user_id, payload=payload))
        return PlainTextResponse("Thank you for the submission! It's being forwarded.")

    async def health(_: Request) -> PlainTextResponse:
        """For the health endpoint, reply with a simple plain text message."""
        return PlainTextResponse(content="The bot is still running fine :)")

    starlette_app = Starlette(
        routes=[
            Route("/telegram", telegram, methods=["POST"]),
            # Route("/healthcheck", health, methods=["GET"]),
            # Route("/submitpayload", custom_updates, methods=["POST", "GET"]),
        ]
    )
    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=starlette_app,
            port=port,
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