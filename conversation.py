from api_client import dialogue
def answerLM(user_prompt,system_prompt):
    resp=dialogue(user_prompt,system_prompt)
    return resp['response']