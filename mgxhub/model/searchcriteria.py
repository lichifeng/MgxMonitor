'''Format of the search criteria for the search API'''

from typing import List, Optional

from pydantic import BaseModel, Field


class SearchCriteria(BaseModel):
    '''Search criteria for the search API'''

    page: Optional[int] = Field(default=1, ge=1)
    page_size: Optional[int] = Field(default=100, ge=1)
    order_by: Optional[str] = Field(default=None)
    order_desc: Optional[bool] = Field(default=False)
    game_guid: Optional[str] = Field(default=None)
    duration_min: Optional[int] = Field(default=0, ge=0)
    duration_max: Optional[int] = Field(default=0, ge=0)
    include_ai: Optional[bool] = Field(default=None)
    is_multiplayer: Optional[bool] = Field(default=None)
    population_min: Optional[int] = Field(default=0, ge=0)
    population_max: Optional[int] = Field(default=0, ge=0)
    instruction: Optional[str] = Field(default=None)
    gametime_min: Optional[str] = Field(default=None)
    gametime_max: Optional[str] = Field(default=None)
    map_name: Optional[str] = Field(default=None)
    # Following fields have limited options
    speed: Optional[List[str]] = Field(default=None)
    victory_type: Optional[List[str]] = Field(default=None)
    version_code: Optional[List[str]] = Field(default=None)
    matchup: Optional[List[str]] = Field(default=None)
    map_size: Optional[List[str]] = Field(default=None)
