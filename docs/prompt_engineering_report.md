# تقرير هندسة وإدارة التوجيهات (Prompt Engineering Report) - Phoenix AI

يوضح هذا المستند تحليلاً تفصيلياً لهندسة التوجيهات (Prompts) المستخدمة لتوجيه نموذج الذكاء الاصطناعي في منصة **Phoenix AI** لضمان الكفاءة والأمان والجودة.

---

## 1. التوجيهات الأساسية للمنصة (Core System Prompts)

تم حصر وتصميم التوجيهات المستخدمة داخل مكونات الواجهة الخلفية لتوجيه المهام اللغوية المختلفة:

### أ. توجيه وكيل البرمجة والمساعد اللغوي (System Prompt)
* **المسار المستهدف**: `ai_project/agents/agent.py`
* **صيغة التوجيه المعتمدة**:
  ```text
  You are Phoenix AI, a highly capable local Python coding assistant.
  Your objective is to help developers write clean, efficient, and secure Python code.
  Always explain technical decisions clearly and write code solutions wrapped in execution tags if requested.
  ```

### ب. توجيه الإصلاح التلقائي للأكواد (Developer & Debugger Prompt)
* **المسار المستهدف**: `ai_project/agents/debugger.py`
* **صيغة التوجيه المعتمدة**:
  ```text
  You are an expert debugger. Analyze the file path, its content, and the provided error message.
  Generate the exact corrected code block to resolve the error. Avoid rewriting unchanged sections.
  Format your response as a valid JSON with keys: "status", "corrected_code", and "explanation".
  ```

### ج. توجيه حماية وتطهير المدخلات (Safety & Guardrail Prompt)
* **المسار المستهدف**: `ai_project/utils/security.py`
* **آلية التصفية**:
  تعتمد حماية المنصة ضد هجمات حقن الأوامر (Prompt Injection) على مطابقة الأنماط وحظر التوجيهات الالتفافية مثل (DAN, jailbreak, system override, instruction bypass) لمنع تسريب توجيه النظام الأساسي أو تشغيل أكواد خبيثة.

### د. توجيه ضغط الذاكرة وتلخيص السياق (Memory Compression Prompt)
* **المسار المستهدف**: `ai_project/memory/vector_db.py`
* **صيغة التوجيه المعتمدة**:
  ```text
  <|system|>
  You are a concise summarizer. Summarize key facts from the text in one short sentence.
  <|user|>
  Text to summarize:
  {text}
  <|assistant|>
  Summary:
  ```

---

## 2. إدارة وتطوير التوجيهات (Prompt Management & Evaluation)

لتحقيق الكفاءة المطلوبة في بيئات التطوير المتقدمة، تم رصد الفجوات الهندسية التالية في نظام التوجيه الحالي للمنصة:

### الفجوات المرصودة في هندسة البرومبت:
1. **غياب نظام إدارة النسخ (Prompt Versioning)**: يتم تضمين التوجيهات بشكل صلب (Hardcoded) في ملفات البايثون، مما يعوق تعديلها دون إعادة نشر الخدمة بالكامل.
2. **غياب قوالب التوجيه المنفصلة (Template Separation)**: لا يوجد ملف تكوين خارجي (مثل YAML أو JSON) لتنظيم وإدارة متغيرات التوجيهات بشكل مستقل عن المنطق.
3. **غياب التقييم الآلي للبرومبت (Prompt Testing & Eval)**: لا تتوفر المنصة حالياً على نصوص أو بيئة فحص لمقارنة جودة توليد النموذج عند تغيير صياغة التوجيه، مما يصعب كشف أي تراجع في دقة المخرجات.

### خطة التطوير المقترحة:
* **تخزين التوجيهات خارجياً**: إنشاء ملف `ai_project/api/prompts.json` لتجميع كافة التوجيهات وتسهيل تحديثها ديناميكياً.
* **إدراج اختبارات جودة الصياغة**: دمج فحص تلقائي لجودة توليد النموذج اللغوي ضمن خط الـ CI/CD للتأكد من توافق المخرجات مع معايير القبول.
