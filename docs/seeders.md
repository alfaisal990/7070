# تقرير بيانات التأسيس والبذر البرمجي (Seeders & Sample Data) - Phoenix AI

يوضح هذا المستند تصميم وسيناريوهات بذر البيانات الأولية (Seed Data) لتجهيز قاعدة البيانات المتجهية ومستودعات المعرفة لعمليات الاختبار والتشغيل المبدئي لمنصة **Phoenix AI**.

---

## 1. بيانات بذر مستودع أنواع الذكاء الاصطناعي (`ai_data.json`)

يتم إعداد ملف [ai_data.json](file:///c:/Users/1/Desktop/7070/ai_project/api/ai_data.json) ليحتوي على التصنيفات والنماذج المبدئية التالية لتجهيز مستكشف النماذج الذكية:
* **التصنيف 1: النماذج اللغوية الكبيرة (Large Language Models)**:
  * `GPT-4o` (طراز متطور من OpenAI مناسب للمهام العامة).
  * `Claude 3.5 Sonnet` (طراز متطور من Anthropic يتميز بقوة البرمجة والمنطق).
  * `Llama 3` (طراز مفتوح المصدر ومحلي من Meta).
* **التصنيف 2: الرؤية الحاسوبية (Computer Vision)**:
  * `YOLOv8` (طراز فائق السرعة لكشف الكيانات من Ultralytics).
  * `DALL-E 3` (طراز متطور لتوليد الصور من OpenAI).
* **التصنيف 3: التعلم التعزيزي (Reinforcement Learning)**:
  * `AlphaGo` (طراز الألعاب التاريخي من Google DeepMind).

---

## 2. بيانات بذر الذاكرة المتجهية RAG

لتجهيز بنك الذاكرة المتجهية ومحاكاة عمليات الاسترجاع الدلالي، يتم كتابة نص بذر آلي يقوم بتسجيل المستندات المعرفية التالية في قاعدة البيانات المتجهية:
1. **المستند الأول**: `"Python functions are defined using the 'def' keyword followed by function name and parentheses."` (بيانات وصفية: `{"category": "python", "importance": 1.5}`)
2. **المستند الثاني**: `"FastAPI uses Pydantic models for data validation and request body constraints."` (بيانات وصفية: `{"category": "fastapi", "importance": 1.8}`)
3. **المستند الثالث**: `"Transformers rely on self-attention mechanisms to weigh the importance of different words in a sequence."` (بيانات وصفية: `{"category": "deep_learning", "importance": 2.0}`)
4. **المستند الرابع**: `"Docker containers isolate applications from the host operating system using namespaces and cgroups."` (بيانات وصفية: `{"category": "docker", "importance": 1.2}`)

---

## 3. سيناريو تشغيل البذر التلقائي

* يتم توفير سكربت بذر تلقائي `ai_project/utils/seed_db.py` يتم استدعاؤه تلقائياً في بيئات التطوير والاختبار للتأكد من جاهزية البيانات وعدم إقلاع الواجهات بصناديق فارغة.
* يتحقق السكربت من عدم وجود بيانات مسبقة لمنع تكرار الإدخال والمحافظة على تماسك قاعدة البيانات.
