import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import VectorizedQuery
import openai

search_endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
search_key = os.environ["AZURE_SEARCH_API_KEY"]
open_ai_endpoint = os.getenv("OpenAIEndpoint")
open_ai_key = os.getenv("OpenAIKey")

def get_uploaded_document_index(name: str):
    from azure.search.documents.indexes.models import (
        SearchIndex,
        SearchField,
        SearchFieldDataType,
        SimpleField,
        SearchableField,
        VectorSearch,
        VectorSearchProfile,
        HnswAlgorithmConfiguration,
    )

    fields = [
        SimpleField(name="content", type=SearchFieldDataType.String, key=True),
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
            sortable=True,
            filterable=True,
        ),
        SearchableField(name="vector_data", type=SearchFieldDataType.String),
        SearchField(
            name="vector_data",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="uploaded-document-vector-config",
        )
    ]
    vector_search = VectorSearch(
        profiles=[VectorSearchProfile(name="uploaded-document-vector-config", algorithm_configuration_name="uploaded-document-algorithms-config")],
        algorithms=[HnswAlgorithmConfiguration(name="uploaded-document-algorithms-config")],
    )
    return SearchIndex(name=name, fields=fields, vector_search=vector_search)

def get_embeddings(text: str):
    # There are a few ways to get embeddings. This is just one example.
    
    client = openai.AzureOpenAI(
        azure_endpoint=open_ai_endpoint,
        api_key=open_ai_key,
        api_version="2023-09-01-preview",
    )
    embedding = client.embeddings.create(input=[text], 
                                         model="text-embedding-ada-002")
    return embedding.data[0].embedding


def get_document_all_chunks(document: str, chunk_size: int = 5000):
    
    #split document into chunks of 5000 characters
    chunks = [document[i:i + chunk_size] for i in range(0, len(document), chunk_size)]
    
    for chunk in chunks:
        document = {
            "content": chunk,
            "vector_data": get_embeddings(chunk),
        }
   
    return document

def index_document(document: str, index_name_for_current_document: str):
    
    # Create the Index
    credential = AzureKeyCredential(search_key)
    index_client = SearchIndexClient(search_endpoint, credential)
    index = get_uploaded_document_index(index_name_for_current_document)
    index_client.create_index(index)

    # Populate the Index
    client = SearchClient(search_endpoint, index_name_for_current_document, credential)
    document__chunks = get_document_all_chunks(document)
    client.upload_documents(documents=document__chunks)

# Main Flow
index_document("This is the content of document # 1", "index-doc-1")