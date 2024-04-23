import time
import requests
from telegram import InlineKeyboardButton,Update,InlineKeyboardMarkup,constants
from telegram.ext import CallbackContext
from logger import logger

def get_buttons(data:dict,type:str)->list:
  buttons=[]
  if type=="reply_button":
    
    for button in data["buttons"]:
      button_title=button.get("reply").get("title")
      button_id=button.get("reply").get("id")
      button_data=[InlineKeyboardButton(button_title,callback_data=button_id)]
      buttons.append(button_data)
    return buttons
  
  else:
    
    for menu in data["sections"][0].get["rows"]:
      menu_title=menu.get("title")
      menu_id=menu.get("id")
      menu_button=[InlineKeyboardButton(menu_title,callback_data=menu_id)]
      buttons.append(menu_button)
    return buttons


def get_clicked_button_text(buttons:tuple,button_callback_data:str)-> str:
  for button in buttons:
    if button[0].callback_data==button_callback_data:
      return button[0].text
  return "Sorry, I can't find the button you clicked"


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
      logger.error(f"Sorry unrecognized media {type}")


async def send_response(update:Update,context,message):
   
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

async def simulate_typing(update: Update, context: CallbackContext)->None:
  await context.bot.send_chat_action(
      chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING
  )
  time.sleep(0.001)