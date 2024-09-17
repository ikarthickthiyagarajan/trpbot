import eventlet
eventlet.monkey_patch()
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from langchain_groq import ChatGroq
#from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Cassandra
import cassio
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

print("Initializing the bot")

app = Flask(__name__, static_folder='../build', static_url_path='')
CORS(app)

# Load environment variables from gapi.env
load_dotenv('SRM_TRP_Chatbot/gapi.env')

groq_api_key = os.getenv("GROQ_API_KEY")
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB")
ASTRA_DB_ID = os.getenv("ASTRA_DB_ID")
nvidia_key = os.getenv("NVIDIA_KEY")
print(f"NVIDIA_KEY: {nvidia_key}")

# Print environment variables for debugging
print(f"ASTRA_DB_APPLICATION_TOKEN: {ASTRA_DB_APPLICATION_TOKEN}")
print(f"ASTRA_DB_ID: {ASTRA_DB_ID}")

# Define env_path before using it
env_path = 'SRM_TRP_Chatbot/gapi.env'  # Update this path if necessary
print(f"Current working directory: {os.getcwd()}")
print(f"Env file path: {env_path}")
print(f"Env file exists: {os.path.exists(env_path)}")

# Initialize cassio and log the URL being accessed
try:
    logging.info("Initializing cassio with token: %s", ASTRA_DB_APPLICATION_TOKEN)
    cassio.init(token=ASTRA_DB_APPLICATION_TOKEN, database_id=ASTRA_DB_ID)
except Exception as e:
    logging.error("Error initializing cassio: %s", e)

# Initialize the embedding model first
try:
    logging.info("Initializing NVIDIA embeddings with key: %s", nvidia_key)
    embedding_model = NVIDIAEmbeddings(model="NV-Embed-QA")
except Exception as e:
    logging.error("Error initializing NVIDIA embeddings: %s", e)

# Then use it to initialize Cassandra
try:
    logging.info("Creating Cassandra vector store")
    astra_vector_store = Cassandra(
        embedding=embedding_model,
        table_name="test2",
        session=None,
        keyspace=None
    )
except Exception as e:
    logging.error("Error creating Cassandra vector store: %s", e)

astra_vector_index = VectorStoreIndexWrapper(vectorstore=astra_vector_store)

model_list = ["llama-3.1-70b-versatile", "llama3-70b-8192", "llama-3.1-8b-instant", "gemma2-9b-it", "mixtral-8x7b-32768"] 
llm = ChatGroq(groq_api_key=groq_api_key, model_name="llama-3.1-70b-versatile")

prompt = ChatPromptTemplate.from_template("""
/Instructions
"Provide accurate information about SRM TRP Engineering College."
"For detailed answers, guide users to specific sections like academics, research, placements, admissions, etc."
"Be polite and helpful in all responses.""")

# Set up retrieval chain
retriever = astra_vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 2})
document_chain = create_stuff_documents_chain(llm, prompt)
retrieval_chain = create_retrieval_chain(retriever, document_chain)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    user_input = request.json['message']
    model_name = request.json['model']
    logging.info("Chat request received with model: %s", model_name)

    try:
        llm = ChatGroq(groq_api_key=groq_api_key, model_name=model_name)
        document_chain = create_stuff_documents_chain(llm, prompt)
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        response = retrieval_chain.invoke({"input": user_input})
        return jsonify({"answer": response["answer"]})
    except Exception as e:
        logging.error("Error during chat processing: %s", e)
        return jsonify({"error": str(e)}), 500

print("app running")
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)