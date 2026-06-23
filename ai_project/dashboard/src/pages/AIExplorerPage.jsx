import React, { useState, useEffect } from 'react';
import * as api from '../services/api';

export function AIExplorerPage({ isOnline, addToast }) {
  const [categories, setCategories] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState('');
  const [loading, setLoading] = useState(false);

  // Add Model Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newModel, setNewModel] = useState({
    category_id: 'gen_ai',
    name: '',
    developer: '',
    type: '',
    parameters: '',
    use_case: ''
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchAIData = async () => {
    setLoading(true);
    try {
      const res = await api.searchAITypes(searchQuery, selectedCategoryFilter);
      setCategories(res.categories || []);
    } catch (err) {
      addToast('فشل تحميل بيانات مستكشف الذكاء الاصطناعي: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAIData();
  }, [searchQuery, selectedCategoryFilter]);

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    if (!newModel.name.trim() || !newModel.developer.trim() || !newModel.type.trim() || !newModel.use_case.trim()) {
      addToast('يرجى ملء جميع الحقول المطلوبة.', 'error');
      return;
    }

    setSubmitting(true);
    try {
      await api.addAIModel(
        newModel.category_id,
        newModel.name,
        newModel.developer,
        newModel.type,
        newModel.parameters || 'غير محدد',
        newModel.use_case
      );
      addToast(`تمت إضافة النموذج "${newModel.name}" بنجاح!`, 'success');
      setIsModalOpen(false);
      setNewModel({
        category_id: 'gen_ai',
        name: '',
        developer: '',
        type: '',
        parameters: '',
        use_case: ''
      });
      fetchAIData();
    } catch (err) {
      addToast('فشل إضافة النموذج: ' + err.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', padding: '24px', gap: '20px', position: 'relative', zIndex: 1 }}>
      
      {/* Header Panel */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', direction: 'rtl' }}>
        <div>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>مستكشف ومصنف أنواع الذكاء الاصطناعي</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            تصفح، ابحث، وصنف أقسام ونماذج الذكاء الاصطناعي المختلفة وقدراتها التشغيلية.
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setIsModalOpen(true)}
          disabled={!isOnline}
        >
          ➕ إضافة نموذج جديد
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', direction: 'rtl', flexWrap: 'wrap' }}>
        {/* Search Input */}
        <div style={{ flex: 1, minWidth: '250px', position: 'relative' }}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="🔍 ابحث عن النماذج، المطورين، أو حالات الاستخدام..."
            style={{
              width: '100%',
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius)',
              color: 'var(--text-primary)',
              padding: '10px 14px',
              fontSize: '0.9rem',
              outline: 'none',
              textAlign: 'right'
            }}
          />
        </div>

        {/* Category Filter Tabs */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className={`btn ${selectedCategoryFilter === '' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setSelectedCategoryFilter('')}
            style={{ padding: '8px 14px', fontSize: '0.85rem' }}
          >
            الكل
          </button>
          <button
            className={`btn ${selectedCategoryFilter === 'gen_ai' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setSelectedCategoryFilter('gen_ai')}
            style={{ padding: '8px 14px', fontSize: '0.85rem' }}
          >
            التوليدي
          </button>
          <button
            className={`btn ${selectedCategoryFilter === 'nlp' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setSelectedCategoryFilter('nlp')}
            style={{ padding: '8px 14px', fontSize: '0.85rem' }}
          >
            اللغات NLP
          </button>
          <button
            className={`btn ${selectedCategoryFilter === 'computer_vision' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setSelectedCategoryFilter('computer_vision')}
            style={{ padding: '8px 14px', fontSize: '0.85rem' }}
          >
            الرؤية CV
          </button>
          <button
            className={`btn ${selectedCategoryFilter === 'reinforcement_learning' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setSelectedCategoryFilter('reinforcement_learning')}
            style={{ padding: '8px 14px', fontSize: '0.85rem' }}
          >
            التعزيزي RL
          </button>
        </div>
      </div>

      {/* Main Grid View */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '24px', direction: 'rtl' }}>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            جاري تحميل البيانات وتصنيفها...
          </div>
        ) : categories.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            لم يتم العثور على أي نماذج أو أقسام تطابق بحثك.
          </div>
        ) : (
          categories.map((cat) => (
            <div
              key={cat.id}
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius)',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px'
              }}
            >
              {/* Category Info */}
              <div>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--accent-1)' }}>{cat.name}</h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  {cat.description}
                </p>
              </div>

              {/* Models Table */}
              <div style={{ overflowX: 'auto', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'right', fontSize: '0.85rem' }}>
                  <thead>
                    <tr style={{ background: 'var(--bg-elevated)', borderBottom: '1px solid var(--border)' }}>
                      <th style={{ padding: '12px 14px', color: 'var(--text-primary)', fontWeight: 600 }}>اسم النموذج</th>
                      <th style={{ padding: '12px 14px', color: 'var(--text-primary)', fontWeight: 600 }}>المطور</th>
                      <th style={{ padding: '12px 14px', color: 'var(--text-primary)', fontWeight: 600 }}>النوع البنيوي</th>
                      <th style={{ padding: '12px 14px', color: 'var(--text-primary)', fontWeight: 600 }}>عدد المعلمات</th>
                      <th style={{ padding: '12px 14px', color: 'var(--text-primary)', fontWeight: 600 }}>حالة الاستخدام الرئيسية</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cat.models.length === 0 ? (
                      <tr>
                        <td colSpan="5" style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                          لا توجد نماذج مضافة في هذا القسم حالياً.
                        </td>
                      </tr>
                    ) : (
                      cat.models.map((model, idx) => (
                        <tr
                          key={idx}
                          style={{
                            borderBottom: idx < cat.models.length - 1 ? '1px solid var(--border)' : 'none',
                            background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)'
                          }}
                        >
                          <td style={{ padding: '12px 14px', fontWeight: 600, color: 'var(--text-primary)' }}>{model.name}</td>
                          <td style={{ padding: '12px 14px', color: 'var(--text-secondary)' }}>{model.developer}</td>
                          <td style={{ padding: '12px 14px', color: 'var(--text-secondary)' }}>
                            <span className="chip chip-cyan" style={{ fontSize: '0.75rem' }}>{model.type}</span>
                          </td>
                          <td style={{ padding: '12px 14px', fontFamily: 'var(--font-code)', color: 'var(--accent-2)' }}>{model.parameters}</td>
                          <td style={{ padding: '12px 14px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>{model.use_case}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Add Model Modal Form */}
      {isModalOpen && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            direction: 'rtl'
          }}
        >
          <div
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius)',
              width: '500px',
              maxWidth: '90%',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '20px',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>إضافة نموذج ذكاء اصطناعي جديد</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {/* Category Select */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>القسم المستهدف *</label>
                <select
                  value={newModel.category_id}
                  onChange={(e) => setNewModel(prev => ({ ...prev, category_id: e.target.value }))}
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--text-primary)',
                    padding: '8px 12px',
                    fontSize: '0.85rem',
                    outline: 'none'
                  }}
                >
                  <option value="gen_ai">الذكاء الاصطناعي التوليدي (Generative AI)</option>
                  <option value="nlp">معالجة اللغات الطبيعية (NLP)</option>
                  <option value="computer_vision">الرؤية الحاسوبية (Computer Vision)</option>
                  <option value="reinforcement_learning">التعلم التعزيزي (Reinforcement Learning)</option>
                </select>
              </div>

              {/* Model Name */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>اسم النموذج *</label>
                <input
                  type="text"
                  value={newModel.name}
                  onChange={(e) => setNewModel(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="مثال: GPT-5, Claude 3.5 Sonnet"
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--text-primary)',
                    padding: '8px 12px',
                    fontSize: '0.85rem',
                    outline: 'none'
                  }}
                  required
                />
              </div>

              {/* Developer */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>الجهة المطورة *</label>
                <input
                  type="text"
                  value={newModel.developer}
                  onChange={(e) => setNewModel(prev => ({ ...prev, developer: e.target.value }))}
                  placeholder="مثال: Anthropic, Google, Meta"
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--text-primary)',
                    padding: '8px 12px',
                    fontSize: '0.85rem',
                    outline: 'none'
                  }}
                  required
                />
              </div>

              {/* Type */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>النوع البنيوي *</label>
                <input
                  type="text"
                  value={newModel.type}
                  onChange={(e) => setNewModel(prev => ({ ...prev, type: e.target.value }))}
                  placeholder="مثال: Transformer Decoder, CNN"
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--text-primary)',
                    padding: '8px 12px',
                    fontSize: '0.85rem',
                    outline: 'none'
                  }}
                  required
                />
              </div>

              {/* Parameters */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>عدد المعلمات (Parameters)</label>
                <input
                  type="text"
                  value={newModel.parameters}
                  onChange={(e) => setNewModel(prev => ({ ...prev, parameters: e.target.value }))}
                  placeholder="مثال: 70B, 3B, 1.8T"
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--text-primary)',
                    padding: '8px 12px',
                    fontSize: '0.85rem',
                    outline: 'none'
                  }}
                />
              </div>

              {/* Use Case */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>حالة الاستخدام الرئيسية *</label>
                <textarea
                  value={newModel.use_case}
                  onChange={(e) => setNewModel(prev => ({ ...prev, use_case: e.target.value }))}
                  placeholder="صف بالتفصيل كيف يتم استخدام هذا النموذج في التطبيقات العملية..."
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--text-primary)',
                    padding: '8px 12px',
                    fontSize: '0.85rem',
                    outline: 'none',
                    resize: 'none',
                    height: '80px'
                  }}
                  required
                />
              </div>

              {/* Buttons */}
              <div style={{ display: 'flex', gap: '10px', marginTop: '10px', justifyContent: 'flex-start' }}>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submitting}
                >
                  {submitting ? 'جاري الإضافة...' : 'إضافة النموذج'}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setIsModalOpen(false)}
                  disabled={submitting}
                >
                  إلغاء
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
