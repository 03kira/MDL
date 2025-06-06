from typing import Any, Dict, Tuple

from app.handlers.fetch import (
    FetchCast,
    FetchDrama,
    FetchDramaList,
    FetchEpisodes,
    FetchList,
    FetchPerson,
    FetchReviews,
    # New fetch classes
    FetchNewsFeeds,
    FetchTopAiring,
    FetchRecommendations,
    FetchEpisodeDetails,
    FetchShowsStartingThisWeek,
    FetchShowsTrendingThisWeek,
    FetchTodaysBirthdays,
)
from app.handlers.search import Search


def error(code: int, description: str) -> Dict[str, Any]:
    return {
        "error": True,
        "code": code,
        "description": (
            "404 Not Found" if code == 404 else description
        ),  # prioritize error 404
    }


# search function
async def search_func(query: str) -> Tuple[int, Dict[str, Any]]:
    f = await Search.scrape(query=query, t="search")
    if not f.ok:
        return f.status_code, error(f.status_code, "An unexpected error occurred.")
    else:
        f._get_search_results()

    return f.status_code, f.search()


fs = {
    "drama": FetchDrama,
    "person": FetchPerson,
    "cast": FetchCast,
    "reviews": FetchReviews,
    "lists": FetchList,
    "dramalist": FetchDramaList,
    "episodes": FetchEpisodes,
    # New fetch types
    "newsfeeds": FetchNewsFeeds,
    "topairing": FetchTopAiring,
    "recommendations": FetchRecommendations,
    "episodedetails": FetchEpisodeDetails,
    "showsstartingthisweek": FetchShowsStartingThisWeek,
    "trendingthisweek": FetchShowsTrendingThisWeek,
    "todaysbirthdays": FetchTodaysBirthdays,
}


# fetch function
async def fetch_func(query: str, t: str) -> Tuple[int, Dict[str, Any]]:
    if t not in fs.keys():
        raise Exception("Invalid Error")

    f = await fs[t].scrape(query=query, t="page")
    if not f.ok:
        return f.status_code, f.res_get_err()
    else:
        f._get()

    return f.status_code, f.fetch()


# New specialized functions for homepage data
async def fetch_homepage_newsfeeds() -> Tuple[int, Dict[str, Any]]:
    """Fetch news feeds from homepage"""
    return await fetch_func(query="", t="newsfeeds")


async def fetch_homepage_topairing() -> Tuple[int, Dict[str, Any]]:
    """Fetch top airing shows from homepage"""
    return await fetch_func(query="", t="topairing")


async def fetch_homepage_shows_starting_this_week() -> Tuple[int, Dict[str, Any]]:
    """Fetch shows starting this week from homepage"""
    return await fetch_func(query="", t="showsstartingthisweek")

async def fetch_homepage_trending_this_week() -> Tuple[int, Dict[str, Any]]:
    """Fetch shows trending this week from homepage"""
    return await fetch_func(query="", t="trendingthisweek")

async def fetch_homepage_todays_birthdays() -> Tuple[int, Dict[str, Any]]:
    """Fetch today's birthdays from homepage"""
    return await fetch_func(query="", t="todaysbirthdays")


async def fetch_drama_recommendations(drama_id: str, page: int = 1) -> Tuple[int, Dict[str, Any]]:
    """Fetch drama recommendations with pagination"""
    query = f"{drama_id}/recs?page={page}"
    return await fetch_func(query=query, t="recommendations")


async def fetch_drama_episode_details(drama_id: str) -> Tuple[int, Dict[str, Any]]:
    """Fetch detailed episode information"""
    query = f"{drama_id}/episodes"
    return await fetch_func(query=query, t="episodedetails")
