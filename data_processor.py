from api_client import search_similar_files

def search_common_database(q, topk):
    d=search_similar_files('common_dataset','token_common',q,topk,'cosine')
    documents=[x['text'] for x in d['files']]
    return documents