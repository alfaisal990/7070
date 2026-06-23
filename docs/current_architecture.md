# Phoenix AI - البنية المعمارية الحالية

## نظرة عامة
منصة ذكاء اصطناعي محلية مبنية على Python/FastAPI + React/Vite

## المكونات الأساسية

### Backend (Python/FastAPI)
| الوحدة | الملف | الوصف |
|--------|-------|-------|
| API Server | `ai_project/api/main.py` (817 سطر) | FastAPI - 22 نقطة وصول |
| Monitoring | `ai_project/api/monitoring.py` | مقاييس الأداء |
| AI Data | `ai_project/api/ai_data.json` | بيانات مستكشف الذكاء الاصطناعي |

### Agents
| الوكيل | الملف | الوظيفة |
|--------|-------|---------|
| Agent | `agents/agent.py` | منفذ المهام الرئيسي |
| Orchestrator | `agents/orchestrator.py` | منسق متعدد الوكلاء |
| Debugger | `agents/debugger.py` | مصحح الأخطاء التلقائي |
| Refactor | `agents/refactor.py` | إعادة هيكلة الكود |
| Sandbox | `agents/sandbox.py` | تنفيذ كود معزول |

### Memory & RAG
| المكون | الملف | الوصف |
|--------|-------|-------|
| Vector DB | `memory/vector_db.py` (21KB) | تخزين متجهي - JSON |
| RAG Pipeline | `memory/rag.py` | خط أنابيب RAG |
| Memory DB | `memory/memory_db.json` (574KB) | قاعدة البيانات - ملف JSON |

### Models & Inference
| المكون | الملف | الوصف |
|--------|-------|-------|
| Transformer | `models/model.py` (17KB) | نموذج Phoenix-54M |
| Engine | `inference/engine.py` | محرك الاستنتاج + KV Cache |
| Tokenizer | `tokenizer/tokenizer_trainer.py` | مدرب المحول اللغوي |

### Frontend (React/Vite)
| المكون | الملف | الوصف |
|--------|-------|-------|
| App | `dashboard/src/App.jsx` | التطبيق الرئيسي |
| Sidebar | `components/Sidebar.jsx` | القائمة الجانبية |
| MessageRenderer | `components/MessageRenderer.jsx` | عارض الرسائل |

### الصفحات (6 صفحات)
- ChatPage, SandboxPage, MemoryPage, DebuggerPage, RefactorPage, AIExplorerPage

### Hooks (7 hooks)
- useChat, useSandbox, useMemory, useDebugger, useRefactor, useHealth, useToast

### Utils
| الأداة | الملف |
|--------|-------|
| Security | `utils/security.py` - كشف حقن البرومبت |
| Path Safety | `utils/path_safety.py` - حماية المسارات |
| Backup | `utils/backup.py` - نسخ احتياطي ذري |
| Logging | `utils/logging.py` - تسجيل JSON منظم |
| Restore | `utils/restore.py` - استعادة النسخ |

### API Routes (22 نقطة وصول)
| Method | Route | Auth |
|--------|-------|------|
| GET | /api/health | ❌ |
| GET | /api/health/liveness | ❌ |
| GET | /api/health/readiness | ❌ |
| POST | /api/chat | ❌ |
| GET | /api/chat/stream | ❌ |
| GET | /api/monitoring/metrics | ❌ |
| GET | /metrics | ❌ |
| POST | /api/memory/upload | ❌ |
| POST | /api/sandbox/run | ❌ |
| GET | /api/memory | ❌ |
| POST | /api/memory/add | ❌ |
| POST | /api/memory/search | ❌ |
| DELETE | /api/memory/clear | ❌ |
| GET | /api/agent/debug/scan | ❌ |
| POST | /api/agent/debug/repair | ❌ |
| POST | /api/agent/refactor | ❌ |
| POST | /api/evaluate | ❌ |
| POST | /api/agent/orchestrate | ❌ |
| POST | /api/evaluate/benchmarks | ❌ |
| POST | /api/model/quantize | ❌ |
| POST | /api/memory/consolidate | ❌ |
| POST | /api/admin/backup | ❌ |
| GET | /api/ai_explorer/search | ❌ |
| POST | /api/ai_explorer/add | ❌ |

### Tests (43 ملف اختبار)
- 81 اختبار ناجح بالكامل

### DevOps
- Docker Compose + Dockerfile.backend + Dockerfile.frontend + nginx.conf
- GitHub Actions CI (lint → test → build)
