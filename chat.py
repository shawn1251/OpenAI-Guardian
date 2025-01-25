from openai import OpenAI
import yaml
import logging
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load configuration from a YAML file
with open('./config.yml', 'r') as file:
    config = yaml.safe_load(file)

# Extract API key and base URL from the configuration
openai_api_key = config.get('API_KEY', 'EMPTY')
mitmproxy_url = config.get('MITMPROXY')


# Log the configuration content
logger.info("Configuration loaded: %s", config)

client = OpenAI(
    api_key=openai_api_key,
    base_url=mitmproxy_url,
)

chat_response = client.chat.completions.create(
    model = "gpt-4o-mini",
    messages=[
        {"role": "user", "content": "say hi"},
    ]
)
print("Chat response:", chat_response)