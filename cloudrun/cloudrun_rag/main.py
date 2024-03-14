from logging import INFO
from typing import Dict

from flask import Flask, request
from flask.logging import create_logger

from dotenv import load_dotenv

import os
from langchain.vectorstores.utils import DistanceStrategy
from langchain_community.vectorstores import BigQueryVectorSearch
from langchain_google_vertexai import VertexAI
from langchain_google_vertexai import VertexAIEmbeddings

load_dotenv()

PROJECT_ID = os.environ.get("PROJECT_ID")
LOCATION = os.environ.get("LOCATION")
VECTOR_SEARCH_DATASET = os.environ.get("VECTOR_SEARCH_DATASET")
VECTOR_SEARCH_TABLE = os.environ.get("VECTOR_SEARCH_TABLE")

embedding = VertexAIEmbeddings(
    model_name="textembedding-gecko-multilingual@latest", project=PROJECT_ID
)
store = BigQueryVectorSearch(
    project_id=PROJECT_ID,
    dataset_name=VECTOR_SEARCH_DATASET,
    table_name=VECTOR_SEARCH_TABLE,
    location=LOCATION,
    embedding=embedding,
    distance_strategy=DistanceStrategy.COSINE,
)

llm_vertex = VertexAI(
    #model_name="text-bison@latest",
    model_name="text-bison-32k@002",
    max_output_tokens=8000,
    temperature=0,
    top_p=0.8,
    top_k=40,
)

app = Flask(__name__)
logger = create_logger(app)
logger.setLevel(INFO)

def get_summary_from_docs(docs):
  prompt_template = """You are a librarian in a company. Please summarize the following document phrases in Korean in 3 to 5 sentences.

  docs: 
  {docs}

  summary:

  """
  llm_response = llm_vertex.invoke(prompt_template.format(docs=docs))
  print(llm_response)
  return llm_response 

@app.route("/document_search", methods=['POST'])
def document_search():
    request_ = request.get_json(force=True)
    question = request_['question']
    docs = store.similarity_search(question, k=3)
    print(docs)
    answer = get_summary_from_docs(docs)
    return {"answer": answer}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


