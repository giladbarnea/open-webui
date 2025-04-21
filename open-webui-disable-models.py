import requests
import re
import json
import sys

# --- Configuration ---
BASE_URL = "http://localhost:8080"
# WARNING: Hardcoding tokens is generally insecure. Consider environment variables or a config file.
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImJmNTY4MDFlLTNmNzItNDhlMy04MGJkLWMzMmIzYzE3NmUxYiJ9.nKqwdgi127wRn3bJWR-3WWHx7LzDpWP9BwgyFFDeVHY"

# --- Regex Pattern (derived from the grep command) ---
# Note: This pattern finds models TO DISABLE (matching the grep list),
# which is the opposite of the grep command's -v (invert match) behavior.
# The grep command filters OUT these models, we want to find them.
DISABLE_PATTERNS = [
    r'distill',
    r'claude(\.|-)2',
    r'claude(\.|-)3(\.|-)[a-zA-Z]', # Note: Corrected regex slightly for clarity
    r'claude(\.|-)3(\.|-)5',
    r'gpt.?4(-| )',
    r'4o.?mini',
    r'gpt.?3(\.|-)5',
    r'gemini.*-1(\.|-)5',
    r'llama',
    r'deepseek-chat',
    r'sonar$',
    r'01-ai',
    r'aetherwing', # Corrected typo from grep example 'aetherwiing'
    r'ai21',
    r'aion-labs',
    r'allenai',
    r'alpindale',
    r'amazon',
    r'anthropic-org', # Corrected typo from grep example 'anthracite-org'
    r'bytedance-research',
    r'cognitivecomputations',
    r'cohere',
    r'eva-unit-01',
    r'featherless',
    r'gemma',
    r'gryphe',
    r'huggingface',
    r'infermatic',
    r'inflection',
    r'jondurbin',
    r'liquid',
    r'mancer', # Corrected typo from grep example '-emancer'
    r'phi-3',
    r'minimax',
    r'mistralai',
    r'moonshotai',
    r'neversleep',
    r'nothingisreal',
    r'nousresearch',
    r'open-r1',
    r'openchat',
    r'openrouter/auto',
    r'pygmalionai',
    r'qwen',
    r'raifle',
    r'rekaai',
    r'sao10k',
    r'sophosympatheia',
    r'steelskull',
    r'teknium',
    r'thedrummer',
    r'undi95',
    r'xwin-lm'
]
# Combine patterns with OR '|' and compile for case-insensitive matching
DISABLE_REGEX = re.compile('|'.join(DISABLE_PATTERNS), re.IGNORECASE)

# --- API Endpoints ---
GET_MODELS_URL = f"{BASE_URL}/api/models"
# Using the create endpoint for updates as shown in the example
UPDATE_MODEL_URL = f"{BASE_URL}/api/v1/models/create"

# --- Headers ---
COMMON_HEADERS = {
    "accept": "application/json",
    "authorization": f"Bearer {AUTH_TOKEN}",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "content-type": "application/json", # Needed for POST
    # Add other headers from example if strictly necessary, but these are key
}

# --- Functions ---

def get_all_models():
    """Fetches the list of all models from the API."""
    print(f"Fetching models from {GET_MODELS_URL}...")
    headers = {**COMMON_HEADERS}
    # Content-Type not needed for GET
    headers.pop("content-type", None)
    try:
        response = requests.get(GET_MODELS_URL, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        # The example response shows models directly in a 'data' array
        data = response.json()
        if 'data' in data and isinstance(data['data'], list):
             print(f"Successfully fetched {len(data['data'])} models.")
             return data['data']
        else:
            print("Error: Unexpected response format. 'data' key with a list not found.")
            print("Response:", json.dumps(data, indent=2))
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching models: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print("Response body:", e.response.text)
            except Exception:
                pass # Ignore if response body can't be read
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        print("Response text:", response.text)
        return None

def disable_model(model_data):
    """Sends a request to disable a specific model."""
    model_id = model_data.get('id')
    model_name = model_data.get('name')

    if not model_id or not model_name:
        print(f"Skipping model due to missing id or name: {model_data}")
        return False

    print(f"Attempting to disable model: ID='{model_id}', Name='{model_name}'...")

    # Construct the payload exactly as in the example
    payload = {
        "id": model_id,
        "name": model_name,
        "base_model_id": None, # Assuming default/null as per example
        "meta": {},            # Assuming default/empty as per example
        "params": {},          # Assuming default/empty as per example
        "access_control": {},  # Assuming default/empty as per example
        "is_active": False     # The key change to disable the model
    }

    try:
        response = requests.post(
            UPDATE_MODEL_URL,
            headers=COMMON_HEADERS,
            json=payload # requests library handles json conversion and content-type
        )
        response.raise_for_status() # Check for HTTP errors

        # Assuming success on 2xx status code
        print(f"Successfully sent disable request for model '{model_name}' ({model_id}). Status: {response.status_code}")
        # You might want to check response.json() for confirmation if the API provides it
        # print("Response:", response.json())
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error disabling model '{model_name}' ({model_id}): {e}")
        if hasattr(e, 'response') and e.response is not None:
             try:
                print("Response status:", e.response.status_code)
                print("Response body:", e.response.text)
             except Exception:
                 pass # Ignore if response details can't be read
        return False
    except Exception as e:
        print(f"An unexpected error occurred while disabling model '{model_name}' ({model_id}): {e}")
        return False


# --- Main Execution ---
if __name__ == "__main__":
    all_models = get_all_models()

    if all_models is None:
        print("Could not retrieve models. Exiting.")
        sys.exit(1)

    models_to_disable = []
    print("\nFiltering models based on disable patterns...")
    for model in all_models:
        model_id = model.get('id', '')
        model_name = model.get('name', '')
        # Check if either id or name matches any of the disable patterns
        if DISABLE_REGEX.search(model_id) or DISABLE_REGEX.search(model_name):
            models_to_disable.append(model)
            # print(f"  Match found: ID='{model_id}', Name='{model_name}'") # Optional: uncomment for debug

    if not models_to_disable:
        print("\nNo models found matching the disable criteria.")
        sys.exit(0)

    print(f"\nFound {len(models_to_disable)} models matching the disable criteria:")
    for i, model in enumerate(sorted(models_to_disable, key=lambda x: x.get('name', ''))):
        print(f"  {i+1}. ID: {model.get('id', 'N/A')}, Name: {model.get('name', 'N/A')}")

    print("\n---")
    try:
        confirm = input("Do you want to disable all the models listed above? (yes/no): ").lower().strip()
    except EOFError: # Handle non-interactive environments
        confirm = 'no'
        print("\nNon-interactive environment detected or input aborted. Assuming 'no'.")


    if confirm in ['yes', 'y']:
        print("\nProceeding with disabling models...")
        disabled_count = 0
        failed_count = 0
        for model in models_to_disable:
            if disable_model(model):
                disabled_count += 1
            else:
                failed_count += 1
            # Optional: Add a small delay between requests if needed
            # import time
            # time.sleep(0.5)

        print(f"\n--- Disable Process Complete ---")
        print(f"Successfully sent disable requests for: {disabled_count} models.")
        print(f"Failed to send disable requests for:   {failed_count} models.")
        if failed_count > 0:
             print("Please check the error messages above for details on failures.")
    else:
        print("\nOperation cancelled by user. No models were disabled.")

    sys.exit(0)