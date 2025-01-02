import yaml
from openai import OpenAI
from pathlib import Path

# Debug file paths
current_dir = Path.cwd()
config_path = current_dir / "config.yaml"
template_path = current_dir / "config.yaml.template"

print(f"Current directory: {current_dir}")
print(f"Config file exists: {config_path.exists()}")
print(f"Template file exists: {template_path.exists()}")

try:
    print(f"\nTrying to open: {config_path}")
    with open(config_path) as f:
        config = yaml.safe_load(f)
        print("\nConfig loaded successfully")
        print("Config keys:", list(config.keys()))
        # Print first few chars of each value securely
        for key in config:
            value = str(config[key])
            print(f"{key}: {value[:5]}...")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=config['openrouter_api_key']
    )

    print("\nMaking API request...")
    response = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": config['site_url'],
            "X-Title": config['app_name']
        },
        model="google/gemini-2.0-flash-exp:free",
        messages=[{"role": "user", "content": "Say hello"}]
    )
    print("\nAPI Response:", response.choices[0].message.content)

except Exception as e:
    print(f"\nError: {type(e).__name__}")
    print(f"Error message: {str(e)}")