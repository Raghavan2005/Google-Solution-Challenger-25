import sys
import google.generativeai as genai
from google.generativeai import types
import os
print(f"Library version from inside script: {genai.__version__}")

def cache_code_files(folder_path):
    """Caches the content of all Python files in a folder."""

    api_key = os.environ.get("AIzaSyCCyDZCOn4jBW4QKlkiCZ0WMGVlgkiQm2I")  # Get API key from environment variable
    print(f"API Key from environment: {api_key}") # add this line.
    if api_key is None:
        print("Error: AIzaSyCCyDZCOn4jBW4QKlkiCZ0WMGVlgkiQm2I environment variable not set.")
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro") # change to a stable model

    all_code_content = ""
    for filename in os.listdir(folder_path):
        if filename.endswith(".py"):  # Only process Python files
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    code_content = file.read()
                    all_code_content += f"\n\n--- {filename} ---\n{code_content}"
            except Exception as e:
                print(f"Error reading {filename}: {e}")

    if all_code_content:
        try:
            response = model.create_cached_content(
                contents=all_code_content,
                display_name="code_file_cache"
            )
            cache_name = response.name
            print(f"Code files cached successfully. Cache name: {cache_name}")
            return cache_name
        except Exception as e:
            print(f"Error creating cache: {e}")
            return None
    else:
        print("No Python files found in the specified folder.")
        return None

def use_cached_code(cache_name, prompt):
    """Uses the cached code in a prompt."""
    api_key = os.environ.get("AIzaSyCCyDZCOn4jBW4QKlkiCZ0WMGVlgkiQm2I")
    if api_key is None:
        print("Error: AIzaSyCCyDZCOn4jBW4QKlkiCZ0WMGVlgkiQm2I environment variable not set.")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro") # change to a stable model


    if cache_name:
        try:
            response = model.generate_content(
                prompt,
                generation_config=types.GenerateContentConfig(cached_content=cache_name)
            )
            print(response.text)
        except Exception as e:
            print(f"Error using cache: {e}")
    else:
        print("No cache name provided.")

# Example usage:
folder_path = r"C:\Users\drivi\gdsc prog files\Google-Solution-Challenger-25\confirmed" #raw string to prevent backslash issues.

cache_name = cache_code_files(folder_path)
if cache_name:
    prompt = "Explain the overall functionality of the code in the cache."
    use_cached_code(cache_name, prompt)
