"""Extract JSON from text and fix invalid escape sequences."""
import json
import re


def extract_json_and_fix_escapes(text):
    """Extract JSON from text and fix invalid escape sequences."""
    # Extract content from first { to last }
    pattern = r'(\{.*\})'
    match = re.search(pattern, text, re.DOTALL)

    if match:
        json_str = match.group(1)
        # Fix invalid escape sequences in JSON
        fixed_json = re.sub(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'\\\\', json_str)
        try:
            # Try to parse the fixed JSON
            json_obj = json.loads(fixed_json)
            return json_obj
        except json.JSONDecodeError as e:
            print(f'JSON parsing error: {e}')
            # Return the fixed string if parsing fails
            return fixed_json
    else:
        return None
