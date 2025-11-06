import os
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler,
    PicklePersistence,
    filters
)
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import CallbackContext
from datetime import datetime, time, timedelta
import re
import pytz
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = 7196380140

COMMISSION_AMOUNT = 2
FEEDBACK_AWAITING = 3
BROADCAST_SELECT_CHAT, BROADCAST_AWAITING_MESSAGE, BROADCAST_CONFIRMATION = range(4, 7)

REPORT_TEMPLATE = (
    "Gmail             - \n"

    " \n"
    "Tele name   - \n"

    " \n"
    "Username    - \n"

    " \n"
    "Date          - \n"

    " \n"
    "Age           - \n"

    " \n"
    "Current work  - \n"

    " \n"
    "Phone number    - \n"


    "\n"
    "Khaifa - "
)

def get_yangon_tz() -> pytz.timezone:
    return pytz.timezone('Asia/Yangon')

def get_data_key() -> str:
    try:
        tz = get_yangon_tz()
        now = datetime.now(tz)
    except Exception:
        now = datetime.now()

    cut_off_time = time(hour=18, minute=30, second=0)

    if now.time() < cut_off_time:
        work_day = now.date() - timedelta(days=1)
    else:
        work_day = now.date()

    return work_day.strftime('%Y-%m-%d')

get_today_key = get_data_key

async def save_chat_id(chat_id: int, context: CallbackContext, chat_type: str) -> None:
    if 'users' not in context.application.bot_data:
        context.application.bot_data['users'] = set()
    if 'groups' not in context.application.bot_data:
        context.application.bot_data['groups'] = set()

    if chat_type == 'private' and chat_id not in context.application.bot_data['users']:
        context.application.bot_data['users'].add(chat_id)
    elif chat_type in ['group', 'supergroup'] and chat_id not in context.application.bot_data['groups']:
        context.application.bot_data['groups'].add(chat_id)

    if context.application.persistence:
        await context.application.persistence.flush()

async def start(update: Update, context: CallbackContext) -> None:
    await main_menu_command(update, context)

async def help_command(update: Update, context: CallbackContext) -> None:
    await save_chat_id(update.effective_chat.id, context, update.effective_chat.type)

    await update.message.reply_text(
        'Bot commands and functions:\n\n'
        '**Data Entry:**\n'
        '1. Send a message containing "Khaifa -" and "Date -" to collect data automatically.\n'
        ' \n'
        '\n**User Commands (Menu Buttons):**\n'
        '• /form - Display the report submission template\n' 
        '• /comm - Commission calculator\n'
        '• /chk <number> - Check and track number usage\n'
        '• /showdata - Show today\'s collected data\n'
        '• /cleardata - Clear today\'s collected data\n'
        '• /feedback - Send feedback to admin\n'
        '• /hidemenu - Hide the menu buttons\n'
        '• /settings - Admin functions (Admin only)\n',
        parse_mode='Markdown'
    )

async def report_form_command(update: Update, context: CallbackContext) -> None:
    await save_chat_id(update.effective_chat.id, context, update.effective_chat.type)

    await update.message.reply_text(
        "**📝 Deposit Report Form Template**\n\n"
        "ကော်ပီကူးယူ၍ ဖြည့်စွက်ပြီး ပို့ပေးပါ:\n\n"
        + REPORT_TEMPLATE,
        parse_mode='Markdown'
    )

async def main_menu_command(update: Update, context: CallbackContext) -> None:
    await save_chat_id(update.effective_chat.id, context, update.effective_chat.type)

    keyboard = [
        [KeyboardButton("/showdata"), KeyboardButton("/cleardata")],
        [KeyboardButton("/comm"), KeyboardButton("/feedback")],
        [KeyboardButton("/chk"), KeyboardButton("/form")],
        [KeyboardButton("/hidemenu")]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

    greeting_text = (
        "**🤖 Main Menu**\n\n"
        "အောက်ပါ ခလုတ်များကို နှိပ်ပြီး အသုံးပြုနိုင်ပါတယ်:\n\n"
        "📢 **တစ်နေ့တာ deposit report ထုတ်ယူပြီးပါက** "
        "**/cleardata** နှိပ်ဖိုမမေ့ပါနဲ့။ **မနှိပ်ပါက Data များရောထွေးနိုင်သည်:\n\n"
        "**Deposit report form ကိုတော့ /form နှိပ်ပြီး ကော်ပီယူ၍ထို့ပုံစံအတိုင်းဖြည့်သွင်းမှသာအလုပ်လုပ်ပါသည်**"
    )

    await update.message.reply_text(
        greeting_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def remove_menu(update: Update, context: CallbackContext) -> None:
    await save_chat_id(update.effective_chat.id, context, update.effective_chat.type)
    reply_markup = ReplyKeyboardRemove()
    await update.message.reply_text(
        "Menu keyboard ကို ဖျက်လိုက်ပါပြီ တောသားရေ.....။ /start ဖြင့် ပြန်ခေါ်နိုင်ပါသည်။😒😒",
        reply_markup=reply_markup
    )

async def check_command(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /chk <number>.")
        return

    check_number = context.args[0].strip()

    records = context.application.bot_data.setdefault('check_records', {})

    current_count = records.get(check_number, 0)
    new_count = current_count + 1
    records[check_number] = new_count

    if new_count > 1:
        await update.message.reply_text(
            f"⚠️ **{check_number}** ⚠️\n\n"
            f"ဤနံပါတ်ကို **{new_count} ကြိမ်** စစ်ဆေးထားပြီး ဖြစ်ပါသည်။"
        )
    else:
        await update.message.reply_text(
            f"✅ **{check_number}** ✅\n\n"
            f"ဤနံပါတ်ကို **ယခုမှ ပထမဆုံးအကြိမ်** စစ်ဆေးမှတ်တမ်းတင်လိုက်ပါသည်။"
        )

    if context.application.persistence:
        await context.application.persistence.flush()

async def clear_data(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    today_key = get_data_key()
    await save_chat_id(update.effective_chat.id, context, update.effective_chat.type)

    if 'group_data' in context.application.bot_data and chat_id in context.application.bot_data['group_data'] and today_key in context.application.bot_data['group_data'][chat_id]:
        del context.application.bot_data['group_data'][chat_id][today_key]

        if context.application.persistence:
            await context.application.persistence.flush()

        await update.message.reply_text(f"✅ Data deleted for today ({today_key}).")
    else:
        await update.message.reply_text(f"🤷‍♂️No data found for today ({today_key}).")

async def show_data(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    today_key = get_data_key()
    await save_chat_id(update.effective_chat.id, context, update.effective_chat.type)

    if 'group_data' not in context.application.bot_data:
        context.application.bot_data['group_data'] = {}

    if chat_id not in context.application.bot_data['group_data']:
        context.application.bot_data['group_data'][chat_id] = {}

    collected_data_list = context.application.bot_data['group_data'][chat_id].get(today_key, [])

    if not collected_data_list:
        await update.message.reply_text(f"No data collected yet for today ({today_key}) in this chat.")
        return

    grouped_data = {}

    for entry in collected_data_list:
        parts = [p.strip() for p in entry.split('     ')] 

        khaifa_name = "N/A"
        if len(parts) >= 2:
            khaifa_name = parts[1].strip()

        normalized_key = khaifa_name.replace(" ", "").lower() if khaifa_name != "N/A" else "n/a"

        if normalized_key not in grouped_data:
            grouped_data[normalized_key] = []

        grouped_data[normalized_key].append(entry)

    final_response_parts = []
    separator = "------------------------------------"

    is_first_group = True
    sorted_groups = sorted(grouped_data.items())

    for normalized_key, entries in sorted_groups:
        if not is_first_group:
            final_response_parts.append(separator)

        is_first_group = False

        final_response_parts.extend(entries)

    response_text = "\n".join(final_response_parts)

    if len(response_text) > 4096:
        await update.message.reply_text("Warning: Data too long. Displaying partial data.")
        await update.message.reply_text(response_text[:4000])
    else:
        await update.message.reply_text(response_text)

    await update.message.reply_text(
        "💡 အသင်တောသား Data များကို ရှင်းလင်းလိုပါက **`/cleardata`** ကို နှိပ်ပါ သို့မဟုတ် **Menu Button** မှ ရွေးချယ်နိုင်ပါသည်",
        parse_mode='Markdown'
    )

async def extract_and_save_data(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    await save_chat_id(update.effective_chat.id, context, update.effective_chat.type)

    full_text = update.message.text or update.message.caption

    if not full_text:
        return

    required_fields_present = all(
        re.search(field, full_text, re.IGNORECASE)
        for field in ["Khaifa", "Date"]
    )

    if not required_fields_present:


        cleaned_text = re.sub(r'[\s\n\-\(\)\+]+', '', full_text).strip()


        if cleaned_text.isdigit() and len(cleaned_text) >= 7:
            check_number = cleaned_text

            records = context.application.bot_data.setdefault('check_records', {})
            current_count = records.get(check_number, 0)
            new_count = current_count + 1
            records[check_number] = new_count


            extra_message = "\n\n‼️ အသင်တောသား 🔍Search-barတွင် နံပါတ်ရိုက်ထည့်၍ ယခင်စစ်ဆေးထားသူအားမေးမြန်းနိုင်သည်။"

            if new_count > 1:
                await update.message.reply_text(
                    f"⚠️ **{check_number}** ⚠️\n\n"
                    f"ဤနံပါတ်ကို **{new_count} ကြိမ်** စစ်ဆေးထားပြီး ဖြစ်ပါသည်။{extra_message}"
                )
            else:
                await update.message.reply_text(
                    f"✅ **{check_number}** ✅\n\n"
                    f"ဤနံပါတ်ကို **ယခုမှ ပထမဆုံးအကြိမ်** စစ်ဆေးမှတ်တမ်းတင်လိုက်ပါသည်။{extra_message}"
                )

            if context.application.persistence:
                await context.application.persistence.flush()


            return


        return


    khaifa_match = re.search(r"(?:Khaifa|Khat)\s*[\-\–]?\s*(.+?)(?:\r?\n|$)", full_text, re.IGNORECASE | re.DOTALL)
    extracted_khaifa = khaifa_match.group(1).strip() if khaifa_match else "N/A"

    date_match = re.search(r"Date\s*[\-\–]?\s*(.+?)(?:\n|$)", full_text, re.IGNORECASE | re.DOTALL)
    extracted_date = date_match.group(1).strip() if date_match else "N/A"

    email_phone_match = re.search(r"(?:Gmail|Email|Phone number|Phone)\s*[\-\–]?\s*(.+?)(?:\n|$)", full_text, re.IGNORECASE | re.DOTALL)
    extracted_email_phone = email_phone_match.group(1).strip() if email_phone_match else "N/A"

    final_output = f"{extracted_date}     {extracted_khaifa}     {extracted_email_phone}"

    today_key = get_data_key()

    if 'group_data' not in context.application.bot_data:
        context.application.bot_data['group_data'] = {}

    if chat_id not in context.application.bot_data['group_data']:
        context.application.bot_data['group_data'][chat_id] = {}

    if today_key not in context.application.bot_data['group_data'][chat_id]:
        context.application.bot_data['group_data'][chat_id][today_key] = []

    context.application.bot_data['group_data'][chat_id][today_key].append(final_output)

    if context.application.persistence:
        await context.application.persistence.flush()

    await update.message.reply_text(final_output)

async def commission_start(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("🔪 Killer", callback_data='comm_killer')],
        [InlineKeyboardButton("💰 Deposit (M2)", callback_data='comm_deposit')],
        [InlineKeyboardButton("🥇 M1", callback_data='comm_m1')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel_commission')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("**💰 Select Commission Type:**", reply_markup=reply_markup, parse_mode='Markdown')
    return COMMISSION_AMOUNT

async def request_amount(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data['comm_type'] = query.data

    await query.edit_message_text(f"You selected **{query.data.split('_')[1].upper()}**.\nPlease send the amount of money to calculate the commission:", parse_mode='Markdown')

    return COMMISSION_AMOUNT

async def calculate_commission(update: Update, context: CallbackContext) -> int:
    try:
        amount_str = update.message.text.replace(',', '').strip()
        amount = float(amount_str)
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Enter a valid number.")
        return ConversationHandler.END

    comm_type = context.user_data.pop('comm_type', None)

    if comm_type == 'comm_killer':
        commission = amount / 1600 * 0.04 * 0.45 * 4.7
    elif comm_type == 'comm_deposit':
        commission = amount / 1600 * 0.04 * 0.3 * 4.7
    elif comm_type == 'comm_m1':
        commission = amount / 1600 * 0.04 * 0.25 * 4.7
    else:
        await update.message.reply_text("❌ Commission type not found. Please try again with /help.")
        return ConversationHandler.END

    type_map = {
        'comm_killer': 'Killer',
        'comm_deposit': 'Deposit (M2)',
        'comm_m1': 'M1'
    }
    type_name = type_map.get(comm_type, "N/A")

    await update.message.reply_text(
        f"**💰 Commission Result for {type_name}:**\n\n"
        f"Input Amount: `{amount_str}`\n"
        f"Calculated Commission: **`{commission:.4f}`**\n\n"
        f"Calculation: `{amount} / 1600 * (Rate) * 4.7`",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def cancel_commission(update: Update, context: CallbackContext) -> int:
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("❌ Commission calculation cancelled.")
    elif update.message:
        await update.message.reply_text("❌ Commission calculation cancelled.")

    return ConversationHandler.END

async def start_feedback(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "သင်သည် Owner အားယခု စာပေးပို့နိုင်ပါသည်။ဤနေရာတွင်ကြိုက်နှစ်သက်ရာ စာကိုပေးပို့လိုက်ပါက Owner ဆီစာရောက်ရှိမည်ဖြစ်သည်။"
    )
    return FEEDBACK_AWAITING

async def process_feedback(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    feedback_text = update.message.text

    await context.application.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"***[NEW FEEDBACK]***\nFrom: {user.full_name} (@{user.username} - ID: {user.id})\n\nFeedback:\n{feedback_text}",
        parse_mode='Markdown'
    )
    await update.message.reply_text("သင်၏အကြံပြုစာအား Owner ထံပေးပို့ပြီးပါပြီ။")
    return ConversationHandler.END

async def cancel_conversation(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('❌ Action cancelled.')
    return ConversationHandler.END

async def set_separator_command(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Admin only.")
        return
    await update.message.reply_text("`Daily Separator` functions have been removed from the code.")

async def broadcast_start_selection(update: Update, context: CallbackContext) -> int:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return ConversationHandler.END

    users = context.application.bot_data.get('users', set())
    groups = context.application.bot_data.get('groups', set())

    keyboard = []

    for user_id in list(users):
        try:
            chat = await context.application.bot.get_chat(chat_id=user_id)
            name = chat.full_name
            keyboard.append([InlineKeyboardButton(f"👤 User: {name} (ID: {user_id})", callback_data=f'bcast_id_{user_id}')])
        except Exception:
            keyboard.append([InlineKeyboardButton(f"👤 User: {user_id}", callback_data=f'bcast_id_{user_id}')])

    for group_id in list(groups):
        try:
            chat = await context.application.bot.get_chat(chat_id=group_id)
            name = chat.title
            keyboard.append([InlineKeyboardButton(f"👥 Group: {name} (ID: {group_id})", callback_data=f'bcast_id_{group_id}')])
        except Exception:
            keyboard.append([InlineKeyboardButton(f"👥 Group: {group_id}", callback_data=f'bcast_id_{group_id}')])

    keyboard.append([InlineKeyboardButton("❌ Cancel Broadcast", callback_data='bcast_cancel')])

    if len(keyboard) == 1 and keyboard[0][0].callback_data == 'bcast_cancel':
        await update.message.reply_text("No tracked users or groups available for broadcast.")
        return ConversationHandler.END

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select the chat ID to broadcast to:", reply_markup=reply_markup)

    return BROADCAST_SELECT_CHAT

async def broadcast_select_target(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    target_id = query.data.split('_')[-1]
    context.user_data['broadcast_target_id'] = target_id

    try:
        chat = await context.application.bot.get_chat(chat_id=target_id)
        chat_name = chat.title or chat.full_name
    except Exception:
        chat_name = f"ID {target_id}"

    await query.edit_message_text(
        f"You selected **{chat_name}** (`{target_id}`).\n"
        f"Please send the message you want to broadcast now:", 
        parse_mode='Markdown'
    )

    return BROADCAST_AWAITING_MESSAGE

async def broadcast_confirm_message(update: Update, context: CallbackContext) -> int:
    message_to_send = update.message.text
    target_id = context.user_data.get('broadcast_target_id')

    if not target_id:
        await update.message.reply_text("Error: Target ID lost. Starting over with /broadcast.")
        return ConversationHandler.END

    context.user_data['message_to_send'] = message_to_send

    keyboard = [
        [InlineKeyboardButton("✅ Confirm and Send", callback_data='bcast_confirm')],
        [InlineKeyboardButton("❌ Cancel", callback_data='bcast_cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        chat = await context.application.bot.get_chat(chat_id=target_id)
        chat_name = chat.title or chat.full_name
    except Exception:
        chat_name = f"ID {target_id}"

    await update.message.reply_text(
        f"You are about to send the following message to **{chat_name}** (`{target_id}`):\n\n"
        f"--- MESSAGE PREVIEW ---\n"
        f"{message_to_send}\n"
        f"-----------------------\n\n"
        f"Are you sure you want to send this?",
        reply_to_message_id=update.message.message_id, 
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return BROADCAST_CONFIRMATION

async def execute_broadcast(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    target_id = context.user_data.pop('broadcast_target_id', None)
    message_to_send = context.user_data.pop('message_to_send', None)

    if not target_id or not message_to_send:
        await query.edit_message_text("❌ Error: Message or target information lost. Broadcast cancelled.")
        return ConversationHandler.END

    try:
        await context.application.bot.send_message(chat_id=target_id, text=f"[ADMIN BROADCAST]\n{message_to_send}")
        await query.edit_message_text(f"✅ Message sent successfully to target ID `{target_id}`.")
    except Exception as e:
        await query.edit_message_text(f"❌ Failed to send message to target ID `{target_id}`. Error: {e}")

    return ConversationHandler.END

async def cancel_broadcast_action(update: Update, context: CallbackContext) -> int:
    context.user_data.pop('broadcast_target_id', None)
    context.user_data.pop('message_to_send', None)

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("❌ Broadcast action cancelled.")
    else:
        await update.message.reply_text("❌ Broadcast action cancelled.")

    return ConversationHandler.END

async def list_groups(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Admin only.")
        return

    groups = context.application.bot_data.get('groups', set())

    if not groups:
        await update.message.reply_text("The bot is not currently in any tracked groups.")
        return

    await update.message.reply_text("👥 **Tracked Groups List:**", parse_mode='Markdown')

    for group_id in list(groups):
        try:
            chat = await context.application.bot.get_chat(chat_id=group_id)
            group_name = chat.title
        except Exception:
            group_name = "Unknown Group (ID may be outdated)"

        response = f"**{group_name}** (`{group_id}`)\n"

        keyboard = [
            [
                InlineKeyboardButton("🗑️ Clear All Data", callback_data=f'admin_clear_{group_id}'),
                InlineKeyboardButton("❌ Cancel", callback_data='admin_cancel')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.application.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def clear_group_data_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("Admin only.")
        return

    try:
        data_parts = query.data.split('_')
        group_id_to_clear = data_parts[2]
    except IndexError:
        await query.edit_message_text("❌ Error: Invalid clear command.")
        return

    chat_id_str = str(group_id_to_clear)

    if 'group_data' in context.application.bot_data and chat_id_str in context.application.bot_data['group_data']:
        del context.application.bot_data['group_data'][chat_id_str]

        if context.application.persistence:
            await context.application.persistence.flush()

        try:
            chat = await context.application.bot.get_chat(chat_id=group_id_to_clear)
            group_name = chat.title
        except Exception:
            group_name = "Unknown Group"

        await query.edit_message_text(f"✅ Group Data Cleared!\n**{group_name}** (`{group_id_to_clear}`)'s daily tracking data has been completely removed.", parse_mode='Markdown')

    else:
        await query.edit_message_text(f"No daily tracking data found for group ID `{group_id_to_clear}`. Action cancelled.")

async def cancel_group_action(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("Admin only.")
        return

    await query.edit_message_text("❌ Action cancelled.")

async def admin_settings_command(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Admin only.")
        return

    await update.message.reply_text(
        f"⚙️ **Admin Settings**\n\n"
        f"Daily Separator Jobs: `REMOVED`\n"
        f"Actions:\n"
        f"• /stats (Admin only)\n"
        f"• /broadcast (Admin only - New interactive system)\n"
        f"• /listgroups (Admin only - Selectively clear group data)",
        parse_mode='Markdown'
    )

async def stats(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    user_count = len(context.application.bot_data.get('users', set()))
    group_count = len(context.application.bot_data.get('groups', set()))
    chk_count = len(context.application.bot_data.get('check_records', {}))

    await update.message.reply_text(
        f"📊 Bot Statistics:\n"
        f"Total Users (Private Chats): {user_count}\n"
        f"Total Groups: {group_count}\n"
        f"Total Unique Numbers Checked (/chk): {chk_count}"
    )

def main():
    if not TOKEN:
        return

    persistence = PicklePersistence(filepath='bot_data.pickle')

    application = (
        Application.builder()
        .token(TOKEN)
        .persistence(persistence)
        .build()
    )

    application.add_handler(CommandHandler("menu", main_menu_command))
    application.add_handler(CommandHandler("hidemenu", remove_menu))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("showdata", show_data))
    application.add_handler(CommandHandler("cleardata", clear_data))
    application.add_handler(CommandHandler("chk", check_command))

    application.add_handler(CommandHandler("form", report_form_command))

    application.add_handler(CommandHandler("settings", admin_settings_command))
    application.add_handler(CommandHandler("stats", stats))

    application.add_handler(CommandHandler("listgroups", list_groups))

    application.add_handler(CallbackQueryHandler(clear_group_data_callback, pattern='^admin_clear_-'))
    application.add_handler(CallbackQueryHandler(cancel_group_action, pattern='^admin_cancel$'))

    broadcast_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start_selection)],
        states={
            BROADCAST_SELECT_CHAT: [
                CallbackQueryHandler(broadcast_select_target, pattern='^bcast_id_-?(\d+)$'),
            ],
            BROADCAST_AWAITING_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_confirm_message),
            ],
            BROADCAST_CONFIRMATION: [
                CallbackQueryHandler(execute_broadcast, pattern='^bcast_confirm$'),
                CallbackQueryHandler(cancel_broadcast_action, pattern='^bcast_cancel$'), 
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_broadcast_action, pattern='^bcast_cancel$'), 
            CommandHandler('cancel', cancel_broadcast_action)
        ],
        allow_reentry=True
    )
    application.add_handler(broadcast_handler)

    comm_handler = ConversationHandler(
        entry_points=[CommandHandler("comm", commission_start)],
        states={
            COMMISSION_AMOUNT: [
                CallbackQueryHandler(request_amount, pattern='^comm_(killer|deposit|m1)$'), 
                MessageHandler(filters.TEXT & ~filters.COMMAND, calculate_commission)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_commission, pattern='^cancel_commission$'),
            CommandHandler('cancel', cancel_conversation)
        ],
        allow_reentry=True
    )
    application.add_handler(comm_handler)

    feedback_handler = ConversationHandler(
        entry_points=[CommandHandler("feedback", start_feedback)],
        states={
            FEEDBACK_AWAITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_feedback)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
        allow_reentry=True
    )
    application.add_handler(feedback_handler)

    application.add_handler(MessageHandler((filters.TEXT & ~filters.COMMAND) | filters.CAPTION, extract_and_save_data))

    application.run_polling(poll_interval=1.0)

if __name__ == '__main__':
    try:
        from web_server import keep_alive
        keep_alive()
    except ImportError:
        pass

    main()
