import os
import argparse
import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env file.")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

def load_master_prompt(prompt_path):
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Master Prompt file not found at {prompt_path}")
        exit(1)

def list_models():
    print("Listing available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)

def generate_report(session, date_str, master_prompt):
    # list_models() # Uncomment to debug
    
    # Try a fallback list of models
    model_names = ['gemini-2.0-flash', 'gemini-1.5-flash-latest']
    
    model = None
    for name in model_names:
        try:
            print(f"Trying model: {name}")
            model = genai.GenerativeModel(name)
            break
        except Exception:
            continue
            
    if not model:
        print("Could not initialize any model.")
        return None
    
    # Construct the full prompt
    # We can inject specific session data here if needed, or rely on the model to fill/ask
    # For now, we will ask the model to generate a report based on the Master Prompt 
    # and the specific session context provided.
    
    user_instruction = f"""
    Please generate a **{session}** report for **{date_str}**.
    Use the guidelines and format provided in the MASTER PROMPT below.
    
    If real-time market data is not provided in this prompt, please use **PLAUSIBLE MOCK DATA** 
    that fits the 'Character' of the session described in the prompt (e.g., if Asian, low volume/ranging).
    Ensure the date and session match the request.
    
    **MASTER PROMPT:**
    {master_prompt}
    """
    
    print(f"Generating {session} report for {date_str}...")
    try:
        response = model.generate_content(user_instruction)
        return response.text
    except Exception as e:
        print(f"Error generating content: {e}")
        return None

def save_report(content, date_str, session):
    output_dir = os.path.join("content", "reports")
    os.makedirs(output_dir, exist_ok=True)
    
    # Sanitize filename
    safe_date = date_str.replace("/", "-")
    safe_session = session.replace(" ", "_")
    filename = f"{safe_date}_{safe_session}.md"
    filepath = os.path.join(output_dir, filename)
    
    # Add Frontmatter for the static site generator
    frontmatter = f"""---
title: "{session} Report - {date_str}"
date: "{date_str}"
type: "report"
session: "{session}"
---

"""
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter + content)
    
    print(f"Report saved to {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Generate Daily Gold Report")
    parser.add_argument("--session", type=str, required=True, choices=["Asian Wrap", "London Session"], help="Session name")
    parser.add_argument("--date", type=str, default=datetime.date.today().strftime("%Y-%m-%d"), help="Date of the report (YYYY-MM-DD)")
    parser.add_argument("--prompt_file", type=str, default="Master_Prompt.md", help="Path to Master Prompt file")
    
    args = parser.parse_args()
    
    master_prompt = load_master_prompt(args.prompt_file)
    content = generate_report(args.session, args.date, master_prompt)
    
    if content:
        save_report(content, args.date, args.session)

if __name__ == "__main__":
    main()
