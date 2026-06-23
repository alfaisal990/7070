# تقرير سير العمليات وتدفق البيانات (Business & Data Flows) - Phoenix AI

يوضح هذا المستند مخططات سير العمليات الأساسية وتدفق البيانات (Business Flows) لمنصة **Phoenix AI** لبيئات التشغيل.

---

## 1. مخطط تدفق المحادثة وسياق الـ RAG (Chat & RAG Data Flow)

يوضح المخطط التالي دورة حياة طلب المستخدم للحصول على إجابة مدعومة ببيانات الذاكرة المتجهية:

```mermaid
sequenceDiagram
    autonumber
    actor User as المستخدم
    participant UI as الواجهة الأمامية (React)
    participant Sec as وحدة الفحص الأمني (Security Guard)
    participant API as خادم الواجهة الخلفية (FastAPI)
    participant DB as بنك المتجهات والذاكرة (Vector DB)
    participant Model as النموذج اللغوي ومحرك الاستدلال

    User->>UI: إدخال السؤال والضغط على إرسال
    UI->>Sec: التحقق من خلو المدخلات من ثغرات الحقن (Prompt Injection)
    alt تم كشف محاولة حقن أو التفاف
        Sec-->>UI: رفض الطلب وإرجاع رمز الخطأ 400
        UI-->>User: عرض رسالة تنبيه أمنية
    else المدخلات سليمة وآمنة
        Sec->>API: تمرير السؤال عبر طلب POST
        API->>DB: البحث الدلالي في المستندات المتجهية (Memory Search)
        DB-->>API: إرجاع المستندات المتطابقة والسياق ذي الصلة
        API->>Model: دمج السياق مع سؤال المستخدم وتمريره للاستدلال
        Model-->>API: توليد الإجابة اللغوية (بما في ذلك كتل الأكواد)
        API-->>UI: إرسال الإجابة (تدفق نصوص لحظي Stream أو حزمة JSON)
        UI-->>User: عرض الإجابة النهائية وتحديث سجل المحادثة
    end
```

---

## 2. مخطط تدفق فحص وتشغيل الأكواد المعزولة (Sandbox Run Flow)

يوضح هذا المخطط كيفية معالجة طلبات تشغيل الأكواد برمجياً وبشكل معزول:

```mermaid
graph TD
    User([المطور]) --> Input[إدخال كود بايثون وتعيين مهلة الانتظار]
    Input --> UI[الواجهة الأمامية]
    UI --> API[خادم FastAPI: /api/sandbox/run]
    API --> Security{فحص القيود الأمنية والرموز الممنوعة}
    
    Security -- كشف رموز محظورة getattr / builtins --> Reject[رفض المعالجة فوراً وإرجاع خطأ أمني]
    Security -- الكود يتوافق مع السياسات الأمنية --> Execution[تمرير الكود لوحدة Sandbox المعزولة]
    
    Execution --> Limit[تضييق وتجريد متغيرات البيئة PATH]
    Limit --> Subprocess[إطلاق عملية فرعية معزولة بمفسر بايثون]
    Subprocess --> Timeout{تجاوز مهلة التنفيذ المحددة؟}
    
    Timeout -- نعم --> Kill[إنهاء العملية فوراً وإرجاع خطأ تجاوز الوقت]
    Timeout -- لا --> Collect[تجميع مخرجات stdout و stderr وكود الخروج]
    
    Collect --> Response[صياغة النتيجة وإرجاعها للواجهة]
    Response --> Display[عرض النتيجة للمطور في لوحة كونسول تفاعلية]
    
    Reject --> Display
    Kill --> Display
```

---

## 3. مخطط تدفق النسخ الاحتياطي والتعافي (Disaster Recovery Flow)

```mermaid
graph TD
    Trigger[إطلاق النسخ الاحتياطي: تلقائي أو يدوي] --> Lock{فحص وجود ملف قاعدة البيانات memory_db.json}
    Lock -- غير متواجد --> Fail[فشل العملية وتنبيه المسؤول]
    Lock -- متواجد --> Copy[إنشاء نسخة مؤقتة باسم .tmp]
    
    Copy --> Validate{التحقق من سلامة وصلاحية بنية ملف الـ JSON المؤقت}
    Validate -- بنيان تالف أو ناقص --> Remove[حذف الملف المؤقت وإرجاع خطأ أمني]
    Validate -- البنيان سليم ومكتمل --> Commit[استبدال الملف للمسار النهائي atomically]
    
    Commit --> Rotate[تطبيق قاعدة تدوير النسخ والاحتفاظ بآخر 5 نسخ فقط]
    Rotate --> Success([اكتمال النسخ بنجاح كامل وتحديث سجلات النظام])
```
