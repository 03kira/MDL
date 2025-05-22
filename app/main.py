from typing import Any, Dict 

import cloudscraper  # bypassing cloudflare anti-bot
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.lib.msgspec_json import MsgSpecJSONResponse
from app.utils import (
    fetch_func, 
    search_func,
    # New specialized functions
    fetch_homepage_newsfeeds,
    fetch_homepage_topairing,
    fetch_homepage_shows_starting_this_week,
    fetch_homepage_todays_birthdays,
    fetch_drama_recommendations,
    fetch_drama_episode_details,
)

app = FastAPI(
    title="Kuryana",
    default_response_class=MsgSpecJSONResponse,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def index() -> Dict[str, Any]:
    return {"message": "A Simple and Basic MDL Scraper API"}


@app.get("/search/q/{query}")
async def search(query: str, response: Response) -> Dict[str, Any]:
    code, r = await search_func(query=query)

    response.status_code = code
    return r


@app.get("/id/{drama_id}")
async def fetch(drama_id: str, response: Response) -> Dict[str, Any]:
    code, r = await fetch_func(query=drama_id, t="drama")

    response.status_code = code
    return r


@app.get("/id/{drama_id}/cast")
async def fetch_cast(drama_id: str, response: Response) -> Dict[str, Any]:
    code, r = await fetch_func(query=f"{drama_id}/cast", t="cast")

    response.status_code = code
    return r


@app.get("/id/{drama_id}/episodes")
async def fetch_episodes(drama_id: str, response: Response) -> Dict[str, Any]:
    code, r = await fetch_func(query=f"{drama_id}/episodes", t="episodes")

    response.status_code = code
    return r


@app.get("/id/{drama_id}/reviews")
async def fetch_reviews(
    drama_id: str, response: Response, page: int = 1
) -> Dict[str, Any]:
    code, r = await fetch_func(query=f"{drama_id}/reviews?page={page}", t="reviews")

    response.status_code = code
    return r


@app.get("/people/{person_id}")
async def person(person_id: str, response: Response) -> Dict[str, Any]:
    code, r = await fetch_func(query=f"people/{person_id}", t="person")

    response.status_code = code
    return r


@app.get("/dramalist/{user_id}")
async def dramalist(user_id: str, response: Response) -> Dict[str, Any]:
    code, r = await fetch_func(query=f"dramalist/{user_id}", t="dramalist")

    response.status_code = code
    return r


@app.get("/list/{list_id}")
async def lists(list_id: str, response: Response) -> Dict[str, Any]:
    code, r = await fetch_func(query=f"list/{list_id}", t="lists")

    response.status_code = code
    return r


# get seasonal drama list -- official api available, use it with cloudflare bypass
@app.get("/seasonal/{year}/{quarter}")
async def mdlSeasonal(year: int, quarter: int) -> Any:
    # year -> ex. ... / 2019 / 2020 / 2021 / ...
    # quarter -> every 3 months (Jan-Mar=1, Apr-Jun=2, Jul-Sep=3, Oct-Dec=4)
    # --- seasonal information --- winter --- spring --- summer --- fall ---

    scraper = cloudscraper.create_scraper()

    return scraper.post(
        "https://mydramalist.com/v1/quarter_calendar",
        data={"quarter": quarter, "year": year},
    ).json()


# NEW ENDPOINTS BASED ON NODE.JS FUNCTIONALITY

@app.get("/api/mdl/newsfeeds")
async def get_newsfeeds(response: Response) -> Dict[str, Any]:
    """Get news feeds from MDL homepage"""
    try:
        code, data = await fetch_homepage_newsfeeds()
        response.status_code = code
        return data
    except Exception as err:
        print(f"Error in mdl newsfeeds request: {err}")
        response.status_code = 422
        return {"errors": [{"msg": "Server Error"}]}


@app.get("/api/mdl/topairing")
async def get_top_airing(response: Response) -> Dict[str, Any]:
    """Get top airing shows from MDL homepage"""
    try:
        code, data = await fetch_homepage_topairing()
        response.status_code = code
        return data
    except Exception as err:
        print(f"Error in mdl top airing request: {err}")
        response.status_code = 422
        return {"errors": [{"msg": "Server Error"}]}


@app.get("/api/mdl/showsstartingthisweek")
async def get_shows_starting_this_week(response: Response) -> Dict[str, Any]:
    """Get shows starting this week from MDL homepage"""
    try:
        code, data = await fetch_homepage_shows_starting_this_week()
        response.status_code = code
        return data
    except Exception as err:
        print(f"Error in mdl shows starting this week request: {err}")
        response.status_code = 422
        return {"errors": [{"msg": "Server Error"}]}


@app.get("/api/mdl/todaysbirthdays")
async def get_todays_birthdays(response: Response) -> Dict[str, Any]:
    """Get today's birthdays from MDL homepage"""
    try:
        code, data = await fetch_homepage_todays_birthdays()
        response.status_code = code
        return data
    except Exception as err:
        print(f"Error in mdl today's birthdays request: {err}")
        response.status_code = 422
        return {"errors": [{"msg": "Server Error"}]}


@app.get("/api/mdl/recommendations")
async def get_recommendations(query: str, page: int = 1, response: Response = None) -> Dict[str, Any]:
    """Get drama recommendations with pagination"""
    try:
        code, data = await fetch_drama_recommendations(drama_id=query, page=page)
        response.status_code = code
        return data
    except Exception as err:
        print(f"Error in mdl recommendations request: {err}")
        response.status_code = 422
        return {"errors": [{"msg": "Server Error"}]}


@app.get("/api/mdl/episode-details")
async def get_episode_details(query: str, response: Response = None) -> Dict[str, Any]:
    """Get detailed episode information"""
    try:
        code, data = await fetch_drama_episode_details(drama_id=query)
        response.status_code = code
        return data
    except Exception as err:
        print(f"Error in mdl episode details request: {err}")
        response.status_code = 422
        return {"errors": [{"msg": "Server Error"}]}
