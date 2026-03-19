"""
Cat Café Multi-Agent System - MCP Prompt Injector

Injects HTTP callback instructions into prompts for non-Claude agents.

Claude has native MCP support, but other agents need HTTP curl commands
injected into their system prompts to interact with the callback system.
"""

from typing import Optional, Dict, Any

from core.invocation_registry import get_invocation_registry, InvocationRegistry


class McpPromptInjector:
    """
    Injects HTTP callback instructions into agent prompts.
    
    Claude agents have native MCP support and don't need injection.
    Other agents receive curl commands in their system prompts to
    POST messages, get thread context, and check for mentions.
    """
    
    # Agent IDs that have native MCP support
    NATIVE_MCP_AGENTS = {"bollumao"}  # Claude-based agents
    
    def __init__(self, invocation_registry: Optional[InvocationRegistry] = None):
        self.invocation_registry = invocation_registry or get_invocation_registry()
    
    def needs_injection(self, agent_id: str) -> bool:
        """
        Check if an agent needs prompt injection.
        
        Claude agents (like bollumao) have native MCP support.
        Other agents need curl commands in their prompts.
        
        Args:
            agent_id: The agent's ID (e.g., "bollumao", "mainemao", "xianluomao")
        
        Returns:
            True if the agent needs prompt injection, False otherwise
        """
        return agent_id.lower() not in self.NATIVE_MCP_AGENTS
    
    def build_instructions(self, api_url: str, invocation_id: str, callback_token: str) -> str:
        """
        Build system prompt instructions with curl commands.
        
        Generates a system prompt section that tells non-Claude agents
        how to use HTTP curl commands to interact with the Cat Café callback system.
        
        Args:
            api_url: Base URL for the Cat Café API (e.g., "http://localhost:8000")
            invocation_id: The agent's invocation ID for callbacks
            callback_token: The agent's callback token for authentication
        
        Returns:
            Formatted system prompt instructions with:
            - Available HTTP tools
            - curl command examples for post_message, thread_context, pending_mentions
            - Environment variable usage recommendations
            - Mention parsing pattern (@布偶猫, @缅因猫, @暹罗猫)
        
        Example prompt section:
        ```
        ## HTTP Callback Tools
        
        You can POST messages, get thread context, and check mentions using HTTP.
        
        ### Post a Message
        Use this to communicate with other agents or share information:
        
        ```bash
        curl -X POST http://localhost:8000/api/callbacks/post-message \\
          -H "Content-Type: application/json" \\
          -d '{
            "invocation_id": "inv-123",
            "callback_token": "token-xyz",
            "content": "Hello, I'm Mainemao!",
            "message_type": "text"
          }'
        ```
        
        To mention other agents, use: @布偶猫, @缅因猫, @暹罗猫
        Example: "Hey @布偶猫, can you help me?"
        
        ### Get Thread Context
        Get recent messages from the current thread:
        
        ```bash
        curl -X GET "http://localhost:8000/api/callbacks/thread-context?invocation_id=inv-123&callback_token=token-xyz&limit=50"
        ```
        
        ### Check Pending Mentions
        Find @mentions targeting you:
        
        ```bash
        curl -X GET "http://localhost:8000/api/callbacks/pending-mentions?invocation_id=inv-123&callback_token=token-xyz"
        ```
        
        ### API Endpoints
        - POST /api/callbacks/post-message
        - GET  /api/callbacks/thread-context
        - GET  /api/callbacks/pending-mentions
        - POST /api/callbacks/update-task
        - POST /api/callbacks/request-permission
        ```
        """
        api_url = api_url.rstrip("/")
        
        instructions = f"""## HTTP Callback Tools

You can communicate with other agents and the Cat Café system using HTTP curl commands.

### Your Callback Configuration
- API URL: {api_url}
- Invocation ID: {invocation_id}
- Callback Token: {callback_token}

### Post a Message

Use this to communicate with other agents or share information:

```bash
curl -X POST {api_url}/api/callbacks/post-message \\\\
  -H "Content-Type: application/json" \\\\
  -d '{{
    "invocation_id": "{invocation_id}",
    "callback_token": "{callback_token}",
    "content": "Your message content here",
    "message_type": "text"
  }}'
```

To mention other agents, use: @布偶猫, @缅因猫, @暹罗猫

**Example mentions:**
- "Hey @布偶猫, can you help me?" - mentions Bollumao (布偶猫 = Ragdoll cat)
- "Does anyone know @缅因猫's opinion?" - mentions Mainemao (缅因猫 = Maine Coon)
- "Answer @暹罗猫's question" - mentions Xianluomao (暹罗猫 = Siamese)

### Get Thread Context

Get recent messages from the current thread to understand context:

```bash
curl -X GET "{api_url}/api/callbacks/thread-context?invocation_id={invocation_id}&callback_token={callback_token}&limit=50"
```

### Check Pending Mentions

Find @mentions targeting you that may require attention:

```bash
curl -X GET "{api_url}/api/callbacks/pending-mentions?invocation_id={invocation_id}&callback_token={callback_token}"
```

### Update Task Status

Mark tasks as completed or update their progress:

```bash
curl -X POST {api_url}/api/callbacks/update-task \\\\
  -H "Content-Type: application/json" \\\\
  -d '{{
    "invocation_id": "{invocation_id}",
    "callback_token": "{callback_token}",
    "task_id": "task-123",
    "status": "completed",
    "result": "Task completed successfully"
  }}'
```

### Request Permission

Ask for permission before expensive operations:

```bash
curl -X POST {api_url}/api/callbacks/request-permission \\\\
  -H "Content-Type: application/json" \\\\
  -d '{{
    "invocation_id": "{invocation_id}",
    "callback_token": "{callback_token}",
    "task_description": "What you want to do",
    "reason": "Why you need to do it"
  }}'
```

### Complete API Endpoint Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | {api_url}/api/callbacks/post-message | Post a message to the chat |
| GET | {api_url}/api/callbacks/thread-context | Get recent thread messages |
| GET | {api_url}/api/callbacks/pending-mentions | Check for @mentions targeting you |
| POST | {api_url}/api/callbacks/update-task | Update task status |
| POST | {api_url}/api/callbacks/request-permission | Request permission for operations |

### Important Notes

- Always use your Invocation ID and Callback Token for authentication
- Mention other agents using: @布偶猫, @缅因猫, @暹罗猫
- The system automatically parses @mentions and routes to the correct agents
- Use thread_context to understand conversation history before responding
- Check pending_mentions periodically for work assigned to you
"""
        
        return instructions.strip()
    
    def inject_into_prompt(
        self,
        system_prompt: str,
        agent_id: str,
        api_url: str,
        invocation_id: str,
        callback_token: str,
    ) -> str:
        """
        Inject HTTP callback instructions into an agent's system prompt.
        
        If the agent already has native MCP support (like Claude/bollumao),
        the prompt is returned unchanged.
        
        Args:
            system_prompt: The original system prompt
            agent_id: The agent's ID
            api_url: Base URL for the Cat Café API
            invocation_id: Agent's invocation ID
            callback_token: Agent's callback token
        
        Returns:
            Modified system prompt with callback instructions added (or original if MCP native)
        """
        if not self.needs_injection(agent_id):
            # Agent has native MCP, use original prompt
            return system_prompt
        
        # Build injection instructions
        injection = self.build_instructions(api_url, invocation_id, callback_token)
        
        # Check if instructions already exist
        if "HTTP Callback Tools" in system_prompt:
            return system_prompt
        
        # Append instructions to system prompt
        # If there's a "##" section, add before the last one
        # Otherwise, append to the end
        
        instructionsDivider = "\n\n"
        
        if system_prompt.endswith("\n"):
            return system_prompt + instructionsDivider + injection
        
        return system_prompt + instructionsDivider + injection
    
    def build_mcp_config_for_claude(self, callback_config: dict) -> Dict[str, Any]:
        """
        Build MCP configuration for Claude native support.
        
        Creates the MCP configuration JSON that Claude can use to
        register the HTTP callback tools as native MCP tools.
        
        Args:
            callback_config: Dict with api_url, invocation_id, callback_token
        
        Returns:
            MCP configuration dict for Claude
        
        Example return:
        {
            "mcpServers": {
                "cat-cafe-callbacks": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-prompt", "..."],
                    "env": {
                        "CAT_CAFE_API_URL": "...",
                        "CAT_CAFE_INVOCATION_ID": "...",
                        "CAT_CAFE_CALLBACK_TOKEN": "..."
                    }
                }
            }
        }
        """
        api_url = callback_config.get("api_url", "")
        invocation_id = callback_config.get("invocation_id", "")
        callback_token = callback_config.get("callback_token", "")
        
        return {
            "mcpServers": {
                "cat-cafe-callbacks": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-prompt"],
                    "env": {
                        "CAT_CAFE_API_URL": api_url,
                        "CAT_CAFE_INVOCATION_ID": invocation_id,
                        "CAT_CAFE_CALLBACK_TOKEN": callback_token,
                    },
                }
            }
        }


# Global instance
_mcp_prompt_injector: Optional[McpPromptInjector] = None


def get_mcp_prompt_injector() -> McpPromptInjector:
    """Get or create the global MCP prompt injector instance."""
    global _mcp_prompt_injector
    
    if _mcp_prompt_injector is None:
        _mcp_prompt_injector = McpPromptInjector()
    
    return _mcp_prompt_injector


__all__ = [
    "McpPromptInjector",
    "get_mcp_prompt_injector",
]
