import json
import datetime
import requests
import os
from typing import Dict, Any, List, Optional
from .function_definitions import function_definitions

# In-memory storage for reminders (in a real app, this would be a database)
reminders = []

def set_reminder(title: str, date: str, time: str, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Set a reminder for a health or wellness activity.
    
    Args:
        title: The title of the reminder
        date: The date for the reminder in YYYY-MM-DD format
        time: The time for the reminder in HH:MM format (24-hour)
        description: A detailed description of the reminder (optional)
        
    Returns:
        Dict containing the reminder details and confirmation message
    """
    try:
        # Validate date and time format
        datetime_obj = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        
        # Create reminder object
        reminder = {
            "id": len(reminders) + 1,
            "title": title,
            "description": description or "",
            "datetime": datetime_obj.isoformat(),
            "created_at": datetime.datetime.now().isoformat()
        }
        
        # Add to reminders list (in a real app, save to database)
        reminders.append(reminder)
        
        return {
            "success": True,
            "message": f"Reminder set for {date} at {time}",
            "reminder": reminder
        }
    except ValueError:
        return {
            "success": False,
            "message": "Invalid date or time format. Please use YYYY-MM-DD for date and HH:MM for time."
        }

def search_nutrition(food_item: str, quantity: float = 100, unit: str = "g") -> Dict[str, Any]:
    """
    Search for nutrition information about a food item.
    
    Args:
        food_item: The food item to search for
        quantity: The quantity of the food item (default: 100)
        unit: The unit of measurement (default: g)
        
    Returns:
        Dict containing the nutrition information
    """
    try:
        # In a real application, you would use a nutrition API like Nutritionix, USDA, or Edamam
        # For this example, we'll simulate a response with mock data
        
        # Mock nutrition data for common foods (per 100g unless specified)
        mock_nutrition_db = {
            "apple": {
                "calories": 52,
                "protein": 0.3,
                "carbs": 14,
                "fat": 0.2,
                "fiber": 2.4,
                "sugar": 10.3,
                "serving_size": 100,
                "serving_unit": "g"
            },
            "banana": {
                "calories": 89,
                "protein": 1.1,
                "carbs": 22.8,
                "fat": 0.3,
                "fiber": 2.6,
                "sugar": 12.2,
                "serving_size": 100,
                "serving_unit": "g"
            },
            "chicken breast": {
                "calories": 165,
                "protein": 31,
                "carbs": 0,
                "fat": 3.6,
                "fiber": 0,
                "sugar": 0,
                "serving_size": 100,
                "serving_unit": "g"
            },
            "salmon": {
                "calories": 206,
                "protein": 22,
                "carbs": 0,
                "fat": 13,
                "fiber": 0,
                "sugar": 0,
                "serving_size": 100,
                "serving_unit": "g"
            },
            "broccoli": {
                "calories": 34,
                "protein": 2.8,
                "carbs": 6.6,
                "fat": 0.4,
                "fiber": 2.6,
                "sugar": 1.7,
                "serving_size": 100,
                "serving_unit": "g"
            },
            "rice": {
                "calories": 130,
                "protein": 2.7,
                "carbs": 28,
                "fat": 0.3,
                "fiber": 0.4,
                "sugar": 0.1,
                "serving_size": 100,
                "serving_unit": "g"
            },
            "egg": {
                "calories": 155,
                "protein": 12.6,
                "carbs": 1.1,
                "fat": 11.5,
                "fiber": 0,
                "sugar": 1.1,
                "serving_size": 100,
                "serving_unit": "g"
            }
        }
        
        # Find the closest match in our mock database
        food_item = food_item.lower()
        matched_food = None
        
        for key in mock_nutrition_db:
            if key in food_item or food_item in key:
                matched_food = key
                break
        
        if not matched_food:
            return {
                "success": False,
                "message": f"Nutrition information for '{food_item}' not found."
            }
        
        # Get the nutrition data
        nutrition_data = mock_nutrition_db[matched_food]
        
        # Calculate based on quantity and unit (simplified conversion)
        conversion_factor = 1.0
        if unit != "g":
            # Simple conversion factors (in a real app, use a proper conversion library)
            unit_conversions = {
                "oz": 28.35,  # 1 oz = 28.35g
                "cup": 128,   # Rough estimate, depends on the food
                "tbsp": 15,   # Tablespoon
                "tsp": 5,     # Teaspoon
                "serving": nutrition_data["serving_size"]  # Use the serving size from the data
            }
            
            if unit in unit_conversions:
                conversion_factor = unit_conversions[unit] / 100  # Convert to per 100g
            else:
                return {
                    "success": False,
                    "message": f"Unsupported unit: {unit}"
                }
        
        # Calculate nutrition values based on quantity and unit
        adjusted_nutrition = {}
        for key, value in nutrition_data.items():
            if key not in ["serving_size", "serving_unit"]:
                adjusted_nutrition[key] = round(value * conversion_factor * quantity, 1)
        
        return {
            "success": True,
            "food_item": matched_food,
            "quantity": quantity,
            "unit": unit,
            "nutrition": adjusted_nutrition
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Error retrieving nutrition information: {str(e)}"
        }

def get_all_reminders() -> List[Dict[str, Any]]:
    """
    Get all reminders.
    
    Returns:
        List of all reminders
    """
    return reminders

def handle_function_call(function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle function calls from the AI.
    
    Args:
        function_name: The name of the function to call
        arguments: The arguments to pass to the function
        
    Returns:
        Dict containing the result of the function call
    """
    if function_name == "set_reminder":
        return set_reminder(
            title=arguments.get("title"),
            date=arguments.get("date"),
            time=arguments.get("time"),
            description=arguments.get("description")
        )
    elif function_name == "search_nutrition":
        return search_nutrition(
            food_item=arguments.get("food_item"),
            quantity=arguments.get("quantity", 100),
            unit=arguments.get("unit", "g")
        )
    else:
        return {
            "success": False,
            "message": f"Unknown function: {function_name}"
        } 