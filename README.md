# dialogflow_with_api

기본적인 RAG 아키텍처를 구성하고 DialogFlow를 통하여, RAG 서비스를 이용하려는 사용자를 대상으로 구성하였다. 

## BackEnd Service 구성

RAG 아키텍처는 기본적으로, Ingestion 부터 Retriver를 구성하여야 하나, 이를 대체할 수 있는 다양한 서비스들이 있기 때문에, 직접 구현하는 방법과 많은 부분을 자동화한 서비스를 이용하는 형태 두가지로 구성해 보자

### 직접 RAG Ingestion Stage와 Retriever를 구성하는 방법

Ingestion Pipeline을 간단하게 구성하기 위하여, LangChain을 이용하여 GCS에 올라와 있는, PDF파일을 대상으로 Chunking과 Indexing을 수행하는 방법을 하나 만들어 보자. 
(이미 많은 Sample이 있기 때문에 이를 참조하였다.)

### Discovery Engine을 이용

Discovery Engine(AI Search)를 이용하면, 기본적으로 GCS에 문서만 등제하면 되기 때문에, Chunking/Indexing 과정 없이 바로 Retrieving을 수행할 수 있다.

## Fronend 구성 (DialogFlow)

Frontend로 DialogFlow를 이용하려고 한다. 하지만 DialogFlow도 ES버전과 CX버젼이 있으며, 어떤 것을 이용해도 괜찮지만, 버젼별로 통합하는 부분이 상이하여 그 부분을 자세하게 설명한다.

### DialogFlow ES

### DialogFlow CX (Search & Conversation)

DialogFlow CX에서 사용하는 API는 Open API면 모두 사용 가능합니다. 따라서 CX/ES 모두 사용하기 위해서는, 먼저 CX용 Open API를 만들어 놓고, 
차후, ES Fulfillment format에 맞는 Wrapper API를 생성하는 형태로 진행하면 됩니다. CX만 사용하는 경우 Wrapper API가 필요 없습니다. 
