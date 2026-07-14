from app.core.exceptions import BadRequestException
from app.modules.business.models import Business
from app.modules.business.repository import BusinessRepository
from app.modules.business.schemas import BusinessCreate
from app.shared.utils.slug import generate_slug


class BusinessService:

    def __init__(
        self,
        repository: BusinessRepository,
    ):
        self.repository = repository

    def create_business(
        self,
        data: BusinessCreate,
    ) -> Business:

        existing_email = self.repository.get_by_email(
            data.email
        )

        if existing_email:
            raise BadRequestException(
                "Business email already exists."
            )

        slug = generate_slug(data.name)

        existing_slug = self.repository.get_by_slug(
            slug
        )

        if existing_slug:
            raise BadRequestException(
                "Business slug already exists."
            )

        business = Business(
            name=data.name,
            slug=slug,
            industry=data.industry,
            email=data.email,
            phone=data.phone,
            website=data.website,
            logo_url=data.logo_url,
        )

        return self.repository.create(business)