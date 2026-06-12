"""
AI 关键词过滤器，用于从综合技术源（如 Hacker News）中筛选 AI 相关内容
"""

AI_KEYWORDS = [
    'AI', 'artificial intelligence', 'machine learning', 'deep learning',
    'LLM', 'GPT', 'Claude', 'Gemini', 'neural network', 'transformer',
    'diffusion', 'stable diffusion', 'reinforcement learning',
    'computer vision', 'NLP', 'natural language processing',
    'OpenAI', 'Anthropic', 'HuggingFace', 'fine-tuning', 'fine-tune',
    'RAG', 'retrieval augmented', 'agent', 'multimodal', 'large language',
    'foundation model', 'generative AI', 'ChatGPT', 'Llama', 'Mistral',
    'image generation', 'text generation', 'embedding', 'vector',
]


def is_ai_related(title: str, description: str = '') -> bool:
    """判断标题或摘要是否与 AI 相关（大小写不敏感）"""
    text = (title + ' ' + (description or '')).lower()
    return any(kw.lower() in text for kw in AI_KEYWORDS)
