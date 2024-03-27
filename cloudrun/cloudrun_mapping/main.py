from logging import INFO
from typing import Dict

from flask import Flask, request
from flask.logging import create_logger

from dotenv import load_dotenv

import pandas as pd
import os
import time
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
    content_field='menu_hier_kor',
    metadata_field='metadata',
    text_embedding_field='desc_vector',
    embedding=embedding,
    distance_strategy=DistanceStrategy.COSINE,
)

llm_vertex = VertexAI(
    model_name="text-bison-32k@002",
    max_output_tokens=8000,
    temperature=0,
    top_p=0.8,
    top_k=40,
)

app = Flask(__name__)
logger = create_logger(app)
logger.setLevel(INFO)

@app.route("/menu_search", methods=['POST', 'GET'])
def menu_search():
    request_ = request.get_json(force=True)
    if request_.get('old_menu_id') is not None:
        old_menu_id = request_['old_menu_id']
        new_menu = store.get_documents(filter={
            "menu_id" : old_menu_id
        })
    elif request_.get('old_program_id') is not None:
        old_program_id = request_['old_program_id']
        new_menu = store.get_documents(filter={
            "program_id" : old_program_id
        })
    elif request_.get('old_menu_name') is not None:
        old_menu_name = request_['old_menu_name']
        new_menu = store.similarity_search(old_menu_name, k=1)
    else:
        return {"new_menu": None}
    if len(new_menu) == 0:
        return {"new_menu": None}
    new_menu = new_menu[0]
    print(new_menu.metadata)
    return_value = new_menu.metadata
    return_value['menu_hier_kor'] = new_menu.page_content
    print(return_value)
    return {"new_menu": return_value}

@app.route("/ingest_all", methods=['GET'])
def ingest_menu():
    menu_all = pd.read_csv('./menumapping.csv')
    menu_all['menu_hier_kor'] = menu_all['menu_hier_kor'].apply(lambda x: x.strip())
    menu_all['menu_id'] = menu_all['menu_id'].astype(str)
    menu_all['program_id'] = menu_all['program_id'].astype(str)
    menu_all['tcode'] = menu_all['tcode'].astype(str)
    menu_all['corp_category'] = menu_all['corp_category'].astype(str)
    failed_list = []
    BATCH_SIZE = 30
    for i in range(0, len(menu_all), BATCH_SIZE):
        time.sleep(1)
        menus = menu_all[i:i+BATCH_SIZE]
        try:
            logger.info("ingesting {} to {}".format(i, i+BATCH_SIZE))
            logger.info(menus['menu_hier_kor'].values)
            store.add_texts(menus['menu_hier_kor'].values, menus[['menu_id', 'program_id', 'tcode', 'corp_category']].to_dict('records'))
        except Exception as e:
            logger.info(e)
            logger.info("retrying...")
            time.sleep(1)
            try :
                store.add_texts(menus['menu_hier_kor'].values, menus[['menu_id', 'program_id', 'tcode', 'corp_category']].to_dict('records'))
            except Exception as nested_e:
                logger.error(nested_e)
                logger.error("Failed Items.")
                logger.error(menus['menu_hier_kor'].values)
                failed_list.append(menus)
    print("Failed Items.")
    print(failed_list)
    print("Failed Items Length.")
    print(len(failed_list))
    print("Success Items Length.")
    print(len(menu_all) - len(failed_list))
    print("Success Items.")
    print(menu_all[~menu_all['menu_id'].isin([failed_item['menu_id'] for failed_item in failed_list])])
    return {"status": "success"}

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


