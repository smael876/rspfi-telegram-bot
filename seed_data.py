import sys
import database

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


def seed():
    database.init_db()
    
    # ពិនិត្យមើលថាតើមានទិន្នន័យស្រាប់ឬនៅ
    existing_categories = database.get_all_categories()
    if existing_categories:
        print("Database មានទិន្នន័យរួចរាល់ហើយ មិនចាំបាច់ Seed ឡើងវិញទេ។")
        return

    print("កំពុងបញ្ចូលទិន្នន័យ...")
    
    # Categories
    cat_care = database.add_category("🌸 ព្យាបាល រោគ ស្ត្រី")
    
    # Products
    database.add_product(
        category_id=cat_care,
        name="ថ្នាំក្រមុំម្តងទៀត",
        description="ជួយព្យាបាលបញ្ហារោគស្ត្រីដូចជា៖\n• ធ្លាក់ស . មេរោគផ្សិត . មានក្លិនមិនល្អ\n• រដូវមិនទៀងទាត់ . ស្បូនស្រុត ស្បូនលាន់\n• ជាពិសេសធ្វើឲ្យតំបន់ទ្វារមាសតឹងណែនដូចក្រមុំម្ដងទៀត។\n🌿 ផលិតផល RSPFI Lady Vaginy ផ្សំពីរុក្ខជាតិធម្មជាតិ 100% ជួយថែរក្សាសុខភាពស្ត្រី ផ្តល់ទំនុកចិត្តខ្ពស់។ (១ ប្រអប់)",
        price=15.0,
        image_url="images/rspfi_lady_vaginy.jpg"
    )

    cat_soap = database.add_category("🧼 សាប៊ូអនាម័យលាងតំបន់ទ្វារមាស")
    database.add_product(
        category_id=cat_soap,
        name="សាប៊ូអនាម័យ RSPFI Lady Soap (18,000៛)",
        description="✨ សាប៊ូអនាម័យ RSPFI Lady Soap (ក្រមុំម្តងទៀត)\n💵 តម្លៃ៖ 18,000 រៀល ($4.50) / មួយប្រអប់\n\n🌸 អត្ថប្រយោជន៍ចម្បងៗ៖\n• ជាសាប៊ូអនាម័យលាងសម្អាតតំបន់ទ្វារមាសបានស្អាតល្អ\n• កាត់បន្ថយក្លិនមិនល្អ ផ្ដល់នូវក្លិនក្រអូប ស្រស់ស្រាយ និងមានទំនុកចិត្ត\n• ជួយសម្អាតតំបន់ស្ត្រីបានស្អាត ទន់រលោង និងជួយបន្ថែមសំណើម\n• រូបមន្តផ្សំពីរុក្ខជាតិធម្មជាតិសុវត្ថិភាពខ្ពស់",
        price=4.50,
        image_url="images/rspfi_lady_soap.jpg"
    )

    cat_mint = database.add_category("💊 វីតាមីនស៊ុលទ្វារមាស")
    database.add_product(
        category_id=cat_mint,
        name="វីតាមីនស៊ុល RSPFI Mint (តំបន់សំណើម)",
        description="✨ ផលិតផល RSPFI FEMININE WELLNESS MINT\n🌿 តំបន់មានសំណើម ផ្តល់ភាពស្រស់ស្រាយ ត្រជាក់ និងមានទំនុកចិត្ត។\n🕒 របៀបប្រើ៖ ប្រើ ២០ នាទី មុនពេលរួមភេទ ធ្វើឱ្យមានសំណើមទ្វារមាស។\n💊 ជាប្រភេទវីតាមីនស៊ុលនៅក្នុងទ្វារមាស (Feminine Suppositories) ផ្សំពីរុក្ខជាតិធម្មជាតិ (១ ប្រអប់មាន ១០ គ្រាប់)។",
        price=15.0,
        image_url="images/rspfi_wellness_mint.jpg"
    )
    database.add_product(
        category_id=cat_mint,
        name="វីតាមីនស៊ុល RSPFI Strawberry (តំបន់សំណើម)",
        description="✨ ផលិតផល RSPFI FEMININE WELLNESS STRAWBERRY\n🍓 តំបន់មានសំណើម ក្លិនស្ត្រប៊ែរីក្រអូប ផ្ដល់ភាពស្រស់ស្រាយ និងមានទំនុកចិត្ត។\n🕒 របៀបប្រើ៖ ប្រើ ២០ នាទី មុនពេលរួមភេទ ធ្វើឱ្យមានសំណើមទ្វារមាស។\n💊 ជាប្រភេទវីតាមីនស៊ុលនៅក្នុងទ្វារមាស (Feminine Suppositories) ផ្សំពីរុក្ខជាតិធម្មជាតិ (១ ប្រអប់មាន ១០ គ្រាប់)។",
        price=15.0,
        image_url="images/rspfi_wellness_strawberry.jpg"
    )

    print("បញ្ចូលទិន្នន័យជោគជ័យ!")



if __name__ == "__main__":
    seed()
