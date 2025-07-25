import google.generativeai as genai
from flask import current_app

def process_user_query(message, columns, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        You are a GIS visualization assistant. Analyze this user query and determine:
        1. Is it a general question about GIS concepts?
        2. Is it a request for a specific action (map, stats, etc)?
        3. What parameters are needed for the action?
        4. For data explanation: brief, friendly with emojis
        
        Available columns: {columns}
        
        Examples:
        - "What is NDVI?" → GENERAL
        - "Show me a map of population" → ACTION:MAP (column=population)
        - "Calculate statistics for income" → ACTION:STATS (column=income)
        - "Add a scale bar to the map" → ACTION:MAP_ELEMENT (element=scale_bar)
        
        Respond in this format:
        TYPE: [GENERAL|ACTION:type]
        RESPONSE: [your response]
        PARAMS: [key=value, ...] (if applicable)
        
        User query: {message}
        """
        
        response = model.generate_content(prompt)
        response_text = response.text
        
        if "TYPE: GENERAL" in response_text:
            return response_text.split("RESPONSE:")[1].strip(), None
        elif "TYPE: ACTION:" in response_text:
            action_type = response_text.split("TYPE: ACTION:")[1].split("\n")[0].strip()
            response_msg = response_text.split("RESPONSE:")[1].split("PARAMS:")[0].strip()
            
            params = {}
            if "PARAMS:" in response_text:
                param_str = response_text.split("PARAMS:")[1].strip()
                for pair in param_str.split(","):
                    if "=" in pair:
                        key, val = pair.split("=", 1)
                        params[key.strip()] = val.strip()
            
            if action_type == "MAP":
                column = params.get("column", "")
                if column and column in columns:
                    return response_msg, [column]
                else:
                    return f"Column '{column}' not found. Available columns: {', '.join(columns)}", None
            else:
                return response_msg, None
        else:
            return response_text, None
            
    except Exception as e:
        return f"AI Error: {str(e)}", None

# import google.generativeai as genai
# from flask import current_app 
# AI_COMMAND = """
# You are a GIS visualization assistant. Follow these rules:

# 1. When asked for column names, return only the list
# 2. For visualization requests, find best column match
# 3. For data explanation: brief, friendly with emojis
# 4. Be concise - column names when possible
# 5. Handle conversation naturally
# """

# def process_user_query(message, columns, api_key):
#     try:
#         genai.configure(api_key=api_key)
#         model = genai.GenerativeModel("gemini-1.5-flash")
        
#         base_prompt = AI_COMMAND
#         if columns:  # Only include columns if we have a file
#             base_prompt += f"\nCOLUMNS: {columns}"
            
#         prompt = f"{base_prompt}\nQUERY: {message}"
#         response = model.generate_content(prompt)
        
#         return parse_response(response.text, columns)
#     except Exception as e:
#         return f"AI Error: {str(e)}", None

# def parse_response(text, columns):
#     text = text.strip()
    
#     # Check for column existence only if we have columns
#     if columns and "doesn't exist" in text:
#         return text, None
        
#     # Extract column name from response
#     if columns:
#         for column in columns:
#             if column.lower() in text.lower():
#                 return text, column  # Return the matched column name
    
#     # For general conversation, return text with no column
#     return text, None