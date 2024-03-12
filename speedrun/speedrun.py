import requests
from collections import defaultdict
from time import sleep

# Define your API key
api_key = "ibfvgc6z2rqtxqw9tn020246l"

# Define the base URL for the Speedrun.com API
base_url = "https://www.speedrun.com/api/v1/"

# Define the output file path
output_file = "Documents/leaderboard_data_8.txt"

# Define the ID of the game you're interested in
game_id = "grid"

# Define the URL to fetch levels for the game
levels_url = base_url + f"games/{game_id}/levels"

# Make the request to fetch levels
response = requests.get(levels_url)
if response.status_code == 200:
    levels_data = response.json()["data"]

    overall_wins = defaultdict(int)

    # Iterate over each level ID
    for level in levels_data:
        level_id = level["id"]
        print(f"Processing level ID: {level_id}")

        # Define the URL to fetch categories for the game
        categories_url = base_url + f"games/{game_id}/categories"

        # Make the request to fetch categories with retry mechanism
        retry_count = 0
        while retry_count < 3:  # Maximum number of retries
            response = requests.get(categories_url)
            if response.status_code == 200:
                categories_data = response.json()["data"]
                break
            elif response.status_code == 420:
                retry_after = int(response.headers.get('Retry-After', 5))  # Default to retry after 5 seconds
                print(f"Rate limit exceeded. Waiting for {retry_after} seconds before retrying...")
                sleep(retry_after)
                retry_count += 1
            else:
                print(f"Failed to fetch categories. Status code: {response.status_code}")
                break
        else:
            print("Failed to fetch categories after maximum retries.")
            continue

        sms_runs = {}

        # Iterate over categories
        for category in categories_data:
            category_id = category["id"]
            category_name = category["name"]

            # Skip specific categories
            if category_name in ["GRID World Any%", "100%", "All Tracks", "Le Mans"]:
                continue

            # Define the URL to fetch leaderboards for the category
            if category["type"] == "per-level":
                leaderboards_url = base_url + f"leaderboards/{game_id}/level/{level_id}/{category_id}?embed=variables"
            else:
                # Otherwise, it's a category without levels
                leaderboards_url = base_url + f"leaderboards/{game_id}/category/{category_id}?embed=variables"

            # Make the request to fetch leaderboards with retry mechanism
            retry_count = 0
            while retry_count < 3:  # Maximum number of retries
                response = requests.get(leaderboards_url)
                if response.status_code == 200:
                    leaderboard_data = response.json()["data"]
                    break
                elif response.status_code == 420:
                    retry_after = int(response.headers.get('Retry-After', 5))  # Default to retry after 5 seconds
                    print(f"Rate limit exceeded. Waiting for {retry_after} seconds before retrying...")
                    sleep(retry_after)
                    retry_count += 1
                else:
                    print(f"Failed to fetch leaderboards for category: {category_name}. Status code: {response.status_code}")
                    break
            else:
                print(f"Failed to fetch leaderboards for category: {category_name} after maximum retries.")
                continue

            # Check if the "runs" key is available and not empty
            if "runs" in leaderboard_data and leaderboard_data["runs"]:
                # Get the first place run
                first_place_run = leaderboard_data["runs"][0]["run"]
                player_id = first_place_run["players"][0]["id"]  # Assuming the first player is the primary player

                # Fetch player information to get username
                player_url = base_url + f"users/{player_id}"
                response = requests.get(player_url)
                if response.status_code == 200:
                    player_data = response.json()["data"]
                    player_name = player_data["names"]["international"]
                else:
                    print(f"Failed to fetch player information for player ID: {player_id}")
                    player_name = "Unknown"

                # Increment overall wins for the player
                overall_wins[player_name] += 1
            else:
                print(f"No first place run available for category: {category_name}")

    # Write the fetched leaderboard data to a text file
    with open(output_file, "w") as file:
        # Sort overall wins by count in descending order, and then alphabetically
        sorted_overall_wins = dict(sorted(overall_wins.items(), key=lambda item: (-item[1], item[0])))

        # Write overall wins to file
        place = 1
        for player_name, wins in sorted_overall_wins.items():
            file.write(f"{place}. {player_name} - {wins}\n")
            place += 1
else:
    print("Failed to fetch levels.")
