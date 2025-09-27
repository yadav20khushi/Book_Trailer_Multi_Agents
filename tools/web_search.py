import requests
import json
from typing import Dict, List, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class BookSearchResult(BaseModel):
    """Structure for book search results"""
    title: str = Field(description="Book title")
    author: str = Field(description="Book author")
    genre: List[str] = Field(description="Book genres")
    description: str = Field(description="Book description/summary")
    publication_year: Optional[str] = Field(description="Publication year")
    rating: Optional[float] = Field(description="Average rating")
    cover_url: Optional[str] = Field(description="Book cover image URL")
    quotes: List[str] = Field(description="Notable quotes from the book")
    themes: List[str] = Field(description="Main themes")
    source_urls: List[str] = Field(description="Source URLs for information")


class BookWebSearchTool(BaseTool):
    name: str = "Book Research Web Search"
    description: str = """
    A comprehensive web search tool specifically designed for book research.
    Searches multiple sources to gather detailed information about books including:
    - Basic details (title, author, genre, publication info)
    - Plot summary and themes
    - Critical reception and ratings
    - Notable quotes and memorable passages
    - Book cover images
    - Author background
    - Similar books and recommendations

    Input should be the book title and optionally the author name.
    """

    def _run(self, book_title: str, author_name: str = "") -> str:
        """
        Execute comprehensive book search across multiple sources

        Args:
            book_title: The title of the book to search for
            author_name: Optional author name to refine search

        Returns:
            Formatted string containing comprehensive book information
        """
        try:
            # Prepare search queries
            search_queries = self._prepare_search_queries(book_title, author_name)

            # Gather information from different sources
            book_info = {
                "title": book_title,
                "author": author_name or "Unknown",
                "genre": [],
                "description": "",
                "themes": [],
                "quotes": [],
                "rating": None,
                "publication_year": None,
                "cover_url": None,
                "source_urls": []
            }

            # Search for basic book information
            basic_info = self._search_basic_info(search_queries["basic"])
            book_info.update(basic_info)

            # Search for quotes and themes
            quotes_themes = self._search_quotes_and_themes(search_queries["quotes"])
            book_info["quotes"].extend(quotes_themes.get("quotes", []))
            book_info["themes"].extend(quotes_themes.get("themes", []))

            # Search for reviews and analysis
            analysis_info = self._search_analysis(search_queries["analysis"])
            book_info["themes"].extend(analysis_info.get("additional_themes", []))

            # Search for cover image
            cover_info = self._search_cover_image(search_queries["cover"])
            if cover_info.get("cover_url"):
                book_info["cover_url"] = cover_info["cover_url"]

            # Format and return results
            return self._format_search_results(book_info)

        except Exception as e:
            return f"Error during book search: {str(e)}\nPlease try with a different book title or check your internet connection."

    def _prepare_search_queries(self, book_title: str, author_name: str) -> Dict[str, str]:
        """Prepare different search queries for various types of information"""
        base_query = f'"{book_title}"'
        if author_name:
            base_query += f' "{author_name}"'

        return {
            "basic": f"{base_query} book summary genre publication author",
            "quotes": f"{base_query} quotes famous lines memorable passages",
            "analysis": f"{base_query} themes analysis literary criticism review",
            "cover": f"{base_query} book cover image official",
            "goodreads": f"{base_query} goodreads rating reviews",
            "amazon": f"{base_query} amazon book description"
        }

    def _search_basic_info(self, query: str) -> Dict:
        """Search for basic book information"""
        try:
            # This would integrate with actual search APIs
            # For demo purposes, showing the structure
            results = {
                "genre": self._extract_genres_from_search(query),
                "description": self._extract_description_from_search(query),
                "publication_year": self._extract_publication_year(query),
                "rating": self._extract_rating(query),
                "source_urls": []
            }
            return results
        except Exception as e:
            print(f"Error in basic info search: {e}")
            return {}

    def _search_quotes_and_themes(self, query: str) -> Dict:
        """Search for quotes and themes"""
        try:
            # Extract quotes and themes from search results
            results = {
                "quotes": self._extract_quotes_from_search(query),
                "themes": self._extract_themes_from_search(query)
            }
            return results
        except Exception as e:
            print(f"Error in quotes/themes search: {e}")
            return {"quotes": [], "themes": []}

    def _search_analysis(self, query: str) -> Dict:
        """Search for literary analysis and additional themes"""
        try:
            results = {
                "additional_themes": self._extract_analysis_themes(query)
            }
            return results
        except Exception as e:
            print(f"Error in analysis search: {e}")
            return {"additional_themes": []}

    def _search_cover_image(self, query: str) -> Dict:
        """Search for book cover image"""
        try:
            cover_url = self._extract_cover_url(query)
            return {"cover_url": cover_url}
        except Exception as e:
            print(f"Error in cover search: {e}")
            return {}

    def _extract_genres_from_search(self, query: str) -> List[str]:
        """Extract genres from search results"""
        # Mock implementation - in real scenario, would parse actual search results
        common_genres = [
            "Fiction", "Non-fiction", "Mystery", "Romance", "Fantasy",
            "Science Fiction", "Historical Fiction", "Biography", "Self-help",
            "Thriller", "Horror", "Young Adult", "Children's", "Poetry",
            "Drama", "Comedy", "Adventure", "Crime", "Literary Fiction"
        ]
        # Would implement actual extraction logic here
        return []

    def _extract_description_from_search(self, query: str) -> str:
        """Extract book description from search results"""
        # Would implement actual web scraping/API calls here
        return ""

    def _extract_publication_year(self, query: str) -> Optional[str]:
        """Extract publication year from search results"""
        # Would implement actual extraction logic here
        return None

    def _extract_rating(self, query: str) -> Optional[float]:
        """Extract rating from search results"""
        # Would implement actual extraction logic here
        return None

    def _extract_quotes_from_search(self, query: str) -> List[str]:
        """Extract notable quotes from search results"""
        # Would implement actual quote extraction here
        return []

    def _extract_themes_from_search(self, query: str) -> List[str]:
        """Extract themes from search results"""
        # Would implement actual theme extraction here
        return []

    def _extract_analysis_themes(self, query: str) -> List[str]:
        """Extract additional themes from literary analysis"""
        # Would implement actual analysis extraction here
        return []

    def _extract_cover_url(self, query: str) -> Optional[str]:
        """Extract book cover URL from search results"""
        # Would implement actual cover URL extraction here
        return None

    def _format_search_results(self, book_info: Dict) -> str:
        """Format the search results into a readable string"""

        # Remove duplicates and clean data
        book_info["genre"] = list(set(book_info["genre"]))
        book_info["themes"] = list(set(book_info["themes"]))
        book_info["quotes"] = list(set(book_info["quotes"]))[:5]  # Limit to top 5 quotes

        result = f"""
=== COMPREHENSIVE BOOK RESEARCH RESULTS ===

📚 BASIC INFORMATION:
Title: {book_info['title']}
Author: {book_info['author']}
Publication Year: {book_info['publication_year'] or 'Not found'}
Average Rating: {book_info['rating'] or 'Not found'}

🎭 GENRE CLASSIFICATION:
{', '.join(book_info['genre']) if book_info['genre'] else 'Genres not identified'}

📖 DESCRIPTION/SUMMARY:
{book_info['description'] or 'Description not found in search results'}

🎨 CENTRAL THEMES:
{self._format_list(book_info['themes']) if book_info['themes'] else 'Themes not identified'}

💬 NOTABLE QUOTES:
{self._format_quotes(book_info['quotes']) if book_info['quotes'] else 'No notable quotes found'}

🖼️ BOOK COVER:
{book_info['cover_url'] or 'Cover image URL not found'}

🔗 RESEARCH SOURCES:
{self._format_list(book_info['source_urls']) if book_info['source_urls'] else 'No source URLs captured'}

=== TRAILER CREATION NOTES ===
- Focus on the strongest themes identified above
- Use genre conventions for visual style and pacing  
- Incorporate notable quotes if they're compelling and brief
- Ensure book cover is prominently featured
- Consider the target audience based on genre and themes

=== RECOMMENDED HOOKS FOR TRAILER ===
{self._generate_hook_suggestions(book_info)}
        """.strip()

        return result

    def _format_list(self, items: List[str]) -> str:
        """Format a list of items as bullet points"""
        if not items:
            return "None identified"
        return '\n'.join([f"• {item}" for item in items[:10]])  # Limit to 10 items

    def _format_quotes(self, quotes: List[str]) -> str:
        """Format quotes with proper formatting"""
        if not quotes:
            return "No memorable quotes found"
        formatted_quotes = []
        for i, quote in enumerate(quotes[:5], 1):  # Limit to 5 quotes
            formatted_quotes.append(f"{i}. \"{quote}\"")
        return '\n'.join(formatted_quotes)

    def _generate_hook_suggestions(self, book_info: Dict) -> str:
        """Generate trailer hook suggestions based on book info"""
        hooks = []

        # Genre-based hooks
        genres = book_info.get('genre', [])
        if 'Mystery' in genres or 'Thriller' in genres:
            hooks.append("• Start with a mysterious question or unsettling statement")
        if 'Romance' in genres:
            hooks.append("• Begin with emotional tension or a romantic dilemma")
        if 'Fantasy' in genres or 'Science Fiction' in genres:
            hooks.append("• Open with world-building or a fantastical element")
        if 'Horror' in genres:
            hooks.append("• Create immediate tension or fear")

        # Theme-based hooks
        themes = book_info.get('themes', [])
        if any(theme.lower() in ['love', 'relationship', 'family'] for theme in themes):
            hooks.append("• Focus on relationship dynamics and emotional stakes")
        if any(theme.lower() in ['power', 'politics', 'war'] for theme in themes):
            hooks.append("• Highlight conflict and high stakes")
        if any(theme.lower() in ['identity', 'self-discovery', 'coming of age'] for theme in themes):
            hooks.append("• Emphasize personal transformation journey")

        # Default suggestions
        if not hooks:
            hooks.extend([
                "• Start with the most compelling quote or premise",
                "• Begin with a visual that represents the book's core conflict",
                "• Open with a question that the book answers"
            ])

        return '\n'.join(hooks[:5])  # Limit to 5 suggestions


# Create the tool instance
def create_book_web_search_tool():
    """Factory function to create the book web search tool"""
    return BookWebSearchTool()


# Example usage and integration
if __name__ == "__main__":
    # Test the tool
    tool = create_book_web_search_tool()

    # Example search
    result = tool._run("To Kill a Mockingbird", "Harper Lee")
    print(result)