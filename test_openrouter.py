import yaml
from openai import OpenAI
from rich import print

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

openrouter_api_key=config['gemini_api_key']

client=OpenAI(api_key=openrouter_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")

response = client.chat.completions.create(
    model="gemini-2.0-flash-exp",
    n=1,
    messages=[{'role':'system', 'content':'You are a helpful assistant.'},
            {
            "role": "user",
            "content": "Explain to me how AI works"
        }]
)

print(response)
print(response.choices[0].message.content)