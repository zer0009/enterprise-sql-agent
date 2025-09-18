#!/usr/bin/env python3
"""
LLM Setup Module
Handles initialization and configuration of Large Language Models
Supports Google Gemini and OpenAI models with fallback logic.
"""

import os
from typing import Optional
from dotenv import load_dotenv

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_openai import ChatOpenAI
except ImportError as e:
    print(f"Missing required packages for LLM setup: {e}")
    print("Run: pip install langchain-google-genai langchain-openai")
    raise

# Load environment variables
load_dotenv()

class LLMManager:
    """Manages LLM initialization and configuration"""
    
    def __init__(self):
        self.llm = None
        self.model_type = None
        self.model_name = None
    
    def setup_llm(self) -> bool:
        """Setup LLM (Google Gemini or OpenAI)"""
        try:
            # Try Google Gemini first
            if self._setup_google_gemini():
                return True
            
            # Try OpenAI as fallback
            if self._setup_openai():
                return True
            
            print("❌ No valid API key found for Google Gemini or OpenAI")
            print("Please set GOOGLE_API_KEY or OPENAI_API_KEY in your .env file")
            return False
            
        except Exception as e:
            print(f"❌ LLM setup failed: {str(e)}")
            return False
    
    def _setup_google_gemini(self) -> bool:
        """Setup Google Gemini LLM"""
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if not google_api_key:
            return False
        
        try:
            model = os.getenv('LLM_MODEL', 'gemini-2.0-flash')
            print(f"Setting up Google Gemini model: {model}...")
            
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=google_api_key,
                temperature=0.1
            )
            
            # Test LLM
            test_response = self.llm.invoke("Hello, can you help me with SQL queries?")
            
            self.model_type = "Google Gemini"
            self.model_name = model
            print("✅ Google Gemini LLM connection successful!")
            return True
            
        except Exception as e:
            print(f"Failed to setup Google Gemini: {str(e)}")
            return False
    
    def _setup_openai(self) -> bool:
        """Setup OpenAI LLM"""
        openai_api_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY_1')
        if not openai_api_key:
            return False
        
        try:
            model = os.getenv('OPENAI_MODEL', 'gpt-4')
            print(f"Setting up OpenAI model: {model}...")
            
            self.llm = ChatOpenAI(
                model=model,
                openai_api_key=openai_api_key,
                temperature=0.1
            )
            
            # Test LLM
            test_response = self.llm.invoke("Hello, can you help me with SQL queries?")
            
            self.model_type = "OpenAI"
            self.model_name = model
            print("✅ OpenAI LLM connection successful!")
            return True
            
        except Exception as e:
            print(f"Failed to setup OpenAI: {str(e)}")
            return False
    
    def get_llm(self):
        """Get the initialized LLM instance"""
        return self.llm
    
    def get_model_info(self) -> dict:
        """Get information about the current model"""
        return {
            "type": self.model_type,
            "name": self.model_name,
            "is_initialized": self.llm is not None
        }
    
    def is_initialized(self) -> bool:
        """Check if LLM is properly initialized"""
        return self.llm is not None
    
    def get_available_models(self) -> dict:
        """Get information about available models and their requirements"""
        return {
            "google_gemini": {
                "models": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
                "env_var": "GOOGLE_API_KEY",
                "model_env_var": "LLM_MODEL",
                "available": bool(os.getenv('GOOGLE_API_KEY'))
            },
            "openai": {
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "env_var": "OPENAI_API_KEY",
                "model_env_var": "OPENAI_MODEL", 
                "available": bool(os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY_1'))
            }
        }
    
    def show_setup_help(self):
        """Show help for setting up LLM API keys"""
        print("\n🔧 LLM Setup Help:")
        print("To use this SQL agent, you need to set up an API key for either:")
        print("\n1. Google Gemini (Recommended):")
        print("   - Get API key from: https://makersuite.google.com/app/apikey")
        print("   - Add to .env file: GOOGLE_API_KEY=your_api_key_here")
        print("   - Optional: Set model with LLM_MODEL=gemini-2.0-flash")
        print("\n2. OpenAI:")
        print("   - Get API key from: https://platform.openai.com/api-keys")
        print("   - Add to .env file: OPENAI_API_KEY=your_api_key_here")
        print("   - Optional: Set model with OPENAI_MODEL=gpt-4")
        print("\nExample .env file:")
        print("GOOGLE_API_KEY=your_google_api_key")
        print("LLM_MODEL=gemini-2.0-flash")
        print("\nOr for OpenAI:")
        print("OPENAI_API_KEY=your_openai_api_key")
        print("OPENAI_MODEL=gpt-4")






