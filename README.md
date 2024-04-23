# Sarufi Telegram-Webhook chatbot blueprint

A blueprint for deploying telegram bots made using [Sarufi](https://docs.sarufi.io/). We need a webhook for this task to receive updates from telegram. Using webhook, we can deploy our chatbot as a lambda function. This way we can save resources and avoid delays.

You can use any of available solutions online. We shall cover setting up webhook using [ngrok](#using-ngrok) and [replit](#using-replit).

## Why use webhook instead of polling?

Using polling may render some delays and consume resorces. So you can use webhook for your chatbot to get rid of delays. Your chatbot will process the requests in time.

## USING NGROK

Make sure you have [ngrok](https://ngrok.com) installed in your local machine.

You will have to modify some commands shown here to suite your working environment. The commands like `python3` and `pip3` will depend on your working environment. You may have to use `python` and `pip` instead.

### Quick configuration

- Create Project directory and Virtual environment

  - Create a project directory `Telegram bot`.
  
    In this directory we are going to create a virtual environment to hold our package.

    ```bash
    mkdir 'Telegram bot'
    cd 'Telegram bot'
    ```

  - Make Virtual Environment

    Using virtual environment is a good practice, so we are going to create one. You can read more on [why use virtual environment](https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/). We shall install all necessary packages in the environment

    - Unix based systems
      - Install virtual environment
      
        This step is optional as you may have python virtual environment already installed. If not, you can install it by running the command below.

        ```bash
        sudo apt install python3-venv
        ```
        
      - Create virtual environment and activate it

        ```bash
        python3 -m venv sarufi
        source sarufi/bin/activate
        ```

    - Windows
      - Install virtual environment

        This step is optional as you may have python virtual environment already installed. If not, you can install it by running the command below.

        ```bash
        pip install virtualenv
        ```

      - Create virtual environment and activate it
  
        ```bash
        virtualenv sarufi
        .\sarufi\Scripts\activate
        ```

### Setting up the project

- Clone and install requirements.

  In this part, we are going to clone the [Sarufi Telegram Chatbot deployment Blueprint](https://github.com/Neurotech-HQ/sarufi-telegram-webhook-blueprint) and install the packages.

  Run the commands below

  ```bash
  git clone https://github.com/Neurotech-HQ/sarufi-telegram-webhook-blueprint.git
  cd sarufi-telegram-webhook-blueprint
  pip3 install -r requirements.txt
    ```

- Environment variables

    After installing packages, we need to configure our credentials. In `telegram-chatbot-blueprint`, create a file(`.env`) to hold environment variables.

    In `.env`, we are going to add the following credetials. To get your public ngrok url read [here](#get-public-url) Using your favourite text editor add the following:-

  ```text
  SARUFI_API_KEY = your API KEY
  SARUFI_BOT_ID= bot id
  TELEGRAM_BOT_TOKEN = telegram token
  START_MESSAGE= Hi {name}, Welcome To {bot_name}, How can i help you
  ```

  **Note**: The Start Message will be bot's reponse when a user sends /start command to your bot.

  You can customize the message to your preference. You have the following variable that you can use in your start message to make it more personalized:-

    - {name} - User's name. This is the name the user has on Telegram
    - {bot_name} - Bot's name from Sarufi Dashboard


### Get Credentials

- Getting Sarufi credentials.
  
    To authorize our chabot, we are are going to use authorization keys from sarufi. Log in into your [sarufi account](https://sarufi.io). Go to your Profile on account to get Authorization keys(client ID and client secret)

    ![Sarufi authorazation keys](img/sarufi_authorization.png)

- Creating a telegram bot

  To create a chatbot on Telegram, you need to contact the [BotFather](https://telegram.me/BotFather), which is essentially a bot used to create other bots.

  To connect to Telegram, you need to create a Telegram bot. You can do this by following the instructions in the [Telegram documentation](https://core.telegram.org/bots#6-botfather). The instructions are as follows:

  1. Open Telegram and search for `@BotFather`.
  2. Click on the bot to start a chat.
  3. Send the `/newbot` command to create a new bot.
  4. Follow the instructions to create a new bot.

  Once you have created a bot, you will receive a `token`. This token is used to authenticate your bot with Telegram.

### Fire up your bot

- Starting ngrok to get public url

  Ngronk is a tool that allows you to expose a web server running on your local machine to the internet. You can read more on [ngrok](https://ngrok.com)
  
  ```bash
  ngrok http 8000
  ```

  You will have a public https url indicating that its forwarding to your `localhost:8000`

- Set Webhook Url

  We are going to set the webhook url to our bot. This is telling telegram server to send updates to our bot via specified url. This way our server can rest whenever there is no update. With this option you can deploy your chatbot as a lambda function.

  Using any of favourate API testing client or curl, set the webhook url as shown below

  ```bash
  curl --request POST 'https://api.telegram.org/bot<your bot token>/setWebhook?url=<your ngrok public url>'
  ```

  **NOTE:** The port number(for this case, 8000) matches the port used in `main.py`

- Running your bot

  Run python script. Its the time you have been waiting for. Lets lauch 🚀 our bot. 

  ```python
  python3 main.py
  ```
  
  **NOTE:** All operations are done in activated virtual environment for convience

  Open your telegram app, search for your bot --> Send it a text. You can see a sample bot [below](#chatbot-at-work)

## USING REPLIT

Have an account at [replit](https://replit.com). what you need is to fork the [blueprint repl](https://replit.com/@neurotechafrica/sarufi-telegram-webhook-blueprint) into your replit account.

### Quick configuration

You will have to make little configuration to get you bot up running.

- Creating a telegram bot

  As you already know, we are integrating our sarufi bot with telegram. So you will need to create a telegram bot.

  To create a chatbot on Telegram, you need to contact the [BotFather](https://telegram.me/BotFather), which is essentially a bot used to create other bots.

  The command you need is `/newbot` which leads to the stair-case steps upto having a complete bot. When finish steps, you will `bot's token`. You need the Bot token in the script.

- Getting Sarufi credentials.
  
  To authorize our chabot, we are are going to use authorization keys from sarufi. Log in into your [sarufi account](https://sarufi.io). Go to your Profile on account to get Authorization keys(client ID and client secret)

  ![Sarufi authorazation keys](img/sarufi_authorization.png)

- Environment variables

  In your repl, on the left lower part, `Tool section`. click **secrets** to add your environment variables.

  Add the following secretes. Get your _BASE_URL_ [here](#fire-up-the-bot)

  ```text
  SARUFI_API_KEY = your API KEY
  SARUFI_BOT_ID= bot id
  TELEGRAM_BOT_TOKEN = telegram bot token
  START_MESSAGE= Hi {user_name}, Welcome To {bot_name}, How can i help you
  ```
  **Note**:

  The Start Message will be bot's reponse when a user sends /start command to your bot.

  You can customize the message to your preference. You have the following variable that you can use in your start message to make it more personalized:-
    - {user_name} - User's name. This is the name the user has on Telegram
    - {bot_name} - Bot's name from Sarufi


### Fire up the bot

Click the run button to start your bot. You will see the bot running on the console. A small webview will open up with a url like `https://<your repl name>.<your replit username>.co`. Copy the url as we are going to use it in the next step to set webhook url.

### Set Webhook Url

You can use any of favourate API testing client or curl, set the webhook url as shown below.

- Using curl

  ```bash
  curl --request POST 'https://api.telegram.org/bot<your bot token>/setWebhook?url=<your replit url>'
  ```
- Using API testing client

  You can use any of your favourate API testing client. I will use [Postman](https://www.postman.com/). 
  
  Then send a POST request to `https://api.telegram.org/bot<your bot token>/setWebhook?url=<your replit url>`

Open your telegram app, search for your bot --> Send it a text. You can see a sample bot [below](#sample-bot-test)

## ChatBot at work

Here is a sample bot deployed in Telegram

![Telegram bot sample video](./img/sample.gif)

## Issues

If you will face any issue, please raise one so as we can fix it as soon as possible

## Contribution

If there is something you would like to contribute, from typos to code to documentation, feel free to do so, `JUST FORK IT`.

## Credits

All the credits to

1. [Jovine](https://github.com/jovyinny)
2. All other contributors
