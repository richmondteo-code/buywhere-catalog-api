# Building a Shopping Copilot with OpenAI Agents SDK and BuyWhere

## Why Structured Catalog Access Beats Scraping for AI Agents

When building AI shopping agents, developers face a critical choice: scrape e-commerce websites or leverage structured product catalog APIs. While scraping might seem straightforward initially, it introduces significant reliability, maintenance, and legal challenges that structured APIs like BuyWhere's solve elegantly.

## Architecture Overview

A shopping copilot built with OpenAI Agents SDK follows this pattern:

```
User Query → OpenAI Agent → BuyWhere API → Structured Product Data → Natural Language Response
```

The key advantage is that the agent interacts with clean, normalized product data rather than parsing HTML, leading to more reliable tool calls and better user experiences.

## Step-by-Step Setup

### 1. Prerequisites
- OpenAI API key
- BuyWhere API key (sign up at developers.buywhere.ai)
- Python 3.8+
- OpenAI Agents SDK installed

### 2. Install Dependencies
```bash
pip install openai-agents buywhere-sdk
```

### 3. Configure Your Environment
```python
import os
from buywhere_sdk import BuyWhere

# Set your API keys
os.environ["OPENAI_API_KEY"] = "your-openai-key"
os.environ["BUYWHERE_API_KEY"] = "your-buywhere-key"

# Initialize BuyWhere client
buywhere_client = BuyWhere(api_key=os.environ["BUYWHERE_API_KEY"])
```

### 4. Create Product Search Tool
```python
from agents import function_tool

@function_tool
def search_products(query: str, max_price: float = None, min_rating: float = None):
    """Search for products using BuyWhere's structured catalog"""
    # Build search parameters
    params = {}
    if max_price:
        params['max_price'] = max_price
    # Note: min_rating would need to be handled differently as it's not a direct API param
    # You might need to filter results post-search or use a different approach
    
    results = buywhere_client.search(query=query, **params)
    return results
```

### 5. Build Your Shopping Copilot Agent
```python
from agents import Agent

shopping_copilot = Agent(
    name="ShoppingCopilot",
    instructions="""You are a helpful shopping assistant that helps users find products.
    Use the search_products tool to find items matching user preferences.
    Always provide concise, helpful responses with key product details:
    - Product name and brand
    - Price and availability
    - Key specifications
    - Where to buy""",
    tools=[search_products],
    model="gpt-4o"
)
```

## Example Usage

### Basic Product Search
```python
result = await shopping_copilot.run(
    "Find me wireless headphones under $150 with good battery life"
)
print(result.final_output)
```

### Singapore-Specific Product Discovery
```python
result = await shopping_copilot.run(
    "Find me Samsung Galaxy S24 phones available in Singapore under SGD 1200"
)
print(result.final_output)
```

### Comparison Shopping with Local Availability
```python
result = await shopping_copilot.run(
    "Compare prices for Nike Air Max shoes in Singapore stores and show me which ones are available for same-day delivery"
)
print(result.final_output)
```

## Why This Approach Works Better Than Scraping

1. **Reliability**: Structured APIs return consistent data formats; scraping breaks when sites change
2. **Performance**: Direct database queries are orders of magnitude faster than page parsing
3. **Legal Compliance**: API usage respects terms of service vs. potential scraping violations
4. **Rich Data**: Access to normalized attributes, categories, and relationships unavailable via scraping
5. **Maintenance**: Zero selector updates needed when retailers redesign their sites

## Tool Call Examples

The OpenAI Agents SDK makes these tool calls behind the scenes:

### Basic Product Search
```json
{
  "tool": "search_products",
  "arguments": {
    "query": "wireless headphones",
    "max_price": 150,
    "min_rating": 4.0
  }
}
```

### Singapore-Specific Search
```json
{
  "tool": "search_products",
  "arguments": {
    "query": "Samsung Galaxy S24",
    "source": "shopee_sg",
    "max_price": 1200
  }
}
```

### Local Availability Check
```json
{
  "tool": "search_products",
  "arguments": {
    "query": "Nike Air Max",
    "source": "shopee_sg"
  }
}
```

Returns structured data like:
```json
{
  "products": [
    {
      "id": "prod_123",
      "name": "Sony WH-1000XM5",
      "brand": "Sony",
      "price": 149.99,
      "rating": 4.5,
      "availability": "in_stock",
      "features": ["Noise Cancelling", "30hr Battery", "Multipoint Connection"]
    }
  ]
}
```

## Getting Started

1. Sign up for a free BuyWhere developer account at developers.buywhere.ai
2. Get your API key from the dashboard
3. Install the OpenAI Agents SDK and BuyWhere Python client
4. Follow the examples above to build your first shopping copilot

## Call to Action

Ready to build reliable AI shopping agents? Get started with BuyWhere's structured product catalog API today. Visit developers.buywhere.ai for documentation, SDKs, and your free API key.

*Suggested illustration: Architecture diagram showing OpenAI Agent → BuyWhere API → Structured Product Data flow, with comparison to brittle scraping approach*