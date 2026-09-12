from dotenv import load_dotenv
import os 
import openai 

load_dotenv()

client = openai.OpenAI (
    base_url = "https://api.groq.com/openai/v1",
    api_key = os.environ.get("GROQ_API_KEY")
)
