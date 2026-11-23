# test_api.py
import openai, os
from dotenv import load_dotenv
load_dotenv()
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
resp = client.models.list()
print('API OK - modelos disponiveis:', len(list(resp)))
