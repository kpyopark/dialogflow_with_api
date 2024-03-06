import os

from logging import INFO
from typing import Dict

from dialogflow_fulfillment import WebhookClient, QuickReplies, Context, Card, Image, Text

from flask import Flask, request
from flask.logging import create_logger
from langchain.embeddings import VertexAIEmbeddings
from vector_util import VectorDatabase

embeddings = VertexAIEmbeddings()
vdb = VectorDatabase()

app = Flask(__name__)
logger = create_logger(app)
logger.setLevel(INFO)

def qna_handler(agent:WebhookClient) -> None:

    agent.add('How are you feeling today?')
    agent.add(QuickReplies(quick_replies=['Happy :)', 'Sad :(']))

def get_related_query(question):
  test_embedding =  embeddings.embed_query(question)
  result = None
  with vdb.get_connection() as conn:
    try:
      with conn.cursor() as cur:
        select_record = (str(test_embedding).replace(' ',''),)
        cur.execute(f"SELECT sql, parameters, description FROM rag_test where (1 - (desc_vector <=> %s)) > 0.6 limit 1", select_record)
        if cur.rowcount == 0:
          return None
        rs = cur.fetchone()
        result = {
          'prepared_statement': rs[0],
          'filter_columns': rs[1],
          'description': rs[2]
        }
        print(result)
    except Exception as e:
      print(e)
  return result

@app.route("/knowledge", methods=['POST'])
def question_and_answer() -> Dict:
    request_ = request.get_json(force=True)

    logger.info(f'Request headers: {dict(request.headers)}')
    logger.info(f'Request body: {request_}')

    agent = WebhookClient(request_)
    agent.handle_request(qna_handler)

    logger.info(f'Response body: {agent.response}')

    return agent.response

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))