from prompt_builder import build_prompt,RAG_ANSWER_PROMPT
from data_processor import search_common_database
from conversation import answerLM
from guard import validate_user_input, validate_prompt

if __name__=="__main__":
    q = input()
    if not validate_user_input(q):
        print("Your input is not safe. I cannot answer your question.")
        exit(1)
    documents = search_common_database(q, 5)
    user_prompt = build_prompt(documents, q)
    if not validate_prompt(user_prompt):
        print("Your prompt is not safe. I cannot answer your question.")
        exit(1)
    print(answerLM(user_prompt, RAG_ANSWER_PROMPT))