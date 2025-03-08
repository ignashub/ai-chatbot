# Function definitions for OpenAI
function_definitions = [
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Set a reminder for a health or wellness activity",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the reminder"
                    },
                    "description": {
                        "type": "string",
                        "description": "A detailed description of the reminder"
                    },
                    "date": {
                        "type": "string",
                        "description": "The date for the reminder in YYYY-MM-DD format"
                    },
                    "time": {
                        "type": "string",
                        "description": "The time for the reminder in HH:MM format (24-hour)"
                    }
                },
                "required": ["title", "date", "time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_nutrition",
            "description": "Search for nutrition information about a food item",
            "parameters": {
                "type": "object",
                "properties": {
                    "food_item": {
                        "type": "string",
                        "description": "The food item to search for nutrition information"
                    },
                    "quantity": {
                        "type": "number",
                        "description": "The quantity of the food item (default: 100g)"
                    },
                    "unit": {
                        "type": "string",
                        "description": "The unit of measurement (g, oz, cup, etc.)",
                        "enum": ["g", "oz", "cup", "tbsp", "tsp", "serving"]
                    }
                },
                "required": ["food_item"]
            }
        }
    }
] 