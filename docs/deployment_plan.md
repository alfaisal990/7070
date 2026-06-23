# خطة ونظام النشر الإنتاجي (Deployment & Infrastructure Plan) - Phoenix AI

تحدد هذه الوثيقة متطلبات وخطط نشر منصة **Phoenix AI** في البيئة الإنتاجية الفعلية باستخدام تقنيات الحاويات، وإدارة الحشود (Kubernetes)، وبوابات التمرير العكسية.

---

## 1. خطة النشر باستخدام Docker Compose (Docker Compose Deployment)

تعتبر هذه الخطة الأنسب للبيئات المحلية وخوادم النشر الافتراضية الفردية (VPS):
* **الملف المستخدم**: [docker-compose.yml](file:///c:/Users/1/Desktop/7070/docker-compose.yml)
* **الخدمات**:
  * `backend`: يبني الحاوية من [Dockerfile.backend](file:///c:/Users/1/Desktop/7070/Dockerfile.backend) ويفتح منفذ الاستماع `8000`.
  * `frontend`: يبني الحاوية من [Dockerfile.frontend](file:///c:/Users/1/Desktop/7070/Dockerfile.frontend) ويفتح المنفذ `80` للعملاء.
* **التخزين الدائم (Volume Mounts)**: دمج مجلدات أوزان النماذج والذاكرة المتجهية RAG خارج الحاويات لضمان بقائها عند البناء الجديد.

---

## 2. معمارية النشر عبر Kubernetes و Helm (Enterprise Kubernetes Architecture)

عند الانتقال لبيئات النشر المؤسسية الكبرى ذات الأحمال العالية، يتم التخلي عن Docker Compose واعتماد معمارية **Kubernetes**:

### أ. مخطط المكونات والخدمات في Kubernetes:
* **خدمة الواجهة الخلفية (Backend Deployment)**:
  * تشغيل عدة نسخ متكررة (Replicas) من حاوية بايثون خلف خدمة داخلية من نوع `ClusterIP`.
  * استخدام مجلدات تخزين مشتركة دائمة (Persistent Volume Claims - PVC) من النوع ReadWriteMany لمشاركة أوزان النماذج والذاكرة المتجهية.
  * تضمين فحوصات الصحة والجاهزية (Readiness & Liveness probes) المتصلة بـ `/api/health/readiness` و `/api/health/liveness`.
* **خدمة الواجهة الأمامية (Frontend Deployment)**:
  * تشغيل حاويات Nginx لخدمة ملفات الواجهة مع توجيه الطلبات لخدمة الواجهة الخلفية.
* **متحكم الدخول (Ingress Controller)**:
  * إدارة وتوجيه المرور الخارجي (HTTPS) باستخدام شهادات تشفير TLS المدارة تلقائياً وتوزيع الأحمال.

### ب. هيكل حزم Helm (Helm Chart Structure)
لتسهيل النشر والترقية وإدارة المتغيرات البيئية لبيئات التطوير والاختبار والإنتاج، يتم تنظيم حزم Helm كالتالي:
```text
phoenix-ai-chart/
  ├── Chart.yaml             # معلومات الحزمة والإصدار
  ├── values.yaml            # المتغيرات البيئية الافتراضية
  ├── templates/
  │     ├── backend-deploy.yaml   # إعداد تشغيل الواجهة الخلفية
  │     ├── backend-svc.yaml      # شبكة الواجهة الخلفية
  │     ├── frontend-deploy.yaml  # إعداد تشغيل الواجهة الأمامية
  │     ├── ingress.yaml          # قواعد متحكم الدخول والتوجيه
  │     └── pvc.yaml              # حجز مساحات التخزين المشتركة
```
