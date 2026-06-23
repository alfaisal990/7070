# دليل استعادة البيانات والتعافي من الكوارث لمنصة Phoenix AGI

يصف هذا الدليل الخطوات اللازمة لاستعادة قاعدة معرفة منصة Phoenix AGI (`memory_db.json`) من النسخ الاحتياطية وتعافي التطبيق في حال حدوث تلف في البيانات، أو انهيار النظام، أو فشل النشر.

---

## 1. خطوات استعادة قاعدة البيانات

يتم تخزين النسخ الاحتياطية لقاعدة المعرفة المتجهة (`memory_db.json`) بشكل ذري وتلقائي داخل المجلد `ai_project/memory/backups/`. 
لاستعادة قاعدة البيانات، يمكنك استخدام نص الاستعادة التلقائي أو اتباع العملية اليدوية.

### الطريقة أ: نص الاستعادة التلقائي المساعد
لقد قمنا بتوفير برنامج نصي عبر سطر الأوامر لتسهيل استعادة قاعدة البيانات إلى نقطة نسخ احتياطي معينة بسرعة.

قم بتشغيل نص التعافي عبر بيئة بايثون:
```powershell
.venv\Scripts\python -m ai_project.utils.restore --file ai_project/memory/backups/memory_db_20260623_000000.json
```

### الطريقة ب: الاستعادة اليدوية
إذا كنت بحاجة إلى تنفيذ عملية الاستعادة يدوياً:
1. قم بإيقاف خادم FastAPI مؤقتاً للتأكد من عدم قفل الملف.
2. حدد ملف النسخة الاحتياطية المطلوبة في مسار `ai_project/memory/backups/`.
3. انسخ ملف النسخة الاحتياطية المحددة إلى المجلد الرئيسي للمشروع وأعد تسميته:
   ```powershell
   Copy-Item "ai_project/memory/backups/memory_db_20260623_000000.json" "ai_project/memory/memory_db.json" -Force
   ```
4. تحقق من سلامة قاعدة البيانات المستعادة (يجب أن تحتوي على تنسيق JSON صالح يضم المفاتيح الرئيسية `"memories"` و `"kg_graph"`).
5. أعد تشغيل خادم FastAPI.

---

## 2. كود برنامج استعادة البيانات المساعد

تمت كتابة وتطبيق كود الاستعادة في الملف المتاح [restore.py](file:///c:/Users/1/Desktop/7070/ai_project/utils/restore.py):
```python
import os
import sys
import json
import argparse
import shutil

def restore_db(backup_file: str, db_file: str = "ai_project/memory/memory_db.json"):
    if not os.path.exists(backup_file):
        print(f"Error: Backup file {backup_file} does not exist.")
        sys.exit(1)
        
    print(f"Validating backup integrity for {backup_file}...")
    try:
        with open(backup_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "memories" not in data or "kg_graph" not in data:
                raise ValueError("Required database root keys are missing.")
        print("Backup integrity validation: OK.")
    except Exception as e:
        print(f"Error: Backup file is corrupt or invalid: {str(e)}")
        sys.exit(1)
        
    print(f"Restoring database to {db_file}...")
    temp_db = db_file + ".restore.tmp"
    try:
        os.makedirs(os.path.dirname(os.path.abspath(db_file)), exist_ok=True)
        shutil.copy2(backup_file, temp_db)
        os.replace(temp_db, db_file)
        print("Database restored successfully.")
    except Exception as e:
        if os.path.exists(temp_db):
            os.remove(temp_db)
        print(f"Error restoring database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restore Phoenix Memory DB from a backup file.")
    parser.add_argument("--file", required=True, help="Path to the backup JSON file.")
    parser.add_argument("--dest", default="ai_project/memory/memory_db.json", help="Path to destination database file.")
    args = parser.parse_args()
    restore_db(args.file, args.dest)
```

---

## 3. مسارات وخطوات الطوارئ البديلة

في حال تعطل الخادم الرئيسي أو عدم استجابته:
1. **كشف التعطل عبر فحص الصحة**: يشير فشل نقطة نهاية `/api/health` إلى تعطل الخادم.
2. **إعادة التشغيل التلقائي**: يمكن لبرنامج مراقبة خادم محلي إعادة تشغيل العملية تلقائياً باستخدام ملف `run_phoenix.bat`.
3. **إعادة تهيئة قاعدة البيانات**: في حال تلف ملف `memory_db.json` تماماً وعدم توفر أي نسخ احتياطية سليمة، قم بتغيير اسم الملف التالف إلى `memory_db.json.corrupt` وأعد تشغيل الخدمة؛ ستقوم المنصة تلقائياً بإنشاء قاعدة بيانات فارغة ونظيفة عند التشغيل لتفادي التوقف الكلي.
