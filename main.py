import telebot
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import requests
import json
import random
import time
import re
from bs4 import BeautifulSoup
import html
import colorama
from colorama import Fore, Back, Style
import os
from typing import Union, Optional
from collections import defaultdict
from admin_panel import AdminPanel
import datetime


colorama.init(autoreset=True)

class Colors:
    HEADER = Fore.CYAN + Style.BRIGHT
    SUCCESS = Fore.GREEN + Style.BRIGHT
    INFO = Fore.BLUE + Style.BRIGHT
    WARNING = Fore.YELLOW
    ERROR = Fore.RED
    CODE = Fore.WHITE + Back.BLACK
    RESET = Style.RESET_ALL



EMOJIS = {
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'code': '💻',
    'convert': '🔄',
    'enhance': '⭐',
    'file': '📄',
    'processing': '⚙️',
    'done': '✨',
    'ban': '🚫',
    'welcome': '👋'
}


user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
]

cookies = {
    '_ga': 'GA1.1.1227995408.1722706452',
    'fpestid': '5PQeaGoS_mVGS5KD8h9wnrEe7ukzzSI-2JFLrC7cNHJGvaK5VnqA7fAGoRrUtpm73jRHMA',
    '_cc_id': 'ff5c656b078ba8a8041eb6c946598324',
    'panoramaId_expiry': '1735789966532',
    'panoramaId': 'e3a8ff370aa5bebd863823aad8b2185ca02c1311c56604543fddc58c73b6abaf',
    'panoramaIdType': 'panoDevice',
    '_ga_KVXDJ93SHK': 'GS1.1.1735185164.6.1.1735185519.0.0.0',
}


user_code_chunks = defaultdict(list)
user_current_chunk = defaultdict(int)
CHUNK_SIZE = 40  

state_storage = StateMemoryStorage()


# your bot token
TOKEN = "7641333049:AAFinIvDX9hRwXSTmMbIALnPkNh4kvh6N2o"
bot = telebot.TeleBot(TOKEN, state_storage=state_storage)


admin_panel = AdminPanel(bot)

class UserStates(StatesGroup):
    waiting_for_python_file = State()  
    waiting_for_enhance_file = State() 
    processing = State() 

def print_box(text, color=Colors.HEADER, padding=1, width=60):
    lines = text.split('\n')
    max_length = min(max(len(line) for line in lines), width)
    
    print(color + '╔' + '═' * (max_length + padding * 2) + '╗')
    print(color + '║' + ' ' * (max_length + padding * 2) + '║')
    
    for line in lines:
        padded_line = line.center(max_length)
        print(color + '║' + ' ' * padding + padded_line + ' ' * padding + '║')
    
    print(color + '║' + ' ' * (max_length + padding * 2) + '║')
    print(color + '╚' + '═' * (max_length + padding * 2) + '╝')

def log_status(message, status_type="info"):


    prefixes = {
        "info": (Colors.INFO, "ℹ"),
        "success": (Colors.SUCCESS, "✔"),
        "warning": (Colors.WARNING, "⚠"),
        "error": (Colors.ERROR, "✖")
    }
    color, symbol = prefixes.get(status_type, prefixes["info"])
    print(f"{color}{symbol} {message}{Colors.RESET}")

def format_code(code):

    try:
        code = html.unescape(code)
        
        replacements = {
            '&#xA;': '\n',
            '&#x27;': "'",
            '&quot;': '"',
            '&lt;': '<',
            '&gt;': '>',
            '&amp;': '&',
        }
        
        for old, new in replacements.items():
            code = code.replace(old, new)
        
        code = code.strip()
        if code.startswith('n'):
            code = code[1:]
            
        lines = code.splitlines()
        if len(lines) > 100:
            return split_long_code(lines)
        
        return format_code_block(code)
        
    except Exception as e:
        log_status(f"Code formatting error: {str(e)}", "error")
        return None

def split_long_code(lines: list) -> list:

    chunks = []
    current_chunk = []
    
    for line in lines:
        current_chunk.append(line)
        if len(current_chunk) >= 100:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

def format_code_block(code: str) -> str:

    formatted_lines = []
    prev_line_empty = False
    
    for line in code.splitlines():
        line = line.rstrip()
        if not line.strip():
            if not prev_line_empty:
                formatted_lines.append('')
                prev_line_empty = True
            continue
        
        formatted_lines.append(line)
        prev_line_empty = False
    
    return '\n'.join(formatted_lines)

def get_message_id(text):
    match = re.search(r'zzz(?:redirect)?messageidzzz: ([a-f0-9-]+)', text)
    if match:
        return match.group(1)
    return None

def get_request_id():
    headers = {
        'accept': '*/*',
        'accept-language': 'ar-AE,ar;q=0.9,en-US;q=0.8,en;q=0.7,tr;q=0.6',
        'content-type': 'application/json',
        'origin': 'https://zzzcode.ai',
        'referer': 'https://zzzcode.ai/code-generator',
        'user-agent': random.choice(user_agents),
    }

    json_data = {
        'id': '',
        'p1': 'Python',
        'p2': code_description,
        'p3': '',
        'p4': '',
        'p5': '',
        'option1': '2 - Generate code',
        'option2': 'Professional',
        'option3': 'English',
        'hasBlocker': True,
    }

    try:
        response = requests.post(
            'https://zzzcode.ai/api/tools/code-generator',
            cookies=cookies,
            headers=headers,
            json=json_data,
            timeout=30
        )
        
        if response.status_code == 200:
            message_id = get_message_id(response.text)
            if message_id:
                return message_id
            else:
                log_status("Not found message ID In response", "error")
        else:
            log_status(f"Request error: {response.status_code}", "error")
            
    except Exception as e:
        log_status(f"Communication error: {str(e)}", "error")
    
    return None

def get_code(message_id, max_retries=3):

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ar-AE,ar;q=0.9,en-US;q=0.8,en;q=0.7,tr;q=0.6',
        'priority': 'u=0, i',
        'referer': 'https://zzzcode.ai/code-generator',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'user-agent': random.choice(user_agents)
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(
                'https://zzzcode.ai/code-generator',
                params={'id': message_id},
                cookies=cookies,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                html_content = response.text
                code = extract_code_from_html(html_content)
                if code:
                    return code
                else:
                    log_status("The code was not found on the page", "error")
            else:
                log_status(f"Request error: {response.status_code}", "error")
            

            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  
                
                log_status(f"waiting {wait_time} seconds before the next attempt  ...", "warning")
                time.sleep(wait_time)
                
        except Exception as e:
            log_status(f"Error in trying {attempt + 1}: {str(e)}", "error")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    return None

def extract_code_from_html(html_content):

    try:

        soup = BeautifulSoup(html_content, 'html.parser')


        pre_tags = soup.find_all('pre')
        for pre in pre_tags:
            code = pre.get_text(strip=True)
            if code and len(code) > 10: 
                return code
        
        content = html_content
        start = content.find('```python')
        if start != -1:
            end = content.find('```', start + 8)
            if end != -1:
                return content[start + 8:end].strip()
        
        start = content.find('```')
        if start != -1:
            end = content.find('```', start + 3)
            if end != -1:
                return content[start + 3:end].strip()
        
        code_tags = soup.find_all('code')
        for code in code_tags:
            code_text = code.get_text(strip=True)
            if code_text and len(code_text) > 10:
                return code_text
        

        code_divs = soup.find_all('div', class_=lambda x: x and 'code' in x.lower())
        for div in code_divs:
            code_text = div.get_text(strip=True)
            if code_text and len(code_text) > 10:
                return code_text
                

        for tag in soup.find_all(['div', 'span', 'p']):
            text = tag.get_text(strip=True)
            if text and len(text) > 50 and ('def ' in text or 'class ' in text or 'import ' in text):
                return text
        
        log_status("The code was not found on the page", "error")
        return None
        
    except Exception as e:
        log_status(f"Error extracting code: {str(e)}", "error")
        return None

def get_next_chunk(code_lines: list, current_chunk: int) -> tuple[list, bool]:

    start_idx = current_chunk * CHUNK_SIZE
    end_idx = start_idx + CHUNK_SIZE
    chunk = code_lines[start_idx:end_idx]
    has_more = end_idx < len(code_lines)
    return chunk, has_more

def format_progress_bar(current: int, total: int, width: int = 30) -> str:

    percentage = current / total
    filled = int(width * percentage)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {int(percentage * 100)}%"

def process_code_chunk(code_chunk: str, is_conversion: bool = False, max_retries: int = 3) -> Optional[str]:

    for attempt in range(max_retries):
        try:
            global code_description
            if is_conversion:
                code_description = "Convert the code from PHP to Python < This is just a piece of code so convert it >\n\n" + code_chunk
            else:
                code_description = "Improve the sent code and make it without problems < This is only part of the code, so improve it >\n\n" + code_chunk
            
            message_id = get_request_id()
            if not message_id:
                log_status(f"Failed to get message ID (attempt {attempt + 1}/{max_retries})", "error")
                if attempt < max_retries - 1:
                    time.sleep(2)
                continue
                
            code = get_code(message_id)
            if code:
                formatted_code = format_code(code)
                if formatted_code:
                    return formatted_code
                    
            if attempt < max_retries - 1:
                log_status(f"attempt {attempt + 1} Failed, trying again...", "warning")
                time.sleep(2)
                
        except Exception as e:
            log_status(f"Error in attempt {attempt + 1}: {str(e)}", "error")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    return None

def create_enhance_keyboard():

    keyboard = InlineKeyboardMarkup()
    enhance_button = InlineKeyboardButton(
        text=f"{EMOJIS['enhance']} Improve the code",
        callback_data='enhance'
    )
    keyboard.add(enhance_button)
    return keyboard

@bot.callback_query_handler(func=lambda call: call.data == "enhance")
def handle_enhance_callback(call):

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=(
            f"{EMOJIS['info']} Optimize files and solve problems\n\n"
            "~ The file will be fully optimized\n"
            "~If the code is large, it is divided into parts\n\n"
            f"{EMOJIS['file']}Submit your file now..."
        ),
        reply_markup=None
    )
    bot.set_state(call.from_user.id, UserStates.waiting_for_file, call.message.chat.id)

@bot.message_handler(commands=['start'])
def send_welcome(message):

    try:
        user_id = message.from_user.id
        username = message.from_user.username or "unknown"
        

        if admin_panel.is_banned(user_id):
            bot.reply_to(
                message,
                f"{EMOJIS['ban']}Sorry, you are banned from using the bot"
            )
            return
            

        if not admin_panel.bot_data['is_active'] and not admin_panel.is_admin(user_id):
            bot.reply_to(
                message,
                f"{EMOJIS['error']} Sorry, the bot is currently down\n"
                f"{EMOJIS['info']}Please try again later..."
            )
            return
            

        not_subscribed = admin_panel.check_force_subscription(user_id)
        if not_subscribed:
            channels_text = "\n".join([f"• {channel}" for channel in not_subscribed])
            bot.reply_to(
                message,
                f"{EMOJIS['error']}Dear user {message.from_user.first_name}, You must subscribe to the following channels first:\n\n"
                f"{channels_text}\n\n"
                f"{EMOJIS['info']} After subscribing, click /start"
            )
            return
            
        user_data = {
            'id': user_id,
            'username': username,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name,
            'joined_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        user_exists = False
        for user in admin_panel.users_data['users']:
            if user['id'] == user_id:
                user_exists = True
                break
                
        if not user_exists:
            admin_panel.users_data['users'].append(user_data)
            admin_panel.save_users_data()
            
            if admin_panel.notifications_enabled:
                admin_notification = (
                    f"{EMOJIS['info']} New user!\n\n"
                    f"├ {EMOJIS['info']} id: @{username}\n"
                    f"├ {EMOJIS['info']} the name: {user_data['first_name']} {user_data['last_name']}\n"
                    f"├ {EMOJIS['info']} The hands: {user_id}\n"
                    f"└ {EMOJIS['info']} Joining date: {user_data['joined_date']}"
                )
                
                for admin_id in admin_panel.admins:
                    try:
                        if admin_id != user_id: 
                            bot.send_message(admin_id, admin_notification)
                    except Exception as e:
                        print(f"Error sending notification to admin {admin_id}: {str(e)}")
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("👨‍💻 DEV BOT", url="https://t.me/ziddo_beatz"))
            
        welcome_text = (
            f"{EMOJIS['success']}Welcome to the code conversion and optimization bot\n\n"
            f"{EMOJIS['info']}User information:\n"
            f"├ {EMOJIS['info']} ID: @{username}\n"
            f"└ {EMOJIS['info']} the condition: {'Musharraf' if admin_panel.is_admin(user_id) else 'user'}\n\n"
            f"{EMOJIS['info']} Available commands:\n"
            f"├ {EMOJIS['convert']} /php_to_python - Convert from PHP to Python\n"
            f"└ {EMOJIS['enhance']} /code_good - Improve code and solve problems\n"
            
        )
        
        bot.reply_to(
            message,
            welcome_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        error_message = (
            f"{EMOJIS['error']}Sorry, an unexpected error occurred\n\n"
            f"{EMOJIS['info']}Please try again"
        )
        
        bot.reply_to(message, error_message)
        print(f"Error in start message: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data in ['php_to_python', 'enhance_code', 'help'])
def handle_welcome_buttons(call):
    try:
        user_id = call.from_user.id
        

        if not admin_panel.bot_data['is_active'] and not admin_panel.is_admin(user_id):
            bot.answer_callback_query(
                call.id,
                f"{EMOJIS['error']}The bot is currently down",
                show_alert=True
            )
            return
            

        if admin_panel.is_banned(user_id):
            bot.answer_callback_query(
                call.id,
                f"{EMOJIS['ban']} You are banned from using the bot",
                show_alert=True
            )
            return
            
        if call.data == 'php_to_python':
            bot.edit_message_text(
                f"{EMOJIS['convert']} Convert from PHP to Python\n\n"
                f"{EMOJIS['file']} Submit the PHP file for conversion...\n"
                f"{EMOJIS['warning']} The file must have a .php extension",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=create_back_keyboard()
            )
            bot.set_state(user_id, UserStates.waiting_for_python_file, call.message.chat.id)
            
        elif call.data == 'enhance_code':
            bot.edit_message_text(
                f"{EMOJIS['enhance']}Improve the code\n\n"
                f"{EMOJIS['file']} Submit the code file to be improved...\n"
                f"{EMOJIS['info']} Supported files:\n"
                f"├ Python (.py)\n"
                f"├ Text (.txt)",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=create_back_keyboard()
            )
            bot.set_state(user_id, UserStates.waiting_for_enhance_file, call.message.chat.id)
            
        elif call.data == 'help':
            help_text = (
                f"{EMOJIS['info']} Bot User Guide\n\n"
                f"{EMOJIS['info']} Steps:\n"
                f"├ 1. Choose the type of operation (conversion/enhancement)\n"
                f"├ 2. Send the required file\n"
                f"├ 3. Wait for processing\n"
                f"└ 4. Receive the result\n\n"
                f"{EMOJIS['info']} Important notes:\n"
                f"├ {EMOJIS['info']} Maximum file size: 20MB\n"
                f"├ {EMOJIS['info']} Files must be text\n"
                f"└ {EMOJIS['info']} Make sure UTF-8 encoding\n\n"
                f"{EMOJIS['info']} For help: @admin"
            )
            
            bot.edit_message_text(
                help_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=create_back_keyboard()
            )
            
    except Exception as e:
        bot.answer_callback_query(
            call.id,
            f"{EMOJIS['error']} An error occurred, please try again",
            show_alert=True
        )
        log_status(f"Error processing buttons: {str(e)}", "error")
def create_back_keyboard():

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(
        f"{EMOJIS['back']} رجوع للقائمة الرئيسية",
        callback_data='back_to_main'
    ))
    return keyboard

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_main')
def back_to_main_menu(call):

    try:
        send_welcome(call.message)
    except Exception as e:
        bot.answer_callback_query(
            call.id,
            f"{EMOJIS['error']} An error occurred, please try again",
            show_alert=True
        )
        log_status(f"Error returning to main menu: {str(e)}", "error")

@bot.message_handler(commands=['php_to_python'])
def request_php_file(message):

    bot.reply_to(
        message,
        f"{EMOJIS['convert']} Convert from PHP to Python\n\n"
        f"{EMOJIS['file']} Submit PHP file for conversion...\n"
        f"{EMOJIS['warning']} The file must have a .php extension"
    )
    bot.set_state(message.from_user.id, UserStates.waiting_for_python_file, message.chat.id)

@bot.message_handler(commands=['code_good'])
def request_enhance_file(message):

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
   keyboard.add(KeyboardButton(f"{EMOJIS['file']} Send File"))
    
    bot.send_message(
        message.chat.id,
        f"{EMOJIS['info']} Please send the code file you want to improve...\n"
        f"{EMOJIS['info']} You can submit Python (.py) or plain text (.txt) files",
        reply_markup=keyboard
    )
    bot.set_state(message.from_user.id, UserStates.waiting_for_enhance_file, message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "how_to_use")
def handle_help_buttons(call):

    try:
        help_text = (
    f"{EMOJIS['info']} How to Use the Bot\n\n"
    f"{EMOJIS['info']} Step 1: Select the File\n"
    "├ Choose the file you want to enhance\n"
    "├ Ensure the file format is supported\n"
    "└ Ensure the file size is appropriate\n\n"
    f"{EMOJIS['info']} Step 2: Send the File\n"
    "├ Click on 📎 in Telegram\n"
    "├ Select the file from your device\n"
    "└ Wait for the file to upload\n\n"
    f"{EMOJIS['info']} Step 3: Wait for Processing\n"
    "├ You will see the progress directly\n"
    "├ Do not close the chat\n"
    "└ Wait until the process is complete\n\n"
    f"{EMOJIS['info']} Step 4: Receive the Result\n"
    "├ You will receive the enhanced file\n"
    "├ Along with a report of improvements\n"
    "└ You can use the file directly"
)

        
        bot.edit_message_text(
            help_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(f"{EMOJIS['back']} Reference", callback_data="back_to_main")
            )
        )
        
    except Exception as e:
        bot.answer_callback_query(
            call.id,
            f"{EMOJIS['error']} Sorry, an error occurred. Please try again"
        )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):

    try:
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton(f"{EMOJIS['info']} How to Use", callback_data="how_to_use"),
InlineKeyboardButton(f"{EMOJIS['warning']} FAQ", callback_data="faq")

welcome_text = (
    f"{EMOJIS['info']} Code Enhancement and Problem Solving\n\n"
    f"{EMOJIS['info']} How to Use:\n"
    "1️⃣ Send the file you want to enhance\n"
    "2️⃣ Wait for the file to be processed\n"
    "3️⃣ Receive the enhanced version\n\n"
    f"{EMOJIS['info']} Supported Files:\n"
    "├ .py\n"
    "├ .txt\n\n"
    f"{EMOJIS['info']} The following enhancements will be applied:\n"
    "├ Code formatting improvements\n"
    "├ Bug fixes\n"
    "├ Performance optimization\n"
    "└ Application of best practices\n\n"
    f"{EMOJIS['file']} Send your file now..."
)

        
        bot.edit_message_text(
            welcome_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        
    except Exception as e:
        bot.answer_callback_query(
            call.id,
            f"{EMOJIS['error']} Sorry, an error occurred. Please try again"
        )

@bot.message_handler(content_types=['document'], state=UserStates.waiting_for_enhance_file)
def handle_enhance_file(message):

    try:

        print(f"Received file: {message.document}")
        print(f"File ID: {message.document.file_id}")
        print(f"File name: {message.document.file_name}")
        print(f"File size: {message.document.file_size}")
        print(f"MIME type: {message.document.mime_type}")
        

        bot.reply_to(
            message,
           f"{EMOJIS['processing']} Receiving file...\n"
            "Wait a moment, please."
            parse_mode='Markdown'
        )


        if not message.document:
            bot.reply_to(
                message,
                f"{EMOJIS['error']} Sorry, file not found\n"
                "Please send the file again",
                parse_mode='Markdown'
            )
            return
            

        if message.document.file_size > 20 * 1024 * 1024: 
            bot.reply_to(
                message,
                f"{EMOJIS['error']} Sorry, the file size is too large\n\n"
                f"{EMOJIS['info']} Maximum: 20 MB\n"
                f"{EMOJIS['warning']} Tip: Split the file into smaller parts",
                parse_mode='Markdown'
            )
            return
            

        file_name = message.document.file_name
        file_ext = os.path.splitext(file_name)[1].lower()
        

        if file_ext not in ['.py', '.txt']:
            supported_files = "\n".join([f"├ {ext}" for ext in ['.py', '.txt']])
            bot.reply_to(
                message,
                f"{EMOJIS['error']} Sorry, this file type is not supported\n\n"
                f"{EMOJIS['info']} Supported files:\n"
                f"{supported_files}\n"
                f"{EMOJIS['warning']} Send a file with one of these extensions",
                parse_mode='Markdown'
            )
            return


        file_info_msg = (
            f"{EMOJIS['file']} File Information\n\n"
f"├ {EMOJIS['info']} Name: `{file_name}`\n"
f"├ {EMOJIS['info']} Size: {format_size(message.document.file_size)}\n"
f"├ {EMOJIS['info']} Type: {file_ext}\n"
f"└ {EMOJIS['info']} MIME: {message.document.mime_type}\n\n"
f"{EMOJIS['processing']} Uploading..."

        

        loading_msg = bot.reply_to(
            message,
            file_info_msg,
            parse_mode='Markdown'
        )

        try:

            try:
                file_info = bot.get_file(message.document.file_id)
                print(f"File path: {file_info.file_path}") 
                
            except Exception as e:
                print(f"Error getting file info: {e}")
                raise Exception("Failed to get file information")

            try:
                downloaded_file = bot.download_file(file_info.file_path)
                print("File downloaded successfully") 
                
            except Exception as e:
                print(f"Error downloading file: {e}")
                raise Exception("Failed to download file")
            

            bot.edit_message_text(
                f"{file_info_msg}\n"
                f"{EMOJIS['processing']}The file is being scanned...\n"
                f"{format_progress_bar(0.4)}",
                chat_id=message.chat.id,
                message_id=loading_msg.message_id,
                parse_mode='Markdown'
            )
            
            try:
                file_content = downloaded_file.decode('utf-8')
                print("File decoded successfully") 
            except UnicodeDecodeError:
                print("Trying alternative encodings") 
                encodings = ['utf-8', 'ascii', 'iso-8859-1', 'cp1252', 'latin1']
                file_content = None
                
                for encoding in encodings:
                    try:
                        file_content = downloaded_file.decode(encoding)
                        print(f"Successfully decoded with {encoding}") 
                        break
                    except:
                        continue
                        
                if not file_content:
                    bot.edit_message_text(
                        f"{file_info_msg}\n\n"
                        f"{EMOJIS['error']} Error reading file\n"
                        f"{EMOJIS['warning']} The file is not compatible with supported codecs\n"
                        f"{EMOJIS['info']} Please make sure the file is encoded in UTF-8",
                        chat_id=message.chat.id,
                        message_id=loading_msg.message_id,
                        parse_mode='Markdown'
                    )
                    return

            bot.edit_message_text(
                f"{file_info_msg}\n\n"
                f"{EMOJIS['success']} Uploaded successfully\n"
                f"{EMOJIS['processing']} Starting optimization...\n"
                f"{format_progress_bar(0.6)}",
                chat_id=message.chat.id,
                message_id=loading_msg.message_id,
                parse_mode='Markdown'
            )

            process_file_for_enhancement(file_content, message, file_name, file_ext, loading_msg)

        except Exception as e:
            print(f"Error in file processing: {e}") 
            error_msg = (
                f"{file_info_msg}\n\n"
f"{EMOJIS['error']} Failed to Process the File\n\n"
f"{EMOJIS['info']} Reason: {str(e)}\n"
f"{EMOJIS['warning']} Suggested Solutions:\n"
f"{EMOJIS['info']} Ensure a stable internet connection\n"
f"{EMOJIS['info']} Try reducing the file size\n"
f"{EMOJIS['info']} Retry after a while"

            )
            
            bot.edit_message_text(
                error_msg,
                chat_id=message.chat.id,
                message_id=loading_msg.message_id,
                parse_mode='Markdown'
            )
            
    except Exception as e:
        print(f"Critical error: {e}") 
        error_message = (
            f"{EMOJIS['error']} Sorry, an unexpected error occurred\n\n"
f"{EMOJIS['info']} Reason: {str(e)}\n\n"
f"{EMOJIS['warning']} Suggested Solutions:\n"
f"{EMOJIS['info']} Ensure the file is valid\n"
f"{EMOJIS['info']} Check the file size\n"
f"{EMOJIS['info']} Try again later"

        )
        
        bot.reply_to(
            message,
            error_message,
            parse_mode='Markdown'
        )
    finally:

        bot.delete_state(message.from_user.id, message.chat.id)

@bot.message_handler(content_types=['document'], state=UserStates.waiting_for_python_file)
def handle_php_file(message):

    try:
        if not message.document.file_name.endswith('.php'):
            bot.reply_to(
                message,
                f"{EMOJIS['error']} Sorry, I can only convert PHP files!\n"
                f"{EMOJIS['info']} Please send a file with .php extension"
            )
            return


        loading_msg = bot.reply_to(
            message,
            f"{EMOJIS['processing']}Loading file..."
        )


        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_content = downloaded_file.decode('utf-8')


        bot.edit_message_text(
           f"{EMOJIS['success']} The file was uploaded successfully!\n"
            f"{EMOJIS['processing']} Starting conversion...",
            chat_id=message.chat.id,
            message_id=loading_msg.message_id
        )


        process_file_for_conversion(file_content, message)

    except Exception as e:
        error_message = f"{EMOJIS['error']} Sorry, an error occurred:\n`{str(e)}`"
        if "codec can't decode" in str(e):
            error_message = (
                f"{EMOJIS['error']} Sorry, the file appears to contain incompatible text.\n"
                f"{EMOJIS['info']} Please make sure the file is UTF-8 encoded"
            )
        elif "file too large" in str(e).lower():
            error_message = (
                f"{EMOJIS['error']} Sorry, the file size is too large.\n"
                f"{EMOJIS['info']} Please split the file into smaller parts"
            )
            
        bot.reply_to(message, error_message)
        bot.delete_state(message.from_user.id, message.chat.id)

def format_size(size_in_bytes):

    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.1f} TB"

def process_file_for_enhancement(file_content: str, message, file_name: str, file_ext: str, loading_msg) -> None:

    try:

        lines = file_content.splitlines()
        total_chunks = (len(lines) + CHUNK_SIZE - 1) // CHUNK_SIZE
        

        status_message = bot.reply_to(
            message,
            f"{EMOJIS['processing']} Start the optimization process\n\n"
            f"{EMOJIS['info']} File information:\n"
            f"├ {EMOJIS['info']} Name: {file_name}\n"
            f"├ {EMOJIS['info']} Type: {file_ext}\n"
            f"├ {EMOJIS['info']} Number of lines: {len(lines):,}\n"
            f"└ {EMOJIS['info']} Number of parts: {total_chunks:,}\n\n"
            f"{EMOJIS['processing']} Optimizing...\n"
            f"{format_progress_bar(0)}"
        )
        

        user_id = message.from_user.id
        user_code_chunks[user_id] = []
        user_current_chunk[user_id] = 0
        

        success = process_file_chunks(message, lines, status_message)
        
        if success:
            enhanced_code = "\n".join(user_code_chunks[user_id])
            
            temp_file = f"enhanced_{file_name}"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(enhanced_code)
            
            with open(temp_file, "rb") as f:
                bot.send_document(
                    message.chat.id,
                    f,
                    caption=(
                        f"{EMOJIS['success']} Code optimized successfully\n\n"
                        f"{EMOJIS['info']} Summary of improvements:\n"
                        f"├ {EMOJIS['info']} Improve code format\n"
                        f"├ {EMOJIS['info']} Bug fixes\n"
                        f"└ {EMOJIS['info']} Performance improvement\n"
                        
                        f"{EMOJIS['success']} You can now use the improved version of the code!"
                    )
                )
            
            cleanup_user_data(user_id)
            os.remove(temp_file)
            
            bot.edit_message_text(
                f"{EMOJIS['success']} Optimization completed successfully\n\n"
                f"{EMOJIS['info']} The above optimized file has been sent.",
                chat_id=message.chat.id,
                message_id=status_message.message_id
            )
        else:
            bot.reply_to(
                message,
                f"{EMOJIS['error']} Sorry, an error occurred while optimizing the file.\n"
                f"{EMOJIS['info']} Please try again."
            )
            
    except Exception as e:
        bot.reply_to(
            message,
            f"{EMOJIS['error']} Sorry, an unexpected error occurred:\n`{str(e)}`"
        )
    finally:
        bot.delete_state(message.from_user.id, message.chat.id)

def process_file_for_conversion(file_content: str, message) -> None:

    try:

        lines = file_content.splitlines()
        total_chunks = (len(lines) + CHUNK_SIZE - 1) // CHUNK_SIZE
        

        status_message = bot.reply_to(
            message,
            f"{EMOJIS['processing']} Starting the conversion process\n\n"
            f"{EMOJIS['info']} File information:\n"
            f"├ {EMOJIS['info']} Number of lines: {len(lines):,}\n"
            f"└ {EMOJIS['info']} Number of parts: {total_chunks:,}\n\n"
            f"{EMOJIS['processing']} Converting...\n"
            f"{format_progress_bar(0)}"
        )
        

        user_id = message.from_user.id
        user_code_chunks[user_id] = []
        user_current_chunk[user_id] = 0
        

        success = process_file_chunks(message, lines, status_message, is_conversion=True)
        
        if success:

            converted_code = "\n".join(user_code_chunks[user_id])
            

            temp_file = f"converted_{message.document.file_name[:-4]}.py"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(converted_code)
            

            with open(temp_file, "rb") as f:
                bot.send_document(
                    message.chat.id,
                    f,
                    caption=(
                        f"{EMOJIS['success']} The code was converted successfully\n\n"
                        f"{EMOJIS['info']} Conversion summary:\n"
                        f"├ {EMOJIS['info']} Converting functions and variables\n"
                        f"├ {EMOJIS['info']} Converting syntax\n"
                        f"├ {EMOJIS['info']} Performance improvement\n"
                        f"└ {EMOJIS['info']} Python standards implementation\n\n"
                        f"{EMOJIS['success']} You can now use the code in Python!"
                    )
                )
            

            cleanup_user_data(user_id)
            os.remove(temp_file)
            

            bot.edit_message_text(
                f"{EMOJIS['success']} The conversion was completed successfully\n\n"
                f"{EMOJIS['info']} The above converted file has been sent.",
                chat_id=message.chat.id,
                message_id=status_message.message_id
            )
        else:

            bot.reply_to(
                message,
                f"{EMOJIS['error']} Sorry, an error occurred while converting the file.\n"
                f"{EMOJIS['info']} Please try again."
            )
            
    except Exception as e:
        bot.reply_to(
            message,
            f"{EMOJIS['error']} Sorry, an unexpected error occurred:\n`{str(e)}`"
        )
    finally:

        bot.delete_state(message.from_user.id, message.chat.id)

def process_file_chunks(message, code_lines: list, status_message, is_conversion: bool = False) -> bool:

    user_id = message.from_user.id
    total_chunks = (len(code_lines) + CHUNK_SIZE - 1) // CHUNK_SIZE
    failed_chunks = []
    
   operation_type = "conversion" if is_conversion else "optimization"
    
    while user_current_chunk[user_id] < total_chunks:
        current_chunk = user_current_chunk[user_id] + 1
        chunk, has_more = get_next_chunk(code_lines, user_current_chunk[user_id])
        

        progress = current_chunk / total_chunks
        progress_bar = format_progress_bar(progress)
        status_text = (
            f"{EMOJIS['processing']} running {operation_type} code...\n\n"
            f"{EMOJIS['info']} Progress:\n"
            f"├ {EMOJIS['info']} Current Chunk: {current_chunk}/{total_chunks}\n"
            f"└ {progress_bar} {progress:.1%}\n\n"
            f"{EMOJIS['processing']} Please wait...”
        )
        
        try:
            bot.edit_message_text(
                status_text,
                message.chat.id,
                status_message.message_id
            )
        except:
            pass
        

        chunk_code = '\n'.join(chunk)
        if is_conversion:
            result = process_code_chunk(chunk_code, is_conversion=True)
        else:
            result = process_code_chunk(chunk_code, is_conversion=False)
        
        if not result:
            failed_chunks.append(current_chunk)
            

            failure_text = (
                f"{EMOJIS['warning']} Warning: Failed in {operation_type} part {current_chunk}\n\n"
                f"{EMOJIS['info']} Progress:\n"
                f"├ {EMOJIS['info']} Failed Chunks: {len(failed_chunks)}\n"
                f"└ {progress_bar} {progress:.1%}\n\n"
                f"{EMOJIS['processing']} Continuing..."
            )
            
            try:
                bot.edit_message_text(
                    failure_text,
                    message.chat.id,
                    status_message.message_id
                )
            except:
                pass
                

            if len(failed_chunks) > 3:
                error_text = (
                   f"{EMOJIS['error']} The process has stopped\n\n"
                    f"{EMOJIS['info']} Error details:\n"
                    f"├ {EMOJIS['info']} Number of failed chunks: {len(failed_chunks)}\n"
                    f"└ {EMOJIS['info']} Chunks: {', '.join(map(str, failed_chunks))}\n\n"
                    f"{EMOJIS['processing']} Please try again"
                )
                
                bot.edit_message_text(
                    error_text,
                    message.chat.id,
                    status_message.message_id
                )
                return False
        else:
            user_code_chunks[user_id].append(result)
            

            success_text = (
                f"{EMOJIS['success']} continued {operation_type} Code...\n\n"
                f"{EMOJIS['info']} Progress:\n"
                f"├ {EMOJIS['info']}It has been completed: {current_chunk}/{total_chunks}\n"
                f"└ {progress_bar} {progress:.1%}\n\n"
                f"{EMOJIS['processing']}Please wait..."
            )
            
            try:
                bot.edit_message_text(
                    success_text,
                    message.chat.id,
                    status_message.message_id
                )
            except:
                pass
        
        user_current_chunk[user_id] += 1
        time.sleep(1)  
    

    if failed_chunks:
        summary_text = (
            f"{EMOJIS['warning']} The process was completed with some errors\n\n"
            f"{EMOJIS['info']}Summary of results:\n"
            f"├ {EMOJIS['info']}Successful parts: {total_chunks - len(failed_chunks)}\n"
            f"├ {EMOJIS['info']} Failed parts: {len(failed_chunks)}\n"
            f"└ {EMOJIS['info']} Success rate: {((total_chunks - len(failed_chunks)) / total_chunks):.1%}"
        )
    else:
        summary_text = (
            f"{EMOJIS['success']}The process completed successfully\n\n"
            f"{EMOJIS['info']}Summary of results:\n"
            f"├ {EMOJIS['info']}Total parts: {total_chunks}\n"
            f"└ {EMOJIS['info']}Success rate: 100%"
        )
    
    try:
        bot.edit_message_text(
            summary_text,
            message.chat.id,
            status_message.message_id
        )
    except:
        pass
    
    return True

def cleanup_user_data(user_id: int) -> None:

    if user_id in user_code_chunks:
        del user_code_chunks[user_id]
    if user_id in user_current_chunk:
        del user_current_chunk[user_id]

def format_progress_bar(percentage: float, width: int = 25) -> str:

    filled = int(width * percentage)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {percentage:.1%}"

def handle_message(message):

    if message.text == '/start':
        send_welcome(message)
    elif message.text == '/php_to_python':
        request_php_file(message)
    elif message.text == '/code_good':
        request_enhance_file(message)

@bot.message_handler(commands=['adm'])
def admin_command(message):

    admin_panel.handle_admin_command(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_callback(call):

    admin_panel.handle_admin_callback(call)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_all_messages(message):


    if not admin_panel.bot_data['is_active'] and not admin_panel.is_admin(message.from_user.id):
        bot.reply_to(
            message,
            f"{EMOJIS['error']}Sorry, the bot is currently down"
        )
        return
        

    if admin_panel.is_banned(message.from_user.id):
        bot.reply_to(
            message,
            f"{EMOJIS['ban']} Sorry, you are banned from using the bot"
        )
        return
        

    admin_panel.notify_admins(message)
    

    handle_message(message)

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        

        file_name = message.document.file_name
        if not file_name.endswith(('.php', '.py', '.txt')):
            bot.reply_to(
                message,
                f"{EMOJIS['error']} Sorry, I can only process PHP و Python و TXT"
            )
            return
            

        file_content = downloaded_file.decode('utf-8')
        


        if file_name.endswith('.php'):
            process_file_for_conversion(file_content, message)
        else:
            process_file_for_enhancement(file_content, message, file_name, file_name.split('.')[-1], None)
            
    except Exception as e:
        bot.reply_to(
            message,
            f"{EMOJIS['error']}Sorry, an error occurred while processing the file:\n`{str(e)}`"
        )
        log_status(f"Error processing file: {str(e)}", "error")

if __name__ == "__main__":
    print_box("Bot convert code from PHP to Python ", Colors.SUCCESS)
    log_status("The bot is running....", "info")
    bot.infinity_polling()
