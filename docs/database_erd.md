# تقرير خطط البيانات الهيكلية (Database ERD Report) - Phoenix AI

يوضح هذا المستند مخطط علاقات الكيانات وقاعدة البيانات (ERD) لمنصة **Phoenix AI** لبيئة الإنتاج المقترحة.

---

## 1. مخطط علاقات الكيانات باستخدام Mermaid (Mermaid ERD)

نظرًا لأن المنصة تعتمد حاليًا على ملفات JSON وتتطلع للتوسع المؤسسي، فإن المخطط الهيكلي المقترح للعلاقات وقواعد البيانات يتضمن الجداول التالية:

```mermaid
erDiagram
    USERS ||--o{ MEMORIES : "manages"
    USERS ||--o{ AUDIT_LOGS : "triggers"
    USERS {
        int id PK
        string username UK
        string email UK
        string password_hash
        string role "admin | developer | user"
        datetime created_at
    }

    MEMORIES ||--o{ KNOWLEDGE_GRAPH_RELATIONS : "contains entities"
    MEMORIES {
        int id PK
        int user_id FK
        string text "Main content"
        vector embedding "32 or 768 float array"
        datetime created_at
        datetime last_accessed
        int access_count
        float importance
    }

    KNOWLEDGE_GRAPH_RELATIONS {
        int id PK
        int memory_id FK
        string source_entity "Indexed lower-case"
        string relation "is a | developed | works at"
        string target_entity "Indexed target"
    }

    AUDIT_LOGS {
        int id PK
        int user_id FK
        string action "chat | sandbox_run | backup"
        string request_id UK "Correlation UUID"
        string status "success | failed"
        datetime timestamp
    }

    AI_MODELS {
        int id PK
        string category_id "llm | vision | reinforcement"
        string name UK
        string developer
        string parameters_count
        string use_case
    }
```

---

## 2. تفاصيل الجداول والحقول البرمجية (Schema Definition)

### أ. جدول المستخدمين (`USERS`)
* يضمن تفريد الهويات وتحديد الصلاحيات للحد من الاستخدام العشوائي وحماية خصوصية بيانات الـ RAG والذاكرة المخصصة لكل مستخدم.

### ب. جدول الذاكرة والوثائق المتجهية (`MEMORIES`)
* يتضمن الحقل `embedding` من نوع المتجهيات (Vector Column) لدعم عمليات البحث وحساب الفروقات المتجهية.
* حقول تتبع الاستخدام (`access_count`, `last_accessed`, `importance`) تستخدم لفرز السجلات دلالياً وتدوير البيانات وحذف القديم غير الفعال.

### ج. جدول علاقات الرسم البياني للمعرفة (`KNOWLEDGE_GRAPH_RELATIONS`)
* يربط الكيانات وعلاقاتها مع مصادر المستندات والذكريات الأصلية في جدول `MEMORIES`.
* يتضمن فهارس مخصصة (Indexes) على الحقول `source_entity` و `target_entity` لتسريع عمليات تتبع العلاقات بالاستعلامات الكبرى.
