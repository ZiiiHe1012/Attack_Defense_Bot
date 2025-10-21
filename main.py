from prompt_builder import build_prompt,RAG_ANSWER_PROMPT
from data_processor import search_common_database
from conversation import answerLM

if __name__=="__main__":
    q=input()
    documents=search_common_database(q,5)
    user_prompt=build_prompt(documents,q)
    print(answerLM(user_prompt,RAG_ANSWER_PROMPT))