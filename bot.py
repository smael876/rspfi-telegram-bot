import os
import sys
import logging
from dotenv import load_dotenv

# Reconfigure stdout/stderr for Windows console Khmer/Unicode support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load environment variables from .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN") or "8878287624:AAGMUN0Y-5bfA1Erq5Pmsn4ZrfXQSOP8ZSM"

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"RSPFI Telegram Bot is Running 24/7!")

    def log_message(self, format, *args):
        pass

def start_health_check_server():
    port_str = os.getenv("PORT")
    if not port_str:
        return
    try:
        port = int(port_str)
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Health check server listening on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Health check server error: {e}")

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

import database
from handlers import customer, admin

# Setup Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def on_startup(application):
    try:
        await application.bot.delete_my_commands()
        logger.info("Bot commands deleted from Telegram menu.")
    except Exception as e:
        logger.warning(f"Failed to delete commands: {e}")

def main():
    # Start health check server if PORT is provided by Railway / Cloud
    if os.getenv("PORT"):
        threading.Thread(target=start_health_check_server, daemon=True).start()

    # Initialize Database
    database.init_db()
    print("✅ Database initialized successfully.")
    
    # Auto-seed sample products if database is freshly created
    try:
        import seed_data
        seed_data.seed()
    except Exception as e:
        logger.warning(f"Auto-seed info: {e}")

    application = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()

    # ==========================
    # Checkout Conversation
    # ==========================
    checkout_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(customer.checkout_start, pattern="^(checkout_start|buynow_)")
        ],

        states={
            customer.STATE_PHONE: [
                CallbackQueryHandler(customer.checkout_cancel, pattern="^(checkout_cancel|pay_cancel)$"),
                MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), customer.checkout_phone)
            ],
            customer.STATE_ADDRESS: [
                CallbackQueryHandler(customer.checkout_cancel, pattern="^(checkout_cancel|pay_cancel)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, customer.checkout_address)
            ],
            customer.STATE_PAYMENT: [
                CallbackQueryHandler(customer.checkout_cancel, pattern="^(checkout_cancel|pay_cancel)$"),
                CallbackQueryHandler(customer.checkout_payment, pattern="^pay_")
            ],
            customer.STATE_KHQR_WAIT: [
                CallbackQueryHandler(customer.on_khqr_paid, pattern="^khqr_paid_"),
                CallbackQueryHandler(customer.on_khqr_cancel, pattern="^khqr_cancel_"),
                MessageHandler(filters.PHOTO, customer.on_khqr_slip_upload)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", customer.checkout_cancel),
            CallbackQueryHandler(customer.checkout_cancel, pattern="^(checkout_cancel|pay_cancel)$"),
            MessageHandler(filters.Regex("^❌"), customer.checkout_cancel)
        ],
        allow_reentry=True,
        per_message=False
    )

    # ==========================
    # Admin Add Product Conversation
    # ==========================
    admin_add_prod_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin.start_add_product, pattern="^admin_add_prod$")
        ],
        states={
            admin.ADD_PROD_CAT: [
                CallbackQueryHandler(admin.add_product_cat_chosen, pattern="^(selcat_|admin_cancel)")
            ],
            admin.ADD_PROD_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_product_name)
            ],
            admin.ADD_PROD_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_product_desc)
            ],
            admin.ADD_PROD_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_product_price)
            ],
            admin.ADD_PROD_IMG: [
                CallbackQueryHandler(admin.add_product_finish, pattern="^skip_img$"),
                MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), admin.add_product_finish)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(admin.cmd_admin, pattern="^admin_dashboard$"),
            CommandHandler("cancel", admin.cmd_admin)
        ],
        allow_reentry=True,
        per_message=False
    )

    # ==========================
    # Admin Add Category Conversation
    # ==========================
    admin_add_cat_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin.start_add_category, pattern="^admin_add_cat$")
        ],
        states={
            admin.ADD_CAT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.add_category_name)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", admin.cmd_admin)
        ],
        allow_reentry=True,
        per_message=False
    )


    # 1. Conversation Handlers
    application.add_handler(checkout_conv)
    application.add_handler(admin_add_prod_conv)
    application.add_handler(admin_add_cat_conv)

    # 2. Main Commands
    application.add_handler(CommandHandler("start", customer.cmd_start))
    application.add_handler(CommandHandler("admin", admin.cmd_admin))
    application.add_handler(CommandHandler("help", customer.show_help))

    # 3. Customer Menu Button Handlers (Text Regex)
    application.add_handler(MessageHandler(filters.Regex(r"^(🛍️\s*)?(មើលផលិតផល|មើលទំនិញ)"), customer.show_products))
    application.add_handler(MessageHandler(filters.Regex("^🛒 កន្ត្រកទំនិញ"), customer.view_cart))
    application.add_handler(MessageHandler(filters.Regex("^📦 ប្រវត្តិបញ្ជាទិញ"), customer.show_orders))
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ ជំនួយ"), customer.show_help))

    # 4. Customer Callback Queries
    application.add_handler(CallbackQueryHandler(customer.show_products, pattern="^(show_all_products|show_categories)$"))
    application.add_handler(CallbackQueryHandler(customer.on_category_selected, pattern="^cat_"))
    application.add_handler(CallbackQueryHandler(customer.on_product_selected, pattern="^prod_"))
    application.add_handler(CallbackQueryHandler(customer.on_product_qty_change, pattern="^pqty_"))
    application.add_handler(CallbackQueryHandler(customer.show_product_qr, pattern="^showqr_"))
    application.add_handler(CallbackQueryHandler(customer.on_add_to_cart, pattern="^(cart_add_|cartadd_)"))
    application.add_handler(CallbackQueryHandler(customer.view_cart, pattern="^view_cart$"))
    application.add_handler(CallbackQueryHandler(customer.on_cart_action, pattern="^(cart_inc_|cart_dec_|cart_del_|cart_clear)"))
    application.add_handler(CallbackQueryHandler(customer.on_khqr_paid, pattern="^khqr_paid_"))
    application.add_handler(CallbackQueryHandler(customer.on_khqr_cancel, pattern="^khqr_cancel_"))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, customer.on_khqr_slip_upload))



    # 5. Admin Callback Queries
    application.add_handler(CallbackQueryHandler(admin.cmd_admin, pattern="^admin_dashboard$"))
    application.add_handler(CallbackQueryHandler(admin.admin_list_products, pattern="^admin_list_prods$"))
    application.add_handler(CallbackQueryHandler(admin.admin_delete_product, pattern="^admdel_"))
    application.add_handler(CallbackQueryHandler(admin.admin_recent_orders, pattern="^admin_orders$"))
    application.add_handler(CallbackQueryHandler(admin.admin_order_details, pattern="^adm_ord_"))
    application.add_handler(CallbackQueryHandler(admin.admin_update_order_status, pattern="^status_"))
    application.add_handler(CallbackQueryHandler(admin.admin_close, pattern="^admin_close$"))

    # Start Polling
    print("🚀 Telegram Bot កំពុងដំណើរការ... (ចុច Ctrl+C ដើម្បីបញ្ឈប់)")
    application.run_polling()


if __name__ == "__main__":
    main()
