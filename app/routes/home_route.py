from database.database import get_session
from fastapi import APIRouter, Depends
from interaction_servise import (checkup_interaction, token_interaction,
                                 user_interaction)

home_route = APIRouter()


@home_route.get("/")
async def index():
    return {"message": "Hello world!"}


@home_route.get("/all_token")
async def token_get_all(session=Depends(get_session)):
    tokens = token_interaction.get_all_tokens(session)
    return {"tokens": tokens}


@home_route.get("/all_users")
async def users_get_all(session=Depends(get_session)):
    users = user_interaction.get_all_users(session)
    return {"users": users}


@home_route.get("/all_checkups")
async def checkups_get_all(session=Depends(get_session)):
    checkups = checkup_interaction.get_all_checkup(session)
    return {"checkups": checkups}
