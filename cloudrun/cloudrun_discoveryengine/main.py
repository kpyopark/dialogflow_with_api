# If you encounter an error like 'bdist_wheel' error, try it after to install the wheel package (pip install wheel)
# You need to set right permissions to the service account for the discovery engine API (Disocvery Engine Viewer) after creating the service account.

from logging import INFO
from typing import Dict, List

from google.cloud import discoveryengine_v1alpha as discoveryengine
from google.api_core.client_options import ClientOptions

from dialogflow_fulfillment import WebhookClient
from flask import Flask, request
from flask.logging import create_logger
from vertexai.language_models import GroundingSource, TextEmbeddingModel
from dotenv import load_dotenv

# Create Flask app and enable info level logging
# embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko-multilingual@latest")

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

def handler(agent: WebhookClient) -> None:
    """Handle the webhook request."""
    logger.info('Dialogflow Request:')
    logger.info(agent.query)
    search_response = search_sample(PROJECT_ID, LOCATION, DATASTORE_ID, agent.query)
    # struct_data = [result.document for result in search_response]
    # content = [f"{result.document.content}" for result in search_list]
    # logger.info(struct_data)
    # #print(content)
    agent.add(search_response.summary.summary_text)
    print(search_response.summary)
    # agent.add("Success.")
    


@app.route('/', methods=['POST','GET'])
def webhook() -> Dict:
    """Handle webhook requests from Dialogflow."""
    # Get WebhookRequest object
    request_ = request.get_json(force=True)

    # Log request headers and body
    logger.info(f'Request headers: {dict(request.headers)}')
    # {'Host': 'xxx.a.run.app', 'Authorization': 'Bearer xxx', 'Content-Type': 'application/json', 'Content-Length': '1248', 'Accept': '*/*', 'User-Agent': 'Google-Dialogflow', 'X-Cloud-Trace-Context': 'xxxxxx/xxxxxxx;o=1', 'Traceparent': '00-68b7baeabae546e19f5be6bf8f90b14b-ee4697bad7987966-01', 'X-Forwarded-For': 'xx.xx.xx.xx', 'X-Forwarded-Proto': 'https', 'Forwarded': 'for="xx.xx.xx.xx";proto=https', 'Accept-Encoding': 'gzip, deflate, br'}
    logger.info(f'Request body: {request_}')
    # {'responseId': 'xxxx', 'queryResult': {'queryText': '라이센스 정보를 알려줘.', 'action': 'input.unknown', 'parameters': {}, 'allRequiredParamsPresent': True, 'fulfillmentText': '제가 제대로 이해하고 있는지 잘 모르겠어요.', 'fulfillmentMessages': [{'text': {'text': ['제가 제대로 이해하고 있는지 잘 모르겠어요.']}}], 'outputContexts': [{'name': 'projects/xxx/locations/global/agent/sessions/xxxx/contexts/__system_counters__', 'lifespanCount': 1, 'parameters': {'no-input': 0.0, 'no-match': 1.0}}], 'intent': {'name': 'projects/xxxx/locations/global/agent/intents/xxxx', 'displayName': 'Default Fallback Intent', 'isFallback': True}, 'intentDetectionConfidence': 1.0, 'languageCode': 'ko'}, 'originalDetectIntentRequest': {'source': 'DIALOGFLOW_CONSOLE', 'payload': {}}, 'session': 'projects/xxx/locations/global/agent/sessions/xxx'}


    # Handle request
    agent = WebhookClient(request_)
    agent.handle_request(handler)

    # Log WebhookResponse object
    logger.info(f'Response body: {agent.response}')

    return agent.response


if __name__ == '__main__':
    app.run(debug=True)