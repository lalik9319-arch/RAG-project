import os
from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

load_dotenv()

# --- NetFree ---
netfree_cert = os.getenv("NETFREE_CERT")

if os.path.exists(netfree_cert):
    os.environ['REQUESTS_CA_BUNDLE'] = netfree_cert
    os.environ['SSL_CERT_FILE'] = netfree_cert
    os.environ['HTTPS_CA_BUNDLE'] = netfree_cert
    os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = netfree_cert
    print("✅ תעודת נטפרי הוגדרה בהצלחה!")
else:
    print("❌ הקובץ עדיין לא נמצא. ודא שסיומת ה-crt. קיימת בנתיב.")

# --- API Keys ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
MY_PROJECT_PATH = os.getenv("MY_PROJECT_PATH")

# --- LLM ---
llm = OpenAI(api_key=OPENAI_API_KEY, model="gpt-4o-mini")
Settings.llm = llm
