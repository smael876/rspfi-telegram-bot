# 🛍️ Telegram E-Commerce Shop Bot (ប្រព័ន្ធលក់ទំនិញតាម Telegram)

កម្មវិធី Telegram Bot សម្រាប់លក់ទំនិញអនឡាញ បង្កើតឡើងដោយប្រើប្រាស់ **Python**, **python-telegram-bot** និង **SQLite** ជាមួយចំណុចប្រទាក់ជាភាសាខ្មែរងាយស្រួលប្រើប្រាស់។

---

## 🌟 មុខងារចម្បងៗ (Features)

### 🛒 សម្រាប់អតិថិជន (Customers)
* 🛍️ **កាតាឡុកទំនិញ (Product Catalog)**៖ មើលទំនិញតាមជំពូក រូបភាព តម្លៃ និងព័ត៌មានលម្អិត។
* 🛒 **កន្ត្រកទំនិញ (Shopping Cart)**៖ បន្ថែមទំនិញ, បង្កើន/បន្ថយចំនួន (`+` / `-`), លុបទំនិញ ឬសម្អាតកន្ត្រក។
* 💳 **ការបញ្ជាទិញ (Checkout Process)**៖
  * ផ្ញើលេខទូរស័ព្ទ (អាចចុចប៊ូតុង Share Phone)
  * បញ្ចូលទីតាំង ឬអាសយដ្ឋានដឹកជញ្ជូន
  * ជ្រើសរើសវិធីទូទាត់ប្រាក់ (សាច់ប្រាក់ផ្ទាល់ ឬស្កេន KHQR)
  * ទទួលបានវិក្កយបត្របញ្ជាក់ការកុម្ម៉ង់ភ្លាមៗ
* 📦 **ប្រវត្តិបញ្ជាទិញ (Order History)**៖ ពិនិត្យមើលស្ថានភាពនៃការកុម្ម៉ង់កន្លងមក។

### 👑 សម្រាប់ម្ចាស់ហាង (Admin)
* 🚨 **សារជូនដំណឹងភ្លាមៗ (Instant Alerts)**៖ ពេលមានអតិថិជនកុម្ម៉ង់ Bot នឹងផ្ញើសារលម្អិត (ឈ្មោះ, លេខទូរស័ព្ទ, អាសយដ្ឋាន, មុខទំនិញ) ទៅកាន់ Telegram Admin ភ្លាមៗ។
* ➕ **បន្ថែមទំនិញ និងជំពូកថ្មី**៖ អាចបន្ថែម Category និងទំនិញថ្មី (ដាក់រូបភាព តម្លៃ និងការពិពណ៌នា) ដោយផ្ទាល់តាម Telegram។
* 🗑️ **គ្រប់គ្រងទំនិញ**៖ មើលបញ្ជីទំនិញ និងលុបទំនិញដែលឈប់លក់។
* 📋 **គ្រប់គ្រងការបញ្ជាទិញ**៖ ផ្លាស់ប្តូរស្ថានភាពកុម្ម៉ង់ (បានបញ្ជាក់ -> កំពុងដឹកជញ្ជូន -> បានដឹកដល់ -> បោះបង់)។

---

## 🚀 របៀបដំឡើង និងដំណើរការ (Quick Start)

### ជំហានទី ១៖ យក Telegram Bot Token & Admin ID
1. បើក Telegram ស្វែងរក [@BotFather](https://t.me/BotFather)
   * ផ្ញើពាក្យបញ្ជា `/newbot`
   * បញ្ចូលឈ្មោះ Bot និង Username (ត្រូវបញ្ចប់ដោយ `bot` ឧទាហរណ៍ `my_shop_demo_bot`)
   * ចម្លងយក **API Token**
2. ស្វែងរក [@userinfobot](https://t.me/userinfobot) រួចចុច Start ដើម្បីមើលលេខ **Id** ផ្ទាល់ខ្លួនរបស់អ្នក (ឧទាហរណ៍: `123456789`)

### ជំហានទី ២៖ កំណត់ `.env` File
បើក file `.env` នៅក្នុង Folder នេះ រួចបំពេញព័ត៌មាន៖
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
ADMIN_ID=123456789
SHOP_NAME=Khmer Online Shop
CURRENCY=$
```

### ជំហានទី ៣៖ បញ្ចូលទិន្នន័យគំរូ (Demo Data)
ដើម្បីមានទំនិញតេស្តភ្លាមៗ សូមដំណើរការ៖
```bash
python seed_data.py
```

### ជំហានទី ៤៖ ដំណើរការ Bot
```bash
python bot.py
```

---

## 📱 ការប្រើប្រាស់ (Bot Commands)

* `/start` - បើកផ្ទាំងទិញទំនិញ និង Menu មេ
* `/admin` - បើកផ្ទាំងគ្រប់គ្រង Admin (សម្រាប់តែ Admin ID ដែលបានកំណត់ប៉ុណ្ណោះ)
* `/help` - មើលព័ត៌មានជំនួយ និងទំនាក់ទំនង

---

## 📁 រចនាសម្ព័ន្ធកូដ (Project Structure)

```
telegram bot/
├── .env                  # កន្លែងកំណត់ Token & Admin ID
├── database.py           # SQLite Database CRUD Functions
├── bot.py                # កូដមេគ្រប់គ្រង Telegram Bot
├── seed_data.py          # Script បញ្ចូលទិន្នន័យគំរូ
├── handlers/
│   ├── customer.py       # Menu, Catalog, Cart, Checkout
│   └── admin.py          # Admin Dashboard, Add Product, Orders
└── requirements.txt      # បណ្ណាល័យ Python
```
