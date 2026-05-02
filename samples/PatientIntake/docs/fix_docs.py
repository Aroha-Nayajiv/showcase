import os
import re

docs_dir = "/Users/vijayan/work/devai/devai/projects/PatientIntake/deliverables/docs"

error_string = "{'status': 'error', 'error': 'All micro-goals failed', 'failed_micro_goals': [{'micro_goal_id': 'auto_goal_1', 'description': 'Consolidate executor content with reviewer feedback into a single coherent artifact artifact. Apply all reviewer improvements while preserving all original content, IDs, and structure. Do not create summaries - enhance and integrate intelligently.', 'result': {'status': 'error', 'error': 'No content generated'}, 'status': 'error', 'error': 'No content generated', 'model': 'gpt-oss-120b'}]}"

for filename in os.listdir(docs_dir):
    if not filename.endswith(".md"):
        continue
    filepath = os.path.join(docs_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    modified = False
    
    # 1. Strip error block
    if error_string in content:
        content = content.replace(error_string + "\n", "")
        content = content.replace(error_string, "")
        modified = True
        
    # 2. Standardize test coverage to >=90%
    if "85" in content and "%" in content:
        new_content = re.sub(r'(?:≥|>=|&ge;)?\s*85\s*%', '≥90%', content)
        if new_content != content:
            content = new_content
            modified = True
            
    if filename == "inception_technology_strategy_stack_selection.md":
        content = content.replace("90 % complete within 2 s", "≥90 % complete within 2 s")
        modified = True
        
    # 3. Clean AES-1 token
    if "AES-1¶" in content:
        content = content.replace("AES-1¶", "")
        modified = True
        
    # 5. Standardize RISK-005 CVE SLA to 7 days
    if "RISK-005" in content:
        new_content = re.sub(r'(RISK-005.*?)30(\s*)days', r'\g<1>7\g<2>days', content, flags=re.IGNORECASE|re.DOTALL)
        if new_content != content:
            content = new_content
            modified = True
            
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Modified {filename}")
