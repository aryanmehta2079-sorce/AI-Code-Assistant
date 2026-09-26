import os
import json
import re
import streamlit as st
from dotenv import load_dotenv

# ============================================================
# 1. PAGE CONFIG MUST BE THE VERY FIRST STREAMLIT CALL
# ============================================================
st.set_page_config(
    page_title="AI Code Assistant",
    page_icon="💻",
    layout="wide"
)

# ============================================================
# 2. RENDER UI HEADER IMMEDIATELY (Prevents Blank Screen)
# ============================================================
st.title("💻 AI Code Assistant")
st.caption("Powered by Python + Streamlit + Groq LLM")

# ============================================================
# 3. ENVIRONMENT & API INITIALIZATION
# ============================================================
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY or API_KEY == "your_groq_api_key_here":
    st.warning("⚠️ GROQ_API_KEY is missing or not configured.")
    st.info("Please open your `.env` file and set `GROQ_API_KEY=gsk_your_actual_key_here`, then refresh this page.")
    st.stop()

# Initialize Groq client inside try-except to catch connection/import errors safely
try:
    from groq import Groq
    client = Groq(api_key=API_KEY)
    MODEL = "openai/gpt-oss-120b"
except Exception as e:
    st.error(f"Failed to initialize Groq client: {e}")
    st.stop()

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def parse_json_response(content):
    content = content.strip()
    content = re.sub(r"^```json\s*", "", content, flags=re.IGNORECASE)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            json_text = content[start:end + 1]
            return json.loads(json_text)
        raise ValueError("The AI returned an invalid response structure. Please try again.")

def generate_code(prompt_text, language):
    prompt = f"""You are an expert lead software developer.
Generate clean, production-ready code in {language} based on the request.
Return strictly valid JSON with this structure:
{{
    "code": "your code here",
    "explanation": "high-level summary of implementation",
    "time_complexity": "e.g., O(N)",
    "space_complexity": "e.g., O(1)",
    "key_features": ["feature 1", "feature 2"],
    "dependencies": ["library1", "library2"]
}}

Request:
{prompt_text}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a code generation assistant. Return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return parse_json_response(response.choices[0].message.content)

def explain_code(code_snippet, language):
    prompt = f"""You are an expert technical instructor.
Explain the following {language} code snippet in simple, structured terms.
Return strictly valid JSON with this structure:
{{
    "summary": "High level purpose of the code",
    "step_by_step": ["Step 1 explanation", "Step 2 explanation"],
    "time_complexity": "e.g., O(N log N)",
    "space_complexity": "e.g., O(N)",
    "key_concepts": ["concept 1", "concept 2"]
}}

Code:
{code_snippet}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are an expert code explainer. Return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return parse_json_response(response.choices[0].message.content)

def fix_bugs(code_snippet, error_log, language):
    err_text = error_log if error_log else "None"
    prompt = f"""You are a senior code auditor and security reviewer.
Analyze the following {language} code for bugs, logic errors, syntax mistakes, and security vulnerabilities.
Return strictly valid JSON with this structure:
{{
    "bugs_found": ["Bug 1 description", "Bug 2 description"],
    "fixed_code": "Complete refactored and working code",
    "explanation": "Summary of changes made",
    "security_warnings": ["Warning 1 or None"]
}}

Error Log (if provided):
{err_text}

Code:
{code_snippet}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a bug-fixing assistant. Return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return parse_json_response(response.choices[0].message.content)

def generate_docs(code_snippet, language):
    prompt = f"""You are a technical writer and developer advocate.
Generate documentation for the following {language} code.
Return strictly valid JSON with this structure:
{{
    "documented_code": "Code with inline comments and standard docstrings added",
    "overview": "Module/Script functional overview",
    "function_signatures": ["func1(param1: type) -> return_type"],
    "usage_example": "Example snippet showing how to invoke the code",
    "readme_md": "Markdown string formatted for a README file"
}}

Code:
{code_snippet}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a technical documentation assistant. Return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return parse_json_response(response.choices[0].message.content)

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
with st.sidebar:
    st.header("⚙️ Settings")
    mode = st.radio(
        "Select Operation Mode",
        [
            "Code Generator",
            "Explain Logic",
            "Fix Bugs & Refactor",
            "Write Documentation"
        ]
    )
    st.divider()
    language = st.selectbox(
        "Target Language",
        ["Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust", "SQL", "HTML/CSS"]
    )

# ============================================================
# MODE ROUTING
# ============================================================
st.subheader(f"Mode: {mode} ({language})")

if mode == "Code Generator":
    user_prompt = st.text_area("Describe what code you want to build:", height=150)
    if st.button("Generate Code", type="primary", use_container_width=True):
        if not user_prompt.strip():
            st.warning("Please enter a description.")
        else:
            with st.spinner("Generating code..."):
                try:
                    res = generate_code(user_prompt, language)
                    st.session_state["gen_result"] = res
                except Exception as e:
                    st.error(f"Error: {e}")

    if "gen_result" in st.session_state:
        res = st.session_state["gen_result"]
        st.divider()
        col1, col2 = st.columns(2)
        col1.metric("Time Complexity", res.get("time_complexity", "N/A"))
        col2.metric("Space Complexity", res.get("space_complexity", "N/A"))
        st.code(res.get("code", ""), language=language.lower())
        st.write("**Explanation:**", res.get("explanation", ""))

elif mode == "Explain Logic":
    code_input = st.text_area("Paste code to explain:", height=200)
    if st.button("Explain Logic", type="primary", use_container_width=True):
        if not code_input.strip():
            st.warning("Please paste code.")
        else:
            with st.spinner("Analyzing code..."):
                try:
                    res = explain_code(code_input, language)
                    st.session_state["explain_result"] = res
                except Exception as e:
                    st.error(f"Error: {e}")

    if "explain_result" in st.session_state:
        res = st.session_state["explain_result"]
        st.divider()
        st.info(res.get("summary", ""))
        for idx, step in enumerate(res.get("step_by_step", []), 1):
            st.write(f"**{idx}.** {step}")

elif mode == "Fix Bugs & Refactor":
    col_c, col_e = st.columns([2, 1])
    code_input = col_c.text_area("Buggy Code:", height=200)
    error_input = col_e.text_area("Error Log (Optional):", height=200)
    if st.button("Fix Bugs", type="primary", use_container_width=True):
        if not code_input.strip():
            st.warning("Please paste code.")
        else:
            with st.spinner("Auditing code..."):
                try:
                    res = fix_bugs(code_input, error_input, language)
                    st.session_state["fix_result"] = res
                except Exception as e:
                    st.error(f"Error: {e}")

    if "fix_result" in st.session_state:
        res = st.session_state["fix_result"]
        st.divider()
        for b in res.get("bugs_found", []):
            st.error(f"❌ {b}")
        st.code(res.get("fixed_code", ""), language=language.lower())
        st.write(res.get("explanation", ""))

elif mode == "Write Documentation":
    code_input = st.text_area("Paste code to document:", height=200)
    if st.button("Generate Docs", type="primary", use_container_width=True):
        if not code_input.strip():
            st.warning("Please paste code.")
        else:
            with st.spinner("Writing documentation..."):
                try:
                    res = generate_docs(code_input, language)
                    st.session_state["doc_result"] = res
                except Exception as e:
                    st.error(f"Error: {e}")

    if "doc_result" in st.session_state:
        res = st.session_state["doc_result"]
        st.divider()
        st.write(res.get("overview", ""))
        st.code(res.get("documented_code", ""), language=language.lower())