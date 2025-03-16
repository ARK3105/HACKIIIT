import os
import json
import datetime
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from moya.conversation.thread import Thread
from moya.tools.base_tool import BaseTool
from moya.tools.ephemeral_memory import EphemeralMemory
from moya.tools.tool_registry import ToolRegistry
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.agents.azure_openai_agent import AzureOpenAIAgent, AzureOpenAIAgentConfig
from moya.conversation.message import Message


class RecipePlanner:
    """Class to handle operations related to recipe planning and meal suggestions."""
    
    @staticmethod
    def load_recipes() -> List[Dict]:
        """
        Load recipe data from JSON file.
        
        Returns:
            List[Dict]: List of recipe items
        """
        try:
            with open("recipe_planning.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Create the file with an empty array if it doesn't exist
            RecipePlanner._ensure_recipe_file()
            return []
            
    @staticmethod
    def _ensure_recipe_file():
        """Create recipe file if it doesn't exist with empty JSON array"""
        if not os.path.exists("recipe_planning.json"):
            with open("recipe_planning.json", 'w') as f:
                json.dump([], f)  # Initialize with empty array
    
    @staticmethod
    def load_inventory() -> List[Dict]:
        """
        Load inventory data from JSON file.
        
        Returns:
            List[Dict]: List of inventory items
        """
        try:
            with open("item_inventory.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Create the file with an empty array if it doesn't exist
            RecipePlanner._ensure_inventory_file()
            return []
            
    @staticmethod
    def _ensure_inventory_file():
        """Create inventory file if it doesn't exist with empty JSON array"""
        if not os.path.exists("item_inventory.json"):
            with open("item_inventory.json", 'w') as f:
                json.dump([], f)  # Initialize with empty array
    
    @staticmethod
    def load_users() -> List[Dict]:
        """
        Load user data from JSON file.
        
        Returns:
            List[Dict]: List of user data
        """
        try:
            with open("users.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Create the file with an empty array if it doesn't exist
            RecipePlanner._ensure_users_file()
            return []
            
    @staticmethod
    def _ensure_users_file():
        """Create users file if it doesn't exist with empty JSON array"""
        if not os.path.exists("users.json"):
            with open("users.json", 'w') as f:
                json.dump([], f)  # Initialize with empty array
    
    @staticmethod
    def save_recipes(recipes: List[Dict]) -> None:
        """
        Save recipe data to JSON file.
        
        Args:
            recipes (List[Dict]): List of recipe items to save
        """
        with open("recipe_planning.json", "w") as f:
            json.dump(recipes, f, indent=2)
    
    @staticmethod
    def get_user_preferences(user_id: str) -> Dict:
        """
        Get user preferences for recipe recommendations.
        
        Args:
            user_id (str): ID of the user
            
        Returns:
            Dict: User preferences including diet restrictions, allergies, etc.
        """
        users = RecipePlanner.load_users()
        
        for user in users:
            if not isinstance(user, dict):
                continue
                
            if user.get("user_id") == user_id:
                return user.get("preferences", {})
                
        return {}  # Return empty dict if user not found
    
    @staticmethod
    def get_available_ingredients() -> List[Dict]:
        """
        Get all available ingredients from inventory.
        
        Returns:
            List[Dict]: List of available ingredients
        """
        inventory = RecipePlanner.load_inventory()
        available_ingredients = []
        
        for item in inventory:
            if not isinstance(item, dict):
                continue
                
            # Skip items with zero or negative quantity
            if item.get("quantity", 0) <= 0:
                continue
                
            # Skip expired items
            if item.get("expiry_date"):
                try:
                    expiry_date = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
                    if expiry_date < datetime.now().date():
                        continue
                except (ValueError, TypeError):
                    pass
                    
            available_ingredients.append(item)
            
        return available_ingredients
    
    @staticmethod
    def find_recipes_by_ingredients(ingredients: List[Dict], match_threshold: float = 0.7) -> List[Dict]:
        """
        Find recipes that can be made with available ingredients.
        
        Args:
            ingredients (List[Dict]): List of available ingredients
            match_threshold (float): Minimum fraction of recipe ingredients that must be available
            
        Returns:
            List[Dict]: List of recipes that can be made, sorted by match percentage
        """
        recipes = RecipePlanner.load_recipes()
        matches = []
        
        ingredient_ids = [ing["item_id"] for ing in ingredients]
        
        for recipe in recipes:
            if not isinstance(recipe, dict):
                continue
                
            # Count number of matching ingredients
            recipe_ingredients = recipe.get("ingredients", [])
            if not recipe_ingredients:
                continue
                
            matching_count = sum(1 for ing in recipe_ingredients if ing.get("item_id") in ingredient_ids)
            match_percentage = matching_count / len(recipe_ingredients)
            
            # Add recipes that meet the threshold
            if match_percentage >= match_threshold:
                recipe_copy = recipe.copy()
                recipe_copy["match_percentage"] = match_percentage
                recipe_copy["matching_ingredients"] = matching_count
                recipe_copy["total_ingredients"] = len(recipe_ingredients)
                recipe_copy["missing_ingredients"] = []
                
                # Add info about missing ingredients
                for ing in recipe_ingredients:
                    if ing.get("item_id") not in ingredient_ids:
                        recipe_copy["missing_ingredients"].append(ing)
                        
                matches.append(recipe_copy)
                
        # Sort by match percentage (highest first)
        matches.sort(key=lambda x: x["match_percentage"], reverse=True)
        return matches
    
    @staticmethod
    def get_recipe_by_id(recipe_id: str) -> Dict:
        """
        Get a specific recipe by ID.
        
        Args:
            recipe_id (str): ID of the recipe to retrieve
            
        Returns:
            Dict: Recipe data or empty dict if not found
        """
        recipes = RecipePlanner.load_recipes()
        
        for recipe in recipes:
            if not isinstance(recipe, dict):
                continue
                
            if recipe.get("recipe_id") == recipe_id:
                return recipe
                
        return {}  # Return empty dict if recipe not found
    
    @staticmethod
    def add_recipe(recipe_data: Dict) -> bool:
        """
        Add a new recipe to the recipes collection.
        
        Args:
            recipe_data (Dict): Recipe data to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate required fields
        required_fields = ["recipe_id", "name", "ingredients", "steps"]
        for field in required_fields:
            if field not in recipe_data:
                return False
                
        recipes = RecipePlanner.load_recipes()
        
        # Check for duplicate recipe_id
        for recipe in recipes:
            if recipe.get("recipe_id") == recipe_data["recipe_id"]:
                return False  # Duplicate recipe ID
                
        # Add the new recipe
        recipes.append(recipe_data)
        RecipePlanner.save_recipes(recipes)
        return True
    
    @staticmethod
    def generate_meal_plan(user_id: str, days: int = 7) -> List[Dict]:
        """
        Generate a meal plan for the specified number of days.
        
        Args:
            user_id (str): ID of the user
            days (int): Number of days to plan for
            
        Returns:
            List[Dict]: Meal plan with recipes for each day
        """
        preferences = RecipePlanner.get_user_preferences(user_id)
        available_ingredients = RecipePlanner.get_available_ingredients()
        
        # Get suitable recipes
        suitable_recipes = RecipePlanner.find_recipes_by_ingredients(available_ingredients, match_threshold=0.6)
        
        # Filter based on dietary preferences
        if preferences.get("diet"):
            diet = preferences["diet"].lower()
            suitable_recipes = [r for r in suitable_recipes if r.get("diet", "").lower() == diet or not r.get("diet")]
            
        # Filter out allergies
        if preferences.get("allergies"):
            allergies = [a.lower() for a in preferences["allergies"]]
            filtered_recipes = []
            
            for recipe in suitable_recipes:
                has_allergen = False
                for allergen in allergies:
                    if allergen in recipe.get("name", "").lower() or any(allergen in ing.get("name", "").lower() for ing in recipe.get("ingredients", [])):
                        has_allergen = True
                        break
                if not has_allergen:
                    filtered_recipes.append(recipe)
                    
            suitable_recipes = filtered_recipes
            
        # Create meal plan
        meal_plan = []
        today = datetime.now().date()
        
        # Ensure we have enough recipes
        while len(suitable_recipes) < days:
            suitable_recipes.extend(suitable_recipes[:days-len(suitable_recipes)])
            
        # Create a plan for each day
        for day in range(days):
            current_date = today + timedelta(days=day)
            day_plan = {
                "date": current_date.strftime("%Y-%m-%d"),
                "day_name": current_date.strftime("%A"),
                "meals": []
            }
            
            # Add breakfast, lunch, dinner
            meal_types = ["Breakfast", "Lunch", "Dinner"]
            for meal_type in meal_types:
                recipe_index = (day * len(meal_types) + meal_types.index(meal_type)) % len(suitable_recipes)
                recipe = suitable_recipes[recipe_index]
                
                day_plan["meals"].append({
                    "meal_type": meal_type,
                    "recipe_id": recipe.get("recipe_id"),
                    "recipe_name": recipe.get("name"),
                    "match_percentage": recipe.get("match_percentage", 1.0),
                    "missing_ingredients": recipe.get("missing_ingredients", [])
                })
                
            meal_plan.append(day_plan)
            
        return meal_plan

def initialize_data_files():
    """Ensure all required data files exist with proper initial structure"""
    # Initialize inventory file
    if not os.path.exists("item_inventory.json"):
        with open("item_inventory.json", "w") as f:
            json.dump([], f)
            
    # Initialize recipe file
    if not os.path.exists("recipe_planning.json"):
        with open("recipe_planning.json", "w") as f:
            json.dump([], f)
            
    # Initialize users file
    if not os.path.exists("users.json"):
        with open("users.json", "w") as f:
            json.dump([], f)

# Tool definitions for the agent
def find_recipes_tool(match_threshold: float = 0.7) -> str:
    """
    Tool to find recipes that can be made with available ingredients.
    
    Args:
        match_threshold (float): Minimum fraction of recipe ingredients that must be available
        
    Returns:
        str: Formatted string with recipe suggestions
    """
    available_ingredients = RecipePlanner.get_available_ingredients()
    matching_recipes = RecipePlanner.find_recipes_by_ingredients(available_ingredients, match_threshold)
    
    if not matching_recipes:
        return "I couldn't find any recipes that match your available ingredients with the given threshold."
        
    result = f"Found {len(matching_recipes)} recipes you can make with your ingredients:\n\n"
    
    for recipe in matching_recipes:
        match_percent = int(recipe["match_percentage"] * 100)
        result += f"• {recipe['name']} (Match: {match_percent}%)\n"
        result += f"  - {recipe['matching_ingredients']} of {recipe['total_ingredients']} ingredients available\n"
        
        if recipe.get("missing_ingredients"):
            result += "  - Missing: " + ", ".join(ing["name"] for ing in recipe["missing_ingredients"]) + "\n"
            
        result += "\n"
        
    return result

def get_recipe_details_tool(recipe_id: str) -> str:
    """
    Tool to get detailed information about a specific recipe.
    
    Args:
        recipe_id (str): ID of the recipe to retrieve
        
    Returns:
        str: Formatted string with recipe details
    """
    recipe = RecipePlanner.get_recipe_by_id(recipe_id)
    
    if not recipe:
        return f"Recipe with ID {recipe_id} not found."
        
    result = f"# {recipe['name']}\n\n"
    
    # Ingredients section
    result += "## Ingredients\n"
    for ingredient in recipe.get("ingredients", []):
        result += f"- {ingredient.get('quantity', '')} {ingredient.get('name', '')}\n"
    
    # Steps section
    result += "\n## Preparation Steps\n"
    for i, step in enumerate(recipe.get("steps", []), 1):
        result += f"{i}. {step}\n"
        
    # Additional information if available
    if recipe.get("prep_time"):
        result += f"\nPreparation Time: {recipe['prep_time']}\n"
    if recipe.get("cook_time"):
        result += f"Cooking Time: {recipe['cook_time']}\n"
    if recipe.get("servings"):
        result += f"Servings: {recipe['servings']}\n"
    if recipe.get("diet"):
        result += f"Diet Type: {recipe['diet']}\n"
    if recipe.get("cuisine"):
        result += f"Cuisine: {recipe['cuisine']}\n"
        
    return result

def add_recipe_tool(recipe_json: str) -> str:
    """
    Tool to add a new recipe to the collection.
    
    Args:
        recipe_json (str): JSON string containing recipe data
        
    Returns:
        str: Success or failure message
    """
    try:
        recipe_data = json.loads(recipe_json)
    except json.JSONDecodeError:
        return "Failed to add recipe. Invalid JSON format."
        
    success = RecipePlanner.add_recipe(recipe_data)
    
    if success:
        return f"Successfully added recipe '{recipe_data.get('name')}' with ID {recipe_data.get('recipe_id')}."
    else:
        return "Failed to add recipe. Please ensure it has a unique recipe_id and all required fields."
def generate_meal_plan_tool(user_id: str, days: int = 7) -> str:
    """
    Tool to generate a meal plan for the specified number of days.
    
    Args:
        user_id (str): ID of the user
        days (int): Number of days to plan for
        
    Returns:
        str: Formatted string with meal plan
    """
    meal_plan = RecipePlanner.generate_meal_plan(user_id, days)
    
    if not meal_plan:
        return f"Could not generate a meal plan for user {user_id}. Please check inventory and recipes."
        
    result = f"📋 {days}-DAY MEAL PLAN\n"
    result += "=" * 40 + "\n\n"
    
    for day in meal_plan:
        result += f"📅 {day['day_name']} ({day['date']})\n"
        result += "-" * 30 + "\n"
        
        for meal in day.get("meals", []):
            match_percent = int(meal.get("match_percentage", 1.0) * 100)
            result += f"• {meal['meal_type']}: {meal['recipe_name']} (Match: {match_percent}%)\n"
            
            if meal.get("missing_ingredients"):
                result += "  - Missing: " + ", ".join(ing["name"] for ing in meal["missing_ingredients"]) + "\n"
                
        result += "\n"
        
    result += "To see detailed recipe instructions, use the get_recipe_details tool with the recipe ID.\n"
    
    return result

def get_available_ingredients_tool() -> str:
    """
    Tool to list all available ingredients in the inventory.
    
    Returns:
        str: Formatted string with available ingredients
    """
    ingredients = RecipePlanner.get_available_ingredients()
    
    if not ingredients:
        return "Your inventory is empty. Please add some ingredients to get started."
        
    # Group by category
    categories = {}
    for item in ingredients:
        category = item.get("category", "Uncategorized")
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
        
    result = "📦 AVAILABLE INGREDIENTS\n"
    result += "=" * 40 + "\n\n"
    
    for category, items in categories.items():
        result += f"📑 {category}\n"
        result += "-" * 20 + "\n"
        
        for item in items:
            expiry_info = ""
            if item.get("expiry_date"):
                try:
                    expiry_date = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
                    days_until_expiry = (expiry_date - datetime.now().date()).days
                    expiry_info = f" (expires in {days_until_expiry} days)"
                except (ValueError, TypeError):
                    pass
                    
            result += f"• {item['name']} - {item.get('quantity', '')} {item.get('unit', '')}{expiry_info}\n"
            
        result += "\n"
        
    return result

def get_user_preferences_tool(user_id: str) -> str:
    """
    Tool to get user preferences for recipe recommendations.
    
    Args:
        user_id (str): ID of the user
        
    Returns:
        str: Formatted string with user preferences
    """
    preferences = RecipePlanner.get_user_preferences(user_id)
    
    if not preferences:
        return f"No preferences found for user {user_id}."
        
    result = "👤 USER PREFERENCES\n"
    result += "=" * 30 + "\n\n"
    
    for key, value in preferences.items():
        result += f"• {key.capitalize()}: "
        
        if isinstance(value, list):
            result += ", ".join(value)
        else:
            result += str(value)
            
        result += "\n"
        
    return result

def setup_agent():
    """
    Set up the AzureOpenAI agent with memory capabilities and return the orchestrator and agent.
    
    Returns:
        tuple: A tuple containing the orchestrator and the agent.
    """
    # Set up memory components
    tool_registry = ToolRegistry()
    EphemeralMemory.configure_memory_tools(tool_registry)
    
    # Register recipe planning tools
    recipes_tool = BaseTool(
        name="find_recipes_tool",
        description="Find recipes that can be made with available ingredients",
        function=find_recipes_tool,
        parameters={
            "match_threshold": {
                "type": "number",
                "description": "Minimum fraction of recipe ingredients that must be available (default: 0.7)"
            }
        },
        required=[]  # Make match_threshold optional
    )
    tool_registry.register_tool(recipes_tool)
    
    recipe_details_tool = BaseTool(
        name="get_recipe_details_tool",
        description="Get detailed information about a specific recipe",
        function=get_recipe_details_tool,
        parameters={
            "recipe_id": {
                "type": "string",
                "description": "ID of the recipe to retrieve"
            }
        },
        required=["recipe_id"]
    )
    tool_registry.register_tool(recipe_details_tool)
    
    add_recipe_tool_obj = BaseTool(
        name="add_recipe_tool",
        description="Add a new recipe to the collection",
        function=add_recipe_tool,
        parameters={
            "recipe_json": {
                "type": "string",
                "description": "JSON string containing recipe data"
            }
        },
        required=["recipe_json"]
    )
    tool_registry.register_tool(add_recipe_tool_obj)
    
    meal_plan_tool = BaseTool(
        name="generate_meal_plan_tool",
        description="Generate a meal plan for the specified number of days",
        function=generate_meal_plan_tool,
        parameters={
            "user_id": {
                "type": "string",
                "description": "ID of the user"
            },
            "days": {
                "type": "integer",
                "description": "Number of days to plan for (default: 7)"
            }
        },
        required=["user_id"]  # Make days optional
    )
    tool_registry.register_tool(meal_plan_tool)
    
    ingredients_tool = BaseTool(
        name="get_available_ingredients_tool",
        description="List all available ingredients in the inventory",
        function=get_available_ingredients_tool,
        parameters={},
        required=[]
    )
    tool_registry.register_tool(ingredients_tool)
    
    preferences_tool = BaseTool(
        name="get_user_preferences_tool",
        description="Get user preferences for recipe recommendations",
        function=get_user_preferences_tool,
        parameters={
            "user_id": {
                "type": "string",
                "description": "ID of the user"
            }
        },
        required=["user_id"]
    )
    tool_registry.register_tool(preferences_tool)
    
    # Create agent configuration
    agent_config = AzureOpenAIAgentConfig(
        agent_name="recipe_planning_agent",
        description="An agent that suggests meal ideas based on available ingredients",
        model_name="gpt-4o",
        agent_type="RecipePlanningAgent",
        tool_registry=tool_registry,
        system_prompt="""
            You are a Recipe & Meal Planning Agent, focused on helping users plan meals without extra shopping trips.
            Your primary responsibilities include:
            1. Suggesting recipes based on available ingredients in the user's inventory
            2. Creating customized meal plans that maximize the use of available ingredients
            3. Considering user preferences, dietary restrictions, and allergies
            4. Providing detailed recipe instructions and information
            5. Helping users make the most of ingredients before they expire
            6. Minimizing food waste by suggesting recipes for soon-to-expire items
            7. Organizing meals efficiently throughout the week
            
            You have access to tools that help you find recipes, generate meal plans, and view available ingredients.
            Always provide practical and actionable meal planning advice.
            
            When users ask about meal ideas, first check their available ingredients, then consider their preferences,
            and finally suggest recipes or meal plans that make the best use of what they have.
            
            Store conversation context in memory to provide personalized recommendations.
        """,
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview",
        organization=None
    )
    
    # Create Azure OpenAI agent with memory capabilities
    agent = AzureOpenAIAgent(
        config=agent_config
    )
    
    # Set up registry and orchestrator
    agent_registry = AgentRegistry()
    agent_registry.register_agent(agent)
    orchestrator = SimpleOrchestrator(
        agent_registry=agent_registry,
        default_agent_name="recipe_planning_agent"
    )
    
    return orchestrator, agent

def main():
    # Initialize data files
    initialize_data_files()
    
    # Set up agent
    orchestrator, agent = setup_agent()
    thread_id = "recipe_planning_001"
    
    # Store initial message
    EphemeralMemory.store_message(
        thread_id=thread_id, 
        sender="system", 
        content=f"Starting recipe planning session, thread ID = {thread_id}"
    )
    
    print("Welcome to Recipe & Meal Planning Assistant! (Type 'quit' or 'exit' to end)")
    print("I'll help you plan meals based on ingredients you already have.")
    print("-" * 60)
    
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        
        # Check for exit command
        if user_input.lower() in ['quit', 'exit']:
            print("\nGoodbye! Happy cooking with your planned meals!")
            break
            
        # Store user message
        EphemeralMemory.store_message(thread_id=thread_id, sender="user", content=user_input)
        
        # Get conversation summary and enrich input
        session_summary = EphemeralMemory.get_thread_summary(thread_id)
        enriched_input = f"{session_summary}\nCurrent user message: {user_input}"
        
        # Print Assistant prompt
        print("\nAssistant: ", end="", flush=True)
        
        # Define callback for streaming
        def stream_callback(chunk):
            print(chunk, end="", flush=True)
            
        # Get response using stream_callback
        response = orchestrator.orchestrate(
            thread_id=thread_id,
            user_message=enriched_input,
            stream_callback=stream_callback
        )
        
        # Store assistant's response in memory
        EphemeralMemory.store_message(thread_id=thread_id, sender="assistant", content=response)
        
        # Print newline after response
        print()

if __name__ == "__main__":
    main()