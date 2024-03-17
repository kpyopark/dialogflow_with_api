# If you encounter an error like 'bdist_wheel' error, try it after to install the wheel package (pip install wheel)
# You need to set right permissions to the service account for the discovery engine API (Disocvery Engine Viewer) after creating the service account.

from logging import INFO
from typing import Dict, List

from google.cloud import discoveryengine_v1alpha as discoveryengine
from google.api_core.client_options import ClientOptions

from flask import Flask, request
from flask.logging import create_logger
from dotenv import load_dotenv
from google.protobuf.json_format import MessageToJson
import proto

import os

# Create Flask app and enable info level logging

load_dotenv()

app = Flask(__name__)
logger = create_logger(app)
logger.setLevel(INFO)

LOCATION='global'
PROJECT_ID=os.getenv('PROJECT_ID') #'<<change your project id>>'
DATASTORE_ID=os.getenv('DATASTORE_ID') #'<<change your target data store>>'

def search_sample(
    project_id: str,
    location: str,
    data_store_id: str,
    search_query: str,
) -> List[discoveryengine.SearchResponse]:
    #  For more information, refer to:
    # https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if LOCATION != "global"
        else None
    )

    # Create a client
    client = discoveryengine.SearchServiceClient(client_options=client_options)

    # The full resource name of the search engine serving config
    # e.g. projects/{project_id}/locations/{location}/dataStores/{data_store_id}/servingConfigs/{serving_config_id}
    serving_config = client.serving_config_path(
        project=project_id,
        location=location,
        data_store=data_store_id,
        serving_config="default_config",
    )

    # Optional: Configuration options for search
    # Refer to the `ContentSearchSpec` reference for all supported fields:
    # https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.SearchRequest.ContentSearchSpec
    content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
        # For information about snippets, refer to:
        # https://cloud.google.com/generative-ai-app-builder/docs/snippets
        snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
            return_snippet=True
        ),
        # For information about search summaries, refer to:
        # https://cloud.google.com/generative-ai-app-builder/docs/get-search-summaries
        summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
            summary_result_count=5,
            # include_citations=False,
            # ignore_adversarial_query=False,
            # ignore_non_summary_seeking_query=False,
        ),
        # extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
        #     max_extractive_answer_count=0,
        #     max_extractive_segment_count=1,
        #     return_extractive_segment_score=False,
        # ),   
    )
    logger.info("Start Searching...")
    # Refer to the `SearchRequest` reference for all supported fields:
    # https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.SearchRequest
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=search_query,
        page_size=1,
        content_search_spec=content_search_spec,
        # query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
        #     condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
        # ),
        # spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
        #     mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
        # ),
        
    )

    response = client.search(request)
    return response

def get_link_summary(results):
    links = []
    for result in results:
        element = result.document.derived_struct_data._pb
        title = ""
        link = ""
        for key, value in element.items():
            if key == "title":
                title = value.string_value
            elif key == "link":
                link = value.string_value
        links.append({"title": title, "link": link})
    return links
        

@app.route('/search_docs', methods=['POST','GET'])
def search_docs() -> Dict:
    request_ = request.get_json(force=True)
    question = request_['question']
    search_response = search_sample(PROJECT_ID, LOCATION, DATASTORE_ID, question)
    links_summary = get_link_summary(search_response.results)
    return {"answer": search_response.summary.summary_text, "links": links_summary}

if __name__ == '__main__':
    app.run(debug=True)