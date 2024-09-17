import os
from langchain_groq import ChatGroq
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain.vectorstores.cassandra import Cassandra
import cassio
from langchain_community.document_loaders import WebBaseLoader
import bs4
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.indexes.vectorstore import VectorStoreIndexWrapper


from dotenv import load_dotenv
load_dotenv()

groq_api_key = os.environ.get("GROQ_API_KEY")

ASTRA_DB_APPLICATION_TOKEN = os.environ.get("ASTRA_DB")
ASTRA_DB_ID = os.environ.get("ASTRA_DB_ID")

cassio.init(token=ASTRA_DB_APPLICATION_TOKEN, database_id=ASTRA_DB_ID)

#WEBSITE LOADER
loader=WebBaseLoader(web_paths=("https://trp.srmtrichy.edu.in/",),
                     bs_kwargs=dict(parse_only=bs4.SoupStrainer(
                         class_=("gdlr-main-menu", "sf-with-ul", "menu-item", "menu-item-type-custom", "menu-item-object-custom",
    "faculty", "faculty-list", "course-material", "footer-wrapper", "footer-container", "footer-widget",
    "dl-submenu", "footer-links", "textwidget", "footer-bottom"))))


text_documents=loader.load()


#SPLIT LOADED TEXT
text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)

docs=text_splitter.split_documents(text_documents)

# embeddings=OllamaEmbeddings(model="mxbai-embed-large")
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings


nvidia_key = os.getenv("NVIDIA_KEY")

embeddings = NVIDIAEmbeddings(
  model="NV-Embed-QA", 
  api_key=nvidia_key,
  truncate="START" 
  )

astra_vector_store=Cassandra(
    embedding=embeddings,
    table_name="test3",
    session=None,
    keyspace=None
)

print("converted to vector")
astra_vector_store.add_documents(docs)
print("Inserted %i headlines." % len(docs))
astra_vector_index = VectorStoreIndexWrapper(vectorstore=astra_vector_store)
print("sent to db")