import os
from dotenv import load_dotenv

def dump_env():
    # Attempt to load the exact same way as main.py
    config_path = "agent/agent_config.env"
    if os.path.exists(config_path):
        print(f"Found config at {config_path}")
        load_dotenv(config_path)
    else:
        print(f"Config NOT found at {config_path}")
        
    print(f"API_BASE_URL: {os.getenv('API_BASE_URL')}")
    print(f"AGENT_API_KEY: {os.getenv('AGENT_API_KEY')}")
    print(f"AGENT_CLIENT_ID: {os.getenv('AGENT_CLIENT_ID')}")

if __name__ == "__main__":
    dump_env()
