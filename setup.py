from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.update import Update
from telegram.error import TelegramError
from EgyRequest.Request import get_shows, get_info, get_links
from EgyFucntions.Function import inline
from EgyRequest.Text import command_prevent_message, all_prevent_message, select_type_message
from telethon import TelegramClient, sync
from pprint import pprint
import logging
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Handler,
    Filters,
    CallbackQueryHandler,
    ConversationHandler,
)

# State definitions for conversation
(
    TYPING,
    SELECTING_SHOW,
    SELECTING_TYPE,
    SELECTING_QUALITY,
    SELECTING_SEASON,
    SELECTING_EPISODE,
    PREVENT_COMMAND,
    PREVENT_ALL,
    BACK_SHOWS,

 ) = map(str,range(0,9))

# Shortcut for ConversationHandler.END
END = ConversationHandler.END
TIMEOUT = ConversationHandler.TIMEOUT

# api_id = 7674707
# api_hash = '165eb092814f4a54e215e0c03b844de7'

# client = TelegramClient('H_hisham', api_id, api_hash).start(phone='+201008568308')
# geting_participants = client.get_participants('Egybot_Community')
# participants = [i.id for i in geting_participants]

# bot = telebot.TeleBot("1979999444:AAGuFJiCYCtVB7m2jQojH8zbuYh4F_lU2_o")

# channel_id = -1001591746087
# user_id = 467288828

# result = bot.get_chat_member(channel_id, user_id)
# print(result)

# bot.polling()

logging.basicConfig(format='|(%(asctime)s)| - |%(name)s| - |%(levelname)s| => %(message)s', level=logging.INFO)
logger = logging.getLogger('Hesham')

def start(update, context):
    '''Getting input from user, then search it'''

    # if update.effective_user.id in participants:
    print(update.message.new_chat_members)
    update.message.reply_text(text='الرجاء كتابة فلمك المفضل')

    return SELECTING_SHOW
    # else:
    #     update.message.reply_text(text='الرجاء الاشتراك في القناة اولا، https://t.me/Egybot_Community')

    #     return END

def input_search(update, context):
    '''Handling inputs received from user'''

    # send the user input fo searching
    if context.user_data.get('shows'):
        shows = context.user_data['shows']
    else:
        shows = get_shows(update.message.text)
        print('no1')

    if shows:
        # getting shows photos and name.
        photos = shows['display']['imgs']

        # sending shows and inline keyboard reply
        buttons = shows['display']['buttons']
        buttons_markup = InlineKeyboardMarkup(buttons)

        if context.user_data.get('shows'):
            print('yes2')
            print(update.callback_query.answer(), update.callback_query)
            update.callback_query.edit_message_text(text='نرجو من اختيار احد الأفلام القادمة مع مراعة اختياراتها بشكل صحيح وشكرا لكم جداا:', reply_markup=buttons_markup)
        else:
            print('no2')
            context.bot.send_media_group(chat_id=update.message.chat_id, media=photos)
            update.message.reply_text(text='نرجو من اختيار احد الأفلام القادمة مع مراعة اختياراتها بشكل صحيح وشكرا لكم جداا:', reply_markup=buttons_markup)

        # saving shows to the user data for next steps
        context.user_data['shows'] = shows
        return SELECTING_TYPE

    else:
        update.message.reply_text(text='لا يوجد نتائج، الرجاء المحاولة مرة اخرى')


def command_prevent(update, context):
    context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    update.message.reply_text(text=command_prevent_message)

def all_prevent(update, context):
    context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    update.message.reply_text(text=all_prevent_message)

def select_type(update, context):
    if not context.user_data.get('selected_show'):
        selected_show = context.user_data['shows'][update.callback_query.data]
        update.callback_query.edit_message_text(text='الرجاء الإنتظار لبضع ثواني', parse_mode=ParseMode.MARKDOWN)
        info = get_info(selected_show)
        context.user_data['selected_show'] = info
    else:
        info = context.user_data['selected_show']

    buttons = [
        [InlineKeyboardButton(text='تحميل', callback_data='dl'),
        InlineKeyboardButton(text='مشاهدة', callback_data='watch')],
        [InlineKeyboardButton(text='الرجوع للخلف', callback_data='back_shows')]
    ]
    buttons_markup = InlineKeyboardMarkup(buttons)

    update.callback_query.edit_message_text(text=select_type_message(info), reply_markup=buttons_markup)

    return SELECTING_QUALITY

def select_quality(update, context):
    selected_type = context.user_data['selected_show']
    update.callback_query.edit_message_text(text='الرجاء الإنتظار لمدة اقصاها 5 ثواني', parse_mode=ParseMode.MARKDOWN)

    # define generator yield
    generator_links = get_links(selected_type['show'], type=update.callback_query.data)

    links = next(generator_links)

    # check if movie is available
    if not links:
        update.callback_query.answer(text='للأسف الفيلم أو المسلسل الذي اخترته غير متاح للمشاهدة أو التحميل', show_alert=True)
        buttons = [[InlineKeyboardButton(text='الرجوع للخلف', callback_data='back_shows')]]
    else:
        links_table = context.user_data['selected_show']['links_table']
        back_show_button = [[InlineKeyboardButton(text='الرجوع للخلف', callback_data='back_type')], [InlineKeyboardButton(text='الرجوع لقائمة العرض', callback_data='back_shows')]]
        buttons = inline([InlineKeyboardButton(text=f'{links_table[i]} - {links_table[i+1]}', callback_data=f'{links_table[i]}', url=links[int(i/2)]) for i in range(0, len(links_table), 2)], add=back_show_button)

    # edit the message and reply markup
    buttons_markup = InlineKeyboardMarkup(buttons)
    update.callback_query.edit_message_text(text=select_type_message(selected_type), reply_markup=buttons_markup)

    # closing browser's window
    next(generator_links)
    
def type_hand(update, context):
    print('handled')

def back_to_shows(update, context):
    print('back_show')
    del context.user_data['selected_show']
    input_search(update, context)

    return SELECTING_TYPE

def back_to_type(update, context):
    print('back_type')
    select_type(update, context)
    return SELECTING_QUALITY

def timeout(update, context):
    print('timeout')
    context.bot.send_message(chat_id=update.message.chat_id, text='انتهى الوقت.')

    return TIMEOUT

def cancel(update, context):
    if context.user_data.get('shows'):
        del context.user_data['shows']
    if context.user_data.get('selected_show'):
        del context.user_data['selected_show']
    
    return END

def error(update, context):
    logging.warning(msg=context.error)

def main():
    '''This Function Initiate The Bot '''

    Token = '1979999444:AAGuFJiCYCtVB7m2jQojH8zbuYh4F_lU2_o'
    updater = Updater(token=Token)
    dispatcher = updater.dispatcher

    inline_conversation_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(select_type), MessageHandler(Filters.text &(~Filters.regex(f'^/cancel$')), all_prevent)],
        states={
            SELECTING_QUALITY: [CallbackQueryHandler(select_quality, pattern=f'^(watch|dl)$')],
        },
        fallbacks=[MessageHandler(Filters.text &(~Filters.regex(f'^/cancel$')), all_prevent),
                   CallbackQueryHandler(back_to_shows, pattern=f'^back_shows$'),
                   CallbackQueryHandler(back_to_type, pattern=f'^back_type$'),
                   CommandHandler('cancel', cancel)
        ],
        map_to_parent={
            SELECTING_TYPE: SELECTING_TYPE,
            END: END,
        }
    )

    search_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, run_async=True)],
        states={
            SELECTING_SHOW: [MessageHandler(Filters.text & (~Filters.command), input_search)],
            SELECTING_TYPE: [inline_conversation_handler]
        },
        fallbacks=[MessageHandler(Filters.command & (~Filters.regex(f'^/cancel$')), command_prevent), CommandHandler('cancel', cancel)],
    )
    
    # type_handler = TypeHandler(Update, type_hand)

    dispatcher.add_handler(search_conversation_handler)
    # dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()

main()
