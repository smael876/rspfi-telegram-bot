import os
import logging
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
import database

logger = logging.getLogger(__name__)

CURRENCY = os.getenv("CURRENCY", "$")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip().lstrip("@").lower()

# States for Adding Product
ADD_PROD_CAT, ADD_PROD_NAME, ADD_PROD_DESC, ADD_PROD_PRICE, ADD_PROD_IMG = range(5)

# States for Adding Category
ADD_CAT_NAME = range(10, 11)

def is_admin(user) -> bool:
    if not user:
        return False
    if ADMIN_ID != 0 and user.id == ADMIN_ID:
        return True
    if ADMIN_USERNAME and user.username and user.username.lower() == ADMIN_USERNAME:
        database.set_setting("admin_id", str(user.id))
        return True
    stored_admin_id = database.get_setting("admin_id")
    if stored_admin_id and str(user.id) == stored_admin_id:
        return True
    return False

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """បង្ហាញផ្ទាំងគ្រប់គ្រងសម្រាប់ Admin"""
    user = update.effective_user
    if not is_admin(user):
        await update.message.reply_text(
            f"🚫 <b>លោកអ្នកគ្មានសិទ្ធិប្រើប្រាស់ Admin Panel ទេ!</b>\n"
            f"Telegram User ID របស់អ្នកគឺ: <code>{user.id}</code>\n"
            f"(សូមដាក់លេខ ID នេះក្នុង .env file ត្រង់ ADMIN_ID ឬដាក់ username ក្នុង ADMIN_USERNAME)",
            parse_mode=ParseMode.HTML
        )
        return


    keyboard = [
        [
            InlineKeyboardButton("➕ បន្ថែមទំនិញថ្មី", callback_data="admin_add_prod"),
            InlineKeyboardButton("➕ បន្ថែមជំពូកថ្មី", callback_data="admin_add_cat")
        ],
        [
            InlineKeyboardButton("📦 បញ្ជីទំនិញទាំងអស់", callback_data="admin_list_prods"),
            InlineKeyboardButton("📋 បញ្ជាទិញថ្មីៗ", callback_data="admin_orders")
        ],
        [
            InlineKeyboardButton("❌ បិទផ្ទាំង Admin", callback_data="admin_close")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "👑 <b>ផ្ទាំងគ្រប់គ្រងអ្នកគ្រប់គ្រង (Admin Dashboard)</b>\n\n"
        "សូមជ្រើសរើសមុខងារដែលអ្នកចង់គ្រប់គ្រងខាងក្រោម៖"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

# ====================================================================
# Add Product Flow
# ====================================================================

async def start_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    categories = database.get_all_categories()
    if not categories:
        await query.edit_message_text(
            "⚠️ សូមបង្កើត 'ជំពូកទំនិញ (Category)' ជាមុនសិន មុននឹងបន្ថែមទំនិញ!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ បន្ថែមជំពូក", callback_data="admin_add_cat")]])
        )
        return ConversationHandler.END

    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(cat["name"], callback_data=f"selcat_{cat['id']}")])
    keyboard.append([InlineKeyboardButton("❌ បោះបង់", callback_data="admin_cancel")])

    context.user_data["new_product"] = {}
    await query.edit_message_text(
        "📂 <b>(Step 1/5) សូមជ្រើសរើសជំពូកសម្រាប់ទំនិញថ្មី៖</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return ADD_PROD_CAT

async def add_product_cat_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "admin_cancel":
        await query.edit_message_text("❌ បានបោះបង់ការបន្ថែមទំនិញ។")
        return ConversationHandler.END

    cat_id = int(query.data.split("_")[1])
    context.user_data["new_product"]["category_id"] = cat_id

    await query.edit_message_text(
        "🏷️ <b>(Step 2/5) សូមវាយបញ្ចូល 'ឈ្មោះទំនិញ'៖</b>",
        parse_mode=ParseMode.HTML
    )
    return ADD_PROD_NAME

async def add_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["new_product"]["name"] = name

    await update.message.reply_text(
        f"✅ ឈ្មោះទំនិញ: <b>{name}</b>\n\n"
        "📝 <b>(Step 3/5) សូមវាយបញ្ចូល 'ការពិពណ៌នា' (Description)៖</b>",
        parse_mode=ParseMode.HTML
    )
    return ADD_PROD_DESC

async def add_product_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text.strip()
    context.user_data["new_product"]["description"] = desc

    await update.message.reply_text(
        "💵 <b>(Step 4/5) សូមវាយបញ្ចូល 'តម្លៃ' ជាលេខ (ឧទាហរណ៍: 15.50 ឬ 25)៖</b>",
        parse_mode=ParseMode.HTML
    )
    return ADD_PROD_PRICE

async def add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price_text = update.message.text.strip().replace("$", "")
    try:
        price = float(price_text)
        if price <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("⚠️ សូមវាយបញ្ចូលជាលេខតម្លៃដែលត្រឹមត្រូវ (ឧទាហរណ៍: 12.50)៖")
        return ADD_PROD_PRICE

    context.user_data["new_product"]["price"] = price

    keyboard = [[InlineKeyboardButton("⏩ រំលង (គ្មានរូប)", callback_data="skip_img")]]
    await update.message.reply_text(
        f"✅ តម្លៃ: <b>{CURRENCY}{price:.2f}</b>\n\n"
        "🖼️ <b>(Step 5/5) សូមផ្ញើ 'រូបភាព' នៃទំនិញ ឬផ្ញើជាតំណភ្ជាប់រូបភាព (URL)៖</b>\n"
        "(បើមិនទាន់មានរូបទេ អាចចុចរំលងបាន)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return ADD_PROD_IMG

async def add_product_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    image_url = None

    if update.callback_query and update.callback_query.data == "skip_img":
        await update.callback_query.answer()
    elif update.message and update.message.photo:
        # Get highest resolution photo file_id
        photo = update.message.photo[-1]
        image_url = photo.file_id
    elif update.message and update.message.text:
        text = update.message.text.strip()
        if text.startswith("http://") or text.startswith("https://"):
            image_url = text

    prod_data = context.user_data.get("new_product", {})
    prod_id = database.add_product(
        category_id=prod_data.get("category_id"),
        name=prod_data.get("name"),
        description=prod_data.get("description"),
        price=prod_data.get("price"),
        image_url=image_url
    )

    success_text = (
        f"🎉 <b>បានបន្ថែមទំនិញថ្មីដោយជោគជ័យ!</b>\n"
        f"លេខសម្គាល់: #{prod_id}\n"
        f"ឈ្មោះ: <b>{prod_data.get('name')}</b>\n"
        f"តម្លៃ: <b>{CURRENCY}{prod_data.get('price'):.2f}</b>"
    )

    keyboard = [[InlineKeyboardButton("🔙 ត្រឡប់ទៅផ្ទាំង Admin", callback_data="admin_dashboard")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(success_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(success_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    return ConversationHandler.END


# ====================================================================
# Add Category Flow
# ====================================================================

async def start_add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📂 <b>សូមវាយបញ្ចូលឈ្មោះជំពូកថ្មី (ឧទាហរណ៍: 👟 ស្បែកជើង)៖</b>",
        parse_mode=ParseMode.HTML
    )
    return ADD_CAT_NAME

async def add_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    cat_id = database.add_category(name)

    if cat_id:
        text = f"✅ បានបង្កើតជំពូកថ្មី: <b>{name}</b> ដោយជោគជ័យ!"
    else:
        text = f"⚠️ ឈ្មោះជំពូក <b>{name}</b> នេះមានរួចហើយ!"

    keyboard = [[InlineKeyboardButton("🔙 ត្រឡប់ទៅផ្ទាំង Admin", callback_data="admin_dashboard")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return ConversationHandler.END


# ====================================================================
# List & Delete Products
# ====================================================================

async def admin_list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    products = database.get_all_products()
    if not products:
        keyboard = [[InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="admin_dashboard")]]
        await query.edit_message_text("📦 បច្ចុប្បន្នគ្មានទំនិញក្នុងប្រព័ន្ធទេ។", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    keyboard = []
    for prod in products[:15]:
        keyboard.append([
            InlineKeyboardButton(f"{prod['name']} (${prod['price']:.2f})", callback_data=f"admview_{prod['id']}"),
            InlineKeyboardButton("🗑️ លុប", callback_data=f"admdel_{prod['id']}")
        ])

    keyboard.append([InlineKeyboardButton("🔙 ត្រឡប់ទៅផ្ទាំង Admin", callback_data="admin_dashboard")])

    await query.edit_message_text(
        "📦 <b>បញ្ជីទំនិញក្នុងហាង (ចុច 🗑️ ដើម្បីលុបចេញពីហាង)៖</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def admin_delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    product_id = int(query.data.split("_")[1])

    product = database.get_product(product_id)
    name = product["name"] if product else "ទំនិញ"

    database.delete_product(product_id)
    await query.answer(f"🗑️ បានលុបទំនិញ '{name}' រួចរាល់!", show_alert=True)
    await admin_list_products(update, context)


# ====================================================================
# Recent Orders & Status Management
# ====================================================================

async def admin_recent_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    orders = database.get_recent_orders(limit=10)
    if not orders:
        keyboard = [[InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="admin_dashboard")]]
        await query.edit_message_text("📋 មិនទាន់មានការបញ្ជាទិញណាមួយនៅឡើយទេ។", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    keyboard = []
    lines = ["📋 <b>បញ្ជាទិញថ្មីៗទាំង ១០៖</b>\n"]
    for ord in orders:
        lines.append(
            f"• <b>#{ord['id']}</b> | {ord['customer_name']} | {CURRENCY}{ord['total_amount']:.2f}\n"
            f"  ស្ថានភាព: <code>{ord['status']}</code>"
        )
        keyboard.append([
            InlineKeyboardButton(f"មើលកុម្ម៉ង់ #{ord['id']}", callback_data=f"adm_ord_{ord['id']}")
        ])

    keyboard.append([InlineKeyboardButton("🔙 ត្រឡប់ទៅផ្ទាំង Admin", callback_data="admin_dashboard")])

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def render_order_details(query, order_id: int):
    order = database.get_order_details(order_id)

    if not order:
        try:
            await query.edit_message_text("⚠️ រកមិនឃើញព័ត៌មានកុម្ម៉ង់នេះទេ!")
        except Exception:
            await query.message.reply_text("⚠️ រកមិនឃើញព័ត៌មានកុម្ម៉ង់នេះទេ!")
        return

    items_text = "\n".join([f"• {it['product_name']} x{it['quantity']} = {CURRENCY}{it['price']*it['quantity']:.2f}" for it in order["items"]])

    details = (
        f"📋 <b>ព័ត៌មានលម្អិតកុម្ម៉ង់ #{order['id']}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 អតិថិជន: <b>{order['customer_name']}</b>\n"
        f"📞 ទូរស័ព្ទ: <code>{order['phone']}</code>\n"
        f"📍 អាសយដ្ឋាន: {order['address']}\n"
        f"💳 ទូទាត់: {order['payment_method']}\n"
        f"🚦 ស្ថានភាពបច្ចុប្បន្ន: <b>{order['status']}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"📦 មុខទំនិញ៖\n{items_text}\n"
        f"━━━━━━━━━━━━━━\n"
        f"💰 <b>សរុប: {CURRENCY}{order['total_amount']:.2f}</b>\n\n"
        f"👇 <b>ចុចប៊ូតុងខាងក្រោមដើម្បីប្តូរស្ថានភាព៖</b>"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ បញ្ជាក់ (Confirm)", callback_data=f"status_{order_id}_បានបញ្ជាក់"),
            InlineKeyboardButton("🚚 កំពុងដឹក (Shipping)", callback_data=f"status_{order_id}_កំពុងដឹកជញ្ជូន")
        ],
        [
            InlineKeyboardButton("🎉 ជោគជ័យ (Done)", callback_data=f"status_{order_id}_បានដឹកដល់ជោគជ័យ"),
            InlineKeyboardButton("❌ បោះបង់ (Cancel)", callback_data=f"status_{order_id}_បានបោះបង់")
        ],
        [
            InlineKeyboardButton("🔙 ត្រឡប់ទៅបញ្ជីកុម្ម៉ង់", callback_data="admin_orders")
        ]
    ]

    try:
        await query.edit_message_text(details, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except Exception:
        try:
            await query.edit_message_caption(details, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except Exception:
            await query.message.reply_text(details, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def admin_order_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = int(query.data.split("_")[2])
    await render_order_details(query, order_id)

async def admin_update_order_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.split("_")
    order_id = int(parts[1])
    new_status = parts[2]

    database.update_order_status(order_id, new_status)
    await query.answer(f"✅ បានផ្លាស់ប្តូរស្ថានភាពទៅជា '{new_status}'", show_alert=True)

    # Refresh details view safely
    await render_order_details(query, order_id)

async def admin_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("👋 បានបិទផ្ទាំង Admin Panel។")
