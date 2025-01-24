"""
Main agent module containing core decision-making logic and tool orchestration.
"""
import concurrent.futures
import json
import openai
from typing import Dict, List, Any
from .tools import WebScraper, CalendarTool
from .preprocessing import clean_query, validate_parameters, preprocess_for_embedding
from .approval import ApprovalManager, call_tool_with_approval
from .rag_config import load_rag_model_config, load_vector_db_config, choose_rag_model, choose_vector_db

class Agent:
    def __init__(self, config_path: str = "config/agent_config.json"):
        # Load all configurations
        self.config = self._load_config("config/agent_config.json")
        self.model_config = self._load_config("config/model_config.json")
        self.tools_config = self._load_config("config/tool_config.json")
        self.keys_config = self._load_config("config/keys_config.json")
        self.rag_config = load_rag_model_config()
        self.vector_db_config = load_vector_db_config()
        
        # Initialize components
        self.approval_manager = ApprovalManager()
        self.tools = self._initialize_tools()
        self._setup_openai()
        
        # Set default RAG and Vector DB
        self.current_rag = self._setup_default_rag()
        self.current_vector_db = self._setup_default_vector_db()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            return json.load(f)
            
    def _setup_openai(self):
        """Configure OpenAI API."""
        openai.api_key = self.keys_config['openai']['api_keys']['normal']
            
    def _initialize_tools(self) -> Dict:
        """Initialize all required tools based on configuration."""
        return {
            'web_scraper': WebScraper(),
            'calendar': CalendarTool()
        }
        
    def _setup_default_rag(self) -> Dict:
        """Setup default RAG model."""
        try:
            return choose_rag_model('simple_rag', self.rag_config)
        except ValueError as e:
            print(f"Error setting up RAG: {e}")
            return None
            
    def _setup_default_vector_db(self) -> Dict:
        """Setup default vector database."""
        try:
            return choose_vector_db('sqlite', self.vector_db_config)
        except ValueError as e:
            print(f"Error setting up Vector DB: {e}")
            return None
            
    def choose_model(self, model_name: str) -> Dict:
        """Select the model and return its parameters."""
        model = self.model_config["models"].get(model_name, None)
        if model:
            return model
        raise ValueError(f"Model {model_name} not found in configuration.")
        
    def call_openai_model(self, model_name: str, prompt: str) -> str:
        """Call OpenAI's API with the selected model and its parameters."""
        model = self.choose_model(model_name)
        response = openai.Completion.create(
            model=model_name,
            prompt=prompt,
            temperature=model["temperature"],
            max_tokens=model["max_tokens"],
            top_p=model["top_p"],
            frequency_penalty=model["frequency_penalty"],
            presence_penalty=model["presence_penalty"]
        )
        return response.choices[0].text.strip()
        
    def run_agents_parallel(self, tasks: List[Dict]) -> List[Any]:
        """Run agents in parallel."""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(self.run_agent_task, tasks))
        return results
        
    def run_agent_task(self, task: Dict) -> Any:
        """Run a specific agent task."""
        # Clean and validate task parameters
        if 'params' in task:
            task['params'] = validate_parameters(task['params'])
            
        if task.get("is_model_task"):
            return self.call_openai_model(
                task["model_name"],
                task["prompt"]
            )
        else:
            return call_tool_with_approval(
                task["tool"],
                task["params"]
            )
            
    def process_tasks(self, tasks: List[Dict]) -> List[Any]:
        """Process multiple tasks in parallel."""
        # Validate all tasks before processing
        for task in tasks:
            if 'query' in task:
                task['query'] = clean_query(task['query'])
            if task.get('needs_embedding'):
                task['text'] = preprocess_for_embedding(task['text'])
                
        return self.run_agents_parallel(tasks)

def main():
    """Main function to run the agent system."""
    agent = Agent()
    
    # Example tasks
    tasks = [
        {
            "tool": "web_scraper",
            "params": {"url": "http://example.com", "max_depth": 3},
            "is_model_task": False
        },
        {
            "tool": "calendar",
            "params": {"calendar_id": "primary", "max_events": 5},
            "is_model_task": False
        },
        {
            "is_model_task": True,
            "model_name": "gpt-4",
            "prompt": "Write a Python script to fetch calendar events."
        }
    ]
    
    results = agent.process_tasks(tasks)
    print(results)

if __name__ == "__main__":
    main()
