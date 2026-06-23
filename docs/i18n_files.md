# تقرير ملفات التعريب والترجمة المتعددة (i18n Localization) - Phoenix AI

تحدد هذه الوثيقة البنية التكوينية لملفات التعريب والترجمة الثنائية (العربية والإنجليزية) لمنصة **Phoenix AI** لتهيئة التطبيق للعمل متعدد اللغات.

---

## 1. بنية تكوين ملفات الترجمة (Translation Schema)

يتم تنظيم نصوص ومفاتيح الترجمة في ملفات JSON مخصصة لكل لغة تحت مسار `src/locales/` لتسهيل إدراجها ديناميكياً باستخدام مكتبات مثل `react-i18next`.

### أ. ملف الترجمة العربية (`ar.json`)
* **المسار المقترح**: `ai_project/dashboard/src/locales/ar.json`
* **المحتوى**:
  ```json
  {
    "sidebar": {
      "chat": "المساعد الذكي",
      "sandbox": "محاكي الأكواد",
      "memory": "الذاكرة المعرفية",
      "debugger": "مكتشف الأخطاء",
      "refactor": "مصلح الأكواد",
      "ai_explorer": "مستكشف النماذج",
      "scan_now": "فحص مساحة العمل",
      "backup": "نسخ احتياطي"
    },
    "chat": {
      "header": "محادثة المساعد الذكي",
      "input_placeholder": "اكتب سؤالك البرمجي هنا...",
      "send": "إرسال",
      "stream_mode": "وضع البث المباشر",
      "error_injection": "تم كشف محاولة اختراق أمني أو حقن أوامر."
    },
    "sandbox": {
      "header": "بيئة تنفيذ الأكواد المعزولة",
      "run": "تشغيل الكود",
      "timeout": "مهلة الانتظار القصوى (ثواني)",
      "output": "مخرجات لوحة التحكم",
      "success": "تم تنفيذ الكود بنجاح كامل!"
    }
  }
  ```

---

### ب. ملف الترجمة الإنجليزية (`en.json`)
* **المسار المقترح**: `ai_project/dashboard/src/locales/en.json`
* **المحتوى**:
  ```json
  {
    "sidebar": {
      "chat": "AI Assistant",
      "sandbox": "Code Sandbox",
      "memory": "Semantic Memory",
      "debugger": "Workspace Debugger",
      "refactor": "Code Refactoring",
      "ai_explorer": "AI Explorer",
      "scan_now": "Scan Workspace",
      "backup": "Trigger Backup"
    },
    "chat": {
      "header": "AI Assistant Chat",
      "input_placeholder": "Write your coding prompt here...",
      "send": "Send",
      "stream_mode": "Stream Output",
      "error_injection": "Potential prompt injection or instruction override detected."
    },
    "sandbox": {
      "header": "Secure Code Execution Sandbox",
      "run": "Run Code",
      "timeout": "Timeout Limit (seconds)",
      "output": "Console Output Terminal",
      "success": "Code executed successfully!"
    }
  }
  ```

---

## 2. آلية التبديل والملاحة في الواجهة الأمامية

* يتم تخزين خيار اللغة المفضل للمستخدم في ذاكرة التصفح المحلية (`localStorage.setItem('lng', selectedLanguage)`) لضمان الاحتفاظ بالتفضيل عند تحديث التطبيق.
* تفعيل التبديل الفوري لتجاه القراءة والأنماط البصرية (RTL لغة الضاد / LTR اللغة الإنجليزية) لتأمين أفضل تجربة قراءة وتصميم للواجهة.
