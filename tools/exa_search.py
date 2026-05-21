from collections.abc import Generator
from typing import Any, Dict, List, Optional
import os
import requests
from datetime import datetime
import json

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class ExaSearchTool(Tool):
    # Backwards-compat mapping: livecrawl → maxAgeHours
    _LIVECRAWL_TO_MAX_AGE = {
        "always": 0,
        "never": -1,
        "fallback": 24,
        "preferred": 0,
        "auto": 24,
    }

    # Backwards-compat mapping: old search types → new
    _SEARCH_TYPE_COMPAT = {
        "neural": "auto",
        "keyword": "auto",
    }

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            # Get API key from runtime credentials
            api_key = self.runtime.credentials["exa_api_key"]
            
            # Required parameter
            query = tool_parameters.get("query")
            if not query:
                raise ValueError("Search query is required")
                
            # Optional parameters with defaults
            search_type = tool_parameters.get("search_type", "auto")
            # Backwards compat: map old search types
            search_type = self._SEARCH_TYPE_COMPAT.get(search_type, search_type)

            num_results = int(tool_parameters.get("num_results", 10))
            include_domains = tool_parameters.get("include_domains", "")
            exclude_domains = tool_parameters.get("exclude_domains", "")
            start_published_date = tool_parameters.get("start_published_date", "")
            end_published_date = tool_parameters.get("end_published_date", "")
            include_highlights = tool_parameters.get("include_highlights", True)
            highlights_max_characters = tool_parameters.get("highlights_max_characters", None)
            include_full_text = tool_parameters.get("include_text", False)
            max_age_hours = tool_parameters.get("max_age_hours", None)
            category = tool_parameters.get("category", None)
            include_text_filter = tool_parameters.get("includeText", None)
            exclude_text_filter = tool_parameters.get("excludeText", None)

            # Backwards compat: map legacy use_autoprompt
            use_autoprompt = tool_parameters.get("use_autoprompt", None)

            # Backwards compat: map legacy livecrawl → maxAgeHours
            livecrawl = tool_parameters.get("livecrawl", None)
            if max_age_hours is None and livecrawl:
                max_age_hours = self._LIVECRAWL_TO_MAX_AGE.get(livecrawl)
            
            # Process domain lists
            include_domains_list = [d.strip() for d in include_domains.split(",")] if include_domains else []
            exclude_domains_list = [d.strip() for d in exclude_domains.split(",")] if exclude_domains else []
            
            # Build request payload
            payload: Dict[str, Any] = {
                "query": query,
                "numResults": num_results,
                "type": search_type if search_type != "auto" else None,
                "includeDomains": include_domains_list if include_domains_list else None,
                "excludeDomains": exclude_domains_list if exclude_domains_list else None,
                "startPublishedDate": start_published_date if start_published_date else None,
                "endPublishedDate": end_published_date if end_published_date else None,
                "category": category,
                "includeText": [include_text_filter] if include_text_filter else None,
                "excludeText": [exclude_text_filter] if exclude_text_filter else None,
            }

            if use_autoprompt is not None:
                payload["useAutoprompt"] = use_autoprompt

            if max_age_hours is not None:
                payload["maxAgeHours"] = max_age_hours

            # Remove None values from payload
            payload = {k: v for k, v in payload.items() if v is not None}

            # Build contents options — highlights default, text opt-in
            contents_options: Dict[str, Any] = {}
            if include_highlights:
                if highlights_max_characters:
                    contents_options["highlights"] = {"maxCharacters": int(highlights_max_characters)}
                else:
                    contents_options["highlights"] = True
            if include_full_text:
                contents_options["text"] = True

            if contents_options:
                payload["contents"] = contents_options
            
            # Make API request
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "x-exa-integration": "dify-community-integration",
            }
            response = requests.post(
                "https://api.exa.ai/search",
                json=payload,
                headers=headers
            )
            
            response.raise_for_status()
            result_data = response.json()
            
            # Yield the raw JSON response first
            yield self.create_json_message(result_data)

            # Format and yield the results as markdown text
            markdown_output = self._format_results_as_markdown(result_data, query)
            yield self.create_text_message(markdown_output)
            
            # Extract urls and images from results
            urls = []
            images = []
            raw_results = result_data.get("results", [])
            for result in raw_results:
                if url := result.get("url"):
                    urls.append(url)
                # Handle image extraction with proper validation
                if "image" in result:
                    image = result["image"]
                    if isinstance(image, str) and image.strip():  # Ensure non-empty string
                        if image.startswith(('http://', 'https://')):  # Basic URL validation
                            images.append(image)

            # Debug output
            print("\n===== EXTRACTED URLS AND IMAGES =====")
            print("URLs:", urls)
            print("Images:", images)
            print("===== END OF EXTRACTION =====\n")

            # Yield urls and images as separate variables
            yield self.create_variable_message("urls", urls)
            yield self.create_variable_message("images", images)

            # Debug output
            print("\n===== AFTER create_variable_message =====")
            print("Variable 'urls' sent to Dify:")
            print(json.dumps(urls, indent=2))
            print("Variable 'images' sent to Dify:")
            print(json.dumps(images, indent=2))
            print("===== END OF DEBUG OUTPUT =====\n")

        except requests.RequestException as e:
            error_message = f"Error when calling Exa Search API: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_message += f" - Status code: {e.response.status_code}"
                if hasattr(e.response, 'text'):
                    error_message += f" - Response: {e.response.text}"
            
            yield self.create_json_message({
                "status": "error",
                "error": error_message
            })
            
            yield self.create_text_message(f"Error: {error_message}")
        except Exception as e:
            error_message = f"Error: {str(e)}"
            
            yield self.create_json_message({
                "status": "error",
                "error": error_message
            })
            
            yield self.create_text_message(f"Error: {error_message}")
    
    def _format_results_as_markdown(self, api_response: Dict, query: str) -> str:
        """Format API response as a readable Markdown string"""
        results = api_response.get("results", [])
        
        markdown = f"## Exa Search Results\n\n"
        markdown += f"**Query:** {query}\n\n"
        markdown += f"**Total Results:** {len(results)}\n\n"
        
        if not results:
            markdown += "No results found.\n"
            return markdown
        
        # Add results
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            domain = result.get("domain", "Unknown source")
            published_date = result.get("publishedDate", "")
            author = result.get("author", "")
            
            markdown += f"### {i}. [{title}]({url})\n\n"
            
            # Add image if available
            image_url = result.get("image", "")
            if image_url:
                markdown += f"![Image from {domain}]({image_url})\n\n"
            
            markdown += f"**Source:** {domain}\n"
            
            if published_date:
                markdown += f"**Published:** {published_date}\n"
            
            if author:
                markdown += f"**Author:** {author}\n"
            
            if "score" in result:
                markdown += f"**Relevance Score:** {result['score']:.2f}\n"
            
            markdown += "\n"
            
            # Add highlights if available
            if "highlights" in result and result["highlights"]:
                markdown += "**Highlights:**\n\n"
                for highlight in result["highlights"]:
                    markdown += f"> {highlight}\n"
                markdown += "\n"
            
            # Add text content if available
            if "text" in result and result["text"]:
                text_excerpt = result["text"]
                # Limit to ~500 characters for readability
                if len(text_excerpt) > 500:
                    text_excerpt = text_excerpt[:500] + "..."
                
                markdown += "**Content Excerpt:**\n\n"
                markdown += f"```\n{text_excerpt}\n```\n\n"
            
            markdown += "---\n\n"
        
        return markdown
