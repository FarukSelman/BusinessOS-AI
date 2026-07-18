from uuid import UUID

from app.core.exceptions import BadRequestException
from app.modules.business.models import Business
from app.modules.business.repository import BusinessRepository
from app.modules.business.schemas import BusinessCreate, BusinessUpdate
from app.shared.utils.slug import generate_slug


class BusinessService:
    """
    Business business logic layer.
    """

    def __init__(self, repository: BusinessRepository):
        self.repository = repository

    # ----------------------------
    # Create
    # ----------------------------

    def create(self, data: BusinessCreate) -> Business:

        if self.repository.get_by_email(data.email):
            raise BadRequestException(
                "Business email already exists."
            )

        slug = generate_slug(data.name)

        if self.repository.get_by_slug(slug):
            raise BadRequestException(
                "Business slug already exists."
            )

        business = Business(
            name=data.name,
            slug=slug,
            industry=data.industry,
            email=data.email,
            phone=data.phone,
            website=str(data.website) if data.website else None,
            logo_url=str(data.logo_url) if data.logo_url else None,
        )

        return self.repository.create(business)

    # ----------------------------
    # Read
    # ----------------------------

    def get(self, business_id: UUID) -> Business:

        business = self.repository.get(business_id)

        if business is None:
            raise BadRequestException(
                "Business not found."
            )

        return business

    def list(self) -> list[Business]:
        return self.repository.get_all()

    # ----------------------------
    # Update
    # ----------------------------

    def update(
        self,
        business_id: UUID,
        data: BusinessUpdate,
    ) -> Business:

        business = self.get(business_id)

        update_data = data.model_dump(exclude_unset=True)

        # Email kontrolü
        if "email" in update_data:

            existing = self.repository.get_by_email(
                update_data["email"]
            )

            if existing and existing.id != business.id:
                raise BadRequestException(
                    "Business email already exists."
                )

        # İsim değiştiyse slug üret
        if "name" in update_data:

            new_slug = generate_slug(
                update_data["name"]
            )

            existing = self.repository.get_by_slug(
                new_slug
            )

            if existing and existing.id != business.id:
                raise BadRequestException(
                    "Business slug already exists."
                )

            business.slug = new_slug

        # HttpUrl -> str dönüşümü
        if "website" in update_data and update_data["website"]:
            update_data["website"] = str(update_data["website"])

        if "logo_url" in update_data and update_data["logo_url"]:
            update_data["logo_url"] = str(update_data["logo_url"])

        # Alanları güncelle
        for field, value in update_data.items():
            setattr(business, field, value)

        return self.repository.update(business)

    # ----------------------------
    # Delete
    # ----------------------------

    def delete(
        self,
        business_id: UUID,
    ) -> None:

        business = self.get(business_id)

        self.repository.delete(business)