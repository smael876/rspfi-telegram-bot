import os
import sys
import time
import asyncio
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ដំឡើង edge-tts ដោយស្វ័យប្រវត្តិបើមិនទាន់មាន (សម្រាប់បង្កើតសំឡេង AI មនុស្សស្រីភាសាខ្មែរ)
try:
    import edge_tts
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts"])
    import edge_tts

# សំឡេង AI មនុស្សស្រីភាសាខ្មែរ (ស្រីមុំ)
KHMER_FEMALE_VOICE = "km-KH-SreymomNeural"

# កំណត់ Folder ដំណើរការឱ្យត្រឹមត្រូវជានិច្ច
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR:
    try:
        os.chdir(SCRIPT_DIR)
    except Exception:
        pass

# ទាញយកការកំណត់ពីឯកសារ .env
load_dotenv(os.path.join(SCRIPT_DIR, ".env") if SCRIPT_DIR else ".env")

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
STRING_SESSION = os.getenv("STRING_SESSION", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# ==========================================
# ការកំណត់សារឆ្លើយតបអូតូ (អាចកែប្រែបានតាមចិត្ត)
# ==========================================

# ១. តារាងសំណួរសម្រាប់ឱ្យភ្ញៀវជ្រើសរើស
ORDER_REPLY_MESSAGE = "បើបងចង់កម្ម៉ង់បងអាចចុចបញ្ជាទិញតាមតេឡេក្រាមនេះបាន t.me/RSPFI_Official_Bot"
ORDER_SPEECH_TEXT = "បើបងចង់កម្ម៉ង់ បងអាចចុចបញ្ជាទិញតាមតំណភ្ជាប់តេឡេក្រាមខាងក្រោមនេះបានចាស។"

QUESTIONS_MENU = {
    "1": {
        "khmer_num": "១",
        "question": "ខ្ញុំមានបញ្ហារោគស្ត្រី",
        "keywords": [
            "ខ្ញុំមានបញ្ហារោគស្ត្រី",
            "បញ្ហារោគស្ត្រី",
            "រោគស្ត្រី",
            "ធ្លាក់ស",
            "មេរោគផ្សិត",
            "ស្បូនស្រុត",
            "ស្បូនលាន់",
            "រដូវមិនទៀង",
        ],
        "speech_text": (
            "ខ្ញុំសូមណែនាំឱ្យបងប្រើផលិតផល ថ្នាំក្រមុំម្ដងទៀត គឺជាថ្នាំស៊ុលក្នុងទ្វារមាសដែលជួយព្យាបាលបញ្ហារោគស្ត្រីមានដូចជា៖ "
            "ធ្លាក់ស, រដូវមិនទៀងទាត់, មានក្លិនមិនល្អ, មេរោគផ្សិត, ស្បូនស្រុត ស្បូនលាន់, "
            f"ជាពិសេសធ្វើឱ្យទ្វារមាសតឹងណែនដូចក្រមុំម្ដងទៀតចាស។ {ORDER_SPEECH_TEXT}"
        ),
        "answer": (
            "ខ្ញុំសូមណែនាំឱ្យបងប្រើផលិតផល ថ្នាំក្រមុំម្ដងទៀត គឺជាថ្នាំស៊ុលក្នុងទ្វារមាសដែលជួយព្យាបាលបញ្ហារោគស្ត្រីមានដូចជា\n"
            "ធ្លាក់ស\n"
            "រដូវមិនទៀងទាត់\n"
            "មានក្លិនមិនល្អ\n"
            "មេរោគផ្សិត\n"
            "ស្បូនស្រុតស្បូនលាន់\n"
            "ជាពិសេសធ្វើឲ្យទ្វារមាសតឹងណែនដូចក្រមុំម្ដងទៀត។\n\n"
            f"{ORDER_REPLY_MESSAGE}"
        ),
        "image": "product_1.jpg",
    },
    "2": {
        "khmer_num": "២",
        "question": "ខ្ញុំមានបញ្ហាក្លិនមិនល្អ",
        "keywords": [
            "ខ្ញុំមានបញ្ហាក្លិនមិនល្អ",
            "បញ្ហាក្លិនមិនល្អ",
            "ក្លិនមិនល្អ",
            "សាប៊ូអនាម័យ",
        ],
        "speech_text": (
            "ខ្ញុំសូមណែនាំបងឱ្យប្រើឈុតសាប៊ូអនាម័យ និងថ្នាំក្រមុំម្ដងទៀតចាស។ "
            "អត្ថប្រយោជន៍មានដូចជា៖ សាប៊ូអនាម័យគឺជាសាប៊ូលាងនៅតំបន់ទ្វារមាស ជួយលាងសម្អាតក្លិនមិនល្អ។ "
            "ចំណែកថ្នាំក្រមុំម្ដងទៀត គឺជាប្រភេទថ្នាំស៊ុលដាក់ចូលក្នុងទ្វារមាស ជួយព្យាបាលរាល់បញ្ហារោគស្ត្រីមានដូចជា៖ "
            "ធ្លាក់ស, មានក្លិនមិនល្អ, មេរោគផ្សិត, ស្បូនស្រុត ស្បូនលាន់, រដូវមិនទៀងទាត់ និងរាល់បញ្ហារោគស្ត្រីផ្សេងៗចាស។ "
            f"{ORDER_SPEECH_TEXT}"
        ),
        "answer": (
            "ខ្ញុំសូមណែនាំបងអោយប្រើឈុតសាប៊ូអនាម័យនិងថ្នាំក្រមុំម្ដងទៀត \n"
            "អត្ថប្រយោជន៍មានដូចជា\n"
            "សាប៊ូអនាម័យគឺជាសាប៊ូលាងនៅតំបន់ទ្វារមាសជួយលាងសម្អាតក្លិនមិនល្អ\n"
            "ថ្នាំក្រមុំម្ដងទៀតគឺជាថ្នាំប្រភេទថ្នាំស៊ុលដាក់ចូលក្នុងទ្វារមាសជួយព្យាបាលរាល់បញ្ហារោគស្ត្រីមានដូចជា\n"
            "ធ្លាក់ស\n"
            "មានក្លិនមិនល្អ\n"
            "មេរោគផ្សិត\n"
            "ស្បូនស្រុតស្បូនលាន់\n"
            "រដូវមិនទៀងទាត់\n"
            "និងរាល់បញ្ហារោគស្ត្រីផ្សេងៗ\n\n"
            f"{ORDER_REPLY_MESSAGE}"
        ),
        "image": "product_2.jpg",
    },
    "3": {
        "khmer_num": "៣",
        "question": "ខ្ញុំមានបញ្ហាស្ងួតតំបន់ទ្វារមាស",
        "keywords": [
            "ខ្ញុំមានបញ្ហាស្ងួតតំបន់ទ្វារមាស",
            "បញ្ហាស្ងួត",
            "ស្ងួតតំបន់ទ្វារមាស",
            "តំបន់សំណើម",
            "តំបន់ សំណើម",
            "វីតាមីនស៊ុល",
        ],
        "speech_text": (
            "ខ្ញុំសូមណែនាំឱ្យបងប្រើផលិតផល តំបន់សំណើម គឺជាប្រភេទវីតាមីនស៊ុលក្នុងទ្វារមាស ដែលជួយរាល់បញ្ហាស្ងួតនៅពេលរួមភេទចាស។ "
            f"បញ្ជាក់៖ សូមប្រើមុនរួមភេទ ២០ នាទីចាស។ {ORDER_SPEECH_TEXT}"
        ),
        "answer": (
            "ខ្ញុំសូមណែនាំឱ្យបងប្រើផលិតផល តំបន់សំណើម គឺជាប្រភេទវីតាមីនស៊ុលក្នុងទ្វារមាសដែលជួយរាល់បញ្ហាស្ងួតនៅពេលរួមភេទ\n"
            "បញ្ជាក់ ប្រើមុនរួមភេទ 20 នាទី\n\n"
            f"{ORDER_REPLY_MESSAGE}"
        ),
        "image": "product_3.jpg",
    },
    "4": {
        "khmer_num": "៤",
        "question": "ខ្ញុំចង់ឱ្យតឹងណែន",
        "keywords": [
            "ខ្ញុំចង់ឱ្យតឹងណែន",
            "ចង់ឱ្យតឹងណែន",
            "ចង់អោយតឹងណែន",
            "តឹងណែន",
        ],
        "speech_text": (
            "ខ្ញុំសូមណែនាំឱ្យបងប្រើ ថ្នាំក្រមុំម្ដងទៀតចាស។ "
            "អត្ថប្រយោជន៍៖ បងប្រើតែមួយគ្រាប់គឺតឹងណែនតែម្ដងចាស។ "
            "របៀបប្រើ៖ ជាប្រភេទថ្នាំស៊ុលដាក់ចូលក្នុងទ្វារមាស។ "
            "មុននឹងយកថ្នាំទៅស៊ុល ត្រូវយកជ្រលក់ទឹកបន្តិច បន្ទាប់មកដាក់ចូលក្នុងទ្វារមាសជម្រៅមួយចង្អុលដៃចាស។ "
            f"{ORDER_SPEECH_TEXT}"
        ),
        "answer": (
            "ខ្ញុំណែនាំឱ្យបងប្រើថ្នាំក្រមុំម្ដងទៀត\n"
            "អត្ថប្រយោជន៍\n"
            "បងប្រើតែមួយគ្រាប់តឹងណែន\n"
            "របៀបប្រើ\n"
            "ជាប្រភេទថ្នាំស៊ុលដាក់ចូលក្នុងទ្វារមាស\n"
            "មុននឹងយកថ្នាំទៅស៊ុល ត្រូវយកជ្រលក់ទឹកបន្តិច បន្ទាប់មកដាក់ចូលក្នុងទ្វារមាសមួយចង្អុលដៃ\n\n"
            f"{ORDER_REPLY_MESSAGE}"
        ),
        "image": "product_1.jpg",
    },
}

MENU_SPEECH_TEXT = (
    "សួស្តីបង! សូមស្វាគមន៍ចាស! សូមបងជ្រើសរើសសំណួរខាងក្រោម ដោយគ្រាន់តែវាយលេខសំណួរ រួចផ្ញើមកវិញចាស៖ "
    "លេខ ១ ខ្ញុំមានបញ្ហារោគស្ត្រី។ "
    "លេខ ២ ខ្ញុំមានបញ្ហាក្លិនមិនល្អ។ "
    "លេខ ៣ ខ្ញុំមានបញ្ហាស្ងួតតំបន់ទ្វារមាស។ "
    "លេខ ៤ ខ្ញុំចង់ឱ្យតឹងណែន។"
)


def build_menu_message() -> str:
    """បង្កើតសារស្វាគមន៍ និងបង្ហាញបញ្ជីសំណួរឱ្យភ្ញៀវជ្រើសរើស"""
    lines = [
        "សួស្តីបង! 🙏 សូមស្វាគមន៍!",
        "សូមបងជ្រើសរើសសំណួរខាងក្រោម (គ្រាន់តែវាយលេខសំណួរ រួចផ្ញើមកវិញ)៖\n",
    ]
    for num, item in QUESTIONS_MENU.items():
        lines.append(f"👉 {num}. {item['question']}")
    return "\n".join(lines)


# ២. កំណត់ពាក្យគន្លឹះបន្ថែម (Keywords)៖ បើគេឆាតមានពាក្យខាងឆ្វេង នឹងតបសារខាងស្ដាំវិញភ្លាម
KEYWORD_REPLIES = {
    "សួស្តី": build_menu_message(),
    "សួស្ដី": build_menu_message(),
    "hello": build_menu_message(),
    "hi": build_menu_message(),
    "menu": build_menu_message(),
    "កម្មង់": ORDER_REPLY_MESSAGE,
    "កម្ម៉ង់": ORDER_REPLY_MESSAGE,
    "កុម្ម៉ង់": ORDER_REPLY_MESSAGE,
    "បញ្ជាទិញ": ORDER_REPLY_MESSAGE,
    "ទិញ": ORDER_REPLY_MESSAGE,
    "order": ORDER_REPLY_MESSAGE,
    "តម្លៃ": f"ចំពោះតម្លៃ សូមបងរង់ចាំបន្តិច ខ្ញុំនឹងឆែកជូនភ្លាមពេលទំនេរណា! 💬\n{ORDER_REPLY_MESSAGE}",
    "ទីតាំង": "ទីតាំងរបស់យើងនៅភ្នំពេញបង! បន្តិចទៀតខ្ញុំផ្ញើ Map ជូនណា 📍",
    "លេខទូរស័ព្ទ": "បងអាចទាក់ទងមកលេខទូរស័ព្ទរបស់ខ្ញុំផ្ទាល់បាន ប្រសិនបើមានការបន្ទាន់ 📞",
}

# ៣. សារឆ្លើយតបស្វ័យប្រវត្តិពេលភ្ញៀវឆាតមកដំបូង (បង្ហាញតារាងសំណួរឱ្យភ្ញៀវជ្រើសរើស)
DEFAULT_BUSY_MESSAGE = build_menu_message()

# ៤. រយៈពេលរង់ចាំ (គិតជាវិនាទី) មុននឹងផ្ញើសារតារាងសំណួរម្ដងទៀតទៅកាន់មនុស្សដដែល
COOLDOWN_SECONDS = 60

# ៥. ការណែនាំសម្រាប់ AI (System Instruction) បើបើកមុខងារ AI
AI_SYSTEM_PROMPT = (
    "អ្នកគឺជាជំនួយការផ្នែកលក់ និងផ្ដល់ប្រឹក្សាផលិតផលសុខភាពនារី RSPFI នៅលើ Telegram។ "
    "សូមឆ្លើយតបសារជាភាសាខ្មែរដោយគួរសម រួសរាយរាក់ទាក់ សុភាពរាបសារ (ប្រើពាក្យ ចាស, បង) ខ្លីៗ និងងាយយល់។\n\n"
    "ព័ត៌មានផលិតផលរបស់យើង៖\n"
    "១. ថ្នាំក្រមុំម្ដងទៀត (Lady Vaginy)៖ ថ្នាំស៊ុលក្នុងទ្វារមាស ព្យាបាលបញ្ហារោគស្ត្រី រួមមាន ធ្លាក់ស, រដូវមិនទៀង, មានក្លិនមិនល្អ, មេរោគផ្សិត, ស្បូនស្រុត ស្បូនលាន់ និងជួយឱ្យទ្វារមាសតឹងណែនដូចក្រមុំម្ដងទៀត។\n"
    "២. ឈុតសាប៊ូអនាម័យ & ថ្នាំក្រមុំម្ដងទៀត៖ ជួយលាងសម្អាតក្លិនមិនល្អ និងព្យាបាលរាល់បញ្ហារោគស្ត្រី។\n"
    "៣. តំបន់សំណើម៖ វីតាមីនស៊ុលក្នុងទ្វារមាស ជួយរាល់បញ្ហាស្ងួតនៅពេលរួមភេទ (ប្រើមុនរួមភេទ ២០ នាទី)។\n"
    "៤. បើភ្ញៀវចង់កម្ម៉ង់ ឬសួរតម្លៃ សូមប្រាប់គាត់ឱ្យចុចបញ្ជាទិញតាមតេឡេក្រាមនេះ៖ t.me/RSPFI_Official_Bot ឬប្រាប់ថាម្ចាស់គណនីនឹងឆែកតម្លៃជូនភ្លាមៗពេលទំនេរ។"
)

# ==========================================
# ស្ថានភាពប្រព័ន្ធ (State)
# ==========================================
state = {
    "auto_reply_enabled": True,
    "use_ai": bool(GEMINI_API_KEY),
    "busy_message": DEFAULT_BUSY_MESSAGE,
}

# កត់ត្រាម៉ោងដែលបានតបទៅអ្នកឆាតម្នាក់ៗចុងក្រោយ
last_replied_time = {}

# រៀបចំ Gemini AI (ប្រសិនបើមានដាក់ GEMINI_API_KEY)
genai_client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        genai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"[!] មិនអាចភ្ជាប់ Gemini AI បានទេ: {e}")


async def generate_ai_reply(user_text: str) -> str:
    """បង្កើតសារឆ្លើយតបតាមរយៈ Gemini AI"""
    if not genai_client:
        return state["busy_message"]
    try:
        response = await asyncio.to_thread(
            genai_client.models.generate_content,
            model="gemini-2.5-flash",
            contents=f"{AI_SYSTEM_PROMPT}\n\nសារពីអ្នកឆាតមក៖ {user_text}",
        )
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print(f"[!] បញ្ហាពេលហៅ AI: {e}")
    return state["busy_message"]


def get_or_prompt_credentials():
    global API_ID, API_HASH
    if not API_ID or not API_HASH or API_ID == "12345678" or API_HASH == "your_api_hash_here":
        print("=" * 65)
        print("🔐 ការភ្ជាប់គណនី Telegram លើកដំបូង")
        print("=" * 65)
        print("ដើម្បីភ្ជាប់គណនីផ្ទាល់ខ្លួន សូមយក API_ID និង API_HASH ពី៖")
        print("👉 1. ចូលទៅកាន់៖ https://my.telegram.org")
        print("👉 2. វាយលេខទូរស័ព្ទ រួចវាយកូដដែលផ្ញើចូល Telegram")
        print("👉 3. ចុច 'API development tools' រួចចម្លង api_id និង api_hash មកដាក់ខាងក្រោម៖")
        print("-" * 65)
        API_ID = input("📌 សូមបញ្ចូល api_id (លេខ): ").strip()
        API_HASH = input("📌 សូមបញ្ចូល api_hash (អក្សរនិងលេខ): ").strip()
        if not API_ID.isdigit() or not API_HASH:
            print("❌ api_id ឬ api_hash មិនត្រឹមត្រូវទេ! សូមសាកល្បងម្ដងទៀត។")
            return False
        # រក្សាទុកចូលក្នុងឯកសារ .env ដោយស្វ័យប្រវត្តិ
        with open(".env", "w", encoding="utf-8") as f:
            f.write(f"API_ID={API_ID}\n")
            f.write(f"API_HASH={API_HASH}\n")
            f.write(f"GEMINI_API_KEY={GEMINI_API_KEY}\n")
        print("✅ បានរក្សាទុក API_ID និង API_HASH ទុកសម្រាប់លើកក្រោយរួចរាល់!\n")
    return True


async def start_health_server():
    """បើក Web Server តូចមួយសម្រាប់ឱ្យ Cloud (ដូចជា Render.com) ដឹងថាកម្មវិធីកំពុងដំណើរការ 24/7"""
    port = os.getenv("PORT")
    if not port:
        return

    async def handle_client(reader, writer):
        try:
            await reader.read(1024)
            body = b"Telegram Auto-Reply Userbot is running 24/7!"
            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain; charset=utf-8\r\n"
                b"Content-Length: " + str(len(body)).encode() + b"\r\n"
                b"Connection: close\r\n\r\n" + body
            )
            writer.write(response)
            await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()

    server = await asyncio.start_server(handle_client, "0.0.0.0", int(port))
    print(f"🌐 Cloud Health Server កំពុងដំណើរការនៅលើ Port {port}")

    external_url = os.getenv("RENDER_EXTERNAL_URL")
    if external_url:
        import urllib.request

        async def keep_alive():
            while True:
                await asyncio.sleep(300)  # រៀងរាល់ 5 នាទីម្ដង
                try:
                    await asyncio.to_thread(urllib.request.urlopen, external_url, timeout=10)
                except Exception:
                    pass

        asyncio.create_task(keep_alive())

    return server


async def main():
    if not get_or_prompt_credentials():
        return

    await start_health_server()

    if STRING_SESSION:
        client = TelegramClient(StringSession(STRING_SESSION), int(API_ID), API_HASH)
    else:
        client = TelegramClient("telegram_auto_reply_session", int(API_ID), API_HASH)

    # ផ្ទុកសារសំឡេង (Voice Messages) និងរូបភាពផលិតផល (Product Images)
    voice_replies = {}
    image_replies = {}

    async def load_saved_media():
        """ទាញយកសារសំឡេង និងរូបភាពដែលបានកំណត់ទុកក្នុង Saved Messages ដោយស្វ័យប្រវត្តិពេលបើកកម្មវិធី"""
        try:
            async for msg in client.iter_messages("me", limit=100):
                text = (msg.raw_text or "").strip()
                if text.startswith("[VOICE_CONFIG:") and "]" in text:
                    tag = text.split("]", 1)[0][14:]  # key:msg_id
                    parts = tag.split(":")
                    if len(parts) == 2:
                        key, target_id_str = parts[0], parts[1]
                        if key not in voice_replies:
                            if target_id_str == "NONE":
                                voice_replies[key] = None
                            elif target_id_str.isdigit():
                                target_msg = await client.get_messages("me", ids=int(target_id_str))
                                if target_msg and target_msg.media:
                                    voice_replies[key] = target_msg.media
                elif text.startswith("[IMAGE_CONFIG:") and "]" in text:
                    tag = text.split("]", 1)[0][14:]  # key:msg_id
                    parts = tag.split(":")
                    if len(parts) == 2:
                        key, target_id_str = parts[0], parts[1]
                        if key not in image_replies:
                            if target_id_str == "NONE":
                                image_replies[key] = None
                            elif target_id_str.isdigit():
                                target_msg = await client.get_messages("me", ids=int(target_id_str))
                                if target_msg and target_msg.media:
                                    image_replies[key] = target_msg.media
            # លុប key ណាដែលត្រូវបានកំណត់ជា None
            for k in [k for k, v in voice_replies.items() if v is None]:
                del voice_replies[k]
            for k in [k for k, v in image_replies.items() if v is None]:
                del image_replies[k]
            if voice_replies:
                print(f"🔊 បានទាញយកសារសំឡេងចំនួន {len(voice_replies)} ពី Saved Messages៖ {list(voice_replies.keys())}")
            if image_replies:
                print(f"🖼️ បានទាញយករូបភាពផលិតផលចំនួន {len(image_replies)} ពី Saved Messages៖ {list(image_replies.keys())}")
        except Exception as e:
            print(f"[!] បញ្ហាពេលទាញយកពី Saved Messages: {e}")

    async def convert_mp3_to_ogg(mp3_path: str, ogg_path: str) -> bool:
        """បំប្លែងឯកសារ .mp3 ទៅជា .ogg (Opus) ដើម្បីឱ្យ Telegram លើទូរស័ព្ទឮសំឡេងច្បាស់ ១០០%"""
        try:
            try:
                import imageio_ffmpeg
            except ImportError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "imageio-ffmpeg"])
                import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            await asyncio.to_thread(
                subprocess.run,
                [ffmpeg_exe, "-y", "-i", mp3_path, "-c:a", "libopus", "-b:a", "48k", "-vbr", "on", ogg_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return os.path.exists(ogg_path) and os.path.getsize(ogg_path) > 0
        except Exception as e:
            print(f"[!] មិនអាចបំប្លែងទៅជា .ogg បានទេ: {e}")
            return False

    async def prepare_ai_voices():
        """បង្កើតឯកសារសំឡេង AI មនុស្សស្រីភាសាខ្មែរ (.ogg Opus) ទុកជាមុនសម្រាប់សំណួរទាំងអស់"""
        print("🎙️ កំពុងរៀបចំសំឡេង AI មនុស្សស្រីភាសាខ្មែរ (ស្រីមុំ)...")
        tasks_to_generate = {"menu": MENU_SPEECH_TEXT}
        for num, item in QUESTIONS_MENU.items():
            if "speech_text" in item:
                tasks_to_generate[num] = item["speech_text"]

        for key, text in tasks_to_generate.items():
            ogg_file = f"ai_voice_{key}.ogg"
            mp3_file = f"ai_voice_{key}.mp3"
            if not os.path.exists(ogg_file):
                try:
                    communicate = edge_tts.Communicate(text, KHMER_FEMALE_VOICE)
                    await communicate.save(mp3_file)
                    await convert_mp3_to_ogg(mp3_file, ogg_file)
                except Exception as e:
                    print(f"[!] បញ្ហាពេលបង្កើតសំឡេង AI ({key}): {e}")
        print("✅ សំឡេង AI មនុស្សស្រីភាសាខ្មែរ រួចរាល់ ១០០%!")

    async def send_voice_if_configured(chat_target, key: str):
        """ផ្ញើសារសំឡេង AI មនុស្សស្រីភាសាខ្មែរទៅកាន់ភ្ញៀវដោយស្វ័យប្រវត្តិ"""
        if key not in voice_replies:
            await load_saved_media()

        if key in voice_replies and voice_replies[key]:
            try:
                await asyncio.sleep(0.5)
                await client.send_file(chat_target, voice_replies[key], voice_note=True)
                return
            except Exception as e:
                print(f"[!] មិនអាចផ្ញើសារសំឡេង ({key}) បានទេ: {e}")

        # ពិនិត្យមើលសំឡេង AI មនុស្សស្រីប្រភេទ .ogg (Opus) ជាមុន
        ogg_file = os.path.join(SCRIPT_DIR, f"ai_voice_{key}.ogg")
        mp3_file = os.path.join(SCRIPT_DIR, f"ai_voice_{key}.mp3")
        if not os.path.exists(ogg_file):
            speech_text = MENU_SPEECH_TEXT if key == "menu" else QUESTIONS_MENU.get(key, {}).get("speech_text")
            if speech_text:
                try:
                    if not os.path.exists(mp3_file):
                        communicate = edge_tts.Communicate(speech_text, KHMER_FEMALE_VOICE)
                        await communicate.save(mp3_file)
                    await convert_mp3_to_ogg(mp3_file, ogg_file)
                except Exception as e:
                    print(f"[!] បញ្ហាពេលបង្កើតសំឡេង AI ({key}): {e}")

        if os.path.exists(ogg_file) and os.path.getsize(ogg_file) > 0:
            try:
                await asyncio.sleep(0.5)
                await client.send_file(chat_target, ogg_file, voice_note=True)
                return
            except Exception as e:
                print(f"[!] មិនអាចផ្ញើសំឡេង AI {ogg_file} បានទេ: {e}")

        if os.path.exists(mp3_file) and os.path.getsize(mp3_file) > 0:
            try:
                await asyncio.sleep(0.5)
                await client.send_file(chat_target, mp3_file)
                return
            except Exception as e:
                print(f"[!] មិនអាចផ្ញើសំឡេង AI {mp3_file} បានទេ: {e}")

        # ពិនិត្យមើលឯកសារសំឡេងក្នុង Folder ផ្ទាល់ (ឧ. voice_1.ogg ឬ voice_1.mp3)
        for ext in (".ogg", ".mp3", ".m4a", ".wav"):
            local_file = os.path.join(SCRIPT_DIR, f"voice_{key}{ext}")
            if os.path.exists(local_file):
                try:
                    await asyncio.sleep(0.5)
                    await client.send_file(chat_target, local_file, voice_note=(ext == ".ogg"))
                    return
                except Exception as e:
                    print(f"[!] មិនអាចផ្ញើឯកសារសំឡេង {local_file} បានទេ: {e}")

    async def send_question_reply(event, num: str, item: dict):
        """ផ្ញើសារឆ្លើយតប រួមទាំងរូបភាពផលិតផល និងសំឡេង AI"""
        target_image = None
        try:
            chat = await event.get_input_chat()
        except Exception:
            chat = event.chat_id

        # ១. ពិនិត្យមើលរូបភាពដែលបានភ្ជាប់តាម Saved Messages (/setimage)
        if num in image_replies and image_replies[num]:
            target_image = image_replies[num]
        else:
            # ២. ពិនិត្យមើលរូបភាពក្នុង Folder តាមឈ្មោះឯកសារ
            configured_img = item.get("image")
            candidates = []
            if configured_img:
                candidates.append(os.path.join(SCRIPT_DIR, configured_img))
                candidates.append(configured_img)
            for ext in (".jpg", ".jpeg", ".png", ".webp"):
                candidates.append(os.path.join(SCRIPT_DIR, f"product_{num}{ext}"))
                candidates.append(f"product_{num}{ext}")

            for p in candidates:
                if os.path.exists(p) and os.path.getsize(p) > 0:
                    target_image = os.path.abspath(p)
                    break

        answer_text = item.get("answer", "")
        # ផ្ញើសារឆ្លើយតប (ជាមួយរូបភាព ឬសារអក្សរធម្មតា)
        sent_with_image = False
        if target_image:
            try:
                # បើមានរូបភាព ផ្ញើរូបភាពភ្ជាប់ដោយ Caption ជាអត្ថបទ
                if len(answer_text) <= 1024:
                    await client.send_file(chat, target_image, caption=answer_text, reply_to=event.id)
                else:
                    await client.send_file(chat, target_image, reply_to=event.id)
                    await event.reply(answer_text)
                sent_with_image = True
            except Exception as e:
                print(f"[!] មិនអាចផ្ញើរូបភាព ({num}) បានទេ: {e}")

        if not sent_with_image:
            await event.reply(answer_text)

        # ផ្ញើសំឡេង AI បន្តបន្ទាប់
        await send_voice_if_configured(chat, num)

    # ------------------------------------------
    # មុខងារ Test ភ្លាមៗក្នុង Saved Messages សម្រាប់ម្ចាស់គណនី
    # ------------------------------------------
    @client.on(events.NewMessage(outgoing=True))
    async def saved_messages_test_handler(event):
        if not event.is_private:
            return
        me_user = await client.get_me()
        if event.chat_id != me_user.id:
            return

        text = (event.raw_text or "").strip()
        kh_to_en = {"១": "1", "២": "2", "៣": "3", "៤": "4"}
        test_num = kh_to_en.get(text, text)
        if test_num in QUESTIONS_MENU:
            item = QUESTIONS_MENU[test_num]
            await asyncio.sleep(0.5)
            await send_question_reply(event, test_num, item)
            print(f"[Test Saved Messages] បានតេស្តសំណួរទី {test_num}")
        elif text.lower() in ("menu", "សួស្តី", "សួស្ដី"):
            chat = await event.get_input_chat()
            await event.reply(state["busy_message"])
            await send_voice_if_configured(chat, "menu")
            print("[Test Saved Messages] បានតេស្ត Menu")

    # ------------------------------------------
    # ១. មុខងារបញ្ជាបិទ/បើក និងកំណត់សំឡេង/រូបភាព តាមរយៈ Saved Messages
    # ------------------------------------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"^/(on|off|ai on|ai off|status|setmsg (.+)|setvoice (.+)|delvoice (.+)|setimage (.+)|delimage (.+)|test (.+)|test)$"))
    async def command_handler(event):
        cmd = event.raw_text.strip()
        cmd_lower = cmd.lower()

        if cmd_lower == "/on":
            state["auto_reply_enabled"] = True
            await event.edit("✅ **បានបើក (ON)** មុខងារឆ្លើយតបឆាតអូតូ!")
        elif cmd_lower == "/off":
            state["auto_reply_enabled"] = False
            await event.edit("⛔ **បានបិទ (OFF)** មុខងារឆ្លើយតបឆាតអូតូ!")
        elif cmd_lower == "/ai on":
            if not genai_client:
                await event.edit("⚠️ មិនទាន់បានដាក់ `GEMINI_API_KEY` ក្នុងឯកសារ `.env` នៅឡើយទេ!")
            else:
                state["use_ai"] = True
                await event.edit("🤖 **បានបើក (ON)** ការឆ្លើយតបដោយ AI!")
        elif cmd_lower == "/ai off":
            state["use_ai"] = False
            await event.edit("🤖 **បានបិទ (OFF)** ការឆ្លើយតបដោយ AI (ប្រើសារធម្មតាវិញ)!")
        elif cmd_lower.startswith("/setmsg "):
            new_msg = cmd[8:].strip()
            state["busy_message"] = new_msg
            await event.edit(f"✏️ បានប្ដូរសារស្វ័យប្រវត្តិទៅជា៖\n\n`{new_msg}`")
        elif cmd_lower.startswith("/setvoice "):
            key = cmd[10:].strip().lower()
            reply_msg = await event.get_reply_message()
            if not reply_msg or not reply_msg.media:
                await event.edit(
                    "⚠️ **របៀបដាក់សំឡេង៖**\n"
                    "សូមថតសំឡេង (Voice Message) ដាក់ក្នុង **Saved Messages** ជាមុនសិន រួចចុច **Reply** លើសំឡេងនោះ ហើយវាយ៖\n"
                    "• `/setvoice 1` (សម្រាប់សំណួរទី ១)\n"
                    "• `/setvoice 2` (សម្រាប់សំណួរទី ២)\n"
                    "• `/setvoice 3` (សម្រាប់សំណួរទី ៣)\n"
                    "• `/setvoice 4` (សម្រាប់សំណួរទី ៤)\n"
                    "• `/setvoice menu` (សម្រាប់សារស្វាគមន៍ដំបូង)"
                )
            else:
                voice_replies[key] = reply_msg.media
                await event.edit(
                    f"[VOICE_CONFIG:{key}:{reply_msg.id}]\n"
                    f"🔊 ✅ **បានភ្ជាប់សារសំឡេងសម្រាប់សំណួរទី `{key}` រួចរាល់!**\n"
                    "ពេលភ្ញៀវសួរសំណួរនេះ ប្រព័ន្ធនឹងឆ្លើយតបទាំងអក្សរ និងផ្ញើសំឡេងនេះទៅជាមួយគ្នាដោយស្វ័យប្រវត្តិ។"
                )
        elif cmd_lower.startswith("/delvoice "):
            key = cmd[10:].strip().lower()
            voice_replies.pop(key, None)
            await event.edit(
                f"[VOICE_CONFIG:{key}:NONE]\n"
                f"🗑️ បានលុបសារសំឡេងសម្រាប់សំណួរទី `{key}` ចេញវិញហើយ!"
            )
        elif cmd_lower.startswith("/setimage "):
            key = cmd[10:].strip().lower()
            reply_msg = await event.get_reply_message()
            if not reply_msg or not reply_msg.media:
                await event.edit(
                    "⚠️ **របៀបដាក់រូបភាពផលិតផល៖**\n"
                    "សូមផ្ញើរូបភាពចូលក្នុង **Saved Messages** ជាមុនសិន រួចចុច **Reply** លើរូបភាពនោះ ហើយវាយ៖\n"
                    "• `/setimage 1` (សម្រាប់សំណួរទី ១)\n"
                    "• `/setimage 2` (សម្រាប់សំណួរទី ២)\n"
                    "• `/setimage 3` (សម្រាប់សំណួរទី ៣)\n"
                    "• `/setimage 4` (សម្រាប់សំណួរទី ៤)"
                )
            else:
                image_replies[key] = reply_msg.media
                await event.edit(
                    f"[IMAGE_CONFIG:{key}:{reply_msg.id}]\n"
                    f"🖼️ ✅ **បានភ្ជាប់រូបភាពផលិតផលសម្រាប់សំណួរទី `{key}` រួចរាល់!**\n"
                    "ពេលភ្ញៀវសួរសំណួរនេះ ប្រព័ន្ធនឹងផ្ញើរូបភាពនេះភ្ជាប់ជាមួយអត្ថបទពន្យល់ និងសំឡេង AI ដោយស្វ័យប្រវត្តិ។"
                )
        elif cmd_lower.startswith("/delimage "):
            key = cmd[10:].strip().lower()
            image_replies.pop(key, None)
            await event.edit(
                f"[IMAGE_CONFIG:{key}:NONE]\n"
                f"🗑️ បានលុបរូបភាពផលិតផលសម្រាប់សំណួរទី `{key}` ចេញវិញហើយ!"
            )
        elif cmd_lower == "/status":
            status_text = (
                "📊 **ស្ថានភាពប្រព័ន្ធឆ្លើយតបអូតូ**\n"
                f"• ឆ្លើយតបអូតូ៖ {'✅ បើក (ON)' if state['auto_reply_enabled'] else '⛔ បិទ (OFF)'}\n"
                f"• សំឡេង AI មនុស្សស្រីខ្មែរ៖ `✅ បើកដំណើរការ (ស្រីមុំ)`\n"
                f"• រូបភាពផលិតផល៖ `✅ គាំទ្រ (Folder / Saved Messages)`\n"
                f"• ចំនួនសំណួរជ្រើសរើស៖ `{len(QUESTIONS_MENU)}` សំណួរ"
            )
            await event.edit(status_text)
        elif cmd_lower.startswith("/test"):
            parts = cmd.split(maxsplit=1)
            t_arg = parts[1].strip() if len(parts) > 1 else "1"
            kh_to_en = {"១": "1", "២": "2", "៣": "3", "៤": "4"}
            test_num = kh_to_en.get(t_arg, t_arg)
            if test_num in QUESTIONS_MENU:
                item = QUESTIONS_MENU[test_num]
                await event.reply(f"🧪 **[TEST សំណួរទី {test_num}]**")
                await send_question_reply(event, test_num, item)
            elif t_arg.lower() == "menu":
                chat = await event.get_input_chat()
                await event.reply(state["busy_message"])
                await send_voice_if_configured(chat, "menu")
            else:
                await event.reply("⚠️ សូមវាយ `/test 1`, `/test 2`, `/test 3` ឬ `/test 4` ដើម្បីតេស្ត!")

    # ------------------------------------------
    # ២. មុខងារទទួលសារ និងឆ្លើយតបអូតូ (ឆាតផ្ទាល់ខ្លួន Private Chat)
    # ------------------------------------------
    @client.on(events.NewMessage(incoming=True))
    async def auto_reply_handler(event):
        # ឆ្លើយតបតែឆាតផ្ទាល់ខ្លួន (Private Chat) មិនតបក្នុង Group ឬ Channel ទេ
        if not event.is_private:
            return

        if not state["auto_reply_enabled"]:
            return

        sender = await event.get_sender()
        # មិនឆ្លើយតបទៅ Bot ផ្សេងៗ ឬគណនីខ្លួនឯងទេ
        if not sender or getattr(sender, "bot", False) or getattr(sender, "is_self", False):
            return

        user_id = event.sender_id
        message_text = (event.raw_text or "").strip()
        message_lower = message_text.lower()
        chat = await event.get_input_chat()

        # ២.១ ពិនិត្យមើលថាតើភ្ញៀវជ្រើសរើសលេខសំណួរ (ឧ. "1", "១") ឬវាយសំណួរក្នុង QUESTIONS_MENU ដែរឬទេ
        for num, item in QUESTIONS_MENU.items():
            is_num_match = (
                message_lower == num
                or message_lower == item["khmer_num"]
                or message_lower.startswith(f"{num} ")
                or message_lower.startswith(f"{num}.")
                or message_lower.startswith(f"{item['khmer_num']} ")
            )
            is_kw_match = any(kw.lower() in message_lower for kw in item["keywords"])
            if is_num_match or is_kw_match:
                await asyncio.sleep(1.0)
                await send_question_reply(event, num, item)
                last_replied_time[user_id] = time.time()
                print(f"[Question {num} - Image & AI Voice] បានតបទៅ {sender.first_name} ({user_id})")
                return

        # ២.២ ពិនិត្យមើលពាក្យគន្លឹះ (Keywords) ផ្សេងៗ
        for keyword, reply_msg in KEYWORD_REPLIES.items():
            if keyword.lower() in message_lower:
                await asyncio.sleep(1.0)
                await event.reply(reply_msg)
                if reply_msg == state["busy_message"]:
                    await send_voice_if_configured(chat, "menu")
                last_replied_time[user_id] = time.time()
                print(f"[Keyword] បានតបទៅ {sender.first_name} ({user_id}) ដោយពាក្យគន្លឹះ '{keyword}'")
                return

        # ២.៣ ប្រសិនបើប្រើ AI ឱ្យឆ្លើយតបគ្រប់សារ
        if state["use_ai"] and genai_client and message_text:
            await asyncio.sleep(2)
            ai_reply = await generate_ai_reply(message_text)
            await event.reply(ai_reply)
            last_replied_time[user_id] = time.time()
            print(f"[AI] បានតបទៅ {sender.first_name} ({user_id})")
            return

        # ២.៤ ប្រសិនបើភ្ញៀវឆាតអ្វីផ្សេង ផ្ញើតារាងសំណួរ (Menu) ឱ្យគាត់ជ្រើសរើស + សំឡេង AI
        now = time.time()
        last_time = last_replied_time.get(user_id, 0)
        if now - last_time >= COOLDOWN_SECONDS:
            await asyncio.sleep(1.0)
            await event.reply(state["busy_message"])
            await send_voice_if_configured(chat, "menu")
            last_replied_time[user_id] = now
            print(f"[Menu Auto-Reply] បានផ្ញើតារាងសំណួរនិងសំឡេង AI ទៅ {sender.first_name} ({user_id})")

    print("🔄 កំពុងភ្ជាប់ទៅកាន់គណនី Telegram របស់អ្នក...")
    try:
        await client.start()
    except Exception as e:
        if "AuthKeyDuplicatedError" in type(e).__name__ or "AuthKeyDuplicatedError" in str(e):
            print("\n⚠️ Session ចាស់ត្រូវបាន Telegram បិទ ដោយសារការប្រើប្រាស់លើ ២ កន្លែងដំណាលគ្នា (AuthKeyDuplicatedError)!")
            print("🔄 សូមបញ្ចូលលេខទូរស័ព្ទដើម្បី Login ម្ដងទៀត...")
            session_file = os.path.join(SCRIPT_DIR, "telegram_auto_reply_session.session")
            if os.path.exists(session_file):
                try:
                    os.remove(session_file)
                except Exception:
                    pass
            client = TelegramClient(os.path.join(SCRIPT_DIR, "telegram_auto_reply_session"), int(API_ID), API_HASH)
            await client.start()
        else:
            raise e
    me = await client.get_me()
    await prepare_ai_voices()
    await load_saved_media()

    # រក្សាទុក STRING_SESSION ទៅក្នុងឯកសារ cloud_keys.txt ដើម្បីងាយស្រួលយកទៅដាក់លើ Cloud 24/7
    if not STRING_SESSION:
        try:
            exported_session = StringSession.save(client.session)
            with open("cloud_keys.txt", "w", encoding="utf-8") as f:
                f.write("=== ព័ត៌មានសម្រាប់ដាក់លើ Cloud Server (Render / Railway) ===\n\n")
                f.write(f"API_ID={API_ID}\n")
                f.write(f"API_HASH={API_HASH}\n")
                f.write(f"STRING_SESSION={exported_session}\n")
        except Exception as e:
            print(f"[!] មិនអាចបង្កើត cloud_keys.txt បានទេ: {e}")

    print("=" * 60)
    print(f"✅ ភ្ជាប់ជោគជ័យ! គណនី៖ {me.first_name}")
    print("🤖 ប្រព័ន្ធឆ្លើយតបអូតូកំពុងដំណើរការ...")
    print("💡 អ្នកអាចវាយបញ្ជាក្នុង Saved Messages របស់អ្នកបាន៖")
    print("   • /status           : មើលស្ថានភាពបច្ចុប្បន្ន")
    print("   • /off              : បិទការឆ្លើយតបអូតូ")
    print("   • /on               : បើកការឆ្លើយតបអូតូវិញ")
    print("   • /setvoice 1..4    : Reply លើសារសំឡេងដើម្បីដាក់សំឡេងឱ្យសំណួរទី 1-4")
    print("   • /delvoice 1..4    : លុបសារសំឡេងចេញវិញ")
    print("   • /setimage 1..4    : Reply លើរូបភាពដើម្បីដាក់រូបផលិតផលឱ្យសំណួរទី 1-4")
    print("   • /delimage 1..4    : លុបរូបភាពផលិតផលចេញវិញ")
    print("   • /setmsg <សារថ្មី>  : ប្ដូរសារឆ្លើយតបពេលរវល់ភ្លាមៗ")
    print("=" * 60)
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
