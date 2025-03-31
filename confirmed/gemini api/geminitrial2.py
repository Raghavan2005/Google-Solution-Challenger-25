import sys
import os
import google.generativeai as genai
import tkinter as tk
from tkinter import filedialog, scrolledtext

# Function to get the API key securely
def get_api_key():
    """Retrieves API key from environment variable."""
    api_key = "AIzaSyCCyDZCOn4jBW4QKlkiCZ0WMGVlgkiQm2I"  # Store API key as environment variable
    if not api_key:
        display_output("Error: GOOGLE_API_KEY environment variable not set.")
        sys.exit(1)
    return api_key

# Function to read Python files in a folder
def read_code_files(folder_path):
    """Reads and concatenates the content of all Python files in a folder."""
    all_code_content = ""

    if not os.path.exists(folder_path):
        display_output(f"Error: Folder '{folder_path}' does not exist.")
        return None

    python_files = [f for f in os.listdir(folder_path) if f.endswith(".py")]

    if not python_files:
        display_output(f"No Python files found in '{folder_path}'.")
        return None

    for filename in python_files:
        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                code_content = file.read()
                all_code_content += f"\n\n# --- {filename} ---\n{code_content}"
        except Exception as e:
            display_output(f"Error reading {filename}: {e}")

    return all_code_content

# Function to analyze code using Gemini AI
def analyze_code():
    """Fetches code from the selected folder and sends it to Gemini."""
    folder_path = folder_var.get()
    prompt = prompt_var.get()

    if not folder_path:
        display_output("Please select a folder.")
        return

    api_key = get_api_key()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro")

    code_content = read_code_files(folder_path)
    if not code_content:
        return

    full_prompt = f"Here is some Python code from multiple files:\n{code_content}\n\n{prompt}"

    try:
        response = model.generate_content(full_prompt)
        display_output(response.text)  # Display response in the UI
    except Exception as e:
        display_output(f"Error generating response: {e}")

# Function to display output in the text box
def display_output(text):
    """Displays the AI response in the output text area."""
    output_text.config(state=tk.NORMAL)
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, text)
    output_text.config(state=tk.DISABLED)

# Function to open a folder selection dialog
def select_folder():
    """Opens a dialog to select a folder and updates the folder path entry."""
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_var.set(folder_selected)

# Creating the UI
root = tk.Tk()
root.title("Python Code Analyzer with Gemini AI")
root.geometry("600x500")

# Folder selection
tk.Label(root, text="Select Folder Containing Python Files:").pack(pady=5)
folder_var = tk.StringVar()
folder_entry = tk.Entry(root, textvariable=folder_var, width=50)
folder_entry.pack(pady=5)
tk.Button(root, text="Browse", command=select_folder).pack(pady=5)

# Prompt input
tk.Label(root, text="Enter Your Prompt:").pack(pady=5)
prompt_var = tk.StringVar()
prompt_entry = tk.Entry(root, textvariable=prompt_var, width=50)
prompt_entry.pack(pady=5)

# Analyze button
tk.Button(root, text="Analyze Code", command=analyze_code).pack(pady=10)

# Output display
tk.Label(root, text="Gemini AI Response:").pack(pady=5)
output_text = scrolledtext.ScrolledText(root, width=70, height=15, wrap=tk.WORD)
output_text.pack(pady=5)
output_text.config(state=tk.DISABLED)

if __name__ == "_main_":
    root.mainloop()