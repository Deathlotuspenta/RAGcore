"""LLM model / API key settings (requires login)."""

from fastapi import APIRouter, Depends, HTTPException, status

from server.auth.deps import get_current_user_id
from server.schemas import LlmSettingsResponse, LlmSettingsUpdate
from server.services import settings_service

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/llm", response_model=LlmSettingsResponse)
def get_llm_settings(_user_id: str = Depends(get_current_user_id)):
    return LlmSettingsResponse(**settings_service.get_llm_settings())


@router.put("/llm", response_model=LlmSettingsResponse)
def update_llm_settings(
    body: LlmSettingsUpdate,
    _user_id: str = Depends(get_current_user_id),
):
    if body.model_name is None and body.model_url is None and body.api_key is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "请至少提供一项要更新的配置")
    try:
        data = settings_service.update_llm_settings(
            model_name=body.model_name,
            model_url=body.model_url,
            api_key=body.api_key,
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e
    return LlmSettingsResponse(**data)
