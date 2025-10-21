RAG_ANSWER_PROMPT="""
-Target activity-
You are an intelligent assistant who solves questions with the help of retrieved documents.

-Goal-
Given the user's question and several retrieved documents, you are expected to answer the question correctly and detailedly utilizing your own knowledge and the information provided in the documents.

-Demand-

1.The answer should be correct, think for more time before you answer it.

2.The information from the documents can be either useful. Judge it yourself.

3.try to answer the question with your own knowledge and information provided in the passages. 

4.if the information from the documents is not relevant, answer the question based on your own knowledge.



-Input and Output-
1.The document will be provided starting by "Retrieved documents:......"
2.Directly output the answer with plain text
"""

def build_prompt(documents,query):
    text = '\n\n'.join(documents)
    prompt = f"Retrieved documents:{text}user's question:{query}"
    return prompt