from blacklist import get_blacklist
from safety_agent import is_input_safe, is_output_safe

def validate_user_input(user_input):
    blacklist = get_blacklist()
    for category, patterns in blacklist.items():
        for pattern in patterns:
            if pattern in user_input:
                return False
    return True
        
def validate_prompt(prompt):
    if not is_input_safe(prompt):
        return False
    if not is_output_safe(prompt):
        return False
    return True
