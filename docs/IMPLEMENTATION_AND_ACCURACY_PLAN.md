# Unified Memory Server - Implementation and Accuracy Plan (June 2nd, 2025)

This document outlines the findings from an architectural review and accuracy check of the `unified-memory-server` against its reference memory system repositories. It also provides a detailed implementation plan for `memory_selector.py` and `cab_tracker.py`.

## 1. Reference Repositories Interface Summary

The analysis involved packing and inspecting the following reference repositories:

*   **`redis-developer/agent-memory-server`**:
    *   **Interface**: REST API consumed via `MemoryAPIClient`.
    *   **Key Functionalities**: Session management, long-term memory (semantic search, preference storage), working memory (conversational context).
    *   **Interaction**: Via methods like `set_working_memory`, `create_long_term_memory`, `search_long_term_memory`.

*   **`basicmachines-co/basic-memory`**:
    *   **Interface**: Comprehensive REST API and an MCP endpoint (`/mcp`).
    *   **Key Functionalities**: Entity/note management, content retrieval, full-text search, project/vault synchronization.
    *   **Interaction**: Via REST endpoints like `/entities`, `/search`, `/tree`, or MCP operations.

*   **`neo4j-contrib/mcp-neo4j`**:
    *   **Interface**: MCP Servers.
        *   `mcp-neo4j-memory`: For entity/relation-based operations (e.g., `create_entities`, `search_nodes`).
        *   `mcp-neo4j-cypher`: For executing raw Cypher queries.
    *   **Interaction**: Via MCP requests formatted for specific operations or Cypher queries.

## 2. Analysis of `unified-memory-server`

### `memory_selector.py`
*   **Strengths**: Clear task/system enums, rule-based routing foundation, fallback logic structure, CAB tracker integration points, data propagation concept.
*   **Key Implementation Areas**:
    1.  **Client Instantiation**: `_get_redis_client`, `_get_basic_memory_client`, `_get_neo4j_client` need to correctly set up clients/wrappers for each backend.
    2.  **Backend Operation Logic**: `_store_in_X`, `_retrieve_from_X` methods must translate unified calls into specific backend API/MCP calls, handling data formats and errors.
    3.  **Configuration Management**: Secure loading of backend connection parameters.
    4.  **Data Propagation**: Implement `propagate_data` and `_propagate_to_X` methods.
    5.  **Task Determination**: Enhance `_determine_task_type` beyond keyword matching for more robust intelligent routing.

### `cab_tracker.py`
*   **Functionality**: Provides good session-based logging to a Markdown file for suggestions, errors, and system events.
*   **Integration**: `MemorySelector` has placeholders; ensure comprehensive logging is implemented.

## 3. Detailed Implementation Plan for `memory_selector.py`

### 3.1. Configuration Management
*   Load backend parameters (URLs, API keys, credentials) from `.env` file.
*   Log errors via `CABTracker` if essential configuration is missing.

### 3.2. Client Instantiation (`_get_X_client` methods)
*   **`_get_redis_client()`**:
    *   Import/adapt `MemoryAPIClient` & `MemoryClientConfig`.
    *   Instantiate with config from loaded parameters.
*   **`_get_basic_memory_client()`**:
    *   Use `httpx` or `requests` for REST API interaction.
    *   Configure with base URL and auth from loaded parameters.
    *   Alternatively, implement an MCP client if targeting its `/mcp` endpoint.
*   **`_get_neo4j_client()`**:
    *   Create a helper/wrapper for sending MCP requests (JSON payloads via HTTP POST) to `mcp-neo4j-memory` and `mcp-neo4j-cypher` server URLs (from config).

### 3.3. Backend Operation Logic (`_store_in_X`, `_retrieve_from_X`)
*   **General**: For each backend:
    1.  Get configured client.
    2.  Map unified API data/query to backend-specific formats/schemas.
    3.  Call appropriate backend methods/endpoints/MCP operations.
    4.  Parse responses and handle errors.
    5.  Log events with `CABTracker`.
*   **Redis Specifics**:
    *   Map `TaskType` to working memory vs. long-term memory client methods.
    *   Use `MemoryRecord`, `LongTermMemoryPayload`, etc.
*   **Basic Memory Specifics (REST)**:
    *   Map `TaskType` to relevant REST endpoints (e.g., `/entities`, `/search`, file paths).
    *   Handle JSON request/response schemas.
*   **Neo4j Specifics (MCP)**:
    *   Target `mcp-neo4j-memory` for entity/relation ops or `mcp-neo4j-cypher` for raw queries.
    *   Construct appropriate MCP JSON payloads. For Cypher, generate query strings.

### 3.4. Data Propagation (`propagate_data`, `_propagate_to_X`)
*   Implement logic to call `_store_in_X` for relevant systems when data needs to be synced.
*   Log inconsistencies via `CABTracker`.

### 3.5. Fallback and Error Handling
*   Ensure `_store_in_X`/`_retrieve_from_X` methods raise exceptions on failure to trigger `execute_with_fallback`.
*   Log API errors via `CABTracker`.

## 4. `cab_tracker.py` Integration
*   Ensure `CABTracker` is initialized and used consistently within `MemorySelector` for logging API errors, fallbacks, performance issues (if instrumented), data inconsistencies, and missing implementations.

## 5. Next Steps & Recommendations
*   Prioritize implementing the client instantiation and backend operation logic in `memory_selector.py`.
*   Develop comprehensive test cases for each backend integration and the fallback mechanism.
*   Consider enhancing `_determine_task_type` with more sophisticated intent recognition.
*   Regularly review `cab_suggestions.md` for insights and areas for improvement.
