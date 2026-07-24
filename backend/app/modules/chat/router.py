from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
)


from app.shared.security.dependencies import (
    get_current_user,
)


from app.modules.user.models import (
    User,
)


from app.modules.chat.dependencies import (
    get_chat_service,
)


from app.modules.chat.schemas import (
    ChatRequest,
    ChatResponse,
)


from app.modules.chat.service import (
    ChatService,
)



router = APIRouter(
    prefix="/businesses/{business_id}/chat",
    tags=["Chat"],
)



@router.post(
    "",
    response_model=ChatResponse,
)
def chat(
    business_id: UUID,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """
    Ask a question about a business knowledge base.
    """


    return service.chat(
        business_id=business_id,
        user_id=current_user.id,
        request=request,
    ) 