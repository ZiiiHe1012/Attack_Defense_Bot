from blacklist import get_blacklist
from safety_agent import is_input_safe, is_output_safe

def validate_user_input(user_input):
    blacklist = get_blacklist()
    user_input_lower = user_input.lower()
    for category, pattern_groups in blacklist.items():
        for pattern_type, patterns in pattern_groups.items():
            for pattern in patterns:
                if pattern.lower() in user_input_lower:
                    return False, f"触发黑名单: {category}/{pattern_type} - '{pattern}'"
    return True, "通过黑名单检测"
        
def validate_prompt(prompt):
    if not is_input_safe(prompt):
        return False
    if not is_output_safe(prompt):
        return False
    return True
