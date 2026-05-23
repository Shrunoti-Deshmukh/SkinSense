from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import time
import requests
from bs4 import BeautifulSoup


class ProductSearchInput(BaseModel):
    """Input schema for the INCIDecoder search tool."""
    product_name: str = Field(..., 
        description="The full commercial name of the skincare or cosmetic product. Example: 'Hyphen Tinted Lip Balm - Vintage'."
    )

class ProductSearchTool(BaseTool):
    name: str = "Name of my tool"
    description: str = (
        "Clear description for what this tool is useful for, your agent will need this information to use it."
    )
    args_schema: Type[BaseModel] = ProductSearchInput

    def _run(self, product_name: str) -> str:
        # Implementation goes here
        """
        Searches INCIDecoder for a given skincare/cosmetic product name, 
        locates the exact page match, and returns a clean, structured list 
        of its ingredients along with a brief description.
        """
        search_url = "https://incidecoder.com/search"
        params = {"query": product_name}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            # Step 1: Run the search query
            search_response = requests.get(search_url, params=params, headers=headers, timeout=10)
            if search_response.status_code != 200:
                return f"Error: Search failed. Server returned status code {search_response.status_code}."
            
            search_soup = BeautifulSoup(search_response.content, "html.parser")
            
            # Step 2: Extract the first viable product link
            product_link = None
            for link in search_soup.find_all("a", href=True):
                if link["href"].startswith("/products/") and not link["href"].endswith("/search"):
                    product_link = "https://incidecoder.com" + link["href"]
                    break

            if not product_link:
                return f"Error: Could not find any product matching '{product_name}' on INCIDecoder."

            time.sleep(1) # Polite scrape delay

            # Step 3: Fetch the direct product detail page
            prod_response = requests.get(product_link, headers=headers, timeout=10)
            if prod_response.status_code != 200:
                return f"Error: Failed to fetch the product page. Status: {prod_response.status_code}."

            prod_soup = BeautifulSoup(prod_response.content, "html.parser")

            # Step 4: Extract metadata details
            brand_span = prod_soup.find("span", {"id": "product-brand-title"})
            full_title = brand_span.text.strip() if brand_span else product_name.title()

            desc_span = prod_soup.find("span", {"id": "product-details"})
            description = desc_span.text.strip() if desc_span else "No summary available."

            # Step 5: Gather and deduplicate ingredient links
            ingredients_list = []
            for link in prod_soup.find_all("a", href=True):
                if link["href"].startswith("/ingredients/"):
                    ing_text = link.text.strip()
                    if ing_text and ing_text.lower() != "[more]":
                        ingredients_list.append(ing_text)

            unique_ingredients = list(dict.fromkeys(ingredients_list))

            if not unique_ingredients:
                return f"Found page for '{full_title}' but failed to parse ingredients layout."

            # Step 6: Construct a structured text report for the Agent to read
            report = [
                f"PRODUCT: {full_title}",
                f"SUMMARY: {description}",
                f"INGREDIENTS LIST ({len(unique_ingredients)} found):",
                ", ".join(unique_ingredients)
            ]
            
            return "\n\n".join(report)

        except Exception as e:
            return f"An exception occurred while processing the request: {str(e)}"
