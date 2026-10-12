import sys
import database

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

DEFAULT_PRODUCTS = [
    {
        "match_keyword": "%ថ្នាំក្រមុំ%",
        "category": "🌸 ព្យាបាល រោគ ស្ត្រី",
        "name": "ថ្នាំក្រមុំម្តងទៀត",
        "description": "ជួយព្យាបាលបញ្ហារោគស្ត្រីដូចជា៖\n• ធ្លាក់ស . មេរោគផ្សិត . មានក្លិនមិនល្អ\n• រដូវមិនទៀងទាត់ . ស្បូនស្រុត ស្បូនលាន់\n• ជាពិសេសធ្វើឲ្យតំបន់ទ្វារមាសតឹងណែនដូចក្រមុំម្ដងទៀត។\n🌿 ផលិតផល RSPFI Lady Vaginy ផ្សំពីរុក្ខជាតិធម្មជាតិ 100% ជួយថែរក្សាសុខភាពស្ត្រី ផ្តល់ទំនុកចិត្តខ្ពស់។ (១ ប្រអប់)",
        "price": 15.0,
        "image_url": "images/rspfi_lady_vaginy.jpg"
    },
    {
        "match_keyword": "%សាប៊ូ%",
        "category": "🧼 សាប៊ូអនាម័យលាងតំបន់ទ្វារមាស",
        "name": "សាប៊ូអនាម័យ RSPFI Lady Soap (18,000៛)",
        "description": "✨ សាប៊ូអនាម័យ RSPFI Lady Soap (ក្រមុំម្តងទៀត)\n💵 តម្លៃ៖ 18,000 រៀល ($4.50) / មួយប្រអប់\n\n🌸 អត្ថប្រយោជន៍ចម្បងៗ៖\n• ជាសាប៊ូអនាម័យលាងសម្អាតតំបន់ទ្វារមាសបានស្អាតល្អ\n• កាត់បន្ថយក្លិនមិនល្អ ផ្ដល់នូវក្លិនក្រអូប ស្រស់ស្រាយ និងមានទំនុកចិត្ត\n• ជួយសម្អាតតំបន់ស្ត្រីបានស្អាត ទន់រលោង និងជួយបន្ថែមសំណើម\n• រូបមន្តផ្សំពីរុក្ខជាតិធម្មជាតិសុវត្ថិភាពខ្ពស់",
        "price": 4.50,
        "image_url": "images/rspfi_lady_soap.jpg"
    },
    {
        "match_keyword": "%Mint%",
        "category": "💊 វីតាមីនស៊ុលទ្វារមាស",
        "name": "វីតាមីនស៊ុល RSPFI Mint (តំបន់សំណើម)",
        "description": "✨ ផលិតផល RSPFI FEMININE WELLNESS MINT\n🌿 តំបន់មានសំណើម ផ្តល់ភាពស្រស់ស្រាយ ត្រជាក់ និងមានទំនុកចិត្ត។\n🕒 របៀបប្រើ៖ ប្រើ ២០ នាទី មុនពេលរួមភេទ ធ្វើឱ្យមានសំណើមទ្វារមាស។\n💊 ជាប្រភេទវីតាមីនស៊ុលនៅក្នុងទ្វារមាស (Feminine Suppositories) ផ្សំពីរុក្ខជាតិធម្មជាតិ (១ ប្រអប់មាន ១០ គ្រាប់)។",
        "price": 15.0,
        "image_url": "images/rspfi_wellness_mint.jpg"
    },
    {
        "match_keyword": "%Strawberry%",
        "category": "💊 វីតាមីនស៊ុលទ្វារមាស",
        "name": "វីតាមីនស៊ុល RSPFI Strawberry (តំបន់សំណើម)",
        "description": "✨ ផលិតផល RSPFI FEMININE WELLNESS STRAWBERRY\n🍓 តំបន់មានសំណើម ក្លិនស្ត្រប៊ែរីក្រអូប ផ្ដល់ភាពស្រស់ស្រាយ និងមានទំនុកចិត្ត។\n🕒 របៀបប្រើ៖ ប្រើ ២០ នាទី មុនពេលរួមភេទ ធ្វើឱ្យមានសំណើមទ្វារមាស។\n💊 ជាប្រភេទវីតាមីនស៊ុលនៅក្នុងទ្វារមាស (Feminine Suppositories) ផ្សំពីរុក្ខជាតិធម្មជាតិ (១ ប្រអប់មាន ១០ គ្រាប់)។",
        "price": 15.0,
        "image_url": "images/rspfi_wellness_strawberry.jpg"
    },
    {
        "match_keyword": "%សាប៊ូអនាម័យ+ថ្នាំក្រមុំ%",
        "category": "🌸 ឈុតក្រមុំម្ដងទៀត (ហ្វ្រីសេវាដឹក)",
        "name": "សាប៊ូអនាម័យ+ថ្នាំក្រមុំម្ដងទៀត",
        "description": "✨ ឈុតក្រមុំម្ដងទៀត (សាប៊ូអនាម័យ + ថ្នាំក្រមុំម្ដងទៀត)\n💵 តម្លៃ៖ $20.00 (80,000 រៀល) / ១ឈុត\n🚚 ពិសេស៖ ហ្វ្រីសេវាដឹកជញ្ជូនទូទាំង ២៥ ខេត្ត-ក្រុង!\n\n🌸 អត្ថប្រយោជន៍ក្នុង ១ឈុត (ឱសថបុរាណបែបធម្មជាតិ 100%)៖\n• 🧼 សាប៊ូអនាម័យ RSPFI Lady Soap៖ លាងសម្អាតតំបន់ស្ត្រីបានស្អាតល្អ កាត់បន្ថយក្លិនមិនល្អ ផ្ដល់ក្លិនក្រអូបស្រស់ស្រាយ ទន់រលោង និងបន្ថែមសំណើម\n• 💊 ថ្នាំក្រមុំម្ដងទៀត RSPFI Lady Vaginy៖ ជួយព្យាបាលបញ្ហាធ្លាក់ស មេរោគផ្សិត ក្លិនមិនល្អ រដូវមិនទៀងទាត់ ស្បូនស្រុត និងជួយឱ្យតំបន់ទ្វារមាសតឹងណែនដូចក្រមុំម្ដងទៀត\n• 🌿 ផ្សំពីរុក្ខជាតិធម្មជាតិ 100% ប្រើប្រាស់ប្រកបដោយសុវត្ថិភាព និងទំនុកចិត្តខ្ពស់។",
        "price": 20.0,
        "image_url": "images/rspfi_combo_set.jpg"
    }
]

def seed():
    database.init_db()
    print("កំពុងពិនិត្យ និងបញ្ចូលផលិតផលទាំងអស់...")
    
    with database.get_connection() as conn:
        cursor = conn.cursor()
        
        for item in DEFAULT_PRODUCTS:
            # 1. Ensure category exists
            cursor.execute("SELECT id FROM categories WHERE name = ?", (item["category"].strip(),))
            row = cursor.fetchone()
            if row:
                cat_id = row["id"]
            else:
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (item["category"].strip(),))
                cat_id = cursor.lastrowid

            # 2. Check if product exists by image_url or exact name
            cursor.execute("SELECT id FROM products WHERE image_url = ? OR name = ?", (item["image_url"], item["name"]))
            prod_row = cursor.fetchone()
            
            if prod_row:
                cursor.execute("""
                    UPDATE products 
                    SET category_id = ?, name = ?, description = ?, price = ?, image_url = ?, is_active = 1
                    WHERE id = ?
                """, (cat_id, item["name"], item["description"], item["price"], item["image_url"], prod_row["id"]))
                print(f"✅ បានធ្វើបច្ចុប្បន្នភាពផលិតផល៖ {item['name']}")
            else:
                cursor.execute("""
                    INSERT INTO products (category_id, name, description, price, image_url, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (cat_id, item["name"], item["description"], item["price"], item["image_url"]))
                print(f"➕ បានបញ្ចូលផលិតផលថ្មី៖ {item['name']}")
                
        conn.commit()
    print("🎉 ដំណើរការ Seed ផលិតផលទាំង ៥ បានជោគជ័យ ១០០%!")

if __name__ == "__main__":
    seed()
