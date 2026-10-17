import os
import re
import time
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==========================================
# ⚙️ Configuration
# ==========================================
REQUIRED_CHANNEL = "@OFFLINE_BOY_OFFICIAL"
CHANNEL_URL = "https://t.me/OFFLINE_BOY_OFFICIAL"
TARGET_GROUP = "@OFFLINE_BOY_OFFICIAL" 

(
    CHECK_PASSWORD,
    GET_FILE, GET_CAPTION,
    GET_BAN_USER, GET_REMOVE_USER,
    GET_POST_TEXT,
    GET_ADD_ADMIN, GET_REMOVE_ADMIN,
    GET_OLD_PASS1, GET_OLD_PASS2, GET_NEW_PASS,
    GET_ADD_GROUP
) = range(12)

bot_config = {
    "password": "1498",
    "master_password": "1498B"
}

failed_attempts = {}
blocked_users = {}

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📢 জয়েন চ্যানেল"), KeyboardButton("➕ অ্যাড গ্রুপ")],
        [KeyboardButton("📁 ফাইল পোস্ট"), KeyboardButton("📢 অটো পোস্ট")],
        [KeyboardButton("🔨 ইউজার ব্যান"), KeyboardButton("👢 ইউজার রিমুভ")],
        [KeyboardButton("🛡️ অ্যাডমিন"), KeyboardButton("🔑 পাসওয়ার্ড পরিবর্তন")]
    ],
    resize_keyboard=True
)

def extract_user(text: str):
    text = text.strip()
    match = re.search(r"(?:https?://)?(?:t.me|telegram.me)/([a-zA-Z0-9_]+)", text)
    if match:
        return f"@{match.group(1)}"
    if text.startswith("@"):
        return text
    if text.isdigit():
        return int(text)
    return text

async def resolve_user_id(user_input: str, context: ContextTypes.DEFAULT_TYPE) -> int | str | None:
    user_input = user_input.strip()
    if user_input.isdigit() or (user_input.startswith("-") and user_input[1:].isdigit()):
        return int(user_input)
    
    clean_username = extract_user(user_input)
    try:
        chat = await context.bot.get_chat(clean_username)
        return chat.id
    except Exception as e:
        logger.error(f"Cannot resolve user ID for {user_input}: {e}")
        return clean_username

async def is_user_allowed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> tuple[bool, bool]:
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        if member.status == 'creator':
            return True, True
        elif member.status in ['administrator', 'member']:
            return True, False
        return False, False
    except Exception as e:
        logger.error(f"Channel join check error: {e}")
        return False, False

async def welcome_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.chat_member.new_chat_members:
        if member.id == context.bot.id:
            continue
        user_mention = f"@{member.username}" if member.username else member.first_name
        welcome_text = f"{user_mention} joyen grup"
        await update.chat_member.chat.send_message(welcome_text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_time = time.time()

    if user_id in blocked_users:  
        unblock_time = blocked_users[user_id]  
        if current_time < unblock_time:  
            remaining_hours = int((unblock_time - current_time) / 3600) + 1  
            await update.message.reply_text(  
                f"🚫 Apni barbar vul password deway 24 ghortar jonno block achen! Pray {remaining_hours} ghorat por chesta korun.",  
                reply_markup=ReplyKeyboardRemove()  
            )  
            return ConversationHandler.END  
        else:  
            del blocked_users[user_id]  
            if user_id in failed_attempts:  
                del failed_attempts[user_id]  

    await update.message.reply_text("🔒 Boter sheba pete daya kore password din:", reply_markup=ReplyKeyboardRemove())  
    return CHECK_PASSWORD

async def verify_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text.strip()
    current_pass = bot_config["password"]
    master_pass = bot_config["master_password"]

    # Delete Password Message for Security
    try:
        await update.message.delete()
    except Exception:
        pass

    # Bypass Password Check (1498B)
    if user_input == master_pass:
        if user_id in failed_attempts:  
            del failed_attempts[user_id]
        await context.bot.send_message(chat_id=user_id, text="👑 WELCOME OWNER! MASTER PASSWORD MATCHED. ALL CONTROLS ARE UNLOCKED ☺️💝", reply_markup=MAIN_KEYBOARD)  
        return ConversationHandler.END

    if user_input == current_pass or (current_pass == "1498" and user_input in ["1498", "198"]):  
        if user_id in failed_attempts:  
            del failed_attempts[user_id]  
          
        allowed, is_owner = await is_user_allowed(user_id, context)  

        if not allowed:  
            join_btn = InlineKeyboardMarkup([  
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],  
                [InlineKeyboardButton("✅ Joyen korechi (Check)", callback_data="check_join")]  
            ])  
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Password sothik! Kintu bot bebohar korar age apnake oboshoy amader channele join thakte hobe.\n\nChannele join kore nicher buttone chap din:",  
                reply_markup=join_btn  
            )  
            return ConversationHandler.END  

        welcome_msg = "WELCOME OWNER! ALL CONTROLS ARE UNLOCKED ☺️💝" if is_owner else "HELLO! HOW CAN I HELP YOU ☺️💝"  
        await context.bot.send_message(chat_id=user_id, text=welcome_msg, reply_markup=MAIN_KEYBOARD)  
        return ConversationHandler.END  

    else:  
        if user_id not in failed_attempts:  
            failed_attempts[user_id] = 0  
        failed_attempts[user_id] += 1  
        attempts = failed_attempts[user_id]  

        if attempts == 5:  
            await context.bot.send_message(chat_id=user_id, text="⚠️ **Sotorkobarta:** Tana 5 bar vul password diyechen! Ar 1 bar vul dile 24 ghortar jonno block hoben.")  
            return CHECK_PASSWORD  
        elif attempts >= 6:  
            blocked_users[user_id] = time.time() + 86400  
            await context.bot.send_message(chat_id=user_id, text="🚫 6 bar vul password dewar karone apnake 24 ghortar jonno block kora holo!")  
            return ConversationHandler.END  
        else:  
            await context.bot.send_message(chat_id=user_id, text=f"❌ Vul password! ({attempts}/6). Sothik password abar din:")  
            return CHECK_PASSWORD

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    allowed, is_owner = await is_user_allowed(user_id, context)  

    if allowed:  
        welcome_msg = "WELCOME OWNER! ALL CONTROLS ARE UNLOCKED ☺️💝" if is_owner else "✅ Joyen shofol hoyeche! HOW CAN I HELP YOU ☺️💝"  
        await query.message.reply_text(welcome_msg, reply_markup=MAIN_KEYBOARD)  
    else:  
        await query.message.reply_text("❌ Apni ekhono channele join kornenni! Age join korun.")

async def change_pass_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔑 Password poriborton korte 2ti password dite hobe.\n\nOld Pass 1 din:")  
    return GET_OLD_PASS1

async def verify_old_pass1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    current_pass = bot_config["password"]
    master_pass = bot_config["master_password"]

    try:
        await update.message.delete()
    except Exception:
        pass

    if user_input == current_pass or user_input == master_pass or user_input == "1498":  
        await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Old Pass 1 sothik!\n\nEbar Old Pass 2 din:")  
        return GET_OLD_PASS2  
    else:  
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Old Pass 1 vul! Batil kora holo.", reply_markup=MAIN_KEYBOARD)  
        return ConversationHandler.END

async def verify_old_pass2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    try:
        await update.message.delete()
    except Exception:
        pass

    if user_input == "198":  
        await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Old Pass 2 sothik!\n\nEbar New Password likhun:")  
        return GET_NEW_PASS  
    else:  
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Old Pass 2 vul! Batil kora holo.", reply_markup=MAIN_KEYBOARD)  
        return ConversationHandler.END

async def save_new_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_pass = update.message.text.strip()
    bot_config["password"] = new_pass
    
    try:
        await update.message.delete()
    except Exception:
        pass

    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Password poriborton shofol hoyeche! New Password: {new_pass}", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END

async def join_channel_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    join_btn = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Official Channel", url=CHANNEL_URL)]])
    await update.message.reply_text("Amader official channel link:", reply_markup=join_btn)

async def add_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("➕ Apnar group link ba group ID pathan:")  
    return GET_ADD_GROUP

async def execute_add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_info = update.message.text.strip()
    await update.message.reply_text(f"✅ Group {group_info} yukto kora hoyeche!", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_chat = TARGET_GROUP
    try:  
        admins = await context.bot.get_chat_administrators(target_chat)  
        admin_list_text = f"<b>🛡️ {target_chat} Group-er bortoman Admin talika:</b>\n\n"  
        for idx, admin in enumerate(admins, 1):  
            user = admin.user  
            name = f"@{user.username}" if user.username else user.first_name  
            admin_list_text += f"{idx}. {name}\n"  

        inline_keyboard = InlineKeyboardMarkup([  
            [  
                InlineKeyboardButton("➕ Add Admin", callback_data="add_admin_action"),  
                InlineKeyboardButton("➖ Remove Admin", callback_data="show_remove_admins")  
            ]  
        ])  

        await update.message.reply_text(admin_list_text, parse_mode="HTML", reply_markup=inline_keyboard)  
    except Exception as e:  
        await update.message.reply_text(f"❌ Admin list anle bartho.\nTruti: {e}")

async def admin_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "add_admin_action":  
        await query.message.reply_text("Jake Admin banate chan tar Profile Link, ID ba @username share korun:")  
        return GET_ADD_ADMIN  
    
    elif query.data == "show_remove_admins":
        try:
            admins = await context.bot.get_chat_administrators(TARGET_GROUP)
            buttons = []
            for admin in admins:
                if admin.user.is_bot:
                    continue
                name = f"@{admin.user.username}" if admin.user.username else admin.user.first_name
                buttons.append([InlineKeyboardButton(f"❌ {name}", callback_data=f"confirm_rem_{admin.user.id}")])
            
            if not buttons:
                await query.message.reply_text("Kono remove korar moto admin pawa jayni.")
                return
            
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.reply_text("Kake Admin theke remove korben ta select korun:", reply_markup=reply_markup)
        except Exception as e:
            await query.message.reply_text(f"Truti: {e}")

    elif query.data.startswith("confirm_rem_"):
        user_id = query.data.split("_")[2]
        confirm_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Ha, Confirm Remove", callback_data=f"do_rem_{user_id}")],
            [InlineKeyboardButton("❌ Batil", callback_data="cancel_rem")]
        ])
        await query.message.reply_text(f"Apni ki shotti ID: {user_id} ke Admin theke remove korte chan?", reply_markup=confirm_btn)

    elif query.data.startswith("do_rem_"):
        user_id = int(query.data.split("_")[2])
        try:
            await context.bot.promote_chat_member(
                chat_id=TARGET_GROUP,
                user_id=user_id,
                can_manage_chat=False,
                can_delete_messages=False,
                can_restrict_members=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_promote_members=False
            )
            await query.message.reply_text(f"✅ ID: {user_id} ke Admin theke remove kora hoyeche!")
        except Exception as e:
            await query.message.reply_text(f"❌ Remove korte bartho!\nTruti: {e}")

    elif query.data == "cancel_rem":
        await query.message.reply_text("Batil kora hoyeche.")

async def execute_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_input = update.message.text.strip()
    user_target = await resolve_user_id(raw_input, context)
    
    if not user_target:
        await update.message.reply_text("❌ User khunje pawa jayni!", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END

    try:
        await context.bot.promote_chat_member(
            chat_id=TARGET_GROUP,
            user_id=user_target,
            can_manage_chat=True,
            can_delete_messages=True,
            can_restrict_members=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_promote_members=False
        )
        await update.message.reply_text(f"✅ {raw_input} ke {TARGET_GROUP} -e All Rules/Permissions shoho Admin বানানো হয়েছে!", reply_markup=MAIN_KEYBOARD)
    except Exception as e:
        await update.message.reply_text(f"❌ Admin banate bartho!\nTruti: {e}", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END

async def file_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Daya kore file (Photo/Video/Document) pathan:")
    return GET_FILE

async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        context.user_data['file_id'] = update.message.document.file_id
        context.user_data['file_type'] = 'document'
    elif update.message.photo:
        context.user_data['file_id'] = update.message.photo[-1].file_id
        context.user_data['file_type'] = 'photo'
    elif update.message.video:
        context.user_data['file_id'] = update.message.video.file_id
        context.user_data['file_type'] = 'video'
    else:
        await update.message.reply_text("Sothik file din ba /cancel chapun.")
        return GET_FILE

    await update.message.reply_text("File peyechi! Ebar caption din:")  
    return GET_CAPTION

async def receive_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = update.message.text
    file_id = context.user_data.get('file_id')
    file_type = context.user_data.get('file_type')

    try:
        if file_type == 'document':  
            await context.bot.send_document(chat_id=TARGET_GROUP, document=file_id, caption=caption)  
        elif file_type == 'photo':  
            await context.bot.send_photo(chat_id=TARGET_GROUP, photo=file_id, caption=caption)  
        elif file_type == 'video':  
            await context.bot.send_video(chat_id=TARGET_GROUP, video=file_id, caption=caption)  
        
        await update.message.reply_text(f"✅ File-ti {TARGET_GROUP} -e post kora hoyeche!", reply_markup=MAIN_KEYBOARD)  
    except Exception as e:
        await update.message.reply_text(f"❌ Post korte bartho!\nTruti: {e}", reply_markup=MAIN_KEYBOARD)

    return ConversationHandler.END

async def ban_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("User ID, Profile Link ba @username din:")
    return GET_BAN_USER

async def execute_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_input = update.message.text.strip()
    user_id = await resolve_user_id(raw_input, context)
    
    if not user_id:
        await update.message.reply_text("❌ User khunje pawa jayni!", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END

    try:
        await context.bot.ban_chat_member(chat_id=TARGET_GROUP, user_id=user_id)
        await update.message.reply_text(f"✅ {raw_input} ke {TARGET_GROUP} theke ban kora hoyeche.", reply_markup=MAIN_KEYBOARD)
    except Exception as e:
        await update.message.reply_text(f"❌ Ban korte bartho!\nTruti: {e}", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END

async def remove_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("User ID, Profile Link ba @username din:")
    return GET_REMOVE_USER

async def execute_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_input = update.message.text.strip()
    user_id = await resolve_user_id(raw_input, context)
    
    if not user_id:
        await update.message.reply_text("❌ User khunje pawa jayni!", reply_markup=MAIN_KEYBOARD)
        return ConversationHandler.END

    try:
        await context.bot.ban_chat_member(chat_id=TARGET_GROUP, user_id=user_id)
        await context.bot.unban_chat_member(chat_id=TARGET_GROUP, user_id=user_id)
        await update.message.reply_text(f"✅ {raw_input} ke {TARGET_GROUP} theke remove kora hoyeche.", reply_markup=MAIN_KEYBOARD)
    except Exception as e:
        await update.message.reply_text(f"❌ Remove korte bartho!\nTruti: {e}", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END

async def post_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Group ba channele post korar jonno message-ti din:")
    return GET_POST_TEXT

async def execute_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post_text = update.message.text
    try:
        await context.bot.send_message(chat_id=TARGET_GROUP, text=post_text)
        await update.message.reply_text(f"✅ Post-ti {TARGET_GROUP} -e pathano hoyeche!", reply_markup=MAIN_KEYBOARD)
    except Exception as e:
        await update.message.reply_text(f"❌ Post korte bartho!\nTruti: {e}", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Batil kora hoyeche.", reply_markup=MAIN_KEYBOARD)
    return ConversationHandler.END

if __name__ == '__main__':
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        logger.error("BOT_TOKEN missing!")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()  

    start_handler = ConversationHandler(  
        entry_points=[CommandHandler('start', start)],  
        states={  
            CHECK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_password)],  
        },  
        fallbacks=[CommandHandler('cancel', cancel)]  
    )  

    pass_change_handler = ConversationHandler(  
        entry_points=[  
            CommandHandler('pass', change_pass_start),  
            MessageHandler(filters.Regex('^🔑 পাসওয়ার্ড পরিবর্তন$'), change_pass_start)  
        ],  
        states={  
            GET_OLD_PASS1: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_old_pass1)],  
            GET_OLD_PASS2: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_old_pass2)],  
            GET_NEW_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_pass)],  
        },  
        fallbacks=[CommandHandler('cancel', cancel)]  
    )  

    add_group_handler = ConversationHandler(  
        entry_points=[MessageHandler(filters.Regex('^➕ অ্যাড গ্রুপ$'), add_group_start)],  
        states={  
            GET_ADD_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_add_group)],  
        },  
        fallbacks=[CommandHandler('cancel', cancel)]  
    )  

    file_handler = ConversationHandler(  
        entry_points=[  
            CommandHandler('file', file_start),  
            MessageHandler(filters.Regex('^📁 ফাইল পোস্ট$'), file_start)  
        ],  
        states={  
            GET_FILE: [MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, receive_file)],  
            GET_CAPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_caption)],  
        },  
        fallbacks=[CommandHandler('cancel', cancel)]  
    )  

    ban_handler = ConversationHandler(  
        entry_points=[  
            CommandHandler('ban', ban_start),  
            MessageHandler(filters.Regex('^🔨 ইউজার ব্যান$'), ban_start)  
        ],  
        states={  
            GET_BAN_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_ban)],  
        },  
        fallbacks=[CommandHandler('cancel', cancel)]  
    )  

    remove_handler = ConversationHandler(  
        entry_points=[  
            CommandHandler('remove', remove_start),  
            MessageHandler(filters.Regex('^👢 ইউজার রিমুভ$'), remove_start)  
        ],  
        states={  
            GET_REMOVE_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_remove)],  
        },  
        fallbacks=[CommandHandler('cancel', cancel)]  
    )  

    post_handler = ConversationHandler(  
        entry_points=[  
            CommandHandler('post', post_start),  
            MessageHandler(filters.Regex('^📢 অটো পোস্ট$'), post_start)  
        ],  
        states={  
            GET_POST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_post)],  
        },  
        fallbacks=[CommandHandler('cancel', cancel)]  
    )  

    admin_handler = ConversationHandler(  
        entry_points=[  
            CallbackQueryHandler(admin_button_click, pattern="^add_admin_action$")  
        ],  
        states={  
            GET_ADD_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, execute_add_admin)],  
        },  
        fallbacks=[CommandHandler('cancel', cancel)]  
    )  

    app.add_handler(start_handler)  
    app.add_handler(pass_change_handler)  
    app.add_handler(add_group_handler)  
      
    app.add_handler(CommandHandler("admin", admin_command))  
    app.add_handler(MessageHandler(filters.Regex('^🛡️ অ্যাডমিন$'), admin_command))  
    app.add_handler(MessageHandler(filters.Regex('^📢 জয়েন চ্যানেল$'), join_channel_btn))  
      
    app.add_handler(file_handler)  
    app.add_handler(ban_handler)  
    app.add_handler(remove_handler)  
    app.add_handler(post_handler)  
    app.add_handler(admin_handler)  
      
    app.add_handler(CallbackQueryHandler(admin_button_click, pattern="^(show_remove_admins|confirm_rem_|do_rem_|cancel_rem)"))  
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))  
    app.add_handler(ChatMemberHandler(welcome_member, ChatMemberHandler.CHAT_MEMBER))  

    logger.info("Bot starting...")  
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
