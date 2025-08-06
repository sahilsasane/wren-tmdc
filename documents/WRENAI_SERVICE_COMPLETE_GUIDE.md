# WrenAI Service - Complete Architecture Guide

## Table of Contents
1. [Overview](#overview)
2. [Architecture & Core Components](#architecture--core-components)
3. [Configuration System](#configuration-system)
4. [Pipeline Framework](#pipeline-framework)
5. [Provider System](#provider-system)
6. [API Endpoints & Services](#api-endpoints--services)
7. [Development Setup](#development-setup)
8. [Usage Guide](#usage-guide)
9. [Evaluation Framework](#evaluation-framework)
10. [Troubleshooting](#troubleshooting)

## Overview

WrenAI Service is an advanced AI-powered service that converts natural language queries into SQL queries using Retrieval-Augmented Generation (RAG) techniques. Built on FastAPI and Haystack, it provides a comprehensive text-to-SQL solution with support for multiple LLMs, embedding models, and database engines.

### Key Features
- **Text-to-SQL Generation**: Convert natural language to SQL queries
- **Multi-LLM Support**: OpenAI, Azure OpenAI, Ollama, and LiteLLM
- **RAG Architecture**: Semantic search with vector embeddings
- **Intent Classification**: Understand user query intent
- **SQL Correction**: Automatic error detection and fixing
- **Streaming Responses**: Real-time query processing
- **Comprehensive Evaluation**: Built-in testing framework

### Technology Stack
- **FastAPI**: Web framework for API development
- **Haystack**: RAG pipeline framework
- **Qdrant**: Vector database for embeddings
- **Hamilton**: Pipeline orchestration
- **LangFuse**: LLM observability and tracing
- **SQLGlot**: SQL parsing and validation
- **Poetry**: Dependency management

## Architecture & Core Components

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Web Layer                       │
├─────────────────────────────────────────────────────────────┤
│                    Service Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Ask Service │  │ Semantics   │  │ Chart/SQL Services  │ │
│  │             │  │ Preparation │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Pipeline Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Generation  │  │ Retrieval   │  │ Indexing            │ │
│  │ Pipelines   │  │ Pipelines   │  │ Pipelines           │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Provider Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ LLM         │  │ Embedder    │  │ Document Store      │ │
│  │ Providers   │  │ Providers   │  │ Providers           │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Application Entry Point (`src/__main__.py`)

The main application initializer with FastAPI lifecycle management:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize components, services, and metadata
    pipe_components = generate_components(settings.components)
    app.state.service_container = create_service_container(pipe_components, settings)
    app.state.service_metadata = create_service_metadata(pipe_components)
    init_langfuse(settings)
    
    yield
    
    # Shutdown: Cleanup and flush traces
    langfuse_context.flush()
```

#### 2. Configuration System (`src/config.py`)

Hierarchical configuration loading with multiple sources:

1. **Default Values**: Built-in defaults
2. **Environment Variables**: Override via ENV vars
3. **`.env.dev` File**: Development environment settings
4. **`config.yaml`**: Highest priority configuration

Key configuration categories:
- **Indexing & Retrieval**: Batch sizes, similarity thresholds
- **Generation**: Model parameters, retry limits
- **Engine**: Timeout settings, connection info
- **Service**: Caching, logging, observability

#### 3. Service Container (`src/globals.py`)

Central registry managing all services:

```python
@dataclass
class ServiceContainer:
    ask_service: AskService                           # Main Q&A service
    question_recommendation: QuestionRecommendation   # Suggest follow-ups
    relationship_recommendation: RelationshipRecommendation
    semantics_description: SemanticsDescription       # Schema explanations
    semantics_preparation_service: SemanticsPreparationService  # Data indexing
    chart_service: ChartService                       # Visualization generation
    sql_answer_service: SqlAnswerService              # SQL explanations
    sql_correction_service: SqlCorrectionService      # Error fixing
    # ... more services
```

## Configuration System

### Environment Variables

Key environment variables for service configuration:

```bash
# Service Configuration
WREN_AI_SERVICE_HOST=0.0.0.0
WREN_AI_SERVICE_PORT=5555

# LLM Configuration
OPENAI_API_KEY=your_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_API_KEY=your_azure_key

# Vector Database
QDRANT_HOST=localhost:6333
QDRANT_API_KEY=your_qdrant_key

# Observability
LANGFUSE_SECRET_KEY=your_langfuse_secret
LANGFUSE_PUBLIC_KEY=your_langfuse_public

# Engine Integration
WREN_UI_ENDPOINT=http://localhost:3000
WREN_IBIS_ENDPOINT=http://localhost:8000
```

### Configuration File Structure (`config.yaml`)

#### LLM Configuration
```yaml
type: llm
provider: litellm_llm  # or openai_llm, azure_openai_llm, ollama_llm
timeout: 120
models:
  - alias: default
    model: gpt-4o-mini
    context_window_size: 128000
    kwargs:
      max_tokens: 4096
      temperature: 0
      seed: 0
  - model: gpt-4
    context_window_size: 8192
    kwargs:
      max_tokens: 4096
      temperature: 0.1
```

#### Embedder Configuration
```yaml
type: embedder
provider: litellm_embedder  # or openai_embedder, azure_openai_embedder
models:
  - model: text-embedding-3-large
    alias: default
    dimension: 3072
    timeout: 120
```

#### Engine Configuration
```yaml
type: engine
provider: wren_ui  # or wren_ibis, wren_engine
endpoint: http://localhost:3000
```

#### Document Store Configuration
```yaml
type: document_store
provider: qdrant
host: localhost
port: 6333
index: default
api_key: your_api_key
```

### Settings Override Mechanism

The configuration system supports multiple override levels:

```python
class Settings(BaseSettings):
    # Default values
    host: str = Field(default="127.0.0.1", alias="WREN_AI_SERVICE_HOST")
    port: int = Field(default=5555, alias="WREN_AI_SERVICE_PORT")
    
    # Override from config.yaml settings section
    def override(self, raw: list[dict]) -> None:
        for doc in raw:
            if "settings" in doc:
                for key, value in doc["settings"].items():
                    if hasattr(self, key):
                        setattr(self, key, value)
```

## Pipeline Framework

### Pipeline Architecture

The service uses a three-layer pipeline architecture:

1. **Indexing Pipelines**: Transform and index data into embeddings
2. **Retrieval Pipelines**: Search and retrieve relevant context
3. **Generation Pipelines**: Generate responses using LLMs

### Indexing Pipelines (`src/pipelines/indexing/`)

#### 1. DB Schema Indexing (`db_schema.py`)
Processes database schema information into searchable embeddings:

```python
class DDLChunker:
    async def run(self, mdl: Dict[str, Any], column_batch_size: int):
        # Process MDL (Modeling Definition Language)
        chunks = await self._get_ddl_commands(mdl, column_batch_size)
        
        # Create documents with metadata
        documents = [
            Document(
                id=str(uuid.uuid4()),
                content=chunk["payload"],
                meta={
                    "type": "TABLE_SCHEMA",
                    "name": chunk["name"],
                    "project_id": project_id
                }
            )
            for chunk in chunks
        ]
        return {"documents": documents}
```

#### 2. Historical Question Indexing (`historical_question.py`)
Indexes previous questions and answers for context retrieval:

```python
async def historical_question_embedding(questions: List[Dict]):
    documents = []
    for question in questions:
        documents.append(Document(
            content=question["question"],
            meta={
                "type": "HISTORICAL_QUESTION",
                "sql": question["sql"],
                "project_id": question.get("project_id")
            }
        ))
    return {"documents": documents}
```

#### 3. SQL Pairs Indexing (`sql_pairs.py`)
Indexes question-SQL pairs for few-shot learning:

```python
class SqlPairsDocumentPreprocessor:
    def run(self, sql_pairs: List[Dict]):
        documents = []
        for pair in sql_pairs:
            documents.append(Document(
                content=f"Question: {pair['question']}\nSQL: {pair['sql']}",
                meta={
                    "type": "SQL_PAIR",
                    "question": pair["question"],
                    "sql": pair["sql"]
                }
            ))
        return {"documents": documents}
```

### Retrieval Pipelines (`src/pipelines/retrieval/`)

#### 1. Database Schema Retrieval (`db_schema_retrieval.py`)
Finds relevant tables and columns for a given query:

```python
async def retrieve_schema(
    query: str,
    retriever: EmbeddingRetriever,
    table_retrieval_size: int = 10,
    column_retrieval_size: int = 100
):
    # Retrieve relevant tables
    table_results = await retriever.run(
        query=query,
        top_k=table_retrieval_size,
        filters={"field": "type", "operator": "==", "value": "TABLE_SCHEMA"}
    )
    
    # Extract and format schema information
    schema_context = format_schema_for_prompt(table_results["documents"])
    return {"documents": schema_context}
```

#### 2. SQL Functions Retrieval (`sql_functions.py`)
Retrieves applicable SQL functions for query context:

```python
@dataclass
class SqlFunction:
    name: str
    description: str
    syntax: str
    examples: List[str]

async def retrieve_sql_functions(
    query: str,
    data_source: str,
    engine: Engine
) -> List[SqlFunction]:
    # Get available functions from engine
    functions = await engine.get_func_list(data_source)
    
    # Filter relevant functions based on query
    relevant_functions = filter_functions_by_query(query, functions)
    return relevant_functions
```

### Generation Pipelines (`src/pipelines/generation/`)

#### 1. SQL Generation (`sql_generation.py`)
Core text-to-SQL generation pipeline:

```python
sql_generation_user_prompt_template = """
### DATABASE SCHEMA ###
{% for document in documents %}
    {{ document }}
{% endfor %}

{% if sql_functions %}
### SQL FUNCTIONS ###
{% for function in sql_functions %}
{{ function }}
{% endfor %}
{% endif %}

{% if sql_samples %}
### SQL SAMPLES ###
{% for sample in sql_samples %}
Question: {{sample.question}}
SQL: {{sample.sql}}
{% endfor %}
{% endif %}

### QUESTION ###
User's Question: {{ query }}

Let's think step by step.
"""

@observe(capture_input=False)
def generate_sql(
    query: str,
    documents: List[str],
    llm: Generator,
    sql_functions: List[SqlFunction] = None,
    sql_samples: List[Dict] = None
):
    # Build prompt with context
    prompt = build_prompt(query, documents, sql_functions, sql_samples)
    
    # Generate SQL using LLM
    response = llm.run(prompt=prompt)
    
    # Post-process and validate
    sql = post_process_sql(response["replies"][0])
    return {"sql": sql}
```

#### 2. Intent Classification (`intent_classification.py`)
Determines user query intent:

```python
INTENT_CLASSIFICATION_PROMPT = """
Classify the user's intent into one of these categories:
1. TEXT_TO_SQL: User wants to query data using natural language
2. GENERAL: User asks general questions about data or needs guidance

Examples:
- "Show me sales by region" → TEXT_TO_SQL
- "What is a database?" → GENERAL
- "How many customers do we have?" → TEXT_TO_SQL

User Query: {query}
Classification:
"""

async def classify_intent(query: str, llm: Generator):
    response = await llm.run(prompt=INTENT_CLASSIFICATION_PROMPT.format(query=query))
    intent = parse_intent(response["replies"][0])
    return {"intent": intent, "reasoning": response["meta"]}
```

#### 3. SQL Correction (`sql_correction.py`)
Automatically fixes SQL syntax and logical errors:

```python
async def correct_sql(
    invalid_sql: str,
    error_message: str,
    schema_context: List[str],
    llm: Generator,
    engine: Engine
):
    correction_prompt = f"""
    The following SQL query has an error:
    
    SQL: {invalid_sql}
    Error: {error_message}
    
    Schema Context:
    {schema_context}
    
    Please provide a corrected SQL query:
    """
    
    # Generate correction
    response = await llm.run(prompt=correction_prompt)
    corrected_sql = post_process_sql(response["replies"][0])
    
    # Validate correction
    is_valid, validation_error = await engine.validate_sql(corrected_sql)
    
    return {
        "corrected_sql": corrected_sql,
        "is_valid": is_valid,
        "validation_error": validation_error
    }
```

### Pipeline Orchestration

#### Hamilton Driver Integration
```python
from hamilton.async_driver import AsyncDriver

async def create_ask_pipeline():
    """Create comprehensive ask pipeline with Hamilton"""
    
    driver = AsyncDriver({
        # Retrieval components
        "retrieve_schema": retrieve_schema,
        "retrieve_sql_functions": retrieve_sql_functions,
        "retrieve_samples": retrieve_sql_samples,
        
        # Generation components
        "classify_intent": classify_intent,
        "generate_reasoning": generate_reasoning,
        "generate_sql": generate_sql,
        "correct_sql": correct_sql,
        
        # Validation components
        "validate_sql": validate_sql,
        "execute_sql": execute_sql
    })
    
    return driver

# Execute pipeline
result = await driver.execute(
    final_vars=["sql", "validation_result"],
    inputs={"query": user_query, "project_id": project_id}
)
```

## Provider System

### Provider Architecture

The provider system abstracts different service implementations:

```python
# Base Provider Classes
class LLMProvider(metaclass=ABCMeta):
    @abstractmethod
    def get_generator(self, *args, **kwargs): ...
    def get_model(self): return self._model
    def get_context_window_size(self): return self._context_window_size

class EmbedderProvider(metaclass=ABCMeta):
    @abstractmethod
    def get_text_embedder(self, *args, **kwargs): ...
    @abstractmethod
    def get_document_embedder(self, *args, **kwargs): ...

class DocumentStoreProvider(metaclass=ABCMeta):
    @abstractmethod
    def get_store(self, *args, **kwargs) -> DocumentStore: ...
    @abstractmethod
    def get_retriever(self, *args, **kwargs): ...
```

### LLM Providers (`src/providers/llm/`)

#### 1. OpenAI Provider (`openai_llm.py`)
```python
@provider("openai_llm")
class OpenAILLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", **kwargs):
        self._api_key = api_key
        self._model = model
        self._model_kwargs = kwargs
        self._context_window_size = self._get_context_window_size(model)
    
    def get_generator(self, streaming_callback=None):
        return OpenAIGenerator(
            api_key=Secret.from_token(self._api_key),
            model=self._model,
            streaming_callback=streaming_callback,
            generation_kwargs=self._model_kwargs
        )
```

#### 2. LiteLLM Provider (`litellm_llm.py`)
Supports multiple LLM providers through LiteLLM:

```python
@provider("litellm_llm")
class LiteLLMLLMProvider(LLMProvider):
    def __init__(self, models: List[Dict], fallback_models: Dict = None, **kwargs):
        self._models = models
        self._fallback_models = fallback_models or {}
        self._primary_model = models[0]["model"] if models else None
    
    def get_generator(self, model_name: str = None):
        target_model = model_name or self._primary_model
        
        # Configure model with fallback support
        model_config = self._fallback_models.get(target_model, {})
        
        return LiteLLMGenerator(
            model=target_model,
            model_config=model_config,
            generation_kwargs=self._model_kwargs
        )
```

#### 3. Ollama Provider (`ollama_llm.py`)
Local LLM support:

```python
@provider("ollama_llm")
class OllamaLLMProvider(LLMProvider):
    def __init__(self, model: str = "llama2", url: str = "http://localhost:11434", **kwargs):
        self._model = model
        self._url = url
        self._model_kwargs = kwargs
    
    def get_generator(self, streaming_callback=None):
        return OllamaGenerator(
            model=self._model,
            url=self._url,
            streaming_callback=streaming_callback,
            generation_kwargs=self._model_kwargs
        )
```

### Embedder Providers (`src/providers/embedder/`)

#### OpenAI Embedder
```python
@provider("openai_embedder")
class OpenAIEmbedderProvider(EmbedderProvider):
    def get_text_embedder(self):
        return OpenAITextEmbedder(
            api_key=Secret.from_token(self._api_key),
            model=self._embedding_model,
            dimensions=self._dimensions
        )
    
    def get_document_embedder(self):
        return OpenAIDocumentEmbedder(
            api_key=Secret.from_token(self._api_key),
            model=self._embedding_model,
            dimensions=self._dimensions
        )
```

### Document Store Providers (`src/providers/document_store/`)

#### Qdrant Provider
```python
@provider("qdrant")
class QdrantProvider(DocumentStoreProvider):
    def __init__(self, host: str = "localhost", port: int = 6333, **kwargs):
        self._host = host
        self._port = port
        self._config = kwargs
    
    def get_store(self, dataset_name: str):
        return QdrantDocumentStore(
            host=self._host,
            port=self._port,
            index=dataset_name,
            **self._config
        )
    
    def get_retriever(self, document_store):
        return QdrantEmbeddingRetriever(
            document_store=document_store,
            top_k=10
        )
```

### Engine Providers (`src/providers/engine/`)

#### WrenUI Engine
```python
@provider("wren_ui")
class WrenUI(Engine):
    async def execute_sql(
        self,
        sql: str,
        session: aiohttp.ClientSession,
        project_id: str | None = None,
        dry_run: bool = True,
        **kwargs
    ):
        data = {
            "sql": remove_limit_statement(sql),
            "projectId": project_id,
            "dryRun": dry_run,
            "limit": 1 if dry_run else kwargs.get("limit", 500)
        }
        
        async with session.post(
            f"{self._endpoint}/api/graphql",
            json={
                "query": "mutation PreviewSql($data: PreviewSQLDataInput) { previewSql(data: $data) }",
                "variables": {"data": data}
            }
        ) as response:
            result = await response.json()
            return self._process_response(result, dry_run)
```

## API Endpoints & Services

### REST API Structure

The API follows RESTful conventions with the following endpoints:

```
/v1/asks                    # Text-to-SQL queries
/v1/semantics-preparations  # Data indexing
/v1/sql-corrections        # SQL error fixing
/v1/charts                 # Chart generation
/v1/question-recommendations # Query suggestions
/v1/sql-answers           # SQL explanations
```

### Core Services

#### 1. Ask Service (`src/web/v1/services/ask.py`)

The primary service for handling natural language to SQL conversion:

```python
class AskService:
    def __init__(
        self,
        pipelines: Dict[str, BasicPipeline],
        allow_intent_classification: bool = True,
        allow_sql_generation_reasoning: bool = True,
        max_sql_correction_retries: int = 3,
        **kwargs
    ):
        self._pipelines = pipelines
        self._ask_results: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._config = {
            "allow_intent_classification": allow_intent_classification,
            "allow_sql_generation_reasoning": allow_sql_generation_reasoning,
            "max_sql_correction_retries": max_sql_correction_retries
        }
```

##### Ask Request Flow:
```python
async def ask(
    self,
    ask_request: AskRequest,
    service_metadata: Dict = None
) -> None:
    """
    Complete ask flow:
    1. Intent classification
    2. Schema retrieval
    3. SQL generation
    4. Validation and correction
    5. Response formatting
    """
    
    try:
        # Update status: understanding
        self._update_ask_result(ask_request.query_id, status="understanding")
        
        # Step 1: Classify user intent
        if self._config["allow_intent_classification"]:
            intent_result = await self._pipelines["intent_classification"].run(
                query=ask_request.query
            )
            
            if intent_result["type"] == "GENERAL":
                return await self._handle_general_query(ask_request, intent_result)
        
        # Update status: searching
        self._update_ask_result(ask_request.query_id, status="searching")
        
        # Step 2: Retrieve relevant schema
        schema_result = await self._pipelines["db_schema_retrieval"].run(
            query=ask_request.query,
            project_id=ask_request.project_id,
            table_retrieval_size=self._table_retrieval_size
        )
        
        # Step 3: Generate SQL reasoning (optional)
        reasoning = None
        if self._config["allow_sql_generation_reasoning"]:
            reasoning_result = await self._pipelines["sql_generation_reasoning"].run(
                query=ask_request.query,
                documents=schema_result["documents"]
            )
            reasoning = reasoning_result["reasoning"]
        
        # Update status: generating
        self._update_ask_result(ask_request.query_id, status="generating")
        
        # Step 4: Generate SQL
        sql_result = await self._pipelines["sql_generation"].run(
            query=ask_request.query,
            documents=schema_result["documents"],
            sql_generation_reasoning=reasoning,
            project_id=ask_request.project_id
        )
        
        # Step 5: Validate and correct if needed
        final_sql = await self._validate_and_correct_sql(
            sql_result["sql"],
            ask_request,
            schema_result["documents"]
        )
        
        # Update status: finished
        self._update_ask_result(
            ask_request.query_id,
            status="finished",
            response=[AskResult(sql=final_sql, type="llm")]
        )
        
    except Exception as e:
        # Update status: failed
        self._update_ask_result(
            ask_request.query_id,
            status="failed",
            error=AskError(code="OTHERS", message=str(e))
        )
```

#### 2. Semantics Preparation Service

Handles data indexing and preparation:

```python
class SemanticsPreparationService:
    async def prepare(
        self,
        prepare_request: SemanticsPreparationRequest
    ) -> SemanticsPreparationResponse:
        """
        Index MDL data into vector store:
        1. Clean existing documents
        2. Index schema information
        3. Index historical questions
        4. Index SQL pairs
        5. Index custom instructions
        """
        
        # Clean existing project data
        if prepare_request.project_id:
            await self._pipelines["db_schema"].clean_documents(
                project_id=prepare_request.project_id
            )
        
        # Index database schema
        await self._pipelines["db_schema"].run(
            mdl=prepare_request.mdl,
            project_id=prepare_request.project_id
        )
        
        # Index historical questions if provided
        if prepare_request.historical_questions:
            await self._pipelines["historical_question"].run(
                questions=prepare_request.historical_questions,
                project_id=prepare_request.project_id
            )
        
        # Index SQL pairs for few-shot learning
        await self._pipelines["sql_pairs"].run(
            project_id=prepare_request.project_id
        )
        
        return SemanticsPreparationResponse(status="finished")
```

#### 3. SQL Correction Service

Handles automatic SQL error detection and correction:

```python
class SqlCorrectionService:
    async def correct(
        self,
        correction_request: SqlCorrectionRequest
    ) -> SqlCorrectionResponse:
        """
        SQL correction flow:
        1. Validate SQL syntax
        2. Identify error type
        3. Generate correction
        4. Re-validate
        """
        
        correction_id = str(uuid.uuid4())
        
        try:
            # Attempt correction
            correction_result = await self._pipelines["sql_correction"].run(
                invalid_sql=correction_request.sql,
                error_message=correction_request.error_message,
                project_id=correction_request.project_id
            )
            
            # Validate corrected SQL
            if correction_result["corrected_sql"]:
                validation_result = await self._validate_sql(
                    correction_result["corrected_sql"],
                    correction_request.project_id
                )
                
                if validation_result["is_valid"]:
                    return SqlCorrectionResponse(
                        correction_id=correction_id,
                        status="finished",
                        response=SqlCorrectionResult(
                            sql=correction_result["corrected_sql"],
                            type="llm"
                        )
                    )
            
            # Correction failed
            return SqlCorrectionResponse(
                correction_id=correction_id,
                status="failed",
                error=SqlCorrectionError(
                    code="CORRECTION_FAILED",
                    message="Unable to correct the SQL query"
                )
            )
            
        except Exception as e:
            return SqlCorrectionResponse(
                correction_id=correction_id,
                status="failed",
                error=SqlCorrectionError(code="OTHERS", message=str(e))
            )
```

### API Request/Response Models

#### Ask Request/Response
```python
class AskRequest(BaseRequest):
    query: str                          # Natural language query
    mdl_hash: Optional[str]            # MDL hash for caching
    histories: Optional[List[AskHistory]]  # Previous Q&A context
    ignore_sql_generation_reasoning: bool = False
    enable_column_pruning: bool = False
    use_dry_plan: bool = False

class AskResponse(BaseModel):
    query_id: str                      # Unique identifier for tracking

class AskResultResponse(BaseModel):
    status: Literal["understanding", "searching", "planning", "generating", "correcting", "finished", "failed", "stopped"]
    response: Optional[List[AskResult]]
    error: Optional[AskError]
    trace_id: Optional[str]           # For observability
```

#### Semantics Preparation Request/Response
```python
class SemanticsPreparationRequest(BaseRequest):
    mdl: Dict[str, Any]               # Modeling Definition Language
    project_id: Optional[str]
    historical_questions: Optional[List[Dict]]
    
class SemanticsPreparationResponse(BaseModel):
    status: Literal["indexing", "finished", "failed"]
    error: Optional[str]
```

### Streaming Support

Real-time response streaming for long-running operations:

```python
async def get_ask_streaming_result(self, query_id: str):
    """Stream real-time updates for ask queries"""
    
    while True:
        result = self._ask_results.get(query_id)
        if not result:
            yield f"data: {json.dumps({'error': 'Query not found'})}\n\n"
            break
            
        # Send current status
        yield f"data: {result.model_dump_json()}\n\n"
        
        # Check if finished
        if result.status in ["finished", "failed", "stopped"]:
            break
            
        await asyncio.sleep(1)  # Poll interval
```

## Development Setup

### Prerequisites

1. **Python 3.12+**: Use pyenv for version management
2. **Poetry 1.8.3+**: Dependency management
3. **Just**: Command runner for development tasks
4. **Docker**: For running dependent services

### Step-by-Step Setup

#### 1. Clone and Install Dependencies
```bash
cd wren-ai-service
poetry install
```

#### 2. Initialize Configuration
```bash
just init  # Creates config.yaml and .env.dev
```

#### 3. Configure Environment Variables
Edit `.env.dev`:
```bash
# LLM Configuration
OPENAI_API_KEY=your_openai_api_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_API_KEY=your_azure_key

# Vector Database
QDRANT_HOST=localhost:6333
QDRANT_API_KEY=your_qdrant_key

# Engine Integration
WREN_UI_ENDPOINT=http://localhost:3000
WREN_IBIS_ENDPOINT=http://localhost:8000

# Observability
LANGFUSE_SECRET_KEY=your_langfuse_secret
LANGFUSE_PUBLIC_KEY=your_langfuse_public
```

#### 4. Configure Components
Edit `config.yaml` to specify your LLM and embedder providers:

```yaml
# Example OpenAI configuration
type: llm
provider: openai_llm
models:
  - model: gpt-4o-mini
    kwargs:
      temperature: 0
      max_tokens: 4096

---
type: embedder
provider: openai_embedder
models:
  - model: text-embedding-3-large
    dimension: 3072

---
type: engine
provider: wren_ui
endpoint: http://localhost:3000

---
type: document_store
provider: qdrant
host: localhost
port: 6333
```

#### 5. Start Development Services
```bash
just up     # Start Qdrant and other dependencies
just start  # Start the AI service
```

### Development Commands

```bash
# Development lifecycle
just init                    # Initialize configuration files
just up                      # Start development dependencies
just down                    # Stop development dependencies
just start                   # Start AI service
just test                    # Run tests
just test-usecases           # Run use case tests
just load-test              # Performance testing

# Evaluation
just curate_eval_data       # Launch dataset curation app
just prep spider1.0         # Prepare Spider dataset
just predict dataset.toml   # Run predictions
just eval results.json      # Evaluate performance
```

### Docker Development

Use Docker for isolated development:

```bash
# Build development image
docker build -f tools/dev/Dockerfile -t wren-ai-service:dev .

# Run with docker-compose
docker-compose -f tools/dev/docker-compose-dev.yaml up
```

## Usage Guide

### Basic API Usage

#### 1. Prepare Semantics (Index Your Data)

First, index your database schema and metadata:

```bash
curl -X POST "http://localhost:5555/v1/semantics-preparations" \
  -H "Content-Type: application/json" \
  -d '{
    "mdl": {
      "catalog": "my_catalog",
      "schema": "public",
      "models": [
        {
          "name": "customers",
          "tableReference": {
            "schema": "public",
            "table": "customers"
          },
          "columns": [
            {"name": "id", "type": "integer"},
            {"name": "name", "type": "varchar"},
            {"name": "email", "type": "varchar"}
          ],
          "primaryKey": "id"
        }
      ]
    },
    "project_id": "my_project"
  }'
```

Response:
```json
{
  "status": "indexing"
}
```

#### 2. Ask Natural Language Questions

Convert natural language to SQL:

```bash
curl -X POST "http://localhost:5555/v1/asks" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all customers with their names and emails",
    "project_id": "my_project"
  }'
```

Response:
```json
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### 3. Get Results

Poll for results:

```bash
curl "http://localhost:5555/v1/asks/550e8400-e29b-41d4-a716-446655440000/result"
```

Response:
```json
{
  "status": "finished",
  "response": [
    {
      "sql": "SELECT name, email FROM customers",
      "type": "llm"
    }
  ]
}
```

#### 4. Stream Real-time Results

For real-time updates:

```bash
curl -N "http://localhost:5555/v1/asks/550e8400-e29b-41d4-a716-446655440000/streaming-result"
```

### Advanced Usage

#### 1. SQL Correction

Fix SQL errors automatically:

```bash
curl -X POST "http://localhost:5555/v1/sql-corrections" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELCT name FROM customers",
    "error_message": "syntax error at or near \"SELCT\"",
    "project_id": "my_project"
  }'
```

#### 2. Chart Generation

Generate visualization code:

```bash
curl -X POST "http://localhost:5555/v1/charts" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Create a bar chart showing customer count by region",
    "sql": "SELECT region, COUNT(*) as customer_count FROM customers GROUP BY region",
    "project_id": "my_project"
  }'
```

#### 3. Question Recommendations

Get suggested follow-up questions:

```bash
curl -X POST "http://localhost:5555/v1/question-recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM customers WHERE region = 'US'",
    "project_id": "my_project",
    "max_questions": 5
  }'
```

### Python SDK Usage

Use the service programmatically:

```python
import aiohttp
import asyncio
import json

class WrenAIClient:
    def __init__(self, base_url: str = "http://localhost:5555"):
        self.base_url = base_url
    
    async def ask(self, query: str, project_id: str = None):
        async with aiohttp.ClientSession() as session:
            # Submit query
            async with session.post(
                f"{self.base_url}/v1/asks",
                json={"query": query, "project_id": project_id}
            ) as response:
                result = await response.json()
                query_id = result["query_id"]
            
            # Poll for results
            while True:
                async with session.get(
                    f"{self.base_url}/v1/asks/{query_id}/result"
                ) as response:
                    result = await response.json()
                    
                    if result["status"] == "finished":
                        return result["response"][0]["sql"]
                    elif result["status"] == "failed":
                        raise Exception(result.get("error", {}).get("message", "Unknown error"))
                    
                    await asyncio.sleep(1)

# Usage
async def main():
    client = WrenAIClient()
    
    # Prepare semantics (one-time setup)
    mdl = {
        "catalog": "ecommerce",
        "schema": "public",
        "models": [
            {
                "name": "orders",
                "columns": [
                    {"name": "id", "type": "integer"},
                    {"name": "customer_id", "type": "integer"},
                    {"name": "total", "type": "decimal"},
                    {"name": "order_date", "type": "date"}
                ]
            }
        ]
    }
    
    await client.prepare_semantics(mdl, project_id="ecommerce")
    
    # Ask questions
    sql = await client.ask("What's the total revenue last month?", "ecommerce")
    print(f"Generated SQL: {sql}")

# Run
asyncio.run(main())
```

### Integration with Applications

#### Web Application Integration

```javascript
// Frontend JavaScript integration
class WrenAIService {
    constructor(baseUrl = 'http://localhost:5555') {
        this.baseUrl = baseUrl;
    }
    
    async ask(query, projectId) {
        // Submit query
        const response = await fetch(`${this.baseUrl}/v1/asks`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query, project_id: projectId})
        });
        
        const {query_id} = await response.json();
        
        // Stream results
        const eventSource = new EventSource(
            `${this.baseUrl}/v1/asks/${query_id}/streaming-result`
        );
        
        return new Promise((resolve, reject) => {
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.status === 'finished') {
                    eventSource.close();
                    resolve(data.response[0].sql);
                } else if (data.status === 'failed') {
                    eventSource.close();
                    reject(new Error(data.error?.message || 'Unknown error'));
                }
                
                // Handle intermediate statuses
                this.onStatusUpdate?.(data.status);
            };
        });
    }
}

// Usage
const wrenAI = new WrenAIService();
wrenAI.onStatusUpdate = (status) => console.log(`Status: ${status}`);

const sql = await wrenAI.ask('Show me top 10 customers by revenue', 'my_project');
console.log('Generated SQL:', sql);
```

## Evaluation Framework

### Overview

The evaluation framework provides comprehensive testing and benchmarking capabilities for the WrenAI service:

- **Dataset Support**: Spider 1.0, Bird, and custom datasets
- **Metrics**: Execution accuracy, SQL validity, semantic similarity
- **Performance Testing**: Load testing with Locust
- **Data Curation**: Interactive dataset preparation

### Setup Evaluation

#### 1. Prepare Evaluation Environment
```bash
# Install evaluation dependencies
poetry install --with eval

# Setup LangFuse for tracking
# Add LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY to .env.dev

# Start services
just up
```

#### 2. Prepare Datasets
```bash
# Download and prepare Spider dataset
just prep spider1.0

# Download and prepare Bird dataset
just prep bird

# List available datasets
ls eval/dataset/
```

#### 3. Run Evaluations
```bash
# Run predictions on Spider dataset
just predict eval/dataset/spider_academic_eval_dataset.toml

# Evaluate results
just eval results/predictions_academic.json

# Run with semantic evaluation
just eval results/predictions_academic.json --semantics
```

### Dataset Curation

Interactive dataset curation app:

```bash
# Launch curation interface
just curate_eval_data
```

Features:
- **Manual Query Review**: Validate generated SQL
- **Quality Scoring**: Rate query accuracy
- **Dataset Export**: Create custom evaluation sets
- **Batch Processing**: Handle large datasets efficiently

### Custom Evaluation Metrics

Create custom evaluation metrics:

```python
# eval/metrics/custom_metric.py
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

class SQLValidityMetric(BaseMetric):
    def __init__(self, engine):
        self.threshold = 1.0  # Binary metric
        self.engine = engine
    
    def measure(self, test_case: LLMTestCase):
        try:
            # Validate SQL syntax
            is_valid = self.engine.validate_sql(test_case.actual_output)
            
            self.success = is_valid
            self.score = 1.0 if is_valid else 0.0
            self.reason = "Valid SQL" if is_valid else "Invalid SQL syntax"
            
            return self.score
        except Exception as e:
            self.success = False
            self.score = 0.0
            self.reason = f"Validation error: {str(e)}"
            return self.score
    
    def is_successful(self):
        return self.success

# Usage in evaluation
from eval.metrics.custom_metric import SQLValidityMetric

def evaluate_predictions(predictions_file):
    engine = create_validation_engine()
    sql_metric = SQLValidityMetric(engine)
    
    results = []
    for prediction in load_predictions(predictions_file):
        test_case = LLMTestCase(
            input=prediction["question"],
            actual_output=prediction["generated_sql"],
            expected_output=prediction["ground_truth_sql"]
        )
        
        score = sql_metric.measure(test_case)
        results.append({
            "question": prediction["question"],
            "score": score,
            "success": sql_metric.is_successful(),
            "reason": sql_metric.reason
        })
    
    return results
```

### Performance Testing

Load testing with Locust:

```bash
# Run load tests
just load-test

# Custom load test configuration
poetry run locust -f tests/locust/ask_test.py --host=http://localhost:5555
```

Load test configuration:

```python
# tests/locust/ask_test.py
from locust import HttpUser, task, between

class WrenAIUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        # Setup test data
        self.prepare_semantics()
    
    @task(3)
    def ask_simple_query(self):
        """Test simple SELECT queries"""
        response = self.client.post("/v1/asks", json={
            "query": "Show me all customers",
            "project_id": "test_project"
        })
        
        if response.status_code == 200:
            query_id = response.json()["query_id"]
            self.poll_result(query_id)
    
    @task(2)
    def ask_complex_query(self):
        """Test complex aggregation queries"""
        response = self.client.post("/v1/asks", json={
            "query": "What's the average order value by customer segment last quarter?",
            "project_id": "test_project"
        })
        
        if response.status_code == 200:
            query_id = response.json()["query_id"]
            self.poll_result(query_id)
    
    def poll_result(self, query_id):
        """Poll for query results"""
        import time
        max_attempts = 30
        
        for _ in range(max_attempts):
            response = self.client.get(f"/v1/asks/{query_id}/result")
            
            if response.status_code == 200:
                result = response.json()
                if result["status"] in ["finished", "failed"]:
                    break
            
            time.sleep(1)
```

## Troubleshooting

### Common Issues

#### 1. Configuration Issues

**Problem**: Service fails to start with configuration errors
```
ERROR: Configuration file config.yaml not found
```

**Solution**:
```bash
# Initialize configuration
just init

# Check configuration syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Validate environment variables
cat .env.dev
```

#### 2. LLM Provider Issues

**Problem**: OpenAI API key errors
```
ERROR: Incorrect API key provided
```

**Solution**:
```bash
# Check API key format
echo $OPENAI_API_KEY | wc -c  # Should be 51 characters

# Test API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

#### 3. Vector Database Issues

**Problem**: Qdrant connection failed
```
ERROR: Could not connect to Qdrant at localhost:6333
```

**Solution**:
```bash
# Check Qdrant status
curl http://localhost:6333/health

# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant:latest

# Check configuration
grep -n "qdrant" config.yaml
```

#### 4. Memory Issues

**Problem**: Out of memory during indexing
```
ERROR: MemoryError during document embedding
```

**Solution**:
```bash
# Reduce batch size in config.yaml
settings:
  column_indexing_batch_size: 10  # Reduce from default 50

# Monitor memory usage
docker stats

# Use smaller embedding models
type: embedder
provider: openai_embedder
models:
  - model: text-embedding-ada-002  # Smaller model
```

#### 5. SQL Generation Issues

**Problem**: Generated SQL is invalid
```
ERROR: SQL syntax error in generated query
```

**Solution**:
```bash
# Enable SQL correction
settings:
  max_sql_correction_retries: 5  # Increase retries

# Check schema indexing
curl "http://localhost:5555/v1/asks/{query_id}/result" | jq '.retrieved_tables'

# Review MDL configuration
python -c "
import json
with open('mdl.json') as f:
    mdl = json.load(f)
    print('Models:', [m['name'] for m in mdl.get('models', [])])
"
```

### Debugging Tools

#### 1. Logging Configuration

Enable detailed logging:

```yaml
# config.yaml
settings:
  logging_level: DEBUG
  development: true
```

#### 2. LangFuse Tracing

Monitor LLM calls and performance:

```python
# Check trace details
from langfuse import Langfuse

langfuse = Langfuse()
traces = langfuse.get_traces(limit=10)

for trace in traces:
    print(f"Trace ID: {trace.id}")
    print(f"Duration: {trace.duration}ms")
    print(f"Total Cost: ${trace.calculated_total_cost}")
```

#### 3. Health Check Endpoints

Monitor service health:

```bash
# Basic health check
curl http://localhost:5555/health

# Detailed component status
curl http://localhost:5555/v1/health/detailed

# Performance metrics
curl http://localhost:5555/metrics
```

#### 4. Database Inspection

Inspect vector database contents:

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

# List collections
collections = client.get_collections()
print("Collections:", [c.name for c in collections.collections])

# Check collection info
info = client.get_collection("default")
print(f"Vector count: {info.points_count}")
print(f"Vector size: {info.config.params.vectors.size}")

# Search for documents
results = client.search(
    collection_name="default",
    query_vector=[0.1] * 1536,  # Dummy vector
    limit=5
)
print("Sample documents:", [r.payload for r in results])
```

### Performance Optimization

#### 1. Caching Optimization

```yaml
# config.yaml
settings:
  query_cache_ttl: 7200        # Increase cache TTL
  query_cache_maxsize: 5000    # Increase cache size
```

#### 2. Batch Processing

```python
# Optimize embedding batch size
settings:
  column_indexing_batch_size: 100  # Increase for better throughput
  table_retrieval_size: 20         # Increase for better context
```

#### 3. Connection Pooling

```yaml
# config.yaml for HTTP clients
settings:
  http_pool_connections: 20
  http_pool_maxsize: 20
  http_max_retries: 3
```

This comprehensive guide covers the complete WrenAI Service architecture, from basic setup to advanced usage and troubleshooting. The service provides a robust foundation for building natural language to SQL applications with enterprise-grade features and extensive customization options.
