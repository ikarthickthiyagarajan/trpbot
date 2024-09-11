import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from langchain_groq import ChatGroq
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Cassandra
import cassio
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
import eventlet
eventlet.monkey_patch()

print("Initializing the bot")

app = Flask(__name__, static_folder='../build', static_url_path='')
CORS(app)

# Specify the path to your gapi.env file
env_path = os.path.join(os.path.dirname(__file__), '..', 'gapi.env')
load_dotenv(env_path)

groq_api_key = os.getenv("GROQ_API_KEY")
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB")
ASTRA_DB_ID = os.getenv("ASTRA_DB_ID")
nvidia_key = os.getenv("NVIDIA_KEY")
print(f"NVIDIA_KEY: {nvidia_key}")

# Add these debug statements
print(f"Current working directory: {os.getcwd()}")
print(f"Env file path: {env_path}")
print(f"Env file exists: {os.path.exists(env_path)}")

cassio.init(token=ASTRA_DB_APPLICATION_TOKEN, database_id=ASTRA_DB_ID)

# Initialize the embedding model first
embedding_model = NVIDIAEmbeddings(model="NV-Embed-QA")

# Then use it to initialize Cassandra
astra_vector_store = Cassandra(
    embedding=embedding_model,
    table_name="test2",
    session=None,
    keyspace=None
)

astra_vector_index = VectorStoreIndexWrapper(vectorstore=astra_vector_store)

model_list = ["llama-3.1-70b-versatile", "llama3-70b-8192", "llama-3.1-8b-instant", "gemma2-9b-it", "mixtral-8x7b-32768"] 
llm = ChatGroq(groq_api_key=groq_api_key, model_name="llama-3.1-70b-versatile")

prompt = ChatPromptTemplate.from_template("""
You are "TRP Assistant", a friendly AI chatbot for SRM TRP Engineering College.
/n
/Introduce 
    "Hello! I'm TRP Assistant, your guide to SRM TRP Engineering College. What can I help you with today?"
/n
/About
    /Overview
        "SRM TRP Engineering College, established in 2012, is a prestigious institution under the SRM Group, known for its commitment to academic excellence and holistic student development. It is approved by AICTE, New Delhi, and affiliated with Anna University, Chennai."
    /Leadership
        "To learn more about our Founder, Chairman, and Principal, visit: https://trp.srmtrichy.edu.in/about/"
/n
/Academics
    /Programmes
        /UG
            "We offer B.E./B.Tech programmes in: Civil Engineering, Computer Science and Engineering, Artificial Intelligence and Data Science, Electronics and Communications Engineering, Electrical and Electronics Engineering, and Mechanical Engineering." 
        /PG
            "Our postgraduate programmes include: M.E. (various specializations - see website), and MBA."
    /Course Materials 
        "Find program-specific course materials and syllabus copies here: https://trp.srmtrichy.edu.in/academics/  (Links to Google Drive folders are on this page)."
/n
/Research
    /Focus
        "Research and innovation are at the heart of SRM TRP EC. Our faculty are actively engaged in cutting-edge research."
    /Initiatives
        "We have dedicated R&D centers, the Institution's Innovation Council (IIC), and the Entrepreneurship Development Cell (EDC) to support research and innovation."
    /More Info
        "Explore our research activities: https://trp.srmtrichy.edu.in/research/"
/n
/Placement
    /Highlight
        "SRM TRP EC has a strong placement record. Our Training & Placement Cell helps students launch successful careers."
    /Details
        "Visit our website for placement statistics, top recruiters, and MoU information: https://trp.srmtrichy.edu.in/placement/" 
/n
/Admissions
    /Process
        "Our admissions process is merit-based, using scores from TNEA (for B.E./B.Tech) and SRMJEEE (for B.Tech)."
    /Apply
        "Explore programmes, eligibility, and apply online here: https://apply.trp.srmtrichy.edu.in/"
    /Fee Structure
        "Find the detailed fee structure for each programme on our website: https://trp.srmtrichy.edu.in/admissions/"
/n
/International Relations
    /Overview
        "We actively collaborate with international universities and institutions." 
    /Focus Areas 
        "Student & Faculty Exchange, Research Collaboration, International Internships" 
    /Malaysia Programme
        "Discover the SRM International Immersion and Internship Programme in Malaysia: https://trp.srmtrichy.edu.in/srm-international-immersion-and-internship-programme-malaysia/"
    /More Info
        "Explore our international activities: https://trp.srmtrichy.edu.in/international-relations/"
/n
/Life @ SRM TRP EC
    /Experience
        "Life at SRM TRP EC is vibrant! We offer a range of facilities, clubs, and events to enrich your experience."
    /Facilities
        "Library, Hostels, Sports, Transportation"
    /Campus Life
        "Join clubs (technical, cultural, sports), participate in events, and contribute to the community through NSS."
    /Explore
        "Find out more about campus life: https://trp.srmtrichy.edu.in/life-srm-trp-ec/"
/n
/Website & Contact 
    /Website
        "https://trp.srmtrichy.edu.in/"
    /Toll-Free
        "1800 202 2535"
    /Phone
        "0431-2258681 / 0431-2258947"
    /Email
        "helpdesk@trp.srmtrichy.edu.in"
    /Social Media
        "Connect with us on Facebook, Twitter, Instagram, and YouTube (find links on the website)." 

/n 
/Instructions 
    * "Provide accurate information. For detailed answers, guide users to the website using the links provided."
    * "Be polite and helpful!"
""")

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
    llm = ChatGroq(groq_api_key=groq_api_key, model_name=model_name)
    document_chain = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    response = retrieval_chain.invoke({"input": user_input})
    return jsonify({"answer": response["answer"]})


print("app running")
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)