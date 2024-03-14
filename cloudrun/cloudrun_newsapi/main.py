from logging import INFO
from typing import Dict
from datetime import datetime, timedelta

from flask import Flask, request
from flask.logging import create_logger

from dotenv import load_dotenv

import requests

import urllib.parse as urlencoder

import os

import vertexai
from langchain_google_vertexai import VertexAI

load_dotenv()

NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
NEWS_API_URL = "https://newsapi.org/v2/everything?q={keyword}&from={from_date}&sortBy=popularity&apiKey={API_KEY}"
NEWS_API_HEADLINE_URL = "https://newsapi.org/v2/top-headlines?category=business&country=kr&apiKey={API_KEY}"

VERTEXAI_LOCATION = os.getenv("VERTEXAI_LOCATION")
vertexai.init(location=VERTEXAI_LOCATION)

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

def get_summary_from_latest_news(headline_news):
  title_and_descprtion = []
  for article in headline_news['articles'][0:40]:
    if article['title'] is None:
      print('None value title occurred.')
      article['title'] = ""
    if article['description'] is None:
      print('None value description occurred.')
      article['description'] = ""
    title_and_descprtion.append(article['title'] + "\n" + article['description'])

  prompt_template = """You are a steel industry analyst. Please summarize the following news articles related to the steel industry in Korean in 3 to 5 sentences.

  news: 
  {news}

  summary:

  """
  llm_response = llm_vertex.invoke(prompt_template.format(news="\n".join(title_and_descprtion)))
  print(llm_response)
  return llm_response

@app.route("/headline_news", methods=['POST'])
def headline_news() -> Dict:
    request_ = request.get_json(force=True)
    question = request_['question']
    response = requests.get(NEWS_API_HEADLINE_URL.format(API_KEY=NEWS_API_KEY))
    result_json = response.json()
    print(result_json)
    answer = get_summary_from_latest_news(result_json)
    return {"answer": answer}

@app.route("/news", methods=['POST'])
def news() -> Dict:
    request_ = request.get_json(force=True)
    keyword = "news"
    from_date = (datetime.now() - timedelta(weeks=1)).strftime('%Y-%m-%d')
    if 'keyword' in request_:
      keyword = request_['keyword']
    if 'from_date' in request_:
      from_date = request_['from_date']

    response = requests.get(NEWS_API_URL.format(keyword=urlencoder.quote(keyword), from_date=from_date, API_KEY=NEWS_API_KEY))
    print(response.json())
    answer = get_summary_from_latest_news(response.json())
    return {"answer": answer}

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


