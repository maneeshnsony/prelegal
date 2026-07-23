---
name: Cerebras Inference
description: Use this to write code to call an LLM using  LiteLLM and OpenRouter with the Cerebras inference provider. Use Structured Outputs to interpret the results and populate fields in the legal document.
---

# Calling an LLM via Cerebras
These instructions allow you write code to call an LLM with Cerebras specified as the inference provider. This method uses LiteLLM and OpenRouter. 

## Setup
The OPENROUTER_API_KEY must be set in the .env file and loaded in as an environment variable.

The us project must include liteLLM and pydantic.
`uv add litellm pydantic`

## Code snippets
Use code like these examples in order to use Cerebras.

### Import and constants
```python
from litellm import LiteLLM
MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}
```

### Code to call via Cerebras for a text response
```python
response = complettion(model=MODEL, messages=messages, reasoning_efforts="low", extra_body=EXTRA_BODY)
result = response.choices[0].message.content
```

### Code to call via Cerebras for a structured output response
```python
response = complettion(model=MODEL, messages=messages, response_format=MyBaseModelSubClass, reasoning_efforts="low", extra_body=EXTRA_BODY)
result = response.choices[0].message.content
result_as_object = MyBaseModelSubClass.model_validate_json(result)
```
