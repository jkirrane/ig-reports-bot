"""
OpenAI client wrapper for IG Reports Bot
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from openai import OpenAI
    from dotenv import load_dotenv
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI library not available. Install with: pip install openai python-dotenv")


# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize client
if OPENAI_AVAILABLE:
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        client = None
        logger.warning("OPENAI_API_KEY not found in environment variables")
else:
    client = None


def call_gpt(
    prompt: str,
    max_tokens: int = 200,
    temperature: float = 0.3,
    response_format: Optional[Dict[str, str]] = None,
    model: str = "gpt-4o-mini"
) -> Optional[str]:
    """
    Wrapper for OpenAI API calls
    
    Args:
        prompt: The prompt text
        max_tokens: Maximum response length (default 200)
        temperature: 0=deterministic, 1=creative (default 0.3)
        response_format: {"type": "json_object"} for JSON responses
        model: OpenAI model to use (default gpt-4o-mini)
    
    Returns:
        Response text or None on error
    """
    if not OPENAI_AVAILABLE or not client:
        logger.error("OpenAI client not available")
        return None
    
    try:
        # Build request parameters
        params = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        if response_format:
            params["response_format"] = response_format
        
        # Make API call
        logger.debug(f"Calling OpenAI API: model={model}, max_tokens={max_tokens}, temp={temperature}")
        
        response = client.chat.completions.create(**params)
        
        # Extract response
        content = response.choices[0].message.content
        
        # Log token usage for cost tracking
        usage = response.usage
        cost = estimate_cost(usage.prompt_tokens, usage.completion_tokens, model)
        
        logger.info(f"✅ OpenAI API success: {usage.prompt_tokens} prompt + {usage.completion_tokens} completion = ${cost:.4f}")
        
        # Log to file for cost tracking
        log_usage(usage.prompt_tokens, usage.completion_tokens, cost, model)
        
        return content
    
    except Exception as e:
        logger.error(f"❌ OpenAI API error: {e}")
        return None


def estimate_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
    """
    Estimate cost of API call based on token usage
    
    GPT-4o-mini pricing (as of 2024):
    - Input: $0.15 per 1M tokens
    - Output: $0.60 per 1M tokens
    """
    if model == "gpt-4o-mini":
        input_cost = (prompt_tokens / 1_000_000) * 0.15
        output_cost = (completion_tokens / 1_000_000) * 0.60
        return input_cost + output_cost
    
    # Default fallback
    return 0.0


def log_usage(prompt_tokens: int, completion_tokens: int, cost: float, model: str) -> None:
    """
    Log API usage to file for cost tracking
    """
    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': prompt_tokens + completion_tokens,
            'cost': cost
        }
        
        with open('llm_usage.log', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    except Exception as e:
        logger.warning(f"Failed to log usage: {e}")


def get_total_cost() -> float:
    """
    Calculate total cost from usage log
    
    Returns:
        Total cost in USD
    """
    try:
        total = 0.0
        with open('llm_usage.log', 'r') as f:
            for line in f:
                entry = json.loads(line)
                total += entry.get('cost', 0.0)
        return total
    except FileNotFoundError:
        return 0.0
    except Exception as e:
        logger.warning(f"Failed to calculate total cost: {e}")
        return 0.0


# Test function
if __name__ == '__main__':
    print("Testing OpenAI client...")
    
    if not client:
        print("❌ OpenAI client not available. Check your OPENAI_API_KEY in .env")
    else:
        # Simple test
        response = call_gpt(
            prompt="Say 'Hello from IG Reports Bot!' in JSON format with a 'message' field",
            max_tokens=50,
            response_format={"type": "json_object"}
        )
        
        if response:
            print(f"✅ Response: {response}")
            print(f"💰 Total cost so far: ${get_total_cost():.4f}")
        else:
            print("❌ API call failed")
