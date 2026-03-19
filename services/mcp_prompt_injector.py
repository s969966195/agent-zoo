"""
MCP Prompt Injector for Zoo Multi-Agent System.

Injects HTTP callback instructions for non-native MCP agents (like Codex, Gemini).
Provides curl command examples and configuration templates.
"""

import textwrap
from typing import Dict, Optional


class MCPPromptInjector:
    """
    Injects MCP callback instructions into prompts for non-native MCP agents.
    
    Handles configuration injection and curl command examples.
    """
    
    def __init__(self, callback_base_url: str = "http://localhost:8000/mcp"):
        """
        Initialize the prompt injector.
        
        Args:
            callback_base_url: Base URL for MCP callbacks
        """
        self.callback_base_url = callback_base_url
        self._credentials_store: Dict[str, str] = {}
    
    def inject_callback_instructions(
        self,
        prompt: str,
        invocation_id: str,
        animal_key: str,
        token: str,
        instructions: Optional[str] = None,
    ) -> str:
        """
        Inject MCP callback instructions into a prompt.
        
        Args:
            prompt: Original prompt text
            invocation_id: Current invocation ID
            animal_key: Animal making the request
            token: Authentication token
            instructions: Optional custom instructions
            
        Returns:
            Prompt with injected MCP callback instructions
        """
        # Build the injection block
        injection = self._build_callback_injection(
            invocation_id=invocation_id,
            animal_key=animal_key,
            token=token,
            instructions=instructions,
        )
        
        # Append to original prompt
        return f"{prompt}\n\n{injection}"
    
    def _build_callback_injection(
        self,
        invocation_id: str,
        animal_key: str,
        token: str,
        instructions: Optional[str] = None,
    ) -> str:
        """Build the callback instruction block."""
        callback_url = f"{self.callback_base_url}/callback"
        thread_url = f"{self.callback_base_url}/thread"
        
        custom_instructions = instructions or ""
        
        injection = textwrap.dedent(f"""\
        === MCP CALLBACK INSTRUCTIONS ===
        
        You are now connected to the Zoo MCP Callback System.
        Your responses will be routed to other animals via @mentions.
        
        Callback Endpoint: {callback_url}
        Thread Endpoint: {thread_url}
        Invocation ID: {invocation_id}
        Animal: {animal_key}
        
        {{custom_instructions}}
        
        === HTTP CALLBACK EXAMPLES ===
        
        1. POST a message to the thread:
        
        curl -X POST "{callback_url}/message" \\
          -H "Content-Type: application/json" \\
          -H "Authorization: Bearer {token}" \\
          -d '{
            "invocation_id": "{invocation_id}",
            "content": "Your message here"
          }'
        
        2. GET thread context:
        
        curl -X GET "{thread_url}/context?invocation_id={invocation_id}&limit=10" \\
          -H "Authorization: Bearer {token}"
        
        3. GET pending @mentions for this animal:
        
        curl -X GET "{thread_url}/mentions?invocation_id={invocation_id}" \\
          -H "Authorization: Bearer {token}"
        
        === MENTION PATTERNS ===
        
        To route to other animals, use:
        - @雪球 or @xueqiu or @雪纳瑞
        - @六六 or @liuliu or @蓝鹦鹉
        - @小黄 or @xiaohuang or @黄鹦鹉
        
        Example: "Hey @雪球, what do you think? @六六, any opinions?"
        === END MCP INSTRUCTIONS ===
        """)
        
        return injection
    
    def get_curl_examples(
        self,
        invocation_id: str,
        token: str,
    ) -> Dict[str, str]:
        """
        Get curl command examples for MCP callbacks.
        
        Args:
            invocation_id: Current invocation ID
            token: Authentication token
            
        Returns:
            Dictionary of example names to curl commands
        """
        base_url = self.callback_base_url
        
        examples = {
            "post_message": f'''curl -X POST "{base_url}/callback/message" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer {token}" \\
  -d '{{
    "invocation_id": "{invocation_id}",
    "content": "Your response here"
  }}' ''',
            
            "get_thread_context": f'''curl -X GET "{base_url}/callback/thread/context?invocation_id={invocation_id}&limit=10" \\
  -H "Authorization: Bearer {token}" ''',
            
            "get_pending_mentions": f'''curl -X GET "{base_url}/callback/thread/mentions?invocation_id={invocation_id}" \\
  -H "Authorization: Bearer {token}" ''',
            
            "register_callback": f'''curl -X POST "{base_url}/callback/register" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer {token}" \\
  -d '{{
    "invocation_id": "{invocation_id}",
    "callback_url": "https://your-server.com/mcp/callback"
  }}' ''',
        }
        
        return examples
    
    def generate_agent_system_prompt(
        self,
        base_prompt: str,
        animal_key: str,
        animal_name: str,
        callback_url: Optional[str] = None,
    ) -> str:
        """
        Generate a complete system prompt for an animal agent.
        
        Args:
            base_prompt: Base system prompt for the animal
            animal_key: Animal's key (xueqiu, liuliu, xiaohuang)
            animal_name: Animal's display name (Chinese)
            callback_url: Optional custom callback URL
            
        Returns:
            Complete system prompt with MCP callbacks
        """
        url = callback_url or self.callback_base_url
        
        prompt = textwrap.dedent(f"""\
        {base_prompt}
        
        === ZOO MCP CONFIGURATION ===
        
        You are {animal_name} (key: {animal_key}) in the Zoo Multi-Agent System.
        
        MCP Endpoint: {url}/callback
        Thread Endpoint: {url}/thread
        
        When you need to:
        - Respond: Use MCP post_message callback
        - Check context: Use MCP get_thread_context callback  
        - Check mentions: Use MCP get_pending_mentions callback
        
        Remember: Other animals may mention you using:
        - @{animal_name}
        - @{animal_key}
        - @<alternative pattern for {animal_name}>
        === END SYSTEM PROMPT ===
        """)
        
        return prompt


# Global instance
_default_injector = MCPPromptInjector()


def get_mcp_injector() -> MCPPromptInjector:
    """Get default prompt injector instance."""
    return _default_injector


def inject_for_animal(
    prompt: str,
    invocation_id: str,
    animal_key: str,
    token: str,
) -> str:
    """Convenience function to inject MCP instructions for an animal."""
    return _default_injector.inject_callback_instructions(
        prompt=prompt,
        invocation_id=invocation_id,
        animal_key=animal_key,
        token=token,
    )


def get_curl_commands(
    invocation_id: str,
    token: str,
) -> Dict[str, str]:
    """Convenience function to get curl examples."""
    return _default_injector.get_curl_examples(invocation_id, token)


# Animal-specific system prompts
ANIMAL_SYSTEM_PROMPTS = {
    "xueqiu": {
        "base": "You are 雪球 (Xueqiu), a雪纳瑞 dog known for being clever and energetic.",
        "description": "雪球 - A clever and energetic 雪纳瑞 dog.",
    },
    "liuliu": {
        "base": "You are 六六 (Liuliu), a 蓝鹦鹉 parrot known for being wise and talkative.",
        "description": "六六 - A wise and talkative 蓝鹦鹉 parrot.",
    },
    "xiaohuang": {
        "base": "You are 小黄 (Xiaohuang), a 黄鹦鹉 parrot known for being cheerful and musical.",
        "description": "小黄 - A cheerful and musical 黄鹦鹉 parrot.",
    },
}


def get_system_prompt_for_animal(
    animal_key: str,
    callback_url: Optional[str] = None,
) -> str:
    """Get a system prompt for a specific animal with MCP injection."""
    animal_data = ANIMAL_SYSTEM_PROMPTS.get(animal_key)
    if not animal_data:
        raise ValueError(f"Unknown animal key: {animal_key}")
    
    return _default_injector.generate_agent_system_prompt(
        base_prompt=animal_data["base"],
        animal_key=animal_key,
        animal_name=_default_injector._get_animal_name(animal_key),
        callback_url=callback_url,
    )


def _get_animal_name(self, animal_key: str) -> str:
    """Helper to get animal name from key."""
    names = {
        "xueqiu": "雪球",
        "liuliu": "六六",
        "xiaohuang": "小黄",
    }
    return names.get(animal_key, animal_key)


# Add helper method dynamically
MCPPromptInjector._get_animal_name = _get_animal_name  # type: ignore
