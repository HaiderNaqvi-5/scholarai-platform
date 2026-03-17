import os
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel

class ModelRouter:
    """
    Service to route prompt requests to different LLMs based on performance or cost requirements.
    Initially supports Gemini 2.0 Flash as the primary workhorse.
    """
    def __init__(self):
        self.primary_model = "gemini-2.0-flash"
        self.api_key = os.getenv("GOOGLE_API_KEY")

    def get_model(
        self, 
        task: str = "general", 
        temperature: float = 0.2,
        streaming: bool = False
    ) -> BaseChatModel:
        """
        Returns a configured LangChain chat model based on the routing logic.
        """
        # Routing Logic
        if task == "critical_reasoning":
            # Logic to switch to Gemini 1.5 Pro if high precision is needed
            model_name = "gemini-1.5-pro"
        else:
            model_name = self.primary_model

        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=self.api_key,
            streaming=streaming
        )

# Global router instance
model_router = ModelRouter()
