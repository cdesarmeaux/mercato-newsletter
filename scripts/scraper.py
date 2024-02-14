import boto3
import os
import shutil
import requests
from datetime import datetime, timedelta
from typing import List, Dict
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

ALLOWED_LEAGUES = [
    {
        "name": "Premier League",
        "country": "England",
    },
    {
        "name": "LaLiga",
        "country": "Spain",
    },
    {
        "name": "Serie A",
        "country": "Italy",
    },
    {
        "name": "Ligue 1",
        "country": "France",
    },
    {
        "name": "Bundesliga",
        "country": "Germany",
    },
]

BUCKET_NAME = "thetransferledger-newsletters"


def render_template(template_path, **kwargs):
    env = Environment(loader=FileSystemLoader("../templates"))
    template = env.get_template(template_path)
    return template.render(**kwargs)


def upload_to_s3(file_path, bucket_name, s3_path):
    s3 = boto3.client("s3")
    with open(file_path, "rb") as f:
        s3.upload_fileobj(f, bucket_name, s3_path, ExtraArgs={"ACL": "public-read"})


def save_html_to_temp_file(html_content: str, filename: str) -> str:
    """Save the given HTML content to a temporary file and return its path."""
    temp_file_path = f"/tmp/{filename}"
    with open(temp_file_path, "w") as file:
        file.write(html_content)
    return temp_file_path


def save_and_upload_image(url, filename, folder):
    response = requests.get(url, stream=True)
    file_path = f"/tmp/{filename}"
    with open(file_path, "wb") as out_file:
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, out_file)
    s3_path = f"images/{folder}/{filename}"
    upload_to_s3(file_path, BUCKET_NAME, s3_path)
    os.remove(file_path)

    # Construct the public URL
    public_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_path}"
    return public_url


def upload_images_for_transfer(transfer_item: Dict) -> None:
    # Upload player image
    player_image = transfer_item.pop("player_image_temp", None)
    if player_image:
        image_filename = transfer_item["player_name"].lower().replace(" ", "_")
        player_url = save_and_upload_image(player_image, image_filename, "players")
        transfer_item["player_image"] = player_url

    # Upload club and league images for both left and joined
    for direction in ["left", "joined"]:
        club_image = transfer_item.pop(f"{direction}_club_image_temp", None)
        league_image = transfer_item.pop(f"{direction}_league_image_temp", None)

        if club_image and league_image:
            club_image_filename = f'{transfer_item[f"{direction}_league"].lower().replace(" ", "_")}_{transfer_item[f"{direction}_club"].lower().replace(" ", "_")}'
            league_image_filename = f'{transfer_item[f"{direction}_league_country"].lower().replace(" ", "_")}_{transfer_item[f"{direction}_league"].lower().replace(" ", "_")}'

            club_url = save_and_upload_image(club_image, club_image_filename, "clubs")
            league_url = save_and_upload_image(
                league_image, league_image_filename, "leagues"
            )

            transfer_item[f"{direction}_club_image"] = club_url
            transfer_item[f"{direction}_league_image"] = league_url


def get_yesterdays_date() -> str:
    """Return yesterday's date in the format YYYY-MM-DD."""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def fetch_html_content(url: str) -> str:
    """Fetch the HTML content of the given URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def is_league_allowed(league_name: str, league_country: str) -> bool:
    """Check if the league is in the allowed list."""
    for league in ALLOWED_LEAGUES:
        if league["name"] == league_name and league["country"] == league_country:
            return True
    return False


def add_player_info(cell: BeautifulSoup, transfer_item: Dict) -> None:
    player_info = cell.select("table > tr > td")
    player_image = None
    player_name = player_info[1].text.strip()
    player_image_elem = player_info[0].find("img")
    if player_image_elem:
        player_image = player_image_elem["data-src"]
    player_position = player_info[2].text.strip()
    player_transfermarkt_url = (
        f'https://www.transfermarkt.com{player_info[1].find("a").get("href", "")}'
    )

    transfer_item.update(
        {
            "player_name": player_name,
            "player_image_temp": player_image,  # Temporary placeholder
            "player_position": player_position,
            "player_transfermarkt_url": player_transfermarkt_url,
        }
    )


def add_player_age(cell: BeautifulSoup, transfer_item: Dict) -> None:
    player_age = cell.text.strip()
    transfer_item.update({"player_age": player_age})


def add_club_info(cell: BeautifulSoup, transfer_item: Dict, direction: str) -> None:
    club_info = cell.select("table > tr > td")
    club_image = None
    club_image_elem = club_info[0].find("img")
    if club_image_elem:
        club_image = club_image_elem["src"]
    club_name = club_info[1].text.strip()
    league_image = None
    league_country = None
    league_image_elem = club_info[2].find("img")
    if league_image_elem:
        league_image = league_image_elem["src"]
        league_country = league_image_elem["title"]
    league_name = club_info[2].text.strip()
    club_transfermarkt_url = (
        f'https://www.transfermarkt.com{club_info[1].find("a").get("href", "")}'
    )
    transfer_item.update(
        {
            f"{direction}_club": club_name,
            f"{direction}_club_image_temp": club_image,
            f"{direction}_league": league_name,
            f"{direction}_league_image_temp": league_image,
            f"{direction}_league_country": league_country,
            f"{direction}_club_transfermarkt_url": club_transfermarkt_url,
        }
    )


def add_fee(cell: BeautifulSoup, transfer_item: Dict) -> None:
    player_fee = cell.text.strip()
    transfer_item.update({"fee": player_fee})


def extract_data_from_html(html_content: str) -> List[Dict]:
    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table", class_="items")
    rows = table.select("tbody > tr")

    data = []
    for row in rows:
        transfer_item = {}
        columns = row.find_all("td", recursive=False)
        add_player_info(columns[0], transfer_item)
        add_player_age(columns[1], transfer_item)
        add_club_info(columns[2], transfer_item, "left")
        add_club_info(columns[3], transfer_item, "joined")
        add_fee(columns[4], transfer_item)
        data.append(transfer_item)

    filtered_data = [
        item
        for item in data
        if is_league_allowed(item["left_league"], item["left_league_country"])
        or is_league_allowed(item["joined_league"], item["joined_league_country"])
    ]
    return filtered_data


def main():
    base_url = "https://www.transfermarkt.com/transfers/transfertagedetail/statistik/top/land_id_zu/0/land_id_ab/0/leihe//datum/"
    date = get_yesterdays_date()
    page_num = 1
    all_data = []
    while True:
        full_url = f"{base_url}{date}/page/{page_num}"
        html_content = fetch_html_content(full_url)
        try:
            all_data.extend(extract_data_from_html(html_content))
        except Exception as e:
            print(f"Error while extracting data from {full_url}")
            raise e
        soup = BeautifulSoup(html_content, "html.parser")
        next_page_elem = soup.find(
            "li",
            class_="tm-pagination__list-item tm-pagination__list-item--icon-next-page",
        )
        if not next_page_elem:
            break
        page_num += 1
    # Upload images for the filtered data
    for item in all_data:
        upload_images_for_transfer(item)

    # Render the template
    rendered_html = render_template("newsletter.html", transfers=all_data)

    # Save the rendered HTML to a temporary file
    date_str = get_yesterdays_date()
    temp_file_path = save_html_to_temp_file(rendered_html, f"{date_str}.html")

    # Upload to S3
    s3_path = f"{date_str}.html"
    upload_to_s3(temp_file_path, BUCKET_NAME, s3_path)

    # Remove the temporary file
    os.remove(temp_file_path)


if __name__ == "__main__":
    main()
