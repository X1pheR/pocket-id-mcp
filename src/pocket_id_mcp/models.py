from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EmptyInput(StrictModel):
    pass


class SearchInput(StrictModel):
    search: str | None = Field(default=None, max_length=200)


class IdentifierInput(StrictModel):
    id: str = Field(min_length=1, max_length=128)


class RestrictedClientCreateInput(StrictModel):
    name: str = Field(min_length=1, max_length=50)
    callback_urls: list[str] = Field(min_length=1, max_length=20)
    allowed_group_names: list[str] = Field(min_length=1, max_length=20)
    logout_callback_urls: list[str] = Field(default_factory=list, max_length=20)
    is_public: bool = False
    pkce_enabled: bool = False
    requires_reauthentication: bool = False
    launch_url: str | None = Field(default=None, max_length=2048)
    requested_client_id: str | None = Field(default=None, min_length=2, max_length=128)


class SetAllowedGroupsInput(StrictModel):
    client_id: str = Field(min_length=1, max_length=128)
    allowed_group_names: list[str] = Field(min_length=1, max_length=20)


class SecretFileInput(StrictModel):
    client_id: str = Field(min_length=1, max_length=128)
    file_name: str = Field(min_length=1, max_length=128)


class DeleteClientInput(StrictModel):
    client_id: str = Field(min_length=1, max_length=128)
    expected_name: str = Field(min_length=1, max_length=50)
    confirm: bool
