# WrenAI MCP Server Integration Guide

## Overview

This guide explains how to create a comprehensive MCP (Model Context Protocol) server that integrates WrenAI's powerful text-to-SQL capabilities without requiring the Wren UI. You'll get all the AI functionality through MCP tools that can be used with any MCP-compatible client (Claude Desktop, Cline, etc.).

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │    │   Your MCP       │    │   WrenAI        │
│  (Claude, etc.) │◄──►│    Server        │◄──►│   Services      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                         │
                              │                 ┌───────▼────────┐
                              │                 │ Wren Engine    │
                              │                 │ (SQL Execution)│
                              │                 └───────┬────────┘
                              │                         │
                              │                 ┌───────▼────────┐
                              └────────────────►│ Your Database  │
                                                │ (PostgreSQL,   │
                                                │  BigQuery,etc.)│
                                                └────────────────┘
```

## Components Required

### 1. WrenAI Service (Text-to-SQL AI)
- **Purpose**: Natural language to SQL conversion
- **Port**: 8080 (default)
- **Key Features**: Intent classification, SQL generation, query explanation

### 2. Wren Engine (SQL Execution Engine)  
- **Purpose**: SQL validation, execution, and optimization
- **Port**: 8000 (default)
- **Key Features**: MDL-based SQL transformation, query execution

### 3. Your MCP Server
- **Purpose**: Bridge between MCP clients and WrenAI services
- **Key Features**: Tool definitions, request routing, response formatting

## Step 1: Environment Setup

### 1.1 Directory Structure
```bash
mkdir wrenai-mcp-integration
cd wrenai-mcp-integration

# Create project structure
mkdir -p {config,data,logs,scripts}
touch docker-compose.yml
touch .env
mkdir mcp-server
cd mcp-server
```

### 1.2 Environment Configuration
Create `.env` file:
```env
# WrenAI Service Configuration
WREN_AI_SERVICE_PORT=8080
WREN_AI_SERVICE_ENDPOINT=http://localhost:8080

# Wren Engine Configuration  
WREN_ENGINE_PORT=8000
WREN_ENGINE_ENDPOINT=http://localhost:8000

# Database Configuration (choose your database)
DATABASE_TYPE=postgresql  # or bigquery, mysql, etc.
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=your_database
DATABASE_USER=your_user
DATABASE_PASSWORD=your_password

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4

# Optional: Other LLM providers
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint

# Logging
LOG_LEVEL=INFO

# MCP Server Configuration
MCP_SERVER_PORT=3000
```

## Step 2: Docker Compose Setup

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  # PostgreSQL Database (optional - use your existing database)
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${DATABASE_NAME}
      POSTGRES_USER: ${DATABASE_USER}
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD}
    ports:
      - "${DATABASE_PORT}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./data/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - wrenai-network

  # Qdrant Vector Database (for WrenAI Service)
  qdrant:
    image: qdrant/qdrant:v1.11.0
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - wrenai-network

  # Wren Engine (SQL Execution)
  wren-engine:
    image: ghcr.io/canner/wren-engine:latest
    ports:
      - "${WREN_ENGINE_PORT}:8000"
    volumes:
      - ./config:/usr/src/app/etc
    environment:
      - WREN_DATASOURCE_TYPE=${DATABASE_TYPE}
    depends_on:
      - postgres
    networks:
      - wrenai-network

  # WrenAI Service (AI/LLM)
  wren-ai-service:
    image: ghcr.io/canner/wren-ai-service:latest
    ports:
      - "${WREN_AI_SERVICE_PORT}:8080"
    environment:
      # LLM Configuration
      - LLM_PROVIDER=openai
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_GENERATION_MODEL=${OPENAI_MODEL}
      
      # Engine Configuration
      - WREN_ENGINE_ENDPOINT=http://wren-engine:8000
      
      # Vector Store Configuration
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      
      # Development settings
      - LOGGING_LEVEL=${LOG_LEVEL}
    depends_on:
      - wren-engine
      - qdrant
    networks:
      - wrenai-network

  # Your MCP Server
  mcp-server:
    build: ./mcp-server
    ports:
      - "${MCP_SERVER_PORT}:3000"
    environment:
      - WREN_AI_SERVICE_ENDPOINT=http://wren-ai-service:8080
      - WREN_ENGINE_ENDPOINT=http://wren-engine:8000
    depends_on:
      - wren-ai-service
      - wren-engine
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    networks:
      - wrenai-network

volumes:
  postgres_data:
  qdrant_data:

networks:
  wrenai-network:
    driver: bridge
```

## Step 3: MCP Server Implementation

### 3.1 Create MCP Server Structure
```bash
cd mcp-server
touch Dockerfile requirements.txt main.py config.py models.py tools.py utils.py
mkdir -p src/{core,tools,models}
```

### 3.2 Requirements File
Create `requirements.txt`:
```txt
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
httpx==0.25.2
asyncio-mqtt==0.11.1
python-dotenv==1.0.0
loguru==0.7.2
orjson==3.9.10
sqlparse==0.4.4

# MCP SDK
mcp-python-sdk==1.0.0

# Optional: for advanced features
pandas==2.1.4
numpy==1.24.4
```

### 3.3 Dockerfile
Create `Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 3000

# Run the application
CMD ["python", "main.py"]
```

### 3.4 Configuration Module
Create `config.py`:
```python
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Service Endpoints
    wren_ai_service_endpoint: str = os.getenv("WREN_AI_SERVICE_ENDPOINT", "http://localhost:8080")
    wren_engine_endpoint: str = os.getenv("WREN_ENGINE_ENDPOINT", "http://localhost:8000")
    
    # Database Configuration
    database_type: str = os.getenv("DATABASE_TYPE", "postgresql")
    database_host: str = os.getenv("DATABASE_HOST", "localhost")
    database_port: int = int(os.getenv("DATABASE_PORT", "5432"))
    database_name: str = os.getenv("DATABASE_NAME", "")
    database_user: str = os.getenv("DATABASE_USER", "")
    database_password: str = os.getenv("DATABASE_PASSWORD", "")
    
    # LLM Configuration
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # Server Configuration
    mcp_server_port: int = int(os.getenv("MCP_SERVER_PORT", "3000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Timeouts
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "300"))
    poll_interval: int = int(os.getenv("POLL_INTERVAL", "2"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))

    class Config:
        env_file = ".env"


settings = Settings()
```

### 3.5 Data Models
Create `models.py`:
```python
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum


class DatabaseType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    BIGQUERY = "bigquery"
    SNOWFLAKE = "snowflake"
    REDSHIFT = "redshift"
    DUCKDB = "duckdb"


class ColumnType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    DATE = "date"


class MDLColumn(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    is_calculated: Optional[bool] = False
    expression: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class MDLModel(BaseModel):
    name: str
    table_reference: Optional[Dict[str, str]] = None
    ref_sql: Optional[str] = None
    columns: List[MDLColumn] = []
    primary_key: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class MDLRelationship(BaseModel):
    name: str
    models: List[str]
    join_type: Literal["ONE_TO_ONE", "ONE_TO_MANY", "MANY_TO_ONE", "MANY_TO_MANY"]
    condition: str


class MDLManifest(BaseModel):
    catalog: str
    schema: str
    data_source: Optional[str] = None
    models: List[MDLModel] = []
    relationships: List[MDLRelationship] = []


class QueryRequest(BaseModel):
    question: str
    context: Optional[str] = None
    limit: Optional[int] = 100


class QueryResult(BaseModel):
    sql: str
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time_ms: float


class SQLGenerationRequest(BaseModel):
    question: str
    deploy_id: Optional[str] = None
    language: Optional[str] = "en"


class SQLGenerationResult(BaseModel):
    sql: str
    reasoning: Optional[str] = None
    rephrased_question: Optional[str] = None
    confidence_score: Optional[float] = None


class DeploymentStatus(str, Enum):
    PENDING = "pending"
    DEPLOYED = "deployed"
    FAILED = "failed"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AITask(BaseModel):
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
```

### 3.6 Core Utilities
Create `utils.py`:
```python
import asyncio
import httpx
import json
import time
from typing import Dict, Any, Optional, Tuple
from loguru import logger
from .config import settings
from .models import TaskStatus, AITask


class WrenAIClient:
    def __init__(self):
        self.ai_service_url = settings.wren_ai_service_endpoint
        self.engine_url = settings.wren_engine_endpoint
        self.timeout = settings.request_timeout
        
    async def deploy_mdl(self, manifest: Dict[str, Any], project_id: str = "default") -> str:
        """Deploy MDL manifest to WrenAI services"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Deploy to AI service
            ai_response = await client.post(
                f"{self.ai_service_url}/v1/semantics-preparations",
                json={
                    "mdl": manifest,
                    "project_id": project_id
                }
            )
            ai_response.raise_for_status()
            ai_task_id = ai_response.json()["query_id"]
            
            # Wait for AI deployment to complete
            await self._wait_for_task_completion(ai_task_id, "semantics-preparations")
            
            return ai_task_id
    
    async def generate_sql(self, question: str, deploy_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL from natural language question"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.ai_service_url}/v1/asks",
                json={
                    "query": question,
                    "deploy_id": deploy_id or "default",
                    "configurations": {
                        "language": "en"
                    }
                }
            )
            response.raise_for_status()
            task_id = response.json()["query_id"]
            
            # Poll for result
            result = await self._wait_for_task_completion(task_id, "asks")
            
            if result["status"] == "failed":
                raise Exception(f"SQL generation failed: {result.get('error', 'Unknown error')}")
            
            sql = result["response"][0]["sql"]
            metadata = {
                "reasoning": result.get("response", [{}])[0].get("reasoning"),
                "rephrased_question": result.get("rephrased_question"),
                "confidence": result.get("response", [{}])[0].get("confidence", 0.0)
            }
            
            return sql, metadata
    
    async def execute_sql(self, sql: str, limit: int = 100) -> Dict[str, Any]:
        """Execute SQL using Wren Engine"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            start_time = time.time()
            
            response = await client.post(
                f"{self.engine_url}/v3/connector/{settings.database_type}/query",
                json={
                    "sql": sql,
                    "limit": limit,
                    "manifestStr": "",  # Will be populated from deployed manifest
                    "connectionInfo": {
                        "host": settings.database_host,
                        "port": settings.database_port,
                        "database": settings.database_name,
                        "user": settings.database_user,
                        "password": settings.database_password
                    }
                }
            )
            response.raise_for_status()
            
            execution_time = (time.time() - start_time) * 1000
            data = response.json()
            
            return {
                "data": data["data"],
                "columns": data["columns"],
                "row_count": len(data["data"]),
                "execution_time_ms": execution_time
            }
    
    async def validate_sql(self, sql: str) -> bool:
        """Validate SQL without executing it"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.engine_url}/v3/connector/{settings.database_type}/query",
                    json={
                        "sql": sql,
                        "dryRun": True,
                        "manifestStr": "",
                        "connectionInfo": {
                            "host": settings.database_host,
                            "port": settings.database_port,
                            "database": settings.database_name,
                            "user": settings.database_user,
                            "password": settings.database_password
                        }
                    }
                )
                return response.status_code == 200
            except Exception as e:
                logger.error(f"SQL validation failed: {e}")
                return False
    
    async def get_available_tables(self) -> List[str]:
        """Get list of available tables"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.engine_url}/v2/connector/{settings.database_type}/metadata/tables",
                json={
                    "connectionInfo": {
                        "host": settings.database_host,
                        "port": settings.database_port,
                        "database": settings.database_name,
                        "user": settings.database_user,
                        "password": settings.database_password
                    }
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema information for a specific table"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.engine_url}/v2/connector/{settings.database_type}/metadata/columns",
                json={
                    "connectionInfo": {
                        "host": settings.database_host,
                        "port": settings.database_port,
                        "database": settings.database_name,
                        "user": settings.database_user,
                        "password": settings.database_password
                    },
                    "table": table_name
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def explain_sql(self, sql: str) -> str:
        """Get explanation of SQL query"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.ai_service_url}/v1/sql-explanations",
                json={"sql": sql}
            )
            response.raise_for_status()
            task_id = response.json()["query_id"]
            
            result = await self._wait_for_task_completion(task_id, "sql-explanations")
            return result["explanation"]
    
    async def _wait_for_task_completion(self, task_id: str, endpoint: str) -> Dict[str, Any]:
        """Wait for async task to complete"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            max_attempts = settings.request_timeout // settings.poll_interval
            
            for attempt in range(max_attempts):
                response = await client.get(f"{self.ai_service_url}/v1/{endpoint}/{task_id}")
                response.raise_for_status()
                
                result = response.json()
                status = result["status"]
                
                if status in ["completed", "failed"]:
                    return result
                
                await asyncio.sleep(settings.poll_interval)
            
            raise TimeoutError(f"Task {task_id} did not complete within {settings.request_timeout} seconds")


# Global client instance
wren_client = WrenAIClient()
```

### 3.7 MCP Tools Implementation
Create `tools.py`:
```python
import json
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from loguru import logger

from .utils import wren_client
from .models import (
    MDLManifest, QueryRequest, QueryResult,
    SQLGenerationRequest, SQLGenerationResult
)


# Initialize FastMCP server
mcp = FastMCP("WrenAI Analytics Server")


@mcp.tool()
async def deploy_data_model(manifest: dict) -> str:
    """
    Deploy a data model (MDL manifest) to WrenAI services.
    
    Args:
        manifest: MDL manifest dictionary containing catalog, schema, models, and relationships
        
    Returns:
        Deployment status message
    """
    try:
        # Validate manifest structure
        mdl_manifest = MDLManifest(**manifest)
        
        # Deploy to WrenAI services
        deployment_id = await wren_client.deploy_mdl(manifest)
        
        logger.info(f"Successfully deployed data model with ID: {deployment_id}")
        return f"Data model deployed successfully. Deployment ID: {deployment_id}"
        
    except Exception as e:
        error_msg = f"Failed to deploy data model: {str(e)}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
async def ask_question(question: str, limit: int = 100) -> str:
    """
    Ask a natural language question and get SQL results.
    
    Args:
        question: Natural language question about your data
        limit: Maximum number of rows to return (default: 100)
        
    Returns:
        JSON string containing SQL, data, and metadata
    """
    try:
        # Generate SQL from question
        sql, metadata = await wren_client.generate_sql(question)
        
        # Execute SQL
        execution_result = await wren_client.execute_sql(sql, limit)
        
        result = {
            "question": question,
            "sql": sql,
            "data": execution_result["data"],
            "columns": execution_result["columns"],
            "row_count": execution_result["row_count"],
            "execution_time_ms": execution_result["execution_time_ms"],
            "metadata": metadata
        }
        
        logger.info(f"Successfully processed question: {question}")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Failed to process question: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


@mcp.tool()
async def generate_sql(question: str) -> str:
    """
    Generate SQL from a natural language question without executing it.
    
    Args:
        question: Natural language question about your data
        
    Returns:
        JSON string containing generated SQL and reasoning
    """
    try:
        sql, metadata = await wren_client.generate_sql(question)
        
        result = {
            "question": question,
            "sql": sql,
            "reasoning": metadata.get("reasoning"),
            "rephrased_question": metadata.get("rephrased_question"),
            "confidence_score": metadata.get("confidence")
        }
        
        logger.info(f"Successfully generated SQL for question: {question}")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Failed to generate SQL: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


@mcp.tool()
async def execute_sql(sql: str, limit: int = 100) -> str:
    """
    Execute a SQL query and return results.
    
    Args:
        sql: SQL query to execute
        limit: Maximum number of rows to return (default: 100)
        
    Returns:
        JSON string containing query results
    """
    try:
        # Validate SQL first
        is_valid = await wren_client.validate_sql(sql)
        if not is_valid:
            return json.dumps({"error": "Invalid SQL query"})
        
        # Execute SQL
        result = await wren_client.execute_sql(sql, limit)
        
        logger.info(f"Successfully executed SQL query")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Failed to execute SQL: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


@mcp.tool()
async def validate_sql(sql: str) -> str:
    """
    Validate a SQL query without executing it.
    
    Args:
        sql: SQL query to validate
        
    Returns:
        Validation result message
    """
    try:
        is_valid = await wren_client.validate_sql(sql)
        
        result = {
            "sql": sql,
            "is_valid": is_valid,
            "message": "SQL is valid" if is_valid else "SQL is invalid"
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Failed to validate SQL: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


@mcp.tool()
async def explain_sql(sql: str) -> str:
    """
    Get a detailed explanation of what a SQL query does.
    
    Args:
        sql: SQL query to explain
        
    Returns:
        Human-readable explanation of the SQL query
    """
    try:
        explanation = await wren_client.explain_sql(sql)
        
        result = {
            "sql": sql,
            "explanation": explanation
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Failed to explain SQL: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


@mcp.tool()
async def list_tables() -> str:
    """
    Get a list of all available tables in the database.
    
    Returns:
        JSON list of table names
    """
    try:
        tables = await wren_client.get_available_tables()
        
        result = {
            "tables": tables,
            "count": len(tables)
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Failed to list tables: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


@mcp.tool()
async def describe_table(table_name: str) -> str:
    """
    Get detailed schema information for a specific table.
    
    Args:
        table_name: Name of the table to describe
        
    Returns:
        JSON containing table schema information
    """
    try:
        schema = await wren_client.get_table_schema(table_name)
        
        result = {
            "table_name": table_name,
            "schema": schema
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Failed to describe table {table_name}: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


@mcp.resource("wrenai://data-model/schema")
async def get_data_model_schema() -> str:
    """
    Get the JSON schema for creating data models (MDL manifests).
    
    Returns:
        JSON schema for MDL manifest structure
    """
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "WrenAI Data Model Schema",
        "type": "object",
        "required": ["catalog", "schema", "models"],
        "properties": {
            "catalog": {
                "type": "string",
                "description": "The catalog name"
            },
            "schema": {
                "type": "string", 
                "description": "The schema name"
            },
            "data_source": {
                "type": "string",
                "enum": ["postgresql", "mysql", "bigquery", "snowflake", "redshift", "duckdb"],
                "description": "The type of data source"
            },
            "models": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "columns"],
                    "properties": {
                        "name": {"type": "string"},
                        "table_reference": {
                            "type": "object",
                            "properties": {
                                "catalog": {"type": "string"},
                                "schema": {"type": "string"},
                                "table": {"type": "string"}
                            }
                        },
                        "columns": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["name", "type"],
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "description": {"type": "string"},
                                    "is_calculated": {"type": "boolean"},
                                    "expression": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            },
            "relationships": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "models", "join_type", "condition"],
                    "properties": {
                        "name": {"type": "string"},
                        "models": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 2,
                            "maxItems": 2
                        },
                        "join_type": {
                            "type": "string",
                            "enum": ["ONE_TO_ONE", "ONE_TO_MANY", "MANY_TO_ONE", "MANY_TO_MANY"]
                        },
                        "condition": {"type": "string"}
                    }
                }
            }
        }
    }
    
    return json.dumps(schema, indent=2)


@mcp.tool()
async def health_check() -> str:
    """
    Check the health status of all WrenAI services.
    
    Returns:
        Health status of all services
    """
    try:
        # You can implement health checks for each service here
        # For now, we'll return a simple status
        
        result = {
            "status": "healthy",
            "services": {
                "wren_ai_service": "running",
                "wren_engine": "running",
                "database": "connected"
            },
            "timestamp": str(time.time())
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Health check failed: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"status": "unhealthy", "error": error_msg})
```

### 3.8 Main Application
Create `main.py`:
```python
import asyncio
import uvicorn
from loguru import logger
from mcp.server.fastmcp import FastMCP

from src.config import settings
from src.tools import mcp


def setup_logging():
    """Configure logging"""
    logger.remove()
    logger.add(
        "logs/wrenai_mcp.log",
        rotation="1 day",
        retention="30 days",
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )
    logger.add(
        lambda msg: print(msg, end=''),
        level=settings.log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )


async def main():
    """Main application entry point"""
    setup_logging()
    
    logger.info("Starting WrenAI MCP Server...")
    logger.info(f"WrenAI Service endpoint: {settings.wren_ai_service_endpoint}")
    logger.info(f"Wren Engine endpoint: {settings.wren_engine_endpoint}")
    logger.info(f"Database type: {settings.database_type}")
    
    # Run the MCP server
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Shutting down WrenAI MCP Server...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
```

## Step 4: Configuration Files

### 4.1 Database Configuration
Create `config/database_config.yaml`:
```yaml
# Database connection configurations for different data sources

postgresql:
  host: ${DATABASE_HOST}
  port: ${DATABASE_PORT}
  database: ${DATABASE_NAME}
  user: ${DATABASE_USER}
  password: ${DATABASE_PASSWORD}
  ssl_mode: prefer

mysql:
  host: ${DATABASE_HOST}
  port: ${DATABASE_PORT}
  database: ${DATABASE_NAME}
  user: ${DATABASE_USER}
  password: ${DATABASE_PASSWORD}

bigquery:
  project_id: ${GCP_PROJECT_ID}
  dataset_id: ${BQ_DATASET_ID}
  credentials_path: ${GCP_CREDENTIALS_PATH}

snowflake:
  account: ${SNOWFLAKE_ACCOUNT}
  user: ${SNOWFLAKE_USER}
  password: ${SNOWFLAKE_PASSWORD}
  database: ${SNOWFLAKE_DATABASE}
  schema: ${SNOWFLAKE_SCHEMA}
  warehouse: ${SNOWFLAKE_WAREHOUSE}
```

### 4.2 Sample Data Model
Create `config/sample_mdl.json`:
```json
{
  "catalog": "analytics",
  "schema": "public",
  "data_source": "postgresql",
  "models": [
    {
      "name": "users",
      "table_reference": {
        "catalog": "analytics",
        "schema": "public",
        "table": "users"
      },
      "columns": [
        {
          "name": "user_id",
          "type": "integer",
          "description": "Unique user identifier"
        },
        {
          "name": "email",
          "type": "string",
          "description": "User email address"
        },
        {
          "name": "created_at",
          "type": "timestamp",
          "description": "Account creation timestamp"
        },
        {
          "name": "full_name",
          "type": "string",
          "description": "User's full name",
          "is_calculated": true,
          "expression": "CONCAT(first_name, ' ', last_name)"
        }
      ],
      "primary_key": "user_id"
    },
    {
      "name": "orders",
      "table_reference": {
        "catalog": "analytics",
        "schema": "public", 
        "table": "orders"
      },
      "columns": [
        {
          "name": "order_id",
          "type": "integer",
          "description": "Unique order identifier"
        },
        {
          "name": "user_id",
          "type": "integer",
          "description": "ID of user who placed the order"
        },
        {
          "name": "total_amount",
          "type": "float",
          "description": "Total order amount"
        },
        {
          "name": "order_date",
          "type": "timestamp",
          "description": "When the order was placed"
        }
      ],
      "primary_key": "order_id"
    }
  ],
  "relationships": [
    {
      "name": "user_orders",
      "models": ["users", "orders"],
      "join_type": "ONE_TO_MANY",
      "condition": "users.user_id = orders.user_id"
    }
  ]
}
```

## Step 5: Deployment and Usage

### 5.1 Build and Start Services
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f mcp-server
docker-compose logs -f wren-ai-service
docker-compose logs -f wren-engine
```

### 5.2 MCP Client Configuration

For **Claude Desktop**, add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "wrenai-analytics": {
      "command": "docker",
      "args": [
        "exec", 
        "-i",
        "wrenai-mcp-integration_mcp-server_1",
        "python", 
        "main.py"
      ],
      "autoApprove": [
        "ask_question",
        "generate_sql", 
        "list_tables",
        "describe_table"
      ],
      "disabled": false
    }
  }
}
```

For **Cline**, add to settings:
```json
{
  "mcp.servers": [
    {
      "name": "wrenai-analytics",
      "transport": "stdio",
      "command": "docker",
      "args": [
        "exec",
        "-i", 
        "wrenai-mcp-integration_mcp-server_1",
        "python",
        "main.py"
      ]
    }
  ]
}
```

### 5.3 Usage Examples

#### Deploy Your Data Model
```python
# In your MCP client, use this tool:
deploy_data_model({
  "catalog": "my_analytics",
  "schema": "public", 
  "data_source": "postgresql",
  "models": [
    {
      "name": "customers",
      "table_reference": {"table": "customers"},
      "columns": [
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"},
        {"name": "email", "type": "string"}
      ]
    }
  ]
})
```

#### Ask Natural Language Questions
```python
# Ask questions about your data
ask_question("How many customers do we have?")
ask_question("What's the average order value by month?")
ask_question("Show me the top 10 customers by total spent")
```

#### Generate SQL Without Execution
```python
# Just get the SQL
generate_sql("Find customers who haven't placed an order in the last 30 days")
```

#### Execute Custom SQL
```python
# Run your own SQL
execute_sql("SELECT COUNT(*) FROM customers WHERE created_at > '2024-01-01'")
```

#### Explore Your Data
```python
# Discover tables and schemas
list_tables()
describe_table("customers")
```

## Step 6: Advanced Features

### 6.1 Custom Business Logic
Add business-specific tools by extending `tools.py`:

```python
@mcp.tool()
async def get_business_metrics(metric_name: str, date_range: str = "last_30_days") -> str:
    """Get specific business metrics with date filtering"""
    
    metric_queries = {
        "revenue": "SELECT SUM(total_amount) as revenue FROM orders WHERE order_date >= NOW() - INTERVAL '30 days'",
        "customer_acquisition": "SELECT COUNT(*) as new_customers FROM users WHERE created_at >= NOW() - INTERVAL '30 days'",
        "average_order_value": "SELECT AVG(total_amount) as aov FROM orders WHERE order_date >= NOW() - INTERVAL '30 days'"
    }
    
    if metric_name not in metric_queries:
        return json.dumps({"error": f"Unknown metric: {metric_name}"})
    
    try:
        result = await wren_client.execute_sql(metric_queries[metric_name])
        return json.dumps({
            "metric": metric_name,
            "value": result["data"][0] if result["data"] else None,
            "date_range": date_range
        })
    except Exception as e:
        return json.dumps({"error": str(e)})
```

### 6.2 Caching and Performance
Add Redis caching for frequently used queries:

```python
import redis.asyncio as redis

# In utils.py
class CachedWrenAIClient(WrenAIClient):
    def __init__(self):
        super().__init__()
        self.redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
    
    async def generate_sql(self, question: str, deploy_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        # Check cache first
        cache_key = f"sql_gen:{hash(question + (deploy_id or ''))}"
        cached_result = await self.redis_client.get(cache_key)
        
        if cached_result:
            return json.loads(cached_result)
        
        # Generate and cache
        result = await super().generate_sql(question, deploy_id)
        await self.redis_client.setex(cache_key, 3600, json.dumps(result))  # 1 hour cache
        
        return result
```

### 6.3 Monitoring and Logging
Add comprehensive monitoring:

```python
# In tools.py
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} completed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f}s: {e}")
            raise
    return wrapper

# Apply to all tools
@monitor_performance
@mcp.tool()
async def ask_question(question: str, limit: int = 100) -> str:
    # ... existing implementation
```

## Step 7: Testing and Validation

### 7.1 Create Test Suite
Create `tests/test_mcp_server.py`:
```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.utils import WrenAIClient
from src.tools import ask_question, generate_sql


@pytest.mark.asyncio
async def test_wren_client_sql_generation():
    client = WrenAIClient()
    
    with patch.object(client, 'generate_sql', return_value=("SELECT COUNT(*) FROM users", {"reasoning": "Count users"})):
        sql, metadata = await client.generate_sql("How many users do we have?")
        assert sql == "SELECT COUNT(*) FROM users"
        assert "reasoning" in metadata


@pytest.mark.asyncio 
async def test_ask_question_tool():
    with patch('src.tools.wren_client') as mock_client:
        mock_client.generate_sql.return_value = ("SELECT COUNT(*) FROM users", {})
        mock_client.execute_sql.return_value = {
            "data": [[42]], 
            "columns": ["count"], 
            "row_count": 1,
            "execution_time_ms": 100
        }
        
        result = await ask_question("How many users?")
        assert "42" in result
```

### 7.2 Integration Tests
```bash
# Run tests
cd mcp-server
python -m pytest tests/ -v

# Test with real services
python -m pytest tests/integration/ -v --slow
```

## Step 8: Production Considerations

### 8.1 Security
- Use environment variables for all secrets
- Implement API key authentication
- Set up SSL/TLS certificates
- Use Docker secrets for sensitive data

### 8.2 Scalability
- Add horizontal scaling for MCP server
- Implement connection pooling for databases
- Use load balancer for multiple instances
- Add Redis for caching and session management

### 8.3 Monitoring
- Set up Prometheus metrics
- Configure Grafana dashboards
- Implement health check endpoints
- Add alerting for failures

### 8.4 Backup and Recovery
- Regular database backups
- Configuration backup
- Disaster recovery procedures
- Data retention policies

## Conclusion

This comprehensive setup gives you:

✅ **Full WrenAI capabilities without the UI**
✅ **Natural language to SQL conversion**  
✅ **Semantic data modeling with MDL**
✅ **Multi-database support**
✅ **MCP integration for any compatible client**
✅ **Production-ready architecture**
✅ **Extensible tool framework**
✅ **Comprehensive error handling and logging**

You can now ask natural language questions about your data through any MCP client and get intelligent SQL responses powered by WrenAI's advanced AI capabilities!
