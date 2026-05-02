import os
import sys
import re

def patch_pyresparser():
    print("Looking for pyresparser in site-packages...")
    site_packages_dir = None
    for path in sys.path:
        if 'site-packages' in path and 'venvapp' in path:
            site_packages_dir = path
            break
    
    if not site_packages_dir:
        # Fallback for Windows standard venv structure
        fallback_path = os.path.join(os.getcwd(), 'venvapp', 'Lib', 'site-packages')
        if os.path.exists(fallback_path):
            site_packages_dir = fallback_path

    if not site_packages_dir:
        print("Error: Could not find venvapp site-packages directory. Make sure you run this script with the virtual environment activated.")
        return

    resume_parser_path = os.path.join(site_packages_dir, 'pyresparser', 'resume_parser.py')
    utils_path = os.path.join(site_packages_dir, 'pyresparser', 'utils.py')

    # Patch resume_parser.py
    if os.path.exists(resume_parser_path):
        with open(resume_parser_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        old_str = "custom_nlp = spacy.load(os.path.dirname(os.path.abspath(__file__)))"
        new_str = "import en_core_web_sm\n        custom_nlp = en_core_web_sm.load()"
        
        if old_str in content:
            content = content.replace(old_str, new_str)
            with open(resume_parser_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Successfully patched resume_parser.py")
        else:
            print("ℹ️ resume_parser.py already patched or target string not found.")
    else:
        print(f"❌ Could not find {resume_parser_path}")

    # Patch utils.py
    if os.path.exists(utils_path):
        with open(utils_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # The extract_name function in pyresparser usually looks something like this:
        # def extract_name(nlp_text, matcher=None):
        #     pattern = [ ... ]
        #     ... return name
        
        # We will use regex to replace the whole function
        # It starts with 'def extract_name(' and ends before 'def extract_email('
        
        pattern = re.compile(r'def extract_name\(nlp_text, matcher.*?\):.*?def extract_mobile_number', re.DOTALL)
        
        new_function = """def extract_name(nlp_text, matcher=None):
    for ent in nlp_text.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None

def extract_mobile_number"""
        
        if re.search(pattern, content):
            content = re.sub(pattern, new_function, content)
            with open(utils_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Successfully patched utils.py (extract_name function)")
        else:
            print("ℹ️ utils.py already patched or extract_name function not found in expected format.")
    else:
        print(f"❌ Could not find {utils_path}")

if __name__ == "__main__":
    patch_pyresparser()
