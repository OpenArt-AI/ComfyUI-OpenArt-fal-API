import json
import requests
from .fal_utils import FalConfig, ImageUtils

# Initialize FalConfig for consistency with other nodes
fal_config = FalConfig()


class CommonAPINode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_url": ("STRING", {"default": "https://openart-ai--llm-service.modal.run/image_to_prompt", "multiline": False}),
                "json_payload": ("STRING", {"default": '{\n  "image_url": "",\n  "model": "florence",\n  "prompt": ""\n}', "multiline": True}),
            },
            "optional": {
                "image": ("IMAGE",),
                "headers": ("STRING", {"default": '{\n  "Content-Type": "application/json"\n}', "multiline": True}),
                "timeout": ("INT", {"default": 30, "min": 5, "max": 300}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "call_api"
    CATEGORY = "FAL/Common"

    def call_api(self, api_url, json_payload, image=None, headers='{"Content-Type": "application/json"}', timeout=30):
        try:
            # Parse the JSON payload
            try:
                payload_data = json.loads(json_payload)
            except json.JSONDecodeError as e:
                return (f"Error: Invalid JSON payload - {str(e)}",)
            
            # Upload image if provided and update payload
            if image is not None:
                print("Uploading image to FAL...")
                image_url = ImageUtils.upload_image(image)
                if image_url:
                    print(f"Image uploaded successfully: {image_url}")
                    # Update image_url in payload if it exists
                    if 'image_url' in payload_data:
                        payload_data['image_url'] = image_url
                    else:
                        # Add image_url to payload if it doesn't exist
                        payload_data['image_url'] = image_url
                else:
                    return ("Error: Failed to upload image to FAL",)
            
            # Parse headers
            try:
                headers_data = json.loads(headers)
            except json.JSONDecodeError as e:
                return (f"Error: Invalid JSON headers - {str(e)}",)
            
            # Make the POST request
            response = requests.post(
                api_url,
                json=payload_data,
                headers=headers_data,
                timeout=timeout
            )
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse the response JSON
            try:
                result_data = response.json()
            except json.JSONDecodeError:
                # If response is not JSON, return the raw text
                return (response.text,)
            
            # Try to extract 'output' field first, then 'text' field, or return the whole response
            if 'output' in result_data:
                if isinstance(result_data['output'], str):
                    return (result_data['output'],)
                elif isinstance(result_data['output'], dict) and 'text' in result_data['output']:
                    return (result_data['output']['text'],)
                else:
                    return (json.dumps(result_data['output'], indent=2),)
            elif 'text' in result_data:
                return (result_data['text'],)
            else:
                # Return the entire response as formatted JSON
                return (json.dumps(result_data, indent=2),)
                
        except requests.exceptions.Timeout:
            return (f"Error: Request timed out after {timeout} seconds",)
        except requests.exceptions.ConnectionError:
            return (f"Error: Failed to connect to {api_url}",)
        except requests.exceptions.HTTPError as e:
            return (f"Error: HTTP {e.response.status_code} - {e.response.text}",)
        except requests.exceptions.RequestException as e:
            return (f"Error: Request failed - {str(e)}",)
        except Exception as e:
            return (f"Error: Unexpected error - {str(e)}",)


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "CommonAPI_fal": CommonAPINode,
}

# Node display name mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "CommonAPI_fal": "Common API (only for image to prompt)",
}