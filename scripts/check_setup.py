import requests

from stress.auth.upstox_auth import get_token

PROFILE_URL = "https://api.upstox.com/v2/user/profile"


def main() -> None:
    token = get_token()
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(PROFILE_URL, headers=headers, timeout=15)
    response.raise_for_status()

    user_name = response.json()["data"]["user_name"]
    print(f"Upstox connection verified! Logged in as: {user_name}")


if __name__ == "__main__":
    main()