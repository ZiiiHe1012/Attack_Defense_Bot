from api_client import dialogue
def answerLM(user_prompt, system_prompt,max_tokens=1200):
    resp = dialogue(user_prompt, system_prompt,max_tokens=max_tokens)
    return resp['response']