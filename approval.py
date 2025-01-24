"""
Module for handling tool approval requirements and validation.
"""
from typing import Dict, Any, Optional, Union
import json
from dataclasses import dataclass
from enum import Enum, auto
from .tools import scrape_website, fetch_calendar_events

class ApprovalStatus(Enum):
    """Enum for approval status."""
    PENDING = auto()
    APPROVED = auto()
    REJECTED = auto()

@dataclass
class ApprovalRequest:
    """Data class for approval requests."""
    tool_name: str
    params: Dict[str, Any]
    description: str
    status: ApprovalStatus = ApprovalStatus.PENDING

class ApprovalManager:
    """Manages tool approvals and parameter validation."""
    
    def __init__(self, config_path: str = "config/tool_config.json"):
        """Initialize the approval manager with tool configurations."""
        self.tool_config = self._load_config(config_path)
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load tool configuration from JSON file."""
        with open(config_path, 'r') as f:
            return json.load(f)
            
    def is_approval_required(self, tool_name: str) -> bool:
        """Check if a tool requires approval."""
        tool_info = self.tool_config["tools"].get(tool_name)
        if not tool_info:
            raise ValueError(f"Tool {tool_name} not found in configuration")
        return tool_info.get("approval_required", False)
        
    def validate_params(self, tool_name: str, params: Dict[str, Any]) -> bool:
        """
        Validate parameters against tool configuration.
        
        Args:
            tool_name: Name of the tool
            params: Parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        tool_info = self.tool_config["tools"].get(tool_name)
        if not tool_info:
            raise ValueError(f"Tool {tool_name} not found in configuration")
            
        expected_params = tool_info.get("params", {})
        
        # Check all required parameters are present
        for param_name, param_type in expected_params.items():
            if param_name not in params:
                return False
            
            # Validate parameter type
            if param_type == "string" and not isinstance(params[param_name], str):
                return False
            elif param_type == "integer" and not isinstance(params[param_name], int):
                return False
                
        return True
        
    def get_user_approval(self, request: ApprovalRequest) -> bool:
        """
        Get approval from user via command line.
        
        Args:
            request: The approval request to present to the user
            
        Returns:
            True if approved, False if rejected
        """
        print(f"\nTool: {request.tool_name} requires approval")
        print(f"Description: {request.description}")
        print(f"Parameters: {request.params}")
        
        while True:
            approval = input("\nDo you approve? (y/n): ").lower()
            if approval in ['y', 'n']:
                return approval == 'y'
            print("Please enter 'y' for yes or 'n' for no.")
        
    def request_approval(self, tool_name: str, params: Dict[str, Any]) -> ApprovalRequest:
        """
        Request approval for tool usage.
        
        Args:
            tool_name: Name of the tool
            params: Tool parameters
            
        Returns:
            ApprovalRequest object
        """
        tool_info = self.tool_config["tools"].get(tool_name)
        if not tool_info:
            raise ValueError(f"Tool {tool_name} not found in configuration")
            
        # Validate parameters before creating request
        if not self.validate_params(tool_name, params):
            raise ValueError(f"Invalid parameters for tool {tool_name}")
            
        request = ApprovalRequest(
            tool_name=tool_name,
            params=params,
            description=tool_info["description"]
        )
        
        self.pending_approvals[tool_name] = request
        
        # Get user approval immediately
        if self.get_user_approval(request):
            self.approve_request(tool_name)
        else:
            self.reject_request(tool_name)
            
        return request
        
    def approve_request(self, tool_name: str) -> None:
        """Approve a pending tool request."""
        request = self.pending_approvals.get(tool_name)
        if not request:
            raise ValueError(f"No pending approval for tool {tool_name}")
        request.status = ApprovalStatus.APPROVED
        
    def reject_request(self, tool_name: str) -> None:
        """Reject a pending tool request."""
        request = self.pending_approvals.get(tool_name)
        if not request:
            raise ValueError(f"No pending approval for tool {tool_name}")
        request.status = ApprovalStatus.REJECTED
        
    def get_request_status(self, tool_name: str) -> Optional[ApprovalStatus]:
        """Get the status of a tool approval request."""
        request = self.pending_approvals.get(tool_name)
        return request.status if request else None

def call_tool_with_approval(tool_name: str, params: Dict[str, Any]) -> Any:
    """
    Call a tool with approval handling.
    
    Args:
        tool_name: Name of the tool to call
        params: Parameters for the tool
        
    Returns:
        Tool execution result or error message
    """
    approval_manager = ApprovalManager()
    
    if approval_manager.is_approval_required(tool_name):
        request = approval_manager.request_approval(tool_name, params)
        if request.status != ApprovalStatus.APPROVED:
            return {"status": "error", "message": f"Tool {tool_name} was not approved"}
    
    # Execute the approved tool
    try:
        if tool_name == "scrape_website":
            result = scrape_website(**params)
        elif tool_name == "fetch_calendar_events":
            result = fetch_calendar_events(**params)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
            
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
