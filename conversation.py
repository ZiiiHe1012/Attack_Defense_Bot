from api_client import dialogue
def answerLM(user_prompt, system_prompt,max_tokens=4096):
    resp = dialogue(user_prompt, system_prompt,max_tokens=4096)
    return resp['response']