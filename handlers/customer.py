import os
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
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
SHOP_NAME = os.getenv("SHOP_NAME", "RSPFI Store")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5775087092"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Smael6667").strip().lstrip("@").lower()
SUPPORT_TELEGRAM = os.getenv("SUPPORT_TELEGRAM", "https://t.me/ceo_yanFi")
DELIVERY_FEE = float(os.getenv("DELIVERY_FEE", "1.50"))

def get_direct_telegram_url(target: str) -> str:
    """
    បង្កើត Link ទៅកាន់ Telegram ដោយស្តង់ដារ https://t.me/<username>
    ដែលដំណើរការ ១០០% លើគ្រប់ឧបករណ៍ (iOS, Android, Desktop) ដោយមិនចេញ Error "Action can't be completed"
    """
    if not target:
        return "https://t.me"
    s = target.strip()
    for prefix in ["https://t.me/", "http://t.me/", "t.me/", "@", "tg://resolve?domain="]:
        if s.startswith(prefix):
            s = s[len(prefix):]
    username = s.strip("/").split("?")[0]
    if username:
        return f"https://t.me/{username}"
    return target

DIRECT_SUPPORT_TELEGRAM = get_direct_telegram_url(SUPPORT_TELEGRAM)

# Checkout Conversation States

STATE_PHONE, STATE_ADDRESS, STATE_PAYMENT, STATE_KHQR_WAIT = range(4)

def get_main_menu_keyboard():
    return ReplyKeyboardRemove()

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ស្វាគមន៍អតិថិជន"""
    user = update.effective_user
    
    # ប្រសិនបើអ្នកចុច Start គឺជា Admin យើងកត់ត្រា ID ស្វ័យប្រវត្តិ
    if ADMIN_USERNAME and user.username and user.username.lower() == ADMIN_USERNAME:
        database.set_setting("admin_id", str(user.id))

    welcome_text = (
        f"👋 សួស្តី <b>{user.first_name}</b>!\n"
        f"សូមស្វាគមន៍មកកាន់ <b>{SHOP_NAME}</b> 🛍️\n\n"
        "យើងខ្ញុំមានលក់ផលិតផលគុណភាពខ្ពស់ដូចជា៖\n"
        "• 🌸 <b>ថ្នាំក្រមុំម្តងទៀត (RSPFI Lady Vaginy)</b>\n"
        "• 🧼 <b>សាប៊ូអនាម័យ RSPFI Lady Soap</b>\n"
        "• 🌿 <b>វីតាមីនស៊ុល RSPFI Mint (តំបន់សំណើម)</b>\n"
        "• 🍓 <b>វីតាមីនស៊ុល RSPFI Strawberry (តំបន់សំណើម)</b>\n\n"
        "សូមចុចប៊ូតុងខាងក្រោមដើម្បីពិនិត្យ និងបញ្ជាទិញ៖"
    )
    start_inline_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ មើលផលិតផល (View Products)", callback_data="show_all_products")],
        [InlineKeyboardButton("💬 សាកសួរព័ត៌មាន (Direct Chat)", url=DIRECT_SUPPORT_TELEGRAM)]
    ])
    await update.message.reply_text(
        welcome_text,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.HTML
    )
    await update.message.reply_text(
        "👇 <b>ចុចប៊ូតុងខាងក្រោមដើម្បីមើលផលិតផលភ្លាមៗ៖</b>",
        reply_markup=start_inline_markup,
        parse_mode=ParseMode.HTML
    )

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """បង្ហាញបញ្ជីផលិតផលទាំងអស់ (Products List) ជាមួយប៊ូតុងជ្រើសរើស"""
    products = database.get_all_products()
    if not products:
        text = "⚠️ បច្ចុប្បន្នមិនទាន់មានផលិតផលដាក់លក់នៅឡើយទេ។ សូមរង់ចាំបន្តិច!"
        if update.callback_query:
            await update.callback_query.answer()
            try:
                await update.callback_query.edit_message_text(text)
            except Exception:
                await update.callback_query.message.reply_text(text)
        else:
            await update.message.reply_text(text)
        return

    keyboard = []
    lines = [
        f"🛍️ <b>បញ្ជីផលិតផលរបស់ {SHOP_NAME}៖</b>\n",
        "សូមជ្រើសរើសផលិតផលខាងក្រោមដើម្បីមើលរូបភាព និងព័ត៌មានលម្អិត៖\n"
    ]

    for idx, prod in enumerate(products, start=1):
        price_str = f"{CURRENCY}{prod['price']:.2f}"
        if prod.get("price") == 4.5:
            price_str = "18,000៛ ($4.50)"
        lines.append(f"{idx}. <b>{prod['name']}</b> — <b>{price_str}</b>")
        keyboard.append([
            InlineKeyboardButton(f"👉 {prod['name']} ({price_str})", callback_data=f"prod_{prod['id']}")
        ])

    keyboard.append([
        InlineKeyboardButton("💬 សាកសួរព័ត៌មាន (Direct Chat)", url=DIRECT_SUPPORT_TELEGRAM)
    ])

    text = "\n".join(lines)
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        try:
            if update.callback_query.message.photo:
                await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            else:
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except Exception:
            await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """បង្ហាញបញ្ជីជំពូកទំនិញ (Categories)"""
    categories = database.get_all_categories()
    if not categories:
        text = "⚠️ បច្ចុប្បន្នមិនទាន់មានទំនិញដាក់លក់នៅឡើយទេ។ សូមរង់ចាំបន្តិច!"
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text)
        else:
            await update.message.reply_text(text)
        return

    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(cat["name"], callback_data=f"cat_{cat['id']}")])
    
    text = "📂 <b>សូមជ្រើសរើសប្រភេទផលិតផលដែលលោកអ្នកចង់មើល៖</b>"
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def on_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """បង្ហាញផលិតផលនៅក្នុង Category ដែលបានជ្រើសរើស"""
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.split("_")[1])
    products = database.get_products_by_category(category_id)

    if not products:
        keyboard = [[InlineKeyboardButton("🔙 ថយក្រោយ (Back)", callback_data="show_categories")]]
        await query.edit_message_text(
            "⚠️ មិនទាន់មានទំនិញនៅក្នុងប្រភេទនេះនៅឡើយទេ។",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    keyboard = []
    for prod in products:
        btn_text = f"{prod['name']} — {CURRENCY}{prod['price']:.2f}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"prod_{prod['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 ថយក្រោយ (Back)", callback_data="show_categories")])
    
    await query.edit_message_text(
        "✨ <b>សូមជ្រើសរើសផលិតផលដើម្បីមើលព័ត៌មានលម្អិត៖</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

def get_product_keyboard(product_id: int, category_id: int, price: float, qty: int = 1) -> InlineKeyboardMarkup:
    total_prod = price * qty
    total_with_del = total_prod + DELIVERY_FEE
    total_khr = total_with_del * 4000
    
    keyboard = [
        # Quantity controls (+ / -)
        [
            InlineKeyboardButton("➖", callback_data=f"pqty_{product_id}_{max(1, qty - 1)}"),
            InlineKeyboardButton(f"🔢 ចំនួន: {qty} ប្រអប់", callback_data="pqty_none"),
            InlineKeyboardButton("➕", callback_data=f"pqty_{product_id}_{qty + 1}")
        ],
        # Order button (dynamically shows quantity, price, and delivery fee)
        [
            InlineKeyboardButton(f"📦 បញ្ជាទិញ {qty} ប្រអប់ — {CURRENCY}{total_with_del:.2f} (សេវា 1.50ដុល្លារ)", callback_data=f"buynow_{product_id}_{qty}")
        ],
        # QR Code & Support Chat
        [
            InlineKeyboardButton("📱 ស្កេន QR ទូទាត់", callback_data=f"showqr_{product_id}"),
            InlineKeyboardButton("💬 សាកសួរព័ត៌មាន (Direct Chat)", url=DIRECT_SUPPORT_TELEGRAM)
        ],
        [
            InlineKeyboardButton("🛍️ មើលផលិតផលផ្សេងទៀត", callback_data="show_all_products")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def on_product_qty_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """កែប្រែចំនួនផលិតផល (+ / -) និងធ្វើបច្ចុប្បន្នភាពប៊ូតុង Order ភ្លាមៗ"""
    query = update.callback_query
    await query.answer()

    if query.data == "pqty_none":
        return

    parts = query.data.split("_")
    product_id = int(parts[1])
    qty = int(parts[2])
    if qty < 1:
        qty = 1

    product = database.get_product(product_id)
    if not product:
        return

    new_markup = get_product_keyboard(product_id, product["category_id"], product["price"], qty)
    try:
        await query.edit_message_reply_markup(reply_markup=new_markup)
    except Exception as e:
        logger.debug(f"Reply markup not modified: {e}")

async def on_product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """បង្ហាញព័ត៌មានលម្អិតរបស់ទំនិញ (រូបភាព, តម្លៃ, ការពិពណ៌នា, ប៊ូតុងបញ្ជាទិញ)"""
    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split("_")[1])
    product = database.get_product(product_id)

    if not product:
        await query.edit_message_text("⚠️ រកមិនឃើញទំនិញនេះទេ!")
        return

    details = (
        f"🏷️ <b>{product['name']}</b>\n"
        f"📂 ប្រភេទ: {product.get('category_name', 'ទូទៅ')}\n"
        f"💵 តម្លៃ: <b>{CURRENCY}{product['price']:.2f}</b> / ប្រអប់\n"
        f"🚚 សេវាដឹកជញ្ជូន: <b>(សេវា 1.50ដុល្លារ)</b>\n\n"
        f"📝 <b>ការពិពណ៌នា៖</b>\n{product['description']}\n"
    )

    reply_markup = get_product_keyboard(product["id"], product["category_id"], product["price"], qty=1)


    # លុបសារចាស់ ឬផ្ញើរូបភាពថ្មី
    if product.get("image_url"):
        img_val = product["image_url"]
        try:
            await query.message.delete()
            if os.path.exists(img_val):
                with open(img_val, "rb") as photo_file:
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=photo_file,
                        caption=details,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML
                    )
            else:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=img_val,
                    caption=details,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            return
        except Exception as e:
            logger.warning(f"Failed to send photo: {e}")

    await query.edit_message_text(
        text=details,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def show_product_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """បង្ហាញរូបភាព ABA KHQR សម្រាប់ផលិតផលជាក់លាក់"""
    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split("_")[1])
    product = database.get_product(product_id)
    if not product:
        await query.message.reply_text("⚠️ រកមិនឃើញទំនិញនេះទេ។")
        return

    price_usd = product["price"]
    total_usd = price_usd + DELIVERY_FEE
    total_khr = total_usd * 4000

    caption = (
        f"📱 <b>ABA' KHQR សម្រាប់ទូទាត់ប្រាក់</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🏷️ ផលិតផល: <b>{product['name']}</b> ({CURRENCY}{price_usd:.2f})\n"
        f"🚚 សេវាដឹកជញ្ជូន: <b>+{CURRENCY}{DELIVERY_FEE:.2f} (ឬ {DELIVERY_FEE*4000:,.0f} ៛)</b>\n"
        f"💰 <b>សរុបត្រូវបង់: {CURRENCY}{total_usd:.2f} (ឬ {total_khr:,.0f} ៛)</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 ឈ្មោះគណនី: <b>SMAEL SOS</b>\n"
        f"🏦 ធនាគារ: <b>ABA BANK</b>\n"
        f"💵 គណនី USD: <code>966 667 335</code>\n"
        f"🇰🇭 គណនី KHR: <code>010 785 006</code>\n"
        f"━━━━━━━━━━━━━━\n"
        f"👉 លោកអ្នកអាចស្កេនទូទាត់រួចចុច <b>'⚡ បញ្ជាទិញភ្លាមៗ'</b> ខាងក្រោម៖"
    )


    keyboard = [
        [InlineKeyboardButton("⚡ បញ្ជាទិញភ្លាមៗ (សេវា 1.50ដុល្លារ)", callback_data=f"buynow_{product['id']}")],
        [InlineKeyboardButton("💬 សាកសួរព័ត៌មានបន្ថែម (Direct Chat)", url=DIRECT_SUPPORT_TELEGRAM)],
        [
            InlineKeyboardButton("🛍️ មើលផលិតផល", callback_data="show_all_products"),
            InlineKeyboardButton("🔙 ត្រឡប់ទៅផលិតផលវិញ", callback_data=f"prod_{product['id']}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)


    qr_path = "images/aba_khqr.jpg"
    try:
        await query.message.delete()
        if os.path.exists(qr_path):
            with open(qr_path, "rb") as f:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=f,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
                return
    except Exception as e:
        logger.warning(f"Failed to send QR photo: {e}")

    await query.message.reply_text(caption, reply_markup=reply_markup, parse_mode=ParseMode.HTML)



async def on_add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """បន្ថែមទំនិញចូលទៅក្នុងកន្ត្រក"""
    query = update.callback_query
    data = query.data
    parts = data.split("_")
    product_id = int(parts[1]) if parts[0] == "cartadd" else int(parts[2])
    qty = int(parts[2]) if parts[0] == "cartadd" and len(parts) > 2 else 1
    user_id = query.from_user.id

    database.add_to_cart(user_id, product_id, quantity=qty)
    product = database.get_product(product_id)
    prod_name = product["name"] if product else "ទំនិញ"

    await query.answer(f"✅ បានដាក់ {qty} ប្រអប់ '{prod_name}' ចូលកន្ត្រក!", show_alert=False)

async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """បង្ហាញបញ្ជីទំនិញក្នុងកន្ត្រក"""
    user_id = update.effective_user.id
    items = database.get_cart(user_id)

    if not items:
        text = "🛒 <b>កន្ត្រកទំនិញរបស់អ្នកទទេស្អាត!</b>\n\nសូមជ្រើសរើសទំនិញដែលអ្នកចូលចិត្តដើម្បីដាក់ចូលកន្ត្រក។"
        keyboard = [[InlineKeyboardButton("🛍️ មើលផលិតផលឥឡូវនេះ", callback_data="show_all_products")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        return

    subtotal = sum(item["subtotal"] for item in items)
    grand_total = subtotal + DELIVERY_FEE
    grand_total_khr = grand_total * 4000
    total_qty = sum(item["quantity"] for item in items)

    lines = ["🛒 <b>កន្ត្រកទំនិញរបស់អ្នក៖</b>\n"]

    keyboard = []
    for idx, item in enumerate(items, start=1):
        lines.append(
            f"{idx}. <b>{item['name']}</b>\n"
            f"   ចំនួន: <code>{item['quantity']}</code> x {CURRENCY}{item['price']:.2f} = <b>{CURRENCY}{item['subtotal']:.2f}</b>"
        )
        keyboard.append([
            InlineKeyboardButton(f"➖", callback_data=f"cart_dec_{item['product_id']}"),
            InlineKeyboardButton(f"{item['name'][:18]} ({item['quantity']})", callback_data=f"prod_{item['product_id']}"),
            InlineKeyboardButton(f"➕", callback_data=f"cart_inc_{item['product_id']}"),
            InlineKeyboardButton(f"❌", callback_data=f"cart_del_{item['product_id']}")
        ])

    lines.append(f"\n━━━━━━━━━━━━━━")
    lines.append(f"📦 តម្លៃទំនិញ: <b>{CURRENCY}{subtotal:.2f}</b>")
    lines.append(f"🚚 សេវាដឹកជញ្ជូន: <b>+{CURRENCY}{DELIVERY_FEE:.2f} (ឬ {DELIVERY_FEE*4000:,.0f} ៛)</b>")
    lines.append(f"💰 <b>សរុបទាំងអស់: {CURRENCY}{grand_total:.2f} (ឬ {grand_total_khr:,.0f} ៛)</b>")

    order_btn_text = f"📦 បញ្ជាទិញ (Order) {total_qty} ប្រអប់ — {CURRENCY}{grand_total:.2f}"
    keyboard.append([
        InlineKeyboardButton(order_btn_text, callback_data="checkout_start")
    ])
    keyboard.append([
        InlineKeyboardButton("🧹 សម្អាតកន្ត្រក", callback_data="cart_clear"),
        InlineKeyboardButton("🛍️ មើលផលិតផលបន្ថែម", callback_data="show_all_products")
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "\n".join(lines)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def on_cart_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """គ្រប់គ្រងការបន្ថែម បន្ថយ ឬលុបទំនិញពីកន្ត្រក"""
    query = update.callback_query
    user_id = query.from_user.id
    action = query.data

    if action.startswith("cart_inc_"):
        pid = int(action.split("_")[2])
        database.update_cart_quantity(user_id, pid, +1)
        await query.answer("➕ បានបន្ថែមចំនួន")
    elif action.startswith("cart_dec_"):
        pid = int(action.split("_")[2])
        database.update_cart_quantity(user_id, pid, -1)
        await query.answer("➖ បានបន្ថយចំនួន")
    elif action.startswith("cart_del_"):
        pid = int(action.split("_")[2])
        database.remove_from_cart(user_id, pid)
        await query.answer("❌ បានលុបទំនិញ")
    elif action == "cart_clear":
        database.clear_cart(user_id)
        await query.answer("🧹 បានសម្អាតកន្ត្រក")

    # Refresh cart view
    items = database.get_cart(user_id)
    if not items:
        await query.edit_message_text(
            "🛒 កន្ត្រកទំនិញរបស់អ្នកទទេស្អាត!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ មើលទំនិញ", callback_data="show_categories")]])
        )
        return

    subtotal = sum(item["subtotal"] for item in items)
    grand_total = subtotal + DELIVERY_FEE
    grand_total_khr = grand_total * 4000
    total_qty = sum(item["quantity"] for item in items)

    lines = ["🛒 <b>កន្ត្រកទំនិញរបស់អ្នក៖</b>\n"]
    keyboard = []
    for idx, item in enumerate(items, start=1):
        lines.append(
            f"{idx}. <b>{item['name']}</b>\n"
            f"   ចំនួន: <code>{item['quantity']}</code> x {CURRENCY}{item['price']:.2f} = <b>{CURRENCY}{item['subtotal']:.2f}</b>"
        )
        keyboard.append([
            InlineKeyboardButton(f"➖", callback_data=f"cart_dec_{item['product_id']}"),
            InlineKeyboardButton(f"{item['name'][:18]} ({item['quantity']})", callback_data=f"prod_{item['product_id']}"),
            InlineKeyboardButton(f"➕", callback_data=f"cart_inc_{item['product_id']}"),
            InlineKeyboardButton(f"❌", callback_data=f"cart_del_{item['product_id']}")
        ])

    lines.append(f"\n━━━━━━━━━━━━━━")
    lines.append(f"📦 តម្លៃទំនិញ: <b>{CURRENCY}{subtotal:.2f}</b>")
    lines.append(f"🚚 សេវាដឹកជញ្ជូន: <b>+{CURRENCY}{DELIVERY_FEE:.2f} (ឬ {DELIVERY_FEE*4000:,.0f} ៛)</b>")
    lines.append(f"💰 <b>សរុបទាំងអស់: {CURRENCY}{grand_total:.2f} (ឬ {grand_total_khr:,.0f} ៛)</b>")

    order_btn_text = f"📦 បញ្ជាទិញ (Order) {total_qty} ប្រអប់ — {CURRENCY}{grand_total:.2f}"
    keyboard.append([
        InlineKeyboardButton(order_btn_text, callback_data="checkout_start")
    ])
    keyboard.append([
        InlineKeyboardButton("🧹 សម្អាតកន្ត្រក", callback_data="cart_clear"),
        InlineKeyboardButton("🛍️ ទិញបន្ថែម", callback_data="show_categories")
    ])

    await query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)


# ====================================================================
# Checkout Conversation Handler (ដំណើរការបញ្ជាទិញ)
# ====================================================================

async def checkout_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ចាប់ផ្តើមការ Checkout"""
    user_id = update.effective_user.id

    if update.callback_query:
        await update.callback_query.answer()
        data = update.callback_query.data
        if data.startswith("buynow_"):
            parts = data.split("_")
            product_id = int(parts[1])
            qty = int(parts[2]) if len(parts) > 2 else 1
            database.add_to_cart(user_id, product_id, quantity=qty)


    cart_items = database.get_cart(user_id)

    if not cart_items:
        if update.callback_query:
            await update.callback_query.answer("កន្ត្រករបស់អ្នកទទេស្អាត!", show_alert=True)
        else:
            await update.message.reply_text("🛒 កន្ត្រករបស់អ្នកទទេស្អាត!")
        return ConversationHandler.END

    # Reset user checkout data
    context.user_data["checkout"] = {
        "user_id": user_id,
        "name": update.effective_user.full_name or "អតិថិជន",
    }

    cancel_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ បោះបង់ការទិញ", callback_data="checkout_cancel")]
    ])

    text = (
        "📦 <b>សុំលេខទូរស័ព្ទ និងទីតាំងរបស់អ្នកមួយ ងាយស្រួលខាងយើងខ្ញុំរៀបចំអីវ៉ាន់ដាក់ផ្ញើជូន។</b>\n\n"
        "🚚 <i>(សេវាដឹកជញ្ជូន 1.50ដុល្លារ បូកបញ្ចូលក្នុងវិក្កយបត្រ)</i>\n"
        "<i>(លោកអ្នកអាចវាយបញ្ចូលទាំងលេខទូរស័ព្ទ និងទីតាំងដឹកជញ្ជូន ផ្ញើមកកាន់ទីនេះបានភ្លាមៗ)</i>"
    )

    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=cancel_keyboard, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=cancel_keyboard, parse_mode=ParseMode.HTML)

    return STATE_PHONE

async def prompt_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """បង្ហាញជម្រើសវិធីសាស្ត្រទូទាត់ប្រាក់"""
    checkout_data = context.user_data.get("checkout", {})
    phone = checkout_data.get("phone", "")
    address = checkout_data.get("address", "")

    keyboard = [
        [
            InlineKeyboardButton("💵 សាច់ប្រាក់ផ្ទាល់ (Cash on Delivery)", callback_data="pay_cash"),
        ],
        [
            InlineKeyboardButton("📱 ស្កេន KHQR (ABA / Bakong)", callback_data="pay_khqr"),
        ],
        [
            InlineKeyboardButton("❌ បោះបង់ការទិញ", callback_data="checkout_cancel")
        ]
    ]

    text = (
        "✅ <b>ទទួលបានព័ត៌មានដឹកជញ្ជូន៖</b>\n"
        f"📞 លេខទូរស័ព្ទ: <code>{phone}</code>\n"
        f"📍 ទីតាំងដឹកជញ្ជូន: <code>{address}</code>\n"
        "🚚 សេវាដឹកជញ្ជូន: <b>(សេវា 1.50ដុល្លារ)</b>\n\n"
        "💳 <b>សូមជ្រើសរើសវិធីសាស្ត្រទូទាត់ប្រាក់៖</b>"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    elif update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    return STATE_PAYMENT

async def checkout_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ទទួលលេខទូរស័ព្ទ និង/ឬ ទីតាំង"""
    if update.callback_query and update.callback_query.data in ["checkout_cancel", "pay_cancel"]:
        return await checkout_cancel(update, context)

    if update.message.contact:
        phone = update.message.contact.phone_number
        text_rest = ""
    else:
        raw_text = update.message.text.strip()
        if raw_text in ["❌ បោះបង់ការទិញ (Cancel)", "❌ បោះបង់", "❌ បោះបង់ការទិញ"]:
            return await checkout_cancel(update, context)

        # ស្វែងរកលេខទូរស័ព្ទក្នុងសារ
        match = re.search(r'(\+?855[\s.-]?\d{1,2}[\s.-]?\d{3}[\s.-]?\d{3,4}|0\d{1,2}[\s.-]?\d{3}[\s.-]?\d{3,4})', raw_text)
        if match:
            phone = match.group(1).strip()
            text_rest = (raw_text[:match.start()] + ' ' + raw_text[match.end():]).strip(' ,-\n\t')
            text_rest = re.sub(r'\s+', ' ', text_rest)
        else:
            # បើគ្មានលេខទូរស័ព្ទ អាចជាគាត់វាយតែទីតាំង
            context.user_data["checkout"]["address"] = raw_text
            cancel_markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ បោះបង់ការទិញ", callback_data="checkout_cancel")]])
            await update.message.reply_text(
                f"✅ ទទួលបានទីតាំង: <code>{raw_text}</code>\n\n"
                "📞 <b>សូមជួយប្រាប់លេខទូរស័ព្ទរបស់អ្នកមួយទៀត (ឧទាហរណ៍: 012345678)៖</b>",
                reply_markup=cancel_markup,
                parse_mode=ParseMode.HTML
            )
            return STATE_PHONE

    context.user_data["checkout"]["phone"] = phone

    # បើមានទាំងទីតាំងក្នុងសារតែមួយ
    if text_rest and len(text_rest) >= 2:
        context.user_data["checkout"]["address"] = text_rest
        return await prompt_payment(update, context)

    # បើមានទីតាំងស្រាប់ពីមុន
    if context.user_data["checkout"].get("address"):
        return await prompt_payment(update, context)

    # បើមិនទាន់មានទីតាំង សុំទីតាំងបន្ត
    cancel_markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ បោះបង់ការទិញ", callback_data="checkout_cancel")]])
    text = (
        f"✅ ទទួលបានលេខទូរស័ព្ទ: <code>{phone}</code>\n\n"
        "📍 <b>សូមជួយប្រាប់ទីតាំង ឬអាសយដ្ឋានរបស់អ្នកមួយទៀត៖</b>\n"
        "<i>(ងាយស្រួលខាងយើងខ្ញុំរៀបចំអីវ៉ាន់ដាក់ផ្ញើជូន)</i>"
    )
    await update.message.reply_text(text, reply_markup=cancel_markup, parse_mode=ParseMode.HTML)
    return STATE_ADDRESS

async def checkout_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ទទួលអាសយដ្ឋានដឹកជញ្ជូន"""
    if update.callback_query and update.callback_query.data in ["checkout_cancel", "pay_cancel"]:
        return await checkout_cancel(update, context)

    address = update.message.text.strip()
    if address in ["❌ បោះបង់ការទិញ (Cancel)", "❌ បោះបង់", "❌ បោះបង់ការទិញ"]:
        return await checkout_cancel(update, context)

    context.user_data["checkout"]["address"] = address
    return await prompt_payment(update, context)

async def send_order_to_admin(context: ContextTypes.DEFAULT_TYPE, order_id: int, cust_user, slip_photo_file_id: Optional[str] = None, time_validation_info: Optional[dict] = None):
    """ផ្ញើសារជូនដំណឹងទៅ Admin តែនៅពេលអតិថិជនបានទូទាត់រួចរាល់ ឬជ្រើសរើស COD ប៉ុណ្ណោះ"""
    target_admin_id = ADMIN_ID if (ADMIN_ID and ADMIN_ID != 0) else database.get_setting("admin_id")
    if not target_admin_id:
        logger.warning(f"No admin_id configured to notify for order #{order_id}")
        return

    order = database.get_order_details(order_id)
    if not order:
        logger.error(f"Cannot find order #{order_id} to notify admin")
        return

    if cust_user:
        if cust_user.username:
            username_str = f"@{cust_user.username} (<a href='https://t.me/{cust_user.username}'>ឆាតផ្ទាល់</a>)"
        else:
            username_str = f"<a href='tg://user?id={cust_user.id}'>ឆាតផ្ទាល់ (Direct)</a>"
    else:
        username_str = "N/A"
    items = order.get("items", [])
    item_lines = [f"• {item['product_name']} x{item['quantity']} = {CURRENCY}{(item['price'] * item['quantity']):.2f}" for item in items]
    items_text = "\n".join(item_lines) if item_lines else "• គ្មានមុខទំនិញ"

    items_total = sum(item["price"] * item["quantity"] for item in items)
    delivery_fee = order.get("delivery_fee", DELIVERY_FEE)
    total = order.get("total_amount", items_total + delivery_fee)
    payment_method = order.get("payment_method", "")
    status = order.get("status", "រង់ចាំពិនិត្យ")

    admin_buttons = []

    if slip_photo_file_id:
        validation_block = ""
        if time_validation_info:
            validation_block = (
                f"🛡️ <b>ការផ្ទៀងផ្ទាត់សុពលភាព (Fraud Protection)៖</b>\n"
                f"• 📅 ម៉ោងកុម្ម៉ង់បង្កើត: <b>{time_validation_info['order_time']}</b>\n"
                f"• 🕒 ម៉ោងផ្ញើ Slip ជាក់ស្តែង: <b>{time_validation_info['slip_time']}</b>\n"
                f"• ⏱️ គម្លាតពេលវេលា: <b>{time_validation_info['diff_str']}</b>\n"
                f"• 🚦 លទ្ធផល: <b>✅ ថ្ងៃខែតែមួយ & ពេលវេលាតែមួយ (សុពលភាពត្រឹមត្រូវ)</b>\n"
                f"━━━━━━━━━━━━━━\n"
            )

        admin_alert = (
            f"🚨 <b>មានការបញ្ជាទិញថ្មី - ពិតជាបានទូទាត់រួចរាល់មែន! (Order #{order_id})</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"{validation_block}"
            f"👤 អតិថិជន: <b>{order['customer_name']}</b> ({username_str})\n"
            f"📞 លេខទូរស័ព្ទ: <code>{order['phone']}</code>\n"
            f"📍 <b>ទីតាំង/អាសយដ្ឋានដឹកជញ្ជូន៖</b>\n<code>{order['address']}</code>\n\n"
            f"💳 ការទូទាត់: <b>{payment_method}</b>\n"
            f"🚦 ស្ថានភាព: <b>✅ ពិតជាបានទូទាត់រួចរាល់ (PAID)</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"📦 <b>ទំនិញដែលបានកុម្ម៉ង់៖</b>\n{items_text}\n"
            f"━━━━━━━━━━━━━━\n"
            f"📦 តម្លៃទំនិញ: {CURRENCY}{items_total:.2f}\n"
            f"🚚 សេវាដឹកជញ្ជូន: +{CURRENCY}{delivery_fee:.2f} (ឬ {delivery_fee*4000:,.0f} ៛)\n"
            f"💰 <b>តម្លៃសរុបបានទូទាត់: {CURRENCY}{total:.2f} (ឬ {total*4000:,.0f} ៛)</b>\n\n"
            f"👉 <i>សូម Admin ផ្ទៀងផ្ទាត់ម៉ោង និងចំនួនទឹកប្រាក់លើរូបភាព Slip របស់អតិថិជនខាងលើនេះ ដើម្បីធានាភាពត្រឹមត្រូវ ១០០%!</i>"
        )

        admin_buttons.append([
            InlineKeyboardButton("✅ យល់ព្រមទទួល (Approve)", callback_data=f"status_{order_id}_បានបញ្ជាក់"),
            InlineKeyboardButton("❌ បដិសេធវិក្កយបត្រ (Reject)", callback_data=f"status_{order_id}_បដិសេធវិក្កយបត្រ")
        ])
    elif "KHQR" in payment_method:
        admin_alert = (
            f"🚨 <b>មានការបញ្ជាទិញថ្មីតាម KHQR! (Order #{order_id})</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"👤 អតិថិជន: <b>{order['customer_name']}</b> ({username_str})\n"
            f"📞 លេខទូរស័ព្ទ: <code>{order['phone']}</code>\n"
            f"📍 <b>ទីតាំង/អាសយដ្ឋានដឹកជញ្ជូន៖</b>\n<code>{order['address']}</code>\n\n"
            f"💳 ការទូទាត់: <b>{payment_method}</b>\n"
            f"🚦 ស្ថានភាព: <b>{status}</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"📦 <b>ទំនិញដែលបានកុម្ម៉ង់៖</b>\n{items_text}\n"
            f"━━━━━━━━━━━━━━\n"
            f"📦 តម្លៃទំនិញ: {CURRENCY}{items_total:.2f}\n"
            f"🚚 សេវាដឹកជញ្ជូន: +{CURRENCY}{delivery_fee:.2f} (ឬ {delivery_fee*4000:,.0f} ៛)\n"
            f"💰 <b>តម្លៃសរុបត្រូវទទួល: {CURRENCY}{total:.2f} (ឬ {total*4000:,.0f} ៛)</b>\n"
        )
        admin_buttons.append([
            InlineKeyboardButton("✅ បញ្ជាក់ទទួល (Confirm)", callback_data=f"status_{order_id}_បានបញ្ជាក់"),
            InlineKeyboardButton("🚚 កំពុងដឹក (Shipping)", callback_data=f"status_{order_id}_កំពុងដឹកជញ្ជូន")
        ])
    else:
        admin_alert = (
            f"🚨 <b>មានការបញ្ជាទិញថ្មី! (COD Order #{order_id})</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"👤 អតិថិជន: <b>{order['customer_name']}</b> ({username_str})\n"
            f"📞 លេខទូរស័ព្ទ: <code>{order['phone']}</code>\n"
            f"📍 <b>ទីតាំង/អាសយដ្ឋានដឹកជញ្ជូន៖</b>\n<code>{order['address']}</code>\n\n"
            f"💳 ការទូទាត់: <b>{payment_method}</b>\n"
            f"🚦 ស្ថានភាព: <b>{status}</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"📦 <b>ទំនិញដែលបានកុម្ម៉ង់៖</b>\n{items_text}\n"
            f"━━━━━━━━━━━━━━\n"
            f"📦 តម្លៃទំនិញ: {CURRENCY}{items_total:.2f}\n"
            f"🚚 សេវាដឹកជញ្ជូន: +{CURRENCY}{delivery_fee:.2f} (ឬ {delivery_fee*4000:,.0f} ៛)\n"
            f"💰 <b>តម្លៃសរុបត្រូវទទួល: {CURRENCY}{total:.2f} (ឬ {total*4000:,.0f} ៛)</b>\n"
        )
        admin_buttons.append([
            InlineKeyboardButton("✅ បញ្ជាក់ទទួល (Confirm)", callback_data=f"status_{order_id}_បានបញ្ជាក់"),
            InlineKeyboardButton("🚚 កំពុងដឹក (Shipping)", callback_data=f"status_{order_id}_កំពុងដឹកជញ្ជូន")
        ])

    if cust_user and cust_user.username:
        admin_buttons.append([InlineKeyboardButton("💬 ឆាតទៅអតិថិជន", url=f"https://t.me/{cust_user.username}")])
    admin_buttons.append([InlineKeyboardButton("📋 គ្រប់គ្រងកុម្ម៉ង់នេះក្នុង Admin", callback_data=f"adm_ord_{order_id}")])

    try:
        if slip_photo_file_id:
            await context.bot.send_photo(
                chat_id=int(target_admin_id),
                photo=slip_photo_file_id,
                caption=f"🧾 <b>វិក្កយបត្របង់ប្រាក់ (Slip) កុម្ម៉ង់ #{order_id}</b>\n\n" + admin_alert,
                reply_markup=InlineKeyboardMarkup(admin_buttons),
                parse_mode=ParseMode.HTML
            )
        else:
            await context.bot.send_message(
                chat_id=int(target_admin_id),
                text=admin_alert,
                reply_markup=InlineKeyboardMarkup(admin_buttons),
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Failed to notify admin for order #{order_id}: {e}")


async def checkout_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ទទួលការជ្រើសរើសវិធីសាស្ត្រទូទាត់"""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data in ["pay_cancel", "checkout_cancel"]:
        return await checkout_cancel(update, context)

    is_khqr = (data == "pay_khqr")
    payment_method = "📱 ស្កេន KHQR / Bakong" if is_khqr else "💵 សាច់ប្រាក់ពេលដឹកដល់ (Cash on Delivery)"
    context.user_data["checkout"]["payment_method"] = payment_method

    user_id = query.from_user.id
    checkout_data = context.user_data["checkout"]
    initial_status = "រង់ចាំការទូទាត់ KHQR" if is_khqr else "រង់ចាំពិនិត្យ"

    # Save order to DB
    order = database.create_order(
        user_id=user_id,
        customer_name=checkout_data.get("name", "Customer"),
        phone=checkout_data.get("phone", ""),
        address=checkout_data.get("address", ""),
        payment_method=payment_method,
        delivery_fee=DELIVERY_FEE,
        status=initial_status
    )

    if not order:
        await query.message.reply_text("⚠️ មានបញ្ហាក្នុងការបង្កើតការបញ្ជាទិញ (កន្ត្រកទទេ)។", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END

    order_id = order["order_id"]
    items_total = order.get("items_total", sum(item["subtotal"] for item in order["items"]))
    delivery_fee = order.get("delivery_fee", DELIVERY_FEE)
    total = order["total_amount"]
    items = order["items"]

    # Build items text
    item_lines = []
    for item in items:
        item_lines.append(f"• {item['name']} x{item['quantity']} = {CURRENCY}{item['subtotal']:.2f}")
    items_text = "\n".join(item_lines)

    # 1. ករណីទូទាត់តាម KHQR (ផ្ញើ ABA QR និងប៊ូតុងផ្ញើវិក្កយបត្រ)
    if is_khqr:
        context.user_data["pending_khqr_order_id"] = order_id

        qr_buttons = [
            [InlineKeyboardButton("📸 ផ្ញើរូបវិក្កយបត្រក្នុង Bot នេះ", callback_data=f"khqr_paid_{order_id}")],
            [InlineKeyboardButton("❌ បោះបង់ការទិញ", callback_data=f"khqr_cancel_{order_id}")]
        ]

        qr_caption = (
            f"📱 <b>ABA' KHQR សម្រាប់ទូទាត់ការបញ្ជាទិញ #{order_id}</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"💰 ចំនួនទឹកប្រាក់ត្រូវបង់ (រួមបញ្ចូលសេវា): <b>{CURRENCY}{total:.2f} (ឬ {total*4000:,.0f} ៛)</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"👤 ឈ្មោះគណនី: <b>SMAEL SOS</b>\n"
            f"🏦 ធនាគារ: <b>ABA BANK</b>\n"
            f"💵 គណនី USD: <code>966 667 335</code>\n"
            f"🇰🇭 គណនី KHR: <code>010 785 006</code>\n"
            f"━━━━━━━━━━━━━━\n"
            f"📸 <i>បន្ទាប់ពីស្កេនទូទាត់រួច សូមចុចប៊ូតុង <b>'📸 ផ្ញើរូបវិក្កយបត្រក្នុង Bot នេះ'</b> ខាងក្រោម ដើម្បីផ្ញើរូបភាពវិក្កយបត្រ (Slip) ផ្ទៀងផ្ទាត់ និងរៀបចំផ្ញើទំនិញជូន!</i>"
        )

        if os.path.exists("images/aba_khqr.jpg"):
            try:
                with open("images/aba_khqr.jpg", "rb") as qr_f:
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=qr_f,
                        caption=qr_caption,
                        reply_markup=InlineKeyboardMarkup(qr_buttons),
                        parse_mode=ParseMode.HTML
                    )
            except Exception as e:
                logger.warning(f"Failed to send ABA QR image: {e}")
                await query.message.reply_text(
                    qr_caption,
                    reply_markup=InlineKeyboardMarkup(qr_buttons),
                    parse_mode=ParseMode.HTML
                )
        else:
            await query.message.reply_text(
                qr_caption,
                reply_markup=InlineKeyboardMarkup(qr_buttons),
                parse_mode=ParseMode.HTML
            )

        # ជូនដំណឹងទៅ Admin ផ្ទាល់ភ្លាមៗ
        await send_order_to_admin(context, order_id, query.from_user)

        return STATE_KHQR_WAIT

    # 2. ករណីទូទាត់ជាសាច់ប្រាក់ COD (Cash on Delivery)
    customer_msg = (
        f"🎉 <b>ការបញ្ជាទិញបានជោគជ័យ!</b>\n"
        f"លេខសម្គាល់កុម្ម៉ង់: <code>#{order_id}</code>\n"
        f"━━━━━━━━━━━━━━\n"
        f"📋 <b>មុខទំនិញ៖</b>\n{items_text}\n"
        f"━━━━━━━━━━━━━━\n"
        f"📦 តម្លៃទំនិញ: <b>{CURRENCY}{items_total:.2f}</b>\n"
        f"🚚 សេវាដឹកជញ្ជូន: <b>+{CURRENCY}{delivery_fee:.2f} (ឬ {delivery_fee*4000:,.0f} ៛)</b>\n"
        f"💰 <b>សរុបត្រូវបង់: {CURRENCY}{total:.2f} (ឬ {total*4000:,.0f} ៛)</b>\n"
        f"💳 វិធីទូទាត់: {payment_method}\n"
        f"📞 លេខទូរស័ព្ទ: <code>{checkout_data['phone']}</code>\n"
        f"📍 អាសយដ្ឋាន: {checkout_data['address']}\n\n"
        f"🙏 <i>សូមអរគុណសម្រាប់ការគាំទ្រហាង {SHOP_NAME}! ក្រុមការងារយើងខ្ញុំនឹងទាក់ទងទៅលោកអ្នកក្នុងពេលឆាប់ៗនេះ។</i>"
    )

    await query.message.reply_text(
        customer_msg,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🛍️ មើលផលិតផលបន្ត", callback_data="show_all_products"),
                InlineKeyboardButton("💬 ទាក់ទងហាង (Direct)", url=DIRECT_SUPPORT_TELEGRAM)
            ]
        ]),
        parse_mode=ParseMode.HTML
    )

    # COD -> Auto Direct ទៅ Admin ភ្លាមៗ
    await send_order_to_admin(context, order_id, query.from_user)

    context.user_data.pop("checkout", None)
    return ConversationHandler.END


async def on_khqr_paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """អតិថិជនចុចប៊ូតុងបញ្ជាក់ថាបានទូទាត់តាម KHQR រួចរាល់"""
    query = update.callback_query
    await query.answer()

    order_id = None
    if query.data and query.data.startswith("khqr_paid_"):
        try:
            order_id = int(query.data.split("_")[-1])
        except ValueError:
            pass

    if not order_id:
        order_id = context.user_data.get("pending_khqr_order_id")

    if not order_id:
        user_orders = database.get_user_orders(query.from_user.id, limit=3)
        for ord_info in user_orders:
            if "KHQR" in ord_info.get("payment_method", "") and ord_info.get("status") in ["រង់ចាំការទូទាត់ KHQR", "រង់ចាំពិនិត្យ"]:
                order_id = ord_info["id"]
                break

    if not order_id:
        await query.message.reply_text(
            "⚠️ មិនអាចស្វែងរកការបញ្ជាទិញនេះបានឡើយ។ សូមទាក់ទងមកកាន់ @ceo_yanFi។",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ មើលផលិតផល", callback_data="show_all_products")]])
        )
        return ConversationHandler.END

def generate_invoice_text(order_id: int, slip_confirmed: bool = False) -> str:
    """បង្កើតទម្រង់វិក្កយបត្របញ្ជាក់ការកុម្ម៉ង់ផ្លូវការសម្រាប់អតិថិជន"""
    order = database.get_order_details(order_id)
    ict = timezone(timedelta(hours=7))
    time_str = datetime.now(ict).strftime("%d/%m/%Y ម៉ោង %I:%M %p")

    if not order:
        return (
            f"🧾 <b>វិក្កយបត្របញ្ជាក់ការបញ្ជាទិញ (RECEIPT #{order_id})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📅 កាលបរិច្ឆេទ: <b>{time_str}</b>\n"
            f"🚦 ស្ថានភាព: <b>✅ បានបញ្ជាទិញជោគជ័យ</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🙏 សូមអរគុណសម្រាប់ការគាំទ្រ!"
        )

    items = order.get("items", [])
    item_lines = []
    items_total = 0.0
    for idx, item in enumerate(items, 1):
        subtotal = item["price"] * item["quantity"]
        items_total += subtotal
        item_lines.append(f" {idx}. <b>{item['product_name']}</b>\n     ▫️ ចំនួន: x{item['quantity']} | តម្លៃ: {CURRENCY}{item['price']:.2f} | សរុប: <b>{CURRENCY}{subtotal:.2f}</b>")

    items_block = "\n".join(item_lines) if item_lines else "• គ្មានមុខទំនិញ"
    delivery_fee = order.get("delivery_fee", DELIVERY_FEE)
    total = order.get("total_amount", items_total + delivery_fee)
    khr_total = total * 4000
    payment_method = order.get("payment_method", "📱 ស្កេន KHQR / Bakong")

    status_text = "✅ ពិតជាបានទូទាត់រួចរាល់ (PAID)" if slip_confirmed else "✅ បានបញ្ជាទិញជោគជ័យ"

    invoice = (
        f"🧾 <b>វិក្កយបត្របញ្ជាក់ការទូទាត់ (OFFICIAL RECEIPT)</b>\n"
        f"🏪 <b>ហាង៖ {SHOP_NAME}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔖 លេខវិក្កយបត្រ: <code>INV-{order_id:05d}</code> (Order #{order_id})\n"
        f"📅 កាលបរិច្ឆេទ: <b>{time_str}</b>\n"
        f"💳 វិធីសាស្ត្រទូទាត់: <b>{payment_method}</b>\n"
        f"🚦 ស្ថានភាព: <b>{status_text}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>ព័ត៌មានអតិថិជន៖</b>\n"
        f"• ឈ្មោះ: <b>{order['customer_name']}</b>\n"
        f"• លេខទូរស័ព្ទ: <code>{order['phone']}</code>\n"
        f"• ទីតាំងដឹកជញ្ជូន: <code>{order['address']}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📋 <b>មុខទំនិញដែលបានទិញ៖</b>\n"
        f"{items_block}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📦 តម្លៃទំនិញសរុប: <b>{CURRENCY}{items_total:.2f}</b>\n"
        f"🚚 សេវាដឹកជញ្ជូន: <b>+{CURRENCY}{delivery_fee:.2f} (ឬ {delivery_fee*4000:,.0f} ៛)</b>\n"
        f"💰 <b>ទឹកប្រាក់សរុប: {CURRENCY}{total:.2f} (ឬ {khr_total:,.0f} ៛)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>បញ្ជាក់៖ ការទូទាត់ប្រាក់ពិតជាទទួលបានជោគជ័យ ១០០%</b>\n"
        f"📦 ខាងហាងបានទទួលព័ត៌មានរួចរាល់ហើយ និងកំពុងរៀបចំវេចខ្ចប់ទំនិញដើម្បីផ្ញើជូនលោកអ្នកយ៉ាងយកចិត្តទុកដាក់បំផុត!\n\n"
        f"🙏 <i>សូមថ្លែងអំណរគុណយ៉ាងជ្រាលជ្រៅចំពោះការបញ្ជាទិញរបស់លោកអ្នក!</i>"
    )
    return invoice


async def on_khqr_paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """អតិថិជនចុចប៊ូតុង -> ណែនាំឱ្យគាត់ផ្ញើរូបភាពវិក្កយបត្រ (Slip) ចូលក្នុង Telegram Bot នេះផ្ទាល់"""
    query = update.callback_query
    await query.answer()

    order_id = None
    if query.data and query.data.startswith("khqr_paid_"):
        try:
            order_id = int(query.data.split("_")[-1])
        except ValueError:
            pass

    if not order_id:
        order_id = context.user_data.get("pending_khqr_order_id")

    if not order_id:
        user_orders = database.get_user_orders(query.from_user.id, limit=3)
        for ord_info in user_orders:
            if "KHQR" in ord_info.get("payment_method", "") and ord_info.get("status") in ["រង់ចាំការទូទាត់ KHQR", "រង់ចាំពិនិត្យ"]:
                order_id = ord_info["id"]
                break

    if not order_id:
        await query.message.reply_text(
            "⚠️ មិនអាចស្វែងរកការបញ្ជាទិញនេះបានឡើយ។",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ មើលផលិតផល", callback_data="show_all_products")]])
        )
        return ConversationHandler.END

    context.user_data["pending_khqr_order_id"] = order_id

    # សារណែនាំឱ្យផ្ញើរូបភាពវិក្កយបត្រ (Slip) ចូលក្នុង Bot នេះផ្ទាល់
    ask_slip_msg = (
        f"📸 <b>សូមផ្ញើរូបភាពវិក្កយបត្រ (Payment Slip) ចូលក្នុង Telegram Bot នេះផ្ទាល់៖</b>\n"
        f"លេខសម្គាល់កុម្ម៉ង់: <code>#{order_id}</code>\n"
        f"━━━━━━━━━━━━━━\n"
        f"👉 សូមចុចលើរូប 📎 (Attachment) ឬរូបភាពក្នុងទូរស័ព្ទរបស់អ្នក ដើម្បីផ្ញើរូបវិក្កយបត្រចូលក្នុង Telegram Bot នេះតែម្តង (មិនចាំបាច់ផ្ញើទៅ Telegram ណាផ្សេងទេ)។\n\n"
        f"✅ នៅពេលលោកអ្នកផ្ញើរូបភាពរួច ប្រព័ន្ធនឹងចេញវិក្កយបត្របញ្ជាក់ថាបានទូទាត់រួចរាល់នៅលើ Bot នេះភ្លាមៗ! 👇"
    )

    await query.message.reply_text(
        ask_slip_msg,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ បោះបង់ការទិញ", callback_data=f"khqr_cancel_{order_id}")]]) if order_id else None,
        parse_mode=ParseMode.HTML
    )

    return STATE_KHQR_WAIT


async def on_khqr_slip_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """អតិថិជនផ្ញើរូបភាពវិក្កយបត្របង់ប្រាក់ (Slip) ចូលក្នុង Telegram Bot ផ្ទាល់"""
    if not update.message or not update.message.photo:
        return

    photo_file_id = update.message.photo[-1].file_id
    user_id = update.effective_user.id

    order_id = context.user_data.get("pending_khqr_order_id")
    if not order_id:
        user_orders = database.get_user_orders(user_id, limit=3)
        for ord_info in user_orders:
            if "KHQR" in ord_info.get("payment_method", "") and ord_info.get("status") in ["រង់ចាំការទូទាត់ KHQR", "រង់ចាំពិនិត្យ"]:
                order_id = ord_info["id"]
                break

    if not order_id:
        # Not during pending checkout, ignore or allow other handlers
        return

    order = database.get_order_details(order_id)
    if not order:
        return

    # ផ្ទៀងផ្ទាត់កាលបរិច្ឆេទ និងពេលវេលា (ថ្ងៃខែតែមួយ ពេលវេលាតែមួយ)
    ict = timezone(timedelta(hours=7))
    current_time_ict = datetime.now(ict)

    created_at_raw = order.get("created_at")
    order_time_ict = current_time_ict
    if created_at_raw:
        try:
            # SQLite CURRENT_TIMESTAMP is UTC
            order_time_utc = datetime.strptime(str(created_at_raw).strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            order_time_ict = order_time_utc.astimezone(ict)
        except Exception:
            try:
                order_time_utc = datetime.fromisoformat(str(created_at_raw)).replace(tzinfo=timezone.utc)
                order_time_ict = order_time_utc.astimezone(ict)
            except Exception:
                order_time_ict = current_time_ict

    # 1. ពិនិត្យថ្ងៃខែ (Same date check)
    is_same_date = (order_time_ict.date() == current_time_ict.date())

    # 2. ពិនិត្យពេលវេលា (Time window check: រង្វង់ ៣០ នាទី)
    elapsed_seconds = (current_time_ict - order_time_ict).total_seconds()
    elapsed_minutes = elapsed_seconds / 60.0

    # បើមិនមែនថ្ងៃខែតែមួយ ឬហួសលើស ៣០ នាទី (វិក្កយបត្រផុតកំណត់ ឬសង្ស័យបន្លំវិក្កយបត្រចាស់)
    if not is_same_date or elapsed_minutes > 30 or elapsed_minutes < -2:
        database.update_order_status(order_id, "ផុតសុពលភាព (លើសម៉ោងកំណត់)")
        context.user_data.pop("pending_khqr_order_id", None)
        context.user_data.pop("checkout", None)

        reject_msg = (
            f"⚠️ <b>ការបញ្ជាទិញនេះបានផុតកំណត់សុពលភាពពេលវេលាហើយ!</b>\n"
            f"លេខសម្គាល់កុម្ម៉ង់: <code>#{order_id}</code>\n"
            f"━━━━━━━━━━━━━━\n"
            f"🛡️ <b>ប្រព័ន្ធសុវត្ថិភាពការពារការលួចបន្លំវិក្កយបត្រ៖</b>\n"
            f"• ដើម្បីធានាថាការទូទាត់ពិតប្រាកដ ប្រព័ន្ធតម្រូវឱ្យវិក្កយបត្រត្រូវតែមាន <b>ថ្ងៃខែតែមួយ និងពេលវេលាតែមួយ</b> (ក្នុងរង្វង់ ៣០ នាទី) នៃការកុម្ម៉ង់។\n"
            f"• ម៉ោងកុម្ម៉ង់បង្កើត៖ <code>{order_time_ict.strftime('%d/%m/%Y %I:%M %p')}</code>\n"
            f"• ម៉ោងផ្ញើ Slip៖ <code>{current_time_ict.strftime('%d/%m/%Y %I:%M %p')}</code>\n"
            f"• ស្ថានភាព៖ <b>❌ ខុសកាលបរិច្ឆេទ ឬលើសពី ៣០ នាទី</b>\n\n"
            f"👉 សូមចុច <b>'🛍️ មើលផលិតផល'</b> ដើម្បីធ្វើការកុម្ម៉ង់ថ្មី និងស្កេនទូទាត់ភ្លាមៗ។"
        )
        await update.message.reply_text(
            reject_msg,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ មើលផលិតផល (កុម្ម៉ង់ថ្មី)", callback_data="show_all_products")]]),
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

    # ករណីត្រឹមត្រូវ៖ ថ្ងៃខែតែមួយ និងពេលវេលាតែមួយ -> ទើបយល់ព្រមលោតវិក្កយបត្រទៅ Admin
    diff_minutes = max(0, int(elapsed_minutes))
    diff_str = f"{diff_minutes} នាទីក្រោយកុម្ម៉ង់ (ស្របពេលគ្នា)" if diff_minutes > 0 else "ភ្លាមៗក្រោយកុម្ម៉ង់ (ស្របពេលគ្នា)"
    time_validation_info = {
        "order_time": order_time_ict.strftime("%d/%m/%Y %I:%M %p"),
        "slip_time": current_time_ict.strftime("%d/%m/%Y %I:%M %p"),
        "diff_str": diff_str
    }

    # Update DB status to truly paid with slip
    database.update_order_status(order_id, "ពិតជាបានទូទាត់រួចរាល់ (ភ្ជាប់ Slip)")

    # Send alert to Admin WITH photo & time validation info!
    await send_order_to_admin(context, order_id, update.effective_user, slip_photo_file_id=photo_file_id, time_validation_info=time_validation_info)

    # Generate Official Invoice Receipt confirming payment is truly received on Telegram Bot
    invoice_msg = generate_invoice_text(order_id, slip_confirmed=True)

    await update.message.reply_text(
        invoice_msg,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🛍️ មើលផលិតផលបន្ត", callback_data="show_all_products"),
                InlineKeyboardButton("💬 ទាក់ទងហាង (Direct)", url=DIRECT_SUPPORT_TELEGRAM)
            ]
        ]),
        parse_mode=ParseMode.HTML
    )

    context.user_data.pop("pending_khqr_order_id", None)
    context.user_data.pop("checkout", None)
    return ConversationHandler.END


async def on_khqr_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """បោះបង់ការកុម្ម៉ង់ KHQR"""
    query = update.callback_query
    await query.answer()

    order_id = None
    if query.data and query.data.startswith("khqr_cancel_"):
        try:
            order_id = int(query.data.split("_")[-1])
        except ValueError:
            pass

    if not order_id:
        order_id = context.user_data.get("pending_khqr_order_id")

    if order_id:
        database.update_order_status(order_id, "បានបោះបង់")

    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    await query.message.reply_text(
        "❌ បានបោះបង់ការបញ្ជាទិញ។",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ មើលផលិតផល", callback_data="show_all_products")]])
    )

    context.user_data.pop("pending_khqr_order_id", None)
    context.user_data.pop("checkout", None)
    return ConversationHandler.END


async def checkout_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """បោះបង់ការ Checkout"""
    await update.message.reply_text(
        "❌ បានបោះបង់ការបញ្ជាទិញ។",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ មើលផលិតផល", callback_data="show_all_products")]])
    )
    return ConversationHandler.END

async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """បង្ហាញប្រវត្តិបញ្ជាទិញរបស់អតិថិជន"""
    user_id = update.effective_user.id
    orders = database.get_user_orders(user_id, limit=5)

    if not orders:
        empty_kb = [[InlineKeyboardButton("🛍️ មើលផលិតផល", callback_data="show_all_products")]]
        await update.message.reply_text(
            "📦 លោកអ្នកមិនទាន់មានប្រវត្តិបញ្ជាទិញនៅឡើយទេ។",
            reply_markup=InlineKeyboardMarkup(empty_kb)
        )
        return

    lines = ["📦 <b>ប្រវត្តិបញ្ជាទិញចុងក្រោយរបស់អ្នក៖</b>\n"]
    for ord in orders:
        lines.append(
            f"• <b>កុម្ម៉ង់ #{ord['id']}</b> ({ord['created_at']})\n"
            f"  💰 សរុប: {CURRENCY}{ord['total_amount']:.2f}\n"
            f"  💳 ទូទាត់: {ord['payment_method']}\n"
            f"  🚦 ស្ថានភាព: <code>{ord['status']}</code>\n"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ មើលផលិតផល", callback_data="show_all_products")]])
    )

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """បង្ហាញព័ត៌មានជំនួយ និងទំនាក់ទំនង"""
    support_username = SUPPORT_TELEGRAM.rstrip("/").split("/")[-1].lstrip("@")
    help_text = (
        f"ℹ️ <b>ជំនួយ និងទំនាក់ទំនងហាង {SHOP_NAME}</b>\n\n"
        "🛍️ <b>របៀបបញ្ជាទិញ៖</b>\n"
        "1. ចុចលើ <b>'🛍️ មើលផលិតផល'</b> ដើម្បីជ្រើសរើសមុខទំនិញដែលអ្នកចង់បាន\n"
        "2. ចុច <b>'📦 បញ្ជាទិញ (Order)'</b>\n"
        "3. បញ្ចូលលេខទូរស័ព្ទ និងអាសយដ្ឋានដឹកជញ្ជូន\n"
        "4. ស្កេនទូទាត់ប្រាក់តាម <b>ABA' KHQR</b> បានយ៉ាងងាយស្រួល!\n\n"
        "📞 <b>ទំនាក់ទំនងសាកសួរព័ត៌មានបន្ថែម៖</b>\n"
        f"• Telegram ផ្ទាល់៖ <a href='{DIRECT_SUPPORT_TELEGRAM}'>@{support_username}</a>\n"
        "• សេវាដឹកជញ្ជូនរហ័សទូទាំង ២៥ រាជធានី-ខេត្ត 🚚\n"
    )
    keyboard = [
        [InlineKeyboardButton("🛍️ មើលផលិតផល (View Products)", callback_data="show_all_products")],
        [InlineKeyboardButton(f"💬 ឆាតសាកសួរព័ត៌មាន (@{support_username})", url=DIRECT_SUPPORT_TELEGRAM)]
    ]
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

