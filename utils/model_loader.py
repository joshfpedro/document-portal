import os
import sys
from dotenv import load_dotenv
from utils.config_loader import load_config

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
# from langchain_openai import ChatOpenAI
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException

log = CustomLogger().get_logger(__name__)

class ModelLoader:
    """
    A utility class to load embeddings and large language models (LLMs) based on configuration.
    """
    
    def __init__(self):
        
        load_dotenv()
        self._validate_env()
        self.config = load_config()
        # self.config = full_config["faiss_db"]
        log.info("Configuration loaded successfully.", config_keys=list(self.config.keys()))
    
    def _validate_env(self):
        """
        Validate required environment variables for model loading.
        Ensure API keys exist for the selected models.
        """
        required_vars = ["GOOGLE_API_KEY", "GROQ_API_KEY"]
        self.api_keys = {key:os.getenv(key) for key in required_vars}
        missing = [k for k, v in self.api_keys.items() if not v]
        if missing:
            log.error("Missing required environment variables", missing_vars=missing)
            raise DocumentPortalException(f"Missing required environment variables", sys)
        log.info("All required environment variables are validated.", available_keys=[k for k in self.api_keys if self.api_keys[k]])
    
    def load_embeddings(self):
        """
        Load and return the embedding model.
        """
        try:
            log.info("Loading embedding model...")
            model_name = self.config["embedding_model"]["model_name"]
            return GoogleGenerativeAIEmbeddings(model=model_name)
        except Exception as e:
            log.error("Failed to load embedding model", error=str(e))
            raise DocumentPortalException("Failed to load embedding model", sys)
    
    def load_llm(self):
        """
        Load and return the LLM model
        """
        """Load LLM dynamically based on provider in config."""
        
        llm_block = self.config["llm"]
        
        # Default provider is groq
        provider_key = os.getenv("LLM_PROVIDER", "groq") # Default groq
        
        if provider_key not in llm_block:
            log.error("LLM provider not found in config", provider_key=provider_key)
            raise ValueError(f"LLM provider '{provider_key}' not found in config.")
        
        llm_config = llm_block[provider_key]
        provider = llm_config.get("provider")
        model_name = llm_config.get("model_name")
        temperature = llm_config.get("temperature", 0.2)
        max_tokens = llm_config.get("max_tokens", 2048)
        
        log.info("Loading LLM model", provider=provider, model=model_name, temperature=temperature, max_tokens=max_tokens)
        
        if provider == "google":
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        elif provider == "groq":
            llm = ChatGroq(
                model=model_name,
                # api_key=self.api_keys["GROQ_API_KEY"], # API key is automatically picked from env variable
                temperature=temperature
            )
        # elif provider == "openai":
        #     llm = ChatOpenAI(
        #         model_name=model_name,
        #         temperature=temperature,
        #         api_key=self.api_keys["OPENAI_API_KEY"],
        #         max_tokens=max_tokens
        #     )
        else:
            log.error("Unsupported LLM provider", provider=provider)
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        return llm
        
        
if __name__ == "__main__":
    loader = ModelLoader()
    
    # Test loading embeddings
    embeddings = loader.load_embeddings()
    print(f"Embeddings loaded: {embeddings}")
    
    # Test loading LLM based on YAML config
    llm = loader.load_llm()
    print(f"LLM loaded: {llm}")
    
    # Test the ModelLoader class
    result = llm.invoke("Hello, how are you?")
    print(f"LLM response: {result.content}")