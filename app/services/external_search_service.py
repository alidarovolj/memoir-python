"""External search service for TMDB, Google Books, etc."""
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.core.exceptions import AIServiceError


class ExternalSearchService:
    """Service for searching external content APIs"""
    
    def __init__(self):
        self.tmdb_api_key = settings.TMDB_API_KEY
        self.google_books_key = settings.GOOGLE_BOOKS_KEY
        self.google_search_key = settings.GOOGLE_SEARCH_KEY
        self.google_search_cx = settings.GOOGLE_SEARCH_CX
        self.spoonacular_key = settings.SPOONACULAR_KEY
        
        self.tmdb_base = "https://api.themoviedb.org/3"
        self.google_books_base = "https://www.googleapis.com/books/v1"
        self.spoonacular_base = "https://api.spoonacular.com"
        self.tmdb_image_base = "https://image.tmdb.org/t/p/w500"
        self.tmdb_backdrop_base = "https://image.tmdb.org/t/p/original"
    
    async def search_movies(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search movies via TMDB API
        
        Args:
            query: Search query
            limit: Maximum results
        
        Returns:
            List of movie results
        """
        if not self.tmdb_api_key:
            print(f"⚠️ TMDB API key not configured")
            return []
        
        try:
            print(f"🔍 Searching TMDB for: {query}")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.tmdb_base}/search/movie",
                    params={
                        "api_key": self.tmdb_api_key,
                        "query": query,
                        "language": "ru-RU",
                        "page": 1,
                    }
                )
                
                print(f"📡 TMDB response status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"❌ TMDB error: {response.text}")
                    return []
                
                data = response.json()
                print(f"✅ TMDB found {len(data.get('results', []))} results")
                
                results = []
                for item in data.get("results", [])[:limit]:
                    results.append({
                        "external_id": str(item["id"]),
                        "title": item.get("title", ""),
                        "original_title": item.get("original_title", ""),
                        "description": item.get("overview", ""),
                        "image_url": f"{self.tmdb_image_base}{item['poster_path']}" if item.get("poster_path") else None,
                        "backdrop_url": f"{self.tmdb_backdrop_base}{item['backdrop_path']}" if item.get("backdrop_path") else None,
                        "year": item.get("release_date", "")[:4] if item.get("release_date") else None,
                        "rating": item.get("vote_average"),
                        "popularity": item.get("popularity"),
                        "source": "tmdb",
                        "type": "movie",
                    })
                
                print(f"📋 Returning {len(results)} parsed results")
                return results
        
        except Exception as e:
            print(f"❌ TMDB search error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def get_movie_details(self, movie_id: str) -> Dict[str, Any]:
        """
        Get detailed movie information from TMDB
        
        Args:
            movie_id: TMDB movie ID
        
        Returns:
            Detailed movie information
        """
        if not self.tmdb_api_key:
            raise AIServiceError("TMDB API key not configured")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get movie details
                movie_response = await client.get(
                    f"{self.tmdb_base}/movie/{movie_id}",
                    params={
                        "api_key": self.tmdb_api_key,
                        "language": "ru-RU",
                    }
                )
                movie = movie_response.json()
                
                # Get credits (director, actors)
                credits_response = await client.get(
                    f"{self.tmdb_base}/movie/{movie_id}/credits",
                    params={"api_key": self.tmdb_api_key}
                )
                credits = credits_response.json()
                
                # Extract director
                director = next(
                    (c["name"] for c in credits.get("crew", []) if c["job"] == "Director"),
                    None
                )
                
                # Extract top 5 actors
                actors = [c["name"] for c in credits.get("cast", [])[:5]]
                
                # Build detailed response
                return {
                    "external_id": str(movie_id),
                    "title": movie.get("title", ""),
                    "original_title": movie.get("original_title", ""),
                    "description": movie.get("overview", ""),
                    "image_url": f"{self.tmdb_image_base}{movie['poster_path']}" if movie.get("poster_path") else None,
                    "backdrop_url": f"{self.tmdb_backdrop_base}{movie['backdrop_path']}" if movie.get("backdrop_path") else None,
                    "year": movie.get("release_date", "")[:4] if movie.get("release_date") else None,
                    "rating": movie.get("vote_average"),
                    "director": director,
                    "actors": actors,
                    "genres": [g["name"] for g in movie.get("genres", [])],
                    "runtime": movie.get("runtime"),
                    "source": "tmdb",
                    "type": "movie",
                    "metadata": {
                        "director": director,
                        "actors": actors,
                        "genres": [g["name"] for g in movie.get("genres", [])],
                        "year": movie.get("release_date", "")[:4] if movie.get("release_date") else None,
                        "runtime": movie.get("runtime"),
                        "rating": movie.get("vote_average"),
                        "tmdb_id": str(movie_id),
                    }
                }
        
        except Exception as e:
            raise AIServiceError(f"Failed to get movie details: {str(e)}")
    
    async def search_books(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search books via Google Books API"""
        if not self.google_books_key:
            return []
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.google_books_base}/volumes",
                    params={
                        "q": query,
                        "key": self.google_books_key,
                        "maxResults": limit,
                        "langRestrict": "ru",
                    }
                )
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                
                results = []
                for item in data.get("items", []):
                    info = item.get("volumeInfo", {})
                    image_links = info.get("imageLinks", {})
                    
                    results.append({
                        "external_id": item["id"],
                        "title": info.get("title", ""),
                        "description": info.get("description", ""),
                        "image_url": image_links.get("thumbnail", image_links.get("smallThumbnail")),
                        "authors": info.get("authors", []),
                        "publisher": info.get("publisher"),
                        "year": info.get("publishedDate", "")[:4] if info.get("publishedDate") else None,
                        "rating": info.get("averageRating"),
                        "source": "google_books",
                        "type": "book",
                    })
                
                return results
        
        except Exception as e:
            print(f"Google Books search error: {e}")
            return []
    
    async def search_web(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Universal web search via Google Custom Search API
        
        Args:
            query: Search query
            limit: Maximum results
        
        Returns:
            List of web search results
        """
        if not self.google_search_key or not self.google_search_cx:
            return []
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": self.google_search_key,
                        "cx": self.google_search_cx,
                        "q": query,
                        "num": min(limit, 10),
                    }
                )
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                
                results = []
                for item in data.get("items", []):
                    # Extract image from pagemap
                    image = None
                    if "pagemap" in item:
                        if "cse_image" in item["pagemap"]:
                            image = item["pagemap"]["cse_image"][0].get("src")
                        elif "metatags" in item["pagemap"]:
                            metatags = item["pagemap"]["metatags"][0]
                            image = metatags.get("og:image") or metatags.get("twitter:image")
                    
                    results.append({
                        "title": item.get("title", ""),
                        "description": item.get("snippet", ""),
                        "url": item.get("link", ""),
                        "image_url": image,
                        "source": "web",
                        "type": "web",
                    })
                
                return results
        
        except Exception as e:
            print(f"Google Custom Search error: {e}")
            return []


# Singleton instance
external_search_service = ExternalSearchService()

