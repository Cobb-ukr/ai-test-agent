# test_runner.py

import os
import sys
import tempfile
import subprocess
import requests
import re
from dotenv import load_dotenv

# Load Groq API key from .env
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def clean_llm_code(text: str) -> str:
    """
    Removes markdown fences and extra formatting from LLM output.
    Returns only valid executable Python test code.
    """
    # Remove markdown-style triple backticks (with or without language identifiers)
    text = re.sub(r"```(?:python)?", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()



def run_test_generation(user_code: str, func_name: str = "is_prime") -> dict:
    """
    Given a string of Python code, automatically generate test cases,
    execute them, and return test results along with generated code.
    """
    user_code_module_name = "user_code"

    # Prompt for the LLM
    prompt = f"""
    You are a Python testing assistant.

    Generate several **independent** PyTest test functions to test the following Python function.

    Please follow these strict formatting rules:
    -  Each test must be a separate function starting with: def test_...
    -  Do NOT include any markdown, comments, explanations, or separators.
    -  Do NOT use triple backticks or code fences.
    -  Do NOT repeat the original function.

    Start your output with:
    from user_code import {func_name}

    Function to test:
    {user_code}
    """


    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": prompt}]
    }

    # Send request to Groq
    response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers)
    response_json = response.json()

    #  FIX: Safely access model response
    raw_llm_output = response_json["choices"][0]["message"]["content"]

    #  Clean unwanted markdown
    cleaned_test_code_body = clean_llm_code(raw_llm_output)

    #  Prepend import to guarantee test file correctness
    full_test_code = f"from {user_code_module_name} import {func_name}\n\n{cleaned_test_code_body}"

    # Use a temp directory to safely isolate
    with tempfile.TemporaryDirectory() as temp_dir:
        code_path = os.path.join(temp_dir, f"{user_code_module_name}.py")
        test_path = os.path.join(temp_dir, "test_code.py")

        # Write user code
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(user_code)

        # Write test file
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(full_test_code)

        # Run tests safely in temp_dir
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_path, "--tb=short", "--no-header", "--disable-warnings"],
            cwd=temp_dir,
            capture_output=True,
            text=True
        )

        test_output = result.stdout

        # Extract summary
        summary_lines = [
            line for line in test_output.splitlines()
            if "passed" in line or "failed" in line or "error" in line
        ]
        summary = "\n".join(summary_lines)

    # Return everything back
    return {
        "generated_tests": full_test_code,
        "test_output": test_output,
        "summary": summary
    }

# For standalone debugging -> run this file in terminal
if __name__ == "__main__":
    sample_function = '''
def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
'''

    result = run_test_generation(sample_function)
    print("✅ Generated PyTest Code:\n")
    print(result["generated_tests"])
    print("\n📊 Test Summary:\n")
    print(result["summary"])
    print("\n🧪 Full PyTest Output:\n")
    print(result["test_output"])
