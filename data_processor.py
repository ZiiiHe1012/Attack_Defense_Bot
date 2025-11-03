from api_client import search_similar_files
from conversation import answerLM
from prompt_builder import RAG_DECOMPOSTION_PROMPT,TRANSLATE_PROMPT,QUERY_REFINEMENT_PROMPT,build_recursive_prompt
token = "jI3sZMsJLctmIl87PAEQNeRq6NE9ymyx7M-rVk_MOWWA-kNbPDx-o8nAG0UUsmC-"
DATABASE=['common_dataset','student_Group3_ATT_CK','student_Group3_D3FEND','student_Group3_OWASP','student_Group3_CYBER_METRIC']
def advanced_search(initial_q, enhance_type):
    if enhance_type == 'decomposition':
        response = answerLM(initial_q, RAG_DECOMPOSTION_PROMPT, max_tokens=200)
        decompose_q = [x for x in response.replace('}{', ',').replace('{', '').replace('}', '').split(',')]
        print(decompose_q)
        tuple_query_docs = []
        for i in range(len(decompose_q)):
            docs = search_database_bilingual(decompose_q[i], 5)
            docstr = '\n\n'.join(docs)
            tuple_query_docs.append([decompose_q[i], docstr])
        return tuple_query_docs
    elif enhance_type=='recursive':
        iter=1
        MAX_ITER=8
        tuple_query_docs=[[initial_q,'\n\n'.join(search_database_bilingual(initial_q, 5))]]
        while True:
            iter+=1
            response=answerLM(build_recursive_prompt(tuple_query_docs),QUERY_REFINEMENT_PROMPT,max_tokens=360)
            print(f"121212{response}")
            if response=='<stop>' or MAX_ITER<=iter:
                break
            tuple_query_docs.append([response,'\n\n'.join(search_database_bilingual(initial_q, 5))])
        print(tuple_query_docs)
        return tuple_query_docs



def search_common_database(q, topk):
    #deprecated
    #i think this function should replace by parametric search after we have own database
    d = search_similar_files('common_dataset', 'token_common', q, topk, 'cosine')
    documents = [(x['text'],x['score']) for x in d['files']]
    return documents

def search_database(q, topk):
    documents=[]
    for database in DATABASE:
        if database=='common_dataset':
            d = search_similar_files(database, 'token_common', q, topk, 'cosine')
            documents.extend([(x['text'],x['score']) for x in d['files']])
        else:
            d = search_similar_files(database, token, q, topk, 'cosine')
            documents.extend([(x['text'], x['score']) for x in d['files']])
    doc = [x[0] for x in sorted(documents, key=lambda x: x[1], reverse=True)[:topk]]
    return doc

def search_database_bilingual(q,topk):
    eng_q=answerLM(q,TRANSLATE_PROMPT,max_tokens=300)
    documents = []
    documents.extend(search_database(q,topk))
    documents.extend(search_database(eng_q,topk))
    return documents