# خطة الاختبارات والتحقق الشاملة (Testing & QA Plan) - Phoenix AI

تحدد هذه الوثيقة استراتيجية الاختبار والتحقق الشاملة لمنصة **Phoenix AI** لضمان جودة الأكواد وخلوها من الأخطاء التشغيلية وصلاحيتها للعمل في البيئة الإنتاجية.

---

## 1. استراتيجية الاختبار وتغطية المكونات (Testing Strategy)

تم تقسيم وتوزيع خطة الاختبار على المستويات الأساسية التالية لضمان السلامة الكاملة:

### أ. اختبارات الوحدة (Unit Testing Plan)
* **الأداة المستخدمة**: `pytest` مع مكتبة المساعدة `pytest-anyio` لمعالجة الطلبات اللامركزية غير المتزامنة (Asynchronous).
* **المكونات المستهدفة**:
  * دوال المفسر والترجمة لـ Tokenizer في [test_tokenizer.py](file:///c:/Users/1/Desktop/7070/tests/test_tokenizer.py).
  * منطق النموذج الأساسي PhoenixTransformer وطبقات الاهتمام (Attention layers) في [test_model.py](file:///c:/Users/1/Desktop/7070/tests/test_model.py).
  * خوارزميات وإجراءات ضغط وتكثيف أوزان النموذج في [test_quantization.py](file:///c:/Users/1/Desktop/7070/tests/test_quantization.py).

### ب. اختبارات التكامل والواجهات (Integration & API Testing Plan)
* **المكونات المستهدفة**:
  * التحقق من عمل مسارات واجهات FastAPI بشكل كامل باستخدام `fastapi.testclient.TestClient`.
  * اختبار آليات الفحص الأمني ومنع الاختراق في [test_prompt_injection.py](file:///c:/Users/1/Desktop/7070/tests/test_prompt_injection.py) و [test_rag_poisoning.py](file:///c:/Users/1/Desktop/7070/tests/test_rag_poisoning.py).
  * التحقق من نقاط فحص الحياة والجاهزية ومقاييس الأداء لـ Prometheus في [test_health_api.py](file:///c:/Users/1/Desktop/7070/tests/test_health_api.py).

### ج. اختبارات السيناريوهات التشغيلية (Scenario & Workflow Testing)
* **المكونات المستهدفة**:
  * محاكاة دورة حياة الذاكرة الدلالية (الاستدعاء، الدمج، الأرشفة، والمسح) في [test_memory_lifecycle.py](file:///c:/Users/1/Desktop/7070/tests/test_memory_lifecycle.py).
  * محاكاة جدولة وكيل التنسيق وتنفيذ المهام التتابعية في [test_orchestrator.py](file:///c:/Users/1/Desktop/7070/tests/test_orchestrator.py).
  * فحص آليات الحماية داخل الـ Sandbox المعزول ومنع استدعاء الدوال المشبوهة في [test_sandbox_hardening.py](file:///c:/Users/1/Desktop/7070/tests/test_sandbox_hardening.py).

---

## 2. جدول الفحص ومعدل النجاح (Validation Metrics)

تتألف المنصة حالياً من **81 اختباراً آلياً متكاملاً** موزعة على كافة المكونات:
* **الأداة المستخدمة**: `pytest`
* **معيار القبول في CI/CD**: يجب أن تجتاز جميع الاختبارات بنسبة نجاح **100%** مع إيقاف البناء فوراً عند حدوث أي فشل مفاجئ.
* **الحالة التشغيلية الحالية**: جميع الاختبارات الـ 81 مجتازة بنجاح كامل وموثقة في التقارير السابقة.
