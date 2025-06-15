/**
 * Unified Memory Server JavaScript/TypeScript SDK
 * 
 * A client library for interacting with the Unified Memory Server API.
 */

/**
 * Available memory systems
 */
const MemorySystem = {
    NEO4J: 'neo4j',
    REDIS: 'redis',
    BASIC_MEMORY: 'basic_memory'
};

/**
 * Main client class for Unified Memory Server
 */
class UnifiedMemoryClient {
    /**
     * Initialize the client
     * @param {Object} options - Configuration options
     * @param {string} options.baseUrl - Base URL for REST API (default: http://localhost:8000)
     * @param {string} options.mcpUrl - Base URL for MCP server (default: http://localhost:9000)
     * @param {number} options.timeout - Request timeout in ms (default: 30000)
     * @param {string} options.apiKey - Optional API key for authentication
     */
    constructor(options = {}) {
        this.baseUrl = (options.baseUrl || 'http://localhost:8000').replace(/\/$/, '');
        this.mcpUrl = (options.mcpUrl || 'http://localhost:9000').replace(/\/$/, '');
        this.timeout = options.timeout || 30000;
        this.apiKey = options.apiKey;
        
        this.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'unified-memory-js-sdk/1.0.0'
        };
        
        if (this.apiKey) {
            this.headers['Authorization'] = `Bearer ${this.apiKey}`;
        }
    }
    
    /**
     * Make HTTP request
     * @private
     */
    async _makeRequest(method, url, data = null) {
        const options = {
            method: method.toUpperCase(),
            headers: this.headers,
            signal: AbortSignal.timeout(this.timeout)
        };
        
        if (data && (method.toUpperCase() === 'POST' || method.toUpperCase() === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url, options);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            if (error.name === 'TimeoutError') {
                throw new Error(`Request timeout after ${this.timeout}ms`);
            }
            throw new Error(`Network error: ${error.message}`);
        }
    }
    
    // Health Check Methods
    
    /**
     * Get system health status
     * @returns {Promise<Object>} Health status
     */
    async healthCheck() {
        return this._makeRequest('GET', `${this.baseUrl}/health/`);
    }
    
    /**
     * Check if server is ready
     * @returns {Promise<Object>} Readiness status
     */
    async readinessCheck() {
        return this._makeRequest('GET', `${this.baseUrl}/health/ready`);
    }
    
    /**
     * Check if server is alive
     * @returns {Promise<Object>} Liveness status
     */
    async livenessCheck() {
        return this._makeRequest('GET', `${this.baseUrl}/health/live`);
    }
    
    // Neo4j Graph Database Methods
    
    /**
     * Create a new entity in Neo4j
     * @param {string} name - Entity name
     * @param {string} entityType - Entity type
     * @param {Object} properties - Optional entity properties
     * @returns {Promise<Object>} Created entity details
     */
    async createEntity(name, entityType, properties = {}) {
        const data = {
            name,
            type: entityType,
            properties
        };
        return this._makeRequest('POST', `${this.baseUrl}/api/v1/entities`, data);
    }
    
    /**
     * Create a relationship between entities in Neo4j
     * @param {string} fromEntity - Source entity name
     * @param {string} toEntity - Target entity name
     * @param {string} relationType - Relationship type
     * @param {Object} properties - Optional relationship properties
     * @returns {Promise<Object>} Created relationship details
     */
    async createRelationship(fromEntity, toEntity, relationType, properties = {}) {
        const data = {
            from_entity: fromEntity,
            to_entity: toEntity,
            relation_type: relationType,
            properties
        };
        return this._makeRequest('POST', `${this.baseUrl}/api/v1/relations`, data);
    }
    
    /**
     * Search the Neo4j graph using natural language
     * @param {string} query - Natural language search query
     * @param {number} limit - Maximum number of results (default: 10)
     * @param {string[]} nodeTypes - Optional filter by node types
     * @returns {Promise<Object>} Search results
     */
    async searchGraph(query, limit = 10, nodeTypes = null) {
        const data = { query, limit };
        if (nodeTypes) {
            data.node_types = nodeTypes;
        }
        return this._makeRequest('POST', `${this.baseUrl}/api/v1/graph/search`, data);
    }
    
    // Redis Memory Methods
    
    /**
     * Create a new memory in Redis
     * @param {string} text - Memory text content
     * @param {string} namespace - Memory namespace (default: 'default')
     * @param {string[]} topics - Optional topics/tags
     * @param {string[]} entities - Optional associated entities
     * @param {Object} metadata - Optional metadata
     * @returns {Promise<Object>} Created memory details
     */
    async createMemory(text, namespace = 'default', topics = [], entities = [], metadata = {}) {
        const data = {
            text,
            namespace,
            topics,
            entities,
            metadata
        };
        return this._makeRequest('POST', `${this.baseUrl}/api/v1/memories`, data);
    }
    
    /**
     * Search memories using semantic search
     * @param {string} query - Search query
     * @param {string} namespace - Search namespace (default: 'default')
     * @param {number} limit - Maximum number of results (default: 10)
     * @returns {Promise<Object>} Search results
     */
    async searchMemories(query, namespace = 'default', limit = 10) {
        const data = { query, namespace, limit };
        return this._makeRequest('POST', `${this.baseUrl}/api/v1/memories/search`, data);
    }
    
    // Basic Memory Methods
    
    /**
     * Create a new note in Basic Memory
     * @param {string} title - Note title
     * @param {string} content - Note content in markdown
     * @param {string[]} tags - Optional tags
     * @returns {Promise<Object>} Created note details
     */
    async createNote(title, content, tags = []) {
        const data = { title, content, tags };
        return this._makeRequest('POST', `${this.baseUrl}/api/v1/notes`, data);
    }
    
    /**
     * Search notes using full-text search
     * @param {string} query - Search query
     * @param {number} limit - Maximum number of results (default: 10)
     * @returns {Promise<Object>} Search results
     */
    async searchNotes(query, limit = 10) {
        const data = { query, limit };
        return this._makeRequest('POST', `${this.baseUrl}/api/v1/search/notes`, data);
    }
    
    // MCP Methods
    
    /**
     * Check MCP server health
     * @returns {Promise<Object>} MCP health status
     */
    async mcpHealthCheck() {
        return this._makeRequest('GET', `${this.mcpUrl}/health`);
    }
    
    /**
     * Get list of available MCP tools
     * @returns {Promise<Object>} Available tools
     */
    async mcpToolsList() {
        const data = {
            jsonrpc: '2.0',
            id: Date.now(),
            method: 'tools/list',
            params: {}
        };
        return this._makeRequest('POST', `${this.mcpUrl}/sse`, data);
    }
    
    /**
     * Call an MCP tool
     * @param {string} toolName - Name of the tool to call
     * @param {Object} arguments - Tool arguments
     * @returns {Promise<Object>} Tool execution result
     */
    async mcpCallTool(toolName, arguments) {
        const data = {
            jsonrpc: '2.0',
            id: Date.now(),
            method: 'tools/call',
            params: {
                name: toolName,
                arguments
            }
        };
        return this._makeRequest('POST', `${this.mcpUrl}/sse`, data);
    }
    
    /**
     * Get WebSocket connection status
     * @returns {Promise<Object>} WebSocket status
     */
    async websocketStatus() {
        return this._makeRequest('GET', `${this.mcpUrl}/ws/status`);
    }
    
    // Convenience Methods
    
    /**
     * Store knowledge using the most appropriate memory system
     * @param {string} content - Content to store
     * @param {string} knowledgeType - Type of knowledge (affects system selection)
     * @param {string} system - Force specific memory system
     * @returns {Promise<Object>} Storage result
     */
    async storeKnowledge(content, knowledgeType = 'general', system = null) {
        if (system === MemorySystem.NEO4J || knowledgeType.toLowerCase().includes('entity') || knowledgeType.toLowerCase().includes('relationship')) {
            // Use Neo4j for structured knowledge
            return this.createEntity(
                `Knowledge-${Date.now()}`,
                'Knowledge',
                { content, type: knowledgeType }
            );
        } else if (system === MemorySystem.BASIC_MEMORY || knowledgeType.toLowerCase().includes('note') || knowledgeType.toLowerCase().includes('document')) {
            // Use Basic Memory for document-like content
            return this.createNote(
                `Knowledge: ${knowledgeType}`,
                content,
                [knowledgeType]
            );
        } else {
            // Default to Redis for general memory
            return this.createMemory(
                content,
                'default',
                [knowledgeType],
                [],
                { type: knowledgeType }
            );
        }
    }
    
    /**
     * Search across all memory systems
     * @param {string} query - Search query
     * @param {number} limit - Results per system (default: 5)
     * @returns {Promise<Object>} Combined search results from all systems
     */
    async searchAll(query, limit = 5) {
        const results = {
            neo4j: [],
            redis: [],
            basic_memory: []
        };
        
        // Search Neo4j
        try {
            const graphResults = await this.searchGraph(query, limit);
            results.neo4j = graphResults.results || [];
        } catch (error) {
            results.neo4j = [{ error: error.message }];
        }
        
        // Search Redis
        try {
            const memoryResults = await this.searchMemories(query, 'default', limit);
            results.redis = memoryResults.results || [];
        } catch (error) {
            results.redis = [{ error: error.message }];
        }
        
        // Search Basic Memory
        try {
            const noteResults = await this.searchNotes(query, limit);
            results.basic_memory = noteResults.results || [];
        } catch (error) {
            results.basic_memory = [{ error: error.message }];
        }
        
        return results;
    }
    
    /**
     * Create WebSocket connection for real-time updates
     * @param {Function} onMessage - Callback for incoming messages
     * @param {Function} onError - Callback for errors
     * @returns {WebSocket} WebSocket connection
     */
    createWebSocket(onMessage = null, onError = null) {
        const wsUrl = this.mcpUrl.replace(/^http/, 'ws') + '/ws';
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log('WebSocket connected to Unified Memory Server');
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (onMessage) {
                    onMessage(data);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            if (onError) {
                onError(error);
            }
        };
        
        ws.onclose = () => {
            console.log('WebSocket connection closed');
        };
        
        return ws;
    }
}

// Export for different environments
if (typeof module !== 'undefined' && module.exports) {
    // Node.js
    module.exports = { UnifiedMemoryClient, MemorySystem };
} else if (typeof window !== 'undefined') {
    // Browser
    window.UnifiedMemoryClient = UnifiedMemoryClient;
    window.MemorySystem = MemorySystem;
}

// Example usage (can be run in Node.js or browser)
if (typeof require !== 'undefined' && require.main === module) {
    // Example for Node.js
    async function example() {
        const client = new UnifiedMemoryClient();
        
        try {
            // Check system health
            const health = await client.healthCheck();
            console.log('System Status:', health.status);
            
            // Create an entity
            const entity = await client.createEntity(
                'Alice Johnson',
                'Person',
                {
                    role: 'Data Scientist',
                    department: 'AI Research'
                }
            );
            console.log('Created entity:', entity);
            
            // Create a memory
            const memory = await client.createMemory(
                'Alice is working on a new machine learning model for sentiment analysis',
                'default',
                ['machine-learning', 'sentiment-analysis'],
                ['Alice Johnson']
            );
            console.log('Created memory:', memory);
            
            // Search across all systems
            const results = await client.searchAll('Alice machine learning');
            console.log('Search results:', results);
            
        } catch (error) {
            console.error('Error:', error.message);
        }
    }
    
    example();
}