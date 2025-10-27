from api_client import search_similar_files
from conversation import answerLM
from prompt_builder import RAG_DECOMPOSTION_PROMPT
def advanced_search(initial_q,enhance_type):
    if enhance_type=='decomposition':
        response=answerLM(initial_q,RAG_DECOMPOSTION_PROMPT,max_tokens=200)
        decompose_q = [x for x in response.replace('}{', ',').replace('{', '').replace('}', '').split(',')]
        print(decompose_q)
        tuple_query_docs=[]
        for i in range(len(decompose_q)):
            docs=search_common_database(decompose_q[i],5)
            docstr='\n\n'.join(docs)
            tuple_query_docs.append([decompose_q[i],docstr])
        return tuple_query_docs

def search_common_database(q, topk):#i think this function should replace by parametric search after we have own database
    d = search_similar_files('common_dataset', 'token_common', q, topk, 'cosine')
    documents = [x['text'] for x in d['files']]
    return documents