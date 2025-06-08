import re
import copy
from typing import Any, Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app import MYDRAMALIST_WEBSITE
from app.handlers.parser import BaseFetch


class FetchDrama(BaseFetch):
    def __init__(self, soup: BeautifulSoup, query: str, code: int, ok: bool) -> None:
        super().__init__(soup, query, code, ok)

    # get the main html container for the each search results
    def _get_main_container(self) -> None:
        container = self.soup.find("div", class_="app-body")

        # append scraped data
        # these are the most important drama infos / details

        # TITLE
        # Example: Goblin (2016)
        # Title = Goblin
        # Complete Title = Goblin (2016)
        film_title = container.find("h1", class_="film-title")
        self.info["title"] = film_title.find("a").get_text().strip()
        self.info["complete_title"] = film_title.get_text().strip()

        # RATING (could be either N/A or with number)
        self.info["rating"] = self._handle_rating(
            container.find("div", class_="col-film-rating").find("div")
        )

        # POSTER
        self.info["poster"] = self._get_poster(container)

        # SYNOPSIS
        synopsis = container.find("div", class_="show-synopsis").find("p")
        self.info["synopsis"] = (
            synopsis.get_text().replace("Edit Translation", "").strip()
            if synopsis
            else ""
        )

        # CASTS
        __casts = container.find_all("li", class_="list-item col-sm-4")
        casts = []
        for i in __casts:
            __temp_cast = i.find("a", class_="text-primary text-ellipsis")
            __temp_cast_slug = __temp_cast["href"].strip()
            casts.append(
                {
                    "name": __temp_cast.find("b").text.strip(),
                    "profile_image": self._get_poster(i),
                    "slug": __temp_cast_slug,
                    "link": urljoin(MYDRAMALIST_WEBSITE, __temp_cast_slug),
                }
            )
        self.info["casts"] = casts

    # get other info
    def _get_other_info(self) -> None:
        others = self.soup.find("div", class_="show-detailsxss").find(
            "ul", class_="list m-a-0"
        )

        try:
            self.info["others"] = {}
            all_others = others.find_all("li")
            for i in all_others:
                # get each li from <ul>
                _title = i.find("b").text.strip()
                self.info["others"][
                    _title.replace(":", "").replace(" ", "_").lower()
                ] = [
                    i.strip()
                    for i in i.text.replace(_title + " ", "").strip().split(", ")
                ]

        except Exception:
            # there was a problem while trying to parse
            # the :> other info section
            pass

    # drama info details handler
    def _get(self) -> None:
        self._get_main_container()
        self._get_details(classname="list m-a-0 hidden-md-up")
        self._get_other_info()


class FetchPerson(BaseFetch):
    non_actors = ["screenwriter", "director", "screenwriter & director"]

    def __init__(self, soup: BeautifulSoup, query: str, code: int, ok: bool) -> None:
        super().__init__(soup, query, code, ok)

    def _get_main_container(self) -> None:
        container = self.soup.find("div", class_="app-body")

        # append scraped data
        # these are the most important drama infos / details

        # NAME
        self.info["name"] = container.find("h1", class_="film-title").text

        # ABOUT?
        __temp_about = container.find("div", class_="col-lg-8 col-md-8").find(
            "div", class_="col-sm-8 col-lg-12 col-md-12"
        )
        self.info["about"] = __temp_about.text.replace(
            __temp_about.find("div", class_="hidden-md-up").text.strip(), ""
        ).strip()

        # IMAGE
        self.info["profile"] = self._get_poster(container)

        # WORKS
        self.info["works"] = {}

        # container
        _works_container = container.find("div", class_="col-lg-8 col-md-8").find_all(
            "div", class_="box-body"
        )[1]

        # get all headers
        _work_headers = [i.text.strip() for i in _works_container.find_all("h5")]
        _work_tables = _works_container.find_all("table")

        for j, k in zip(_work_headers, _work_tables, strict=False):
            # theaders = ['episodes' if i.text.strip() == '#' else i.text.strip() for i in k.find("thead").find_all("th")]
            bare_works: List[Dict[str, Any]] = []

            for i in k.find("tbody").find_all("tr"):
                _raw_year = i.find("td", class_="year").text
                _raw_title = i.find("td", class_="title").find("a")

                r = {
                    "_slug": i["class"][0],
                    "year": _raw_year if _raw_year == "TBA" else int(_raw_year),
                    "title": {
                        "link": urljoin(MYDRAMALIST_WEBSITE, _raw_title["href"]),
                        "name": _raw_title.text,
                    },
                    "rating": self._handle_rating(
                        i.find("td", class_="text-center").find(class_="text-sm")
                    ),
                }

                _raw_role = i.find("td", class_="role")

                # applicable only on dramas / tv-shows (this is different for non-actors)
                try:
                    _raw_role_name = _raw_role.find("div", class_="name").text.strip()
                except Exception:
                    _raw_role_name = None

                # use `type` for non-dramas, etc while `role` otherwise
                try:
                    if j in FetchPerson.non_actors:
                        r["type"] = _raw_role.find(class_="roleid").text.strip()
                    else:
                        r["role"] = {
                            "name": _raw_role_name,
                            "type": _raw_role.find("div", class_="roleid").text.strip(),
                        }
                except Exception:
                    pass

                # not applicable for movies
                try:
                    episodes = i.find("td", class_="episodes").text
                    r["episodes"] = int(episodes)
                except Exception:
                    pass

                bare_works.append(r)

            self.info["works"][j] = bare_works

    def _get(self) -> None:
        self._get_main_container()
        self._get_details(classname="list m-b-0")


class FetchCast(BaseFetch):
    def __init__(self, soup: BeautifulSoup, query: str, code: int, ok: bool) -> None:
        super().__init__(soup, query, code, ok)

    def _get_main_container(self) -> None:
        container = self.soup.find("div", class_="app-body")

        # append scraped data
        # these are the most important drama infos / details

        # TITLE
        self.info["title"] = container.find("h1", class_="film-title").find("a").text

        # POSTER
        self.info["poster"] = self._get_poster(container)

        # CASTS?
        self.info["casts"] = {}
        __casts_container = container.find("div", class_="box cast-credits").find(
            "div", class_="box-body"
        )

        __temp_cast_headers = __casts_container.find_all("h3")
        __temp_cast_lists = __casts_container.find_all("ul")

        for j, k in zip(__temp_cast_headers, __temp_cast_lists, strict=False):
            casts = []
            for i in k.find_all("li"):
                __temp_cast = i.find("a", class_="text-primary")
                __temp_cast_slug = __temp_cast["href"].strip()
                __temp_cast_data = {
                    "name": __temp_cast.find("b").text.strip(),
                    "profile_image": self._get_poster(i).replace(
                        "s.jpg", "m.jpg"
                    ),  # replaces the small images to a link with a bigger one
                    "slug": __temp_cast_slug,
                    "link": urljoin(MYDRAMALIST_WEBSITE, __temp_cast_slug),
                }

                try:
                    __temp_cast_data["role"] = {
                        "name": i.find("small").text.strip(),
                        "type": i.find("small", class_="text-muted").text.strip(),
                    }
                except Exception:
                    pass

                casts.append(__temp_cast_data)

            self.info["casts"][j.text.strip()] = casts

    def _get(self) -> None:
        self._get_main_container()


class FetchReviews(BaseFetch):
    def __init__(self, soup: BeautifulSoup, query: str, code: int, ok: bool) -> None:
        super().__init__(soup, query, code, ok)

    def _get_main_container(self) -> None:
        container = self.soup.find("div", class_="app-body")

        # append scraped data
        # these are the most important drama infos / details

        # TITLE
        self.info["title"] = container.find("h1", class_="film-title").find("a").text

        # POSTER
        self.info["poster"] = self._get_poster(container)

        # REVIEWS?
        self.info["reviews"] = []
        __temp_reviews = container.find_all("div", class_="review")

        for i in __temp_reviews:
            __temp_review: Dict[str, Any] = {}

            try:
                # reviewer / person
                __temp_review["reviewer"] = {
                    "name": i.find("a").text.strip(),
                    "user_link": urljoin(MYDRAMALIST_WEBSITE, i.find("a")["href"]),
                    "user_image": self._get_poster(i).replace(
                        "1t", "1c"
                    ),  # replace 1t to 1c so that it will return a bigger image than the smaller one
                    "info": i.find("div", class_="user-stats").text.strip(),
                }

                __temp_review_ratings = i.find(
                    "div", class_="box pull-right text-sm m-a-sm"
                )
                __temp_review_ratings_overall = __temp_review_ratings.find(
                    "div", class_="rating-overall"
                )

                # start parsing the review section
                __temp_review_contents = []

                __temp_review_container = i.find(
                    "div", class_=re.compile("review-body")
                )

                __temp_review_spoiler = __temp_review_container.find(
                    "div", "review-spoiler"
                )
                if __temp_review_spoiler is not None:
                    __temp_review_contents.append(__temp_review_spoiler.text.strip())

                __temp_review_strong = __temp_review_container.find("strong")
                if __temp_review_strong is not None:
                    __temp_review_contents.append(__temp_review_strong.text.strip())

                __temp_review_read_more = __temp_review_container.find(
                    "p", class_="read-more"
                ).text.strip()
                __temp_review_vote = __temp_review_container.find(
                    "div", class_="review-helpful"
                ).text.strip()

                for i in __temp_review_container.find_all("br"):
                    i.replace_with("\n")

                __temp_review_content = (
                    __temp_review_container.text.replace(
                        __temp_review_ratings.text.strip(), ""
                    )
                    .replace(__temp_review_read_more, "")
                    .replace(__temp_review_vote, "")
                )

                if __temp_review_spoiler is not None:
                    __temp_review_content = __temp_review_content.replace(
                        __temp_review_spoiler.text.strip(), ""
                    )
                if __temp_review_strong is not None:
                    __temp_review_content = __temp_review_content.replace(
                        __temp_review_strong.text.strip(), ""
                    )

                __temp_review_contents.append(__temp_review_content.strip())
                __temp_review["review"] = __temp_review_contents
                # end parsing the review section

                __temp_review["ratings"] = {
                    "overall": float(
                        __temp_review_ratings_overall.find("span").text.strip()
                    )
                }
                __temp_review_ratings_others = __temp_review_ratings.find(
                    "div", class_="review-rating"
                ).find_all("div")

                # other review ratings, it might be different in each box?
                for k in __temp_review_ratings_others:
                    __temp_review["ratings"][
                        k.text.replace(k.find("span").text.strip(), "").strip()
                    ] = float(k.find("span").text.strip())

            except Exception as e:
                print(e)
                # if failed to parse, do nothing
                pass

            # append to list
            self.info["reviews"].append(__temp_review)

    def _get(self) -> None:
        self._get_main_container()


class FetchDramaList(BaseFetch):
    def __init__(self, soup: BeautifulSoup, query: str, code: int, ok: bool) -> None:
        super().__init__(soup, query, code, ok)

    def _get_main_container(self) -> None:
        container = self.soup.find_all("div", class_="mdl-style-list")
        titles = [self._parse_title(item) for item in container]
        dramas = [self._parse_drama(item) for item in container]
        stats = [self._parse_total_stats(item) for item in container]

        items = {}
        for title, drama, stat in zip(titles, dramas, stats, strict=False):
            items[title] = {"items": drama, "stats": stat}

        self.info["list"] = items

    def _parse_title(self, item: BeautifulSoup) -> str:
        return item.find("h3", class_="mdl-style-list-label").get_text(strip=True)

    def _parse_total_stats(self, item: BeautifulSoup) -> Dict[str, str]:
        drama_stats = item.find("label", class_="mdl-style-dramas")
        tvshows_stats = item.find("label", class_="mdl-style-tvshows")
        episodes_stats = item.find("label", class_="mdl-style-episodes")
        movies_stats = item.find("label", class_="mdl-style-movies")
        days_stats = item.find("label", class_="mdl-style-days")
        return {
            label.find("span", class_="name").get_text(strip=True): label.find(
                "span", class_="cnt"
            ).get_text(strip=True)
            for label in [
                drama_stats,
                tvshows_stats,
                episodes_stats,
                movies_stats,
                days_stats,
            ]
        }

    def _parse_drama(self, item: BeautifulSoup) -> Dict[str, str]:
        item_names = item.find_all("a", class_="title")
        item_scores = item.find_all("span", class_="score")
        item_episode_seens = item.find_all("span", class_="episode-seen")
        item_episode_totals = item.find_all("span", class_="episode-total")

        parsed_data = []
        for name, score, seen, total in zip(
            item_names,
            item_scores,
            item_episode_seens,
            item_episode_totals,
            strict=False,
        ):
            parsed_item = {
                "name": name.get_text(strip=True),
                "id": name.get("href", "").split("/")[-1],
                "score": score.get_text(strip=True),
                "episode_seen": seen.get_text(strip=True),
                "episode_total": total.get_text(strip=True),
            }
            parsed_data.append(parsed_item)

        return parsed_data

    def _get(self) -> None:
        self._get_main_container()


class FetchList(BaseFetch):
    def __init__(self, soup: BeautifulSoup, query: str, code: int, ok: bool) -> None:
        super().__init__(soup, query, code, ok)

    def _get_main_container(self) -> None:
        container = self.soup.find("div", class_="app-body")

        # get list title
        header = container.find("div", class_="box-header")
        self.info["title"] = header.find("h1").get_text().strip()

        description = header.find("div", class_="description")
        self.info["description"] = (
            description.get_text().strip() if description is not None else ""
        )

        # get list
        container_list = container.find("div", class_="collection-list")
        all_items = container_list.find_all("li")
        list_items = []
        for i in all_items:
            i_url = i.find("a").get("href")
            if "/people/" in i_url:
                list_items.append(self._parse_person(i))
                continue

            list_items.append(self._parse_show(i))

        self.info["list"] = list_items

    def _parse_person(self, item: BeautifulSoup) -> Dict[str, Any]:
        # parse person image
        person_img_container = str(
            item.find("img", class_="img-responsive")["data-src"]
        ).split("/1280/")
        person_img = ""
        if len(person_img_container) > 1:
            person_img = person_img_container[1]
        else:
            person_img = person_img_container[0]

        person_img = person_img.replace(
            "s.jpg", "m.jpg"
        )  # replace image url to give the bigger size

        item_header = item.find("div", class_="content")
        person_name = item_header.find("a").get_text().strip()
        person_slug = item_header.find("a").get("href")
        person_url = urljoin(MYDRAMALIST_WEBSITE, person_slug)

        person_nationality = item.find(class_="text-muted").get_text().strip()
        person_details_xx = item.find_all("p")
        person_details = ""
        if len(person_details_xx) > 1:
            person_details = person_details_xx[-1].get_text().strip()

        return {
            "name": person_name,
            "type": "person",  # todo: change this
            "image": person_img,
            "slug": person_slug,
            "url": person_url,
            "nationality": person_nationality,
            "details": person_details,
        }

    def _parse_show(self, item: BeautifulSoup) -> Dict[str, Any]:
        # parse list image
        list_img_container = str(
            item.find("img", class_="img-responsive")["data-src"]
        ).split("/1280/")
        list_img = ""
        if len(list_img_container) > 1:
            list_img = list_img_container[1]
        else:
            list_img = list_img_container[0]

        list_img = list_img.replace(
            "t.jpg", "c.jpg"
        )  # replace image url to give the bigger size

        list_header = item.find("h2")
        list_title = list_header.find("a").get_text().strip()
        list_title_rank = (
            list_header.get_text().replace(list_title, "").strip().strip(".")
        )
        list_url = urljoin(MYDRAMALIST_WEBSITE, list_header.find("a").get("href"))
        list_slug = list_header.find("a").get("href")

        # parse example: `Korean Drama - 2020, 16 episodes`
        list_details_container = item.find(class_="text-muted")  # could be `p` or `div`
        list_details_xx = list_details_container.get_text().split(",")
        list_details_type = list_details_xx[0].split("-")[0].strip()
        list_details_year = list_details_xx[0].split("-")[1].strip()

        list_details_episodes = None
        if len(list_details_xx) > 1:
            list_details_episodes = int(
                list_details_xx[1].replace("episodes", "").strip()
            )

        # try to get description, it is missing on some lists
        list_short_summary = ""
        list_short_summary_container = item.find("div", class_="col-xs-12 m-t-sm")
        if list_short_summary_container is not None:
            list_short_summary = (
                list_short_summary_container.get_text()
                .replace("...more", "...")
                .strip()
            )

        return {
            "title": list_title,
            "image": list_img,
            "rank": list_title_rank,
            "url": list_url,
            "slug": list_slug,
            "type": list_details_type,
            "year": list_details_year,
            "episodes": list_details_episodes,
            "short_summary": list_short_summary,
        }

    def _get(self) -> None:
        self._get_main_container()


class FetchEpisodes(BaseFetch):
    def __init__(self, soup, query, code, ok):
        super().__init__(soup, query, code, ok)

    def _get_main_container(self) -> None:
        container = self.soup.find("div", class_="app-body")
        title = self._parse_title(container)
        episodes = self._parse_episodes(container)

        self.info = {
            "title": title,
            "episodes": episodes,
        }

    def _parse_episodes(self, item: BeautifulSoup) -> List[Dict[str, Any]]:
        episodes_container = item.find("div", class_="episodes")
        epi_list = episodes_container.find_all(
            "div", class_="col-xs-12 col-sm-6 col-md-4 p-a episode"
        )

        episodes = []
        for epi in epi_list:
            title = epi.find("h2", class_="title").get_text(strip=True)

            cover = epi.find("div", class_="cover")
            img = cover.find("img")["data-src"]
            link = urljoin(MYDRAMALIST_WEBSITE, cover.find("a")["href"])

            rating = (
                epi.find("div", class_="rating-panel m-b-0")
                .find("div")
                .get_text(strip=True)
            )
            air_date = epi.find("div", class_="air-date").get_text(strip=True)

            episodes.append(
                {
                    "title": title,
                    "image": img,
                    "link": link,
                    "rating": rating,
                    "air_date": air_date,
                }
            )

        return episodes

    def _parse_title(self, item: BeautifulSoup) -> str:
        title = item.find("h1", class_="film-title").get_text(strip=True)
        return title

    def _get(self):
        self._get_main_container()


# NEW CLASSES BASED ON NODE.JS FUNCTIONALITY

class FetchNewsFeeds(BaseFetch):
    """Fetch news feeds from homepage"""
    
    def __init__(self, soup: BeautifulSoup, query: str, code: int, ok: bool) -> None:
        super().__init__(soup, query, code, ok)

    def _get_main_container(self) -> None:
        # Find the news container
        feature_news_container = self.soup.find("div", id="articles-list-popular")
        
        if not feature_news_container:
            self.info["newsFeeds"] = []
            return

        news_feeds = []
        news_items = feature_news_container.find_all("div", class_="list-item article-item")

        for item in news_items:
            try:
                # Extract image source
                img_element = item.find("div", class_="list-left").find("a").find("img")
                img_src = self._get_poster_from_element(img_element)

                # Extract type/category
                category_element = item.find("div", class_="list-body").find("div", class_="category-name").find("strong")
                news_type = category_element.get_text().strip() if category_element else ""

                # Extract title and link
                title_element = item.find("div", class_="list-body").find("h6", class_="title").find("a")
                title = title_element.get_text().strip() if title_element else ""
                link = title_element.get("href") if title_element else ""

                # Extract description
                desc_element = item.find("div", class_="list-body").find("p")
                desc = desc_element.get_text().strip() if desc_element else ""

                # Extract publication date
                pub_date_element = item.find("div", class_="list-bottom").find("div", class_="pub-date")
                pub_date = pub_date_element.get_text().strip() if pub_date_element else ""

                news_feeds.append({
                    "imgSrc": img_src,
                    "type": news_type,
                    "title": title,
                    "desc": desc,
                    "link": urljoin(MYDRAMALIST_WEBSITE, link) if link else "",
                    "pubDate": pub_date,
                })

            except Exception as e:
                print(f"Error parsing news item: {e}")
                continue

        self.info["newsFeeds"] = news_feeds

    def _get_poster_from_element(self, img_element) -> str:
        """Extract image URL from img element"""
        if not img_element:
            return ""
        
        for attr in self._img_attrs:
            if img_element.has_attr(attr):
                return img_element[attr]
        return ""

    def _get(self) -> None:
        self._get_main_container()


class FetchTopAiring(BaseFetch):
    """Fetch top airing shows by country"""
    
    def __init__(self, soup: BeautifulSoup, query: str, code: int, ok: bool) -> None:
        super().__init__(soup, query, code, ok)

    def _get_main_container(self) -> None:
        top_shows = []
        country_ids = [
            "tpa-1",    # Japan
            "tpa-2",    # China
            "tpa-3",    # South Korea
            "tpa-4",    # Hong Kong
            "tpa-5",    # Taiwan
            "tpa-6",    # Thailand
            "tpa-140",  # Philippines
        ]

        for country_id in country_ids:
            country_container = self.soup.find("div", id=country_id)
            if not country_container:
                continue

            list_container = country_container.find("ul", class_="list top-list")
            if not list_container:
                continue
                
            list_items = list_container.find_all("li", class_="list-item")

            for item in list_items:
                try:
                    # Extract rank
                    rank_element = item.find("div", class_="list-left rank")
                    rank = rank_element.get_text().strip() if rank_element else ""

                    # Extract title and link
                    title_element = item.find("a", class_="title")
                    title = title_element.get_text().strip() if title_element else ""
                    link = title_element.get("href") if title_element and title_element.get("href") else ""

                    # Extract image
                    img_element = item.find("img", class_="lazy")
                    img_src = self._get_poster_from_element(img_element)

                    # Extract score
                    score_element = item.find("div", class_="list-info").find("span", class_="score")
                    score = score_element.get_text().strip() if score_element else ""

                    # Extract details (drama type, episodes, watchers)
                    list_info = item.find("div", class_="list-info")
                    detail_elements = list_info.find_all("div", class_="text-sm")
                    details = []
                    for detail in detail_elements:
                        details.append(detail.get_text().strip())
                    detail_string = ", ".join(details)

                    top_shows.append({
                        "rank": rank,
                        "title": title,
                        "link": urljoin(MYDRAMALIST_WEBSITE, link) if link else "",
                        "imgSrc": img_src,
                        "score": score,
                        "details": detail_string,
                        "countryId": country_id,
                    })

                except Exception as e:
                    print(f"Error parsing top airing item: {e}")
                    continue

        self.info["topAiringShows"] = top_shows

    def _get_poster_from_element(self, img_element) -> str:
        """Extract image URL from img element"""
        if not img_element:
            return ""
        
        # Check for data-src first (lazy loading), then src
        if img_element.has_attr("data-src"):
            return img_element["data-src"]
        elif img_element.has_attr("src"):
            return img_element["src"]
        return ""

    def _get(self) -> None:
        self._get_main_container()


class FetchRecommendations(BaseFetch):
    """Fetch drama recommendations with pagination"""

    def __init__(self, soup: BeautifulSoup, query: str, code: int, ok: bool) -> None:
        super().__init__(soup, query, code, ok)

    def _get_main_container(self) -> None:
        recommendations = []
        pages = []

        rec_containers = self.soup.find_all("div", class_="recs-box")

        for recs_box in rec_containers:
            try:
                recommendation = {}

                # Image
                img_element = recs_box.find("img", class_="img-responsive")
                recommendation["imageSrc"] = self._get_poster_from_element(img_element)

                # Title & Link
                title_element = recs_box.find("b").find("a", class_="text-primary")
                recommendation["title"] = title_element.get_text(strip=True) if title_element else ""
                recommendation["link"] = urljoin(MYDRAMALIST_WEBSITE, title_element.get("href", "")) if title_element else ""

                # Rating
                score_element = recs_box.find("span", class_="score")
                recommendation["rating"] = score_element.get_text(strip=True) if score_element else ""

                # Description
                recs_body = recs_box.find("div", class_="recs-body")
                if recs_body:
                    recs_body_copy = copy.copy(recs_body)
                    for cls in ["recs-by", "more-recs-container"]:
                        div_to_remove = recs_body_copy.find("div", class_=cls)
                        if div_to_remove:
                            div_to_remove.decompose()
                    recommendation["description"] = recs_body_copy.get_text(strip=True)
                else:
                    recommendation["description"] = ""

                # Recommended by and Like Count
                recs_by_section = recs_box.find("div", class_="recs-by")
                if recs_by_section:
                    author = recs_by_section.find("span", class_="recs-author")
                    rec_by = author.find("a", class_="text-primary") if author else None
                    recommendation["recommendedBy"] = rec_by.get_text(strip=True) if rec_by else ""

                    like_cnt = recs_by_section.find("span", class_="like-cnt")
                    recommendation["likeCount"] = like_cnt.get_text(strip=True) if like_cnt else "0"
                else:
                    recommendation["recommendedBy"] = ""
                    recommendation["likeCount"] = "0"

                recommendations.append(recommendation)

            except Exception as e:
                print(f"Error parsing recommendation: {e}")

        # Pagination
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

                pages.append({
                    "currentPage": current_page,
                    "prevPageSlug": extract_page_slug(prev) or False,
                    "nextPageSlug": extract_page_slug(next_) or False,
                    "totalPages": int(extract_page_slug(last) or current_page),
                })
        except Exception as e:
            print(f"Error parsing pagination: {e}")

        self.info["recommendations"] = recommendations
        self.info["pages"] = pages

    def _get_poster_from_element(self, img_element) -> str:
        if not img_element:
            return ""
        
        for attr in self._img_attrs:
            if img_element.has_attr(attr):
                return img_element[attr]
        return ""

    def _get(self) -> None:
        self._get_main_container()

class FetchEpisodeDetails(BaseFetch):
    """Fetch detailed episode information"""
    
    def __init__(self, soup: BeautifulSoup, query: str, code: int, ok: bool) -> None:
        super().__init__(soup, query, code, ok)

    def _get_main_container(self) -> None:
        episode_details = []

        # Find all episode items
        episodes = self.soup.find_all("div", class_="episode")

        for episode in episodes:
            try:
                # Extract title
                title_element = episode.find(class_="title")
                title = title_element.get_text().strip() if title_element else ""

                # Extract link and episode number
                link_element = title_element.find("a") if title_element else None
                link = link_element.get("href") if link_element else ""
                
                # Extract episode number from link
                episode_number = None
                if link:
                    import re
                    match = re.search(r'episode/(\d+)', link)
                    if match:
                        episode_number = int(match.group(1))

                # Extract rating
                rating_element = episode.find("div", class_="rating-panel").find("b")
                rating = rating_element.get_text().strip() if rating_element else ""
                rating_int = None
                try:
                    rating_int = int(rating) if rating else None
                except ValueError:
                    rating_int = None

                # Extract air date
                air_date_element = episode.find("div", class_="air-date")
                air_date = air_date_element.get_text().strip() if air_date_element else ""

                # Extract poster image
                cover_element = episode.find("div", class_="cover")
                poster = ""
                if cover_element:
                    img_element = cover_element.find("img")
                    poster = self._get_poster_from_element(img_element)

                episode_detail = {
                    "title": title,
                    "link": urljoin(MYDRAMALIST_WEBSITE, link) if link else "",
                    "rating": rating_int,
                    "airDate": air_date,
                    "episodeNumber": episode_number,
                    "poster": poster,
                }

                episode_details.append(episode_detail)

            except Exception as e:
                print(f"Error parsing episode detail: {e}")
                continue

        self.info["episodeDetails"] = episode_details

    def _get_poster_from_element(self, img_element) -> str:
        """Extract image URL from img element"""
        if not img_element:
            return ""
        
        for attr in self._img_attrs:
            if img_element.has_attr(attr):
                return img_element[attr]
        return ""

    def _get(self) -> None:
        self._get_main_container()


class FetchShowsStartingThisWeek(BaseFetch):
    """Fetch shows starting this week from homepage"""
    
    def __init__(self, soup: BeautifulSoup, query: str, code: int, ok: bool) -> None:
        super().__init__(soup, query, code, ok)

    def _get_main_container(self) -> None:
        shows_starting = []

        # Target the specific section for "Shows Starting This Week" using the exact selector from Node.js
        starting_slides = self.soup.select("#slide-started .swiper-slide")

        for slide in starting_slides:
            try:
                # Extract title
                title_element = slide.find(class_="film-title")
                title = title_element.get_text().strip() if title_element else ""

                # Extract link
                link_element = slide.find(class_="film-cover")
                link = link_element.get("href") if link_element else ""

                # Extract image (check data-src first, then src)
                img_element = slide.find("img")
                img_src = self._get_poster_from_element(img_element)

                # Extract country/details
                country_element = slide.find(class_="text-muted")
                country = country_element.get_text().strip() if country_element else ""

                shows_starting.append({
                    "title": title,
                    "link": urljoin(MYDRAMALIST_WEBSITE, link) if link else "",
                    "imgSrc": img_src,
                    "country": country,
                })

            except Exception as e:
                print(f"Error parsing starting show: {e}")
                continue

        self.info["statingThisWeek"] = shows_starting  # Match Node.js property name

    def _get_poster_from_element(self, img_element) -> str:
        """Extract image URL from img element"""
        if not img_element:
            return ""
        
        for attr in self._img_attrs:
            if img_element.has_attr(attr):
                return img_element[attr]
        return ""

    def _get(self) -> None:
        self._get_main_container()

class FetchShowsTrendingThisWeek(BaseFetch):
    """Fetch shows trending this week from homepage"""
    
    def __init__(self, soup: BeautifulSoup, query: str, code: int, ok: bool) -> None:
        super().__init__(soup, query, code, ok)

    def _get_main_container(self) -> None:
        trending_shows = []

        # Target the specific section for "Shows Trending This Week" using the exact selector from Node.js
        trending_slides = self.soup.select("#slide-trending .swiper-slide")

        for slide in trending_slides:
            try:
                # Extract title
                title_element = slide.find(class_="film-title")
                title = title_element.get_text().strip() if title_element else ""

                # Extract link
                link_element = slide.find(class_="film-cover")
                link = link_element.get("href") if link_element else ""

                # Extract image (check data-src first, then src)
                img_element = slide.find("img")
                img_src = self._get_poster_from_element(img_element)

                # Extract country/details
                country_element = slide.find(class_="text-muted")
                country = country_element.get_text().strip() if country_element else ""

                trending_shows.append({
                    "title": title,
                    "link": urljoin(MYDRAMALIST_WEBSITE, link) if link else "",
                    "imgSrc": img_src,
                    "country": country,
                })

            except Exception as e:
                print(f"Error parsing trending show: {e}")
                continue

        self.info["trendingThisWeek"] = trending_shows

    def _get_poster_from_element(self, img_element) -> str:
        """Extract image URL from img element"""
        if not img_element:
            return ""
        
        for attr in self._img_attrs:
            if img_element.has_attr(attr):
                return img_element[attr]
        return ""

    def _get(self) -> None:
        self._get_main_container()

class FetchTodaysBirthdays(BaseFetch):
    """Fetch today's birthdays from homepage"""
    
    def __init__(self, soup: BeautifulSoup, query: str, code: int, ok: bool) -> None:
        super().__init__(soup, query, code, ok)

    def _get_main_container(self) -> None:
        birthdays = []

        # Target the specific section for "Today's Birthday" using the exact selector from Node.js
        birthday_slides = self.soup.select("#slide-birthday .swiper-slide")

        for slide in birthday_slides:
            try:
                # Extract name
                name_element = slide.find(class_="people-name")
                name = name_element.get_text().strip() if name_element else ""

                # Extract link
                link_element = slide.find(class_="image")
                link = link_element.get("href") if link_element else ""

                # Extract image (check data-src first, then src)
                img_element = slide.find("img")
                img_src = self._get_poster_from_element(img_element)

                # Extract details
                details_element = slide.find(class_="text-muted")
                details = details_element.get_text().strip() if details_element else ""

                birthdays.append({
                    "name": name,
                    "link": urljoin(MYDRAMALIST_WEBSITE, link) if link else "",
                    "imgSrc": img_src,
                    "details": details,
                })

            except Exception as e:
                print(f"Error parsing birthday person: {e}")
                continue

        self.info["todaysBirthday"] = birthdays  # Match Node.js property name

    def _get_poster_from_element(self, img_element) -> str:
        """Extract image URL from img element"""
        if not img_element:
            return ""
        
        for attr in self._img_attrs:
            if img_element.has_attr(attr):
                return img_element[attr]
        return ""

    def _get(self) -> None:
        self._get_main_container()
