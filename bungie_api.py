from bungio.client import Client as BungieClient
from bungio.models import BungieMembershipType, DestinyComponentType, ExactSearchRequest, DestinyActivityModeType
from config import BUNGIE_API_KEY, BUNGIE_CLIENT_ID, BUNGIE_CLIENT_SECRET

bungie_client = BungieClient(
    bungie_token=BUNGIE_API_KEY,
    bungie_client_id=BUNGIE_CLIENT_ID,
    bungie_client_secret=BUNGIE_CLIENT_SECRET
)

async def search_destiny_player(display_name, bungie_code):
    search_request = ExactSearchRequest(
        display_name=display_name,
        display_name_code=int(bungie_code)
    )
    return await bungie_client.api.search_destiny_player_by_bungie_name(
        data=search_request,
        membership_type=BungieMembershipType.ALL
    )

# Add other Bungie API-related functions here