from typing import Any, Optional, Tuple, Union
from urllib.parse import urljoin
import re

from bs4 import BeautifulSoup
from bs4.element import NavigableString, ResultSet, Tag

from app import MYDRAMALIST_WEBSITE
from app.handlers.parser import BaseSearch


class Search(BaseSearch):
    """Search"""

    def __init__(self, soup: BeautifulSoup, query: str, code: int, ok: bool) -> None:
        super().__init__(soup, query, code, ok)
        self.url = "search?q=" + self.query.replace(" ", "+")
        self.mdl_container_id = "mdl-"

    def _get_container(self) -> ResultSet:
        return self.soup.find("div", class_="col-lg-8 col-md-8").find_all(
            "div", class_="box"
        )

    def _res_get_ranking(self, result_container: BeautifulSoup) -> Any:
        try:
            ranking = result_container.find("div", class_="ranking pull-right").find(
                "span"
            )
        except AttributeError:
            return None
        return ranking.text

    def _res_get_year_info(
        self, result_container: Union[NavigableString, Tag]
    ) -> Tuple[Union[str, None], Union[int, None], Union[str, bool]]:
        _typeyear = result_container.find("span", class_="text-muted").text
        _year_eps = _typeyear.split("-")[1]

        year: Optional[int] = None
        try:
            t = _typeyear.split("-")[0].strip()
        except Exception:
            t = None

        try:
            year = int(_year_eps.split(",")[0].strip())
        except Exception:
            year = None

        try:
            series_ep = _year_eps.split(",")[1].strip()
        except Exception:
            series_ep = False

        return t, year, series_ep

    def _res_get_url(self, result_container: Union[Tag, NavigableString]) -> str:
        return urljoin(
            MYDRAMALIST_WEBSITE,
            result_container.find("h6", class_="text-primary title")
            .find("a")["href"]
            .replace("/", ""),
        )

    def _get_search_results(self) -> None:
        results = self._get_container()

        _dramas = []
        _people = []

        for result in results:
            title_elem = result.find("h6", class_="text-primary title")
            if title_elem is None:
                continue

            r = {}
            title = title_elem.text.strip()

            url_slug = title_elem.find("a").get("href")
            if url_slug is not None:
                r["slug"] = url_slug.replace("/", "", 1)
            else:
                continue

            _thumb = str(result.find("img", class_="img-responsive")["data-src"]).split(
                "/1280/"
            )
            if len(_thumb) > 1:
                r["thumb"] = _thumb[1]
            else:
                r["thumb"] = _thumb[0]

            if result.has_attr("id"):
                r["mdl_id"] = result["id"]
                r["title"] = title.strip()
                r["ranking"] = self._res_get_ranking(result)
                r["type"], r["year"], r["series"] = self._res_get_year_info(result)
                _dramas.append(r)
                continue

            r["name"] = title.strip()
            r["nationality"] = result.find("div", class_="text-muted").text.strip()
            _people.append(r)

        self.search_results["dramas"] = _dramas
        self.search_results["people"] = _people

        # Add pagination info
        self.search_results["pages"] = self._get_pagination_info()

    def _get_pagination_info(self) -> dict:
        pages_info = {}

        try:
            pagination = self.soup.select_one("ul.pagination")
            if pagination:
                current = pagination.find("li", class_="active")
                current_page = current.get_text(strip=True) if current else "1"

                prev = pagination.find("li", class_="prev")
                next_ = pagination.find("li", class_="next")
                last = pagination.find("li", class_="last")

                def extract_page_slug(elem):
                    if elem and elem.find("a"):
                        href = elem.find("a").get("href", "")
                        match = re.search(r"page=(\d+)", href)
                        return match.group(1) if match else ""
                    return ""

                pages_info = {
                    "currentPage": current_page,
                    "prevPageSlug": extract_page_slug(prev) or False,
                    "nextPageSlug": extract_page_slug(next_) or False,
                    "totalPages": int(extract_page_slug(last) or current_page),
                }
        except Exception as e:
            print(f"Error parsing pagination: {e}")

        return pages_info
