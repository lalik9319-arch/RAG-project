import gradio as gr
from llama_index.utils.workflow import draw_all_possible_flows

from workflow import rag_workflow


# --- Chat Function ---
async def chat_with_workflow(user_query, history):
    try:
        response = await rag_workflow.run(query=user_query)
        return str(response)

    except Exception as e:
        if "blockByNetFree" in str(e) or "418" in str(e):
            return "אופסס... נטפרי לא מרשה לי לדבר איתך על זה, לפרטים נוספים עיינו בקישור הזה <https://netfree.link/wiki/%D7%A6%D7%90%D7%98_AI_%D7%91%D7%A0%D7%98%D7%A4%D7%A8%D7%99>"
        return f"שגיאה בתהליך: {str(e)}"


# --- Gradio UI ---
demo = gr.ChatInterface(
    fn=chat_with_workflow,
    title="Memory Game - Agentic Workflow 🤖",
    description="מערכת RAG מונעת אירועים (Event-Driven) עם ולידציות חכמות",
    examples=[
        "מהן ההוראות העיקריות במסמך?",
        "איזה אפקטים של אנימציה קיימים?",
        "איך עובד ה-Full Screen?"
    ]
)
