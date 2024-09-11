import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Access the Groq API key
groq_api_key = os.getenv('GROQ_API_KEY')

def main():
    print("SRM TRP Chatbot")
    print(f"Groq API Key: {groq_api_key}")

if __name__ == "__main__":
    main()