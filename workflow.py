import os
import glob
import json
from datetime import datetime
from typing import List

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.workflow import Workflow, StartEvent, StopEvent, Event, step
from llama_index.core.schema import NodeWithScore
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.utils.workflow import draw_all_possible_flows
from pinecone import Pinecone

from config import COHERE_API_KEY, PINECONE_API_KEY, MY_PROJECT_PATH
from models import ExtractedProjectData, Decision, Rule, WarningItem


# --- Events ---
class QueryEvent(Event):
    query: str

class RetrieveEvent(Event):
    nodes: List[NodeWithScore]
    query: str

class ExtractionEvent(Event):
    structured_data: ExtractedProjectData
    query: str

class ValidationEvent(Event):
    nodes: List[NodeWithScore]
    query: str


# --- Data Loading ---
def get_metadata_for_file(file_path):
    """
    פונקציית עזר שמוסיפה מטא-דאטה לכל קובץ.
    זה הסוד שיאפשר ל-LLM לענות על שאלות כמו: "מה ווינדסרף החליט?"
    """
    file_path_lower = file_path.lower()

    source_tool = "Unknown AI"
    if ".windsurf" in file_path_lower:
        source_tool = "Windsurf"
    elif ".copilot" in file_path_lower:
        source_tool = "Copilot"

    return {
        "file_name": os.path.basename(file_path),
        "source_tool": source_tool,
        "full_path": file_path,
        "category": "AI Documentation"
    }

def load_all_ai_docs(project_root):
    """
    הפונקציה המרכזית שטוענת את כל חומרי הגלם
    """
    print(f"🚀 מתחיל לסרוק את הפרויקט בכתובת: {project_root}")

    patterns = [
        os.path.join(project_root, ".windsurf", "**", "*.md"),
        os.path.join(project_root, ".copilot", "**", "*.md")
    ]

    all_files = []
    for pattern in patterns:
        found_files = glob.glob(pattern, recursive=True)
        all_files.extend(found_files)

    if not all_files:
        print("❌ לא נמצאו קבצי תיעוד! וודאי שהנתיב נכון ושיש קבצי .md בתיקיות הכלים.")
        return []

    print(f"🔍 נמצאו {len(all_files)} קבצי תיעוד. מתחיל בטעינה...")

    reader = SimpleDirectoryReader(
        input_files=all_files,
        file_metadata=get_metadata_for_file
    )

    documents = reader.load_data()

    print("✅ הטעינה הושלמה בהצלחה!")
    for doc in documents[:3]:
        print(f"📄 נטען קובץ: {doc.metadata['file_name']} | כלי: {doc.metadata['source_tool']}")

    return documents


# --- Indexing ---
def build_and_save_index(documents):
    parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    nodes = parser.get_nodes_from_documents(documents)
    print(f"✂️  המסמכים נחתכו ל-{len(nodes)} יחידות מידע (Nodes).")

    embed_model = CohereEmbedding(
        cohere_api_key=COHERE_API_KEY,
        model_name="embed-multilingual-v3.0",
    )

    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index_name = "memory-game-docs"

        pinecone_index = pc.Index(index_name)
        vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        index = VectorStoreIndex(nodes, storage_context=storage_context, embed_model=embed_model)
        print("✅ האינדקס נשמר בהצלחה ב-Pinecone!")

    except Exception as e:
        print(f"⚠️ שגיאה בחיבור ל-Pinecone: {e}")
        print("⏳ עובר למצב זיכרון מקומי (Local Index)...")
        index = VectorStoreIndex(nodes, embed_model=embed_model)
        print("✅ האינדקס מוכן לשימוש זמני בזיכרון!")

    return index


# --- Extraction ---
async def extract_structured_data(nodes):
    prompt_template_str = """
    עבור קטעי הטקסט הבאים מתוך תיעוד הפרויקט, חלץ את כל ההחלטות, הכללים והאזהרות.
    השתמש בעברית. לכל פריט, ציין גם מאיזה כלי ומאיזה קובץ הוא הגיע (מתוך ה-metadata).

    הטקסט (כולל metadata):
    {context_str}
    """

    program = LLMTextCompletionProgram.from_defaults(
        output_cls=ExtractedProjectData,
        prompt_template_str=prompt_template_str,
        llm=Settings.llm,
        verbose=True
    )

    context_str = "\n---\n".join([n.node.get_content() for n in nodes])

    structured_output = program(context_str=context_str)
    return structured_output

def save_extracted_data(data: ExtractedProjectData, path="extracted_data.json"):
    output = {
        "generated_at": datetime.now().isoformat(),
        "items": {
            "decisions": [d.dict() for d in data.decisions],
            "rules": [r.dict() for r in data.rules],
            "warnings": [w.dict() for w in data.warnings]
        }
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


# --- Build index on import ---
docs = load_all_ai_docs(MY_PROJECT_PATH)
index = build_and_save_index(docs)


# --- Workflow ---
class RAGWorkflow(Workflow):
    @step
    async def validate_query(self, ev: StartEvent) -> QueryEvent | StopEvent:
        query = ev.get("query")
        if not query or len(query) < 3:
            return StopEvent(result="השאלה קצרה מדי.")
        return QueryEvent(query=query)

    @step
    async def retrieve(self, ev: QueryEvent) -> ValidationEvent:
        retriever = index.as_retriever(similarity_top_k=3)
        nodes = retriever.retrieve(ev.query)
        return ValidationEvent(nodes=nodes, query=ev.query)

    @step
    async def validate_results(self, ev: ValidationEvent) -> RetrieveEvent | StopEvent:
        """ולידציה: בודק אם המידע רלוונטי לפני שממשיכים לניתוב"""
        if not ev.nodes or ev.nodes[0].score < 0.35:
            return StopEvent(result="לא מצאתי מידע מספיק רלוונטי בתיעוד.")
        return RetrieveEvent(nodes=ev.nodes, query=ev.query)

    @step
    async def router(self, ev: RetrieveEvent) -> RetrieveEvent | ExtractionEvent:
        routing_prompt = f"""
        השאלה הבאה מחייבת איזה סוג חיפוש?
        שאלה: "{ev.query}"
        
        ענה ONLY עם מילה אחת:
        - "semantic" — אם השאלה מחפשת הסבר/תיאור/מידע כללי
        - "structured" — אם השאלה מחפשת רשימה, החלטות, כללים, אזהרות, עדכניות
        """
        decision = await Settings.llm.acomplete(routing_prompt)
        if "structured" in str(decision).lower():
            structured_data = await extract_structured_data(ev.nodes)
            return ExtractionEvent(structured_data=structured_data, query=ev.query)
        return ev

    @step
    async def synthesize(self, ev: RetrieveEvent) -> StopEvent:
        postprocessor = SimilarityPostprocessor(similarity_cutoff=0.4)
        filtered_nodes = postprocessor.postprocess_nodes(ev.nodes)
        summarizer = get_response_synthesizer(response_mode="compact")
        response = summarizer.synthesize(ev.query, nodes=filtered_nodes)
        return StopEvent(result=str(response))

    @step
    async def synthesize_structured(self, ev: ExtractionEvent) -> StopEvent:
        """עיצוב הנתונים שחולצו לרשימה קריאה ב-Markdown"""
        data = ev.structured_data

        if not any([data.decisions, data.rules, data.warnings]):
            return StopEvent(result="לא מצאתי החלטות או כללים מוגדרים בקטעי הטקסט הרלוונטיים.")

        res = "## 📊 סיכום נתונים מובנים מהתיעוד\n\n"

        if data.decisions:
            res += "### ✅ החלטות טכניות\n"
            for d in data.decisions:
                res += f"- **{d.title}**: {d.summary} *(סטטוס: {d.status})*\n"
            res += "\n"

        if data.rules:
            res += "### 📋 כללים והנחיות\n"
            for r in data.rules:
                res += f"- **[{r.scope}]** {r.rule}\n"
            res += "\n"

        if data.warnings:
            res += "### ⚠️ אזהרות ורגישויות\n"
            for w in data.warnings:
                res += f"- **{w.area}**: {w.message} *(חומרה: {w.severity})*\n"

        res += "\n---\n*המידע חולץ באופן אוטומטי מתוך מסמכי הפרויקט.*"
        return StopEvent(result=res)


# --- Init workflow ---
rag_workflow = RAGWorkflow(timeout=120, verbose=True)
