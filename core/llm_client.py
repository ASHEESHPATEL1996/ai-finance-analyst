from core.config import settings

MODELS = {
    "groq": "llama-3.1-8b-instant",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
}

def get_llm(temperature: float = 0.3):
    provider = settings.llm_provider.lower()

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=settings.groq_api_key,
            model=MODELS["groq"],
            temperature=temperature,
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model=MODELS["openai"],
            temperature=temperature,
        )

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model=MODELS["anthropic"],
            temperature=temperature,
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Choose from: groq, openai, anthropic")