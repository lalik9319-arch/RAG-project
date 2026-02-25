# 🦙 RAG - Agentic Coding Docs Explorer

מערכת RAG לתשאול קבצי תיעוד של כלי Agentic Coding (Windsurf, Copilot ועוד).

## 🗂️ מבנה הפרויקט
```
rag-project/
│
├── main.py            # נקודת כניסה — הרצה ויצירת תרשים זרימה
├── app.py             # ממשק Gradio + פונקציית הצ'אט
├── workflow.py        # לוגיקה מרכזית: טעינה, אינדקס, RAGWorkflow
├── models.py          # מודלי נתונים (Decision, Rule, WarningItem)
├── config.py          # הגדרות סביבה, NetFree, LLM
├── workflow_vis.html  # תרשים זרימה (נוצר אוטומטית)
│
├── lib/               # ספריות עזר
├── .env               # מפתחות API (לא להעלות ל-Git!)
├── .gitignore
└── requirements.txt
```


---

## 🚀 הרצה

### 1. התקנת תלויות
```bash
pip install -r requirements.txt
```

### 2. הגדרת מפתחות API
```bash
cp .env.example .env
# ערוך את .env והכנס את המפתחות שלך
```

### 3. עדכון נתיב הפרויקט
פתח את `.env` והוסף:
```
MY_PROJECT_PATH=C:\path\to\your\project
```

### 4. הרצה
```bash
python main.py
```

---

## 💬 דוגמאות לשאלות

**שאלות סמנטיות (חיפוש וקטורי):**
- "איך עובד ה-Full Screen?"
- "איזה אפקטים של אנימציה קיימים?"
- "מהן ההוראות העיקריות במסמך?"

**שאלות מובנות (חילוץ נתונים + Router):**
- "תן לי רשימה של כל ההחלטות הטכניות"
- "מה הכללים הקיימים בפרויקט?"
- "אילו אזהרות ורגישויות מוגדרות?"

---

## 🏗️ ארכיטקטורה

```
StartEvent
    │
    ▼
validate_query ──(קצר מדי)──► StopEvent
    │
    ▼
retrieve
    │
    ▼
validate_results ──(לא רלוונטי)──► StopEvent
    │
    ▼
router
    ├──(semantic)──► synthesize ──► StopEvent
    └──(structured)──► synthesize_structured ──► StopEvent
```

---

## 🔑 טכנולוגיות

| כלי | שימוש |
|-----|-------|
| LlamaIndex | Framework לRAG |
| Cohere | Embeddings (embed-multilingual-v3.0) |
| Pinecone | Vector Database |
| OpenAI GPT-4o-mini | LLM לתשובות וניתוב |
| Gradio | ממשק משתמש |
