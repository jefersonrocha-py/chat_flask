def get_prompt(query: str, mode: str, audio_info: str = None) -> str:
    """
    Constructs the prompt for the agent based on the operation mode and the user's query.
    
    Args:
        query (str): User query.
        mode (str): Operation mode ("Educacional", "Pesquisa Web", "Análise").
        audio_info (str, optional): Audio information if provided.
    
    Returns:
        str: Formatted prompt in English.
    """
    mode_prefixes = {
        "Educacional": (
            "You are an educational expert specialized in language teaching and correction (English, Spanish, and French). "
            "If the user sends an audio file, transcribe it, correct the pronunciation, identify errors, and provide detailed feedback "
            "including grammar, vocabulary, and pronunciation tips. If the user sends text, correct it and suggest improvements."
        ),
        "Pesquisa Web": (
            "You are a research agent specialized in providing detailed, well-sourced answers based on web information. "
            "Provide accurate data, explain concepts clearly, and cite relevant sources if necessary."
        ),
        "Análise": (
            "You are a data analysis agent. Your task is to extract, interpret, and visualize raw data, generating insights and reports "
            "to support strategic decisions. Use your statistical and visualization skills to transform data into actionable insights. "
            "Always explain your methodology and the analysis performed."
        ),
    }
    prefix = mode_prefixes.get(mode, "")
    user_query = query.strip() if query and query.strip() else "[Audio Input]"
    if audio_info and audio_info.strip():
        user_query += f"\nAudio: {audio_info.strip()}"
    return f"{prefix}\n\nUser Query: {user_query}"
