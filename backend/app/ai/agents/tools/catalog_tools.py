"""
Catalog tools: products, stock and service packages (Sales agent; customer
packages also used by the Appointment agent). Read-only.
"""
from app.ai.agents.tools.base import ToolResult
from app.ai.agents.tools.common import MAX_ROWS, BusinessTool, find_customer, money


def _product_service(db):
    from app.db.unit_of_work import UnitOfWork
    from app.modules.products.repository import ProductRepository, ProductSaleRepository, StockMovementRepository
    from app.modules.products.service import ProductService

    return ProductService(ProductRepository(db), StockMovementRepository(db), ProductSaleRepository(db), UnitOfWork(db))


def _package_service(db):
    from app.db.unit_of_work import UnitOfWork
    from app.modules.packages.repository import (
        CustomerPackageRepository,
        InstallmentRepository,
        PackageSessionRepository,
        ServicePackageRepository,
    )
    from app.modules.packages.service import PackageService

    return PackageService(
        ServicePackageRepository(db), CustomerPackageRepository(db),
        PackageSessionRepository(db), InstallmentRepository(db), UnitOfWork(db),
    )


def _stock_label(p) -> str:
    if p.current_stock <= 0:
        return "stokta yok"
    if p.current_stock <= p.min_stock_level:
        return f"{p.current_stock} {p.unit} (azaldı)"
    return f"{p.current_stock} {p.unit}"


class SearchProductsTool(BusinessTool):
    @property
    def name(self) -> str:
        return "search_products"

    @property
    def description(self) -> str:
        return "Satılan ürünleri ada, markaya veya SKU'ya göre arar; satış fiyatı ve stok durumunu gösterir."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Aranacak ürün adı/marka/SKU (boşsa tüm ürünler)"},
                "category": {"type": "string", "description": "Kategori filtresi (opsiyonel)"},
                "only_in_stock": {"type": "boolean", "description": "Sadece stokta olanlar"},
            },
        }

    def execute(self, **kwargs) -> ToolResult:
        products = _product_service(self.db).list_products(
            self.business_id, size=50,
            search=(kwargs.get("query") or None), category=(kwargs.get("category") or None),
        )
        if kwargs.get("only_in_stock"):
            products = [p for p in products if p.current_stock > 0]
        if not products:
            return ToolResult(success=True, output="Eşleşen ürün bulunamadı.")
        lines = ["Ürün | Kategori | Satış fiyatı | Stok"]
        for p in products[:MAX_ROWS]:
            lines.append(f"{p.name}{f' ({p.brand})' if p.brand else ''} | {p.category or '-'} | {money(p.sale_price)} | {_stock_label(p)}")
        if len(products) > MAX_ROWS:
            lines.append(f"... ve {len(products) - MAX_ROWS} ürün daha; aramayı daraltın.")
        return ToolResult(success=True, output="\n".join(lines))


class ListLowStockProductsTool(BusinessTool):
    @property
    def name(self) -> str:
        return "list_low_stock_products"

    @property
    def description(self) -> str:
        return "Stoğu minimum seviyenin altına düşmüş veya tükenmiş ürünleri ve genel stok özetini listeler. Stok değiştirmez."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs) -> ToolResult:
        from app.modules.products.repository import ProductRepository

        service = _product_service(self.db)
        summary = service.get_stock_summary(self.business_id)
        low = ProductRepository(self.db).get_low_stock_products(self.business_id)
        lines = [
            f"Stok özeti: {summary['total_products']} ürün, {summary['low_stock_count']} azalan, {summary['out_of_stock_count']} tükenmiş",
        ]
        if self.can_view_finance:
            lines.append(f"Toplam stok değeri (alış fiyatıyla): {money(summary['total_stock_value'])}")
        if not low:
            lines.append("Minimum seviyenin altında ürün yok.")
        else:
            lines.append("Ürün | Mevcut | Minimum")
            for p in low[:MAX_ROWS]:
                lines.append(f"{p.name} | {p.current_stock} {p.unit} | {p.min_stock_level}")
        return ToolResult(success=True, output="\n".join(lines))


class ListServicePackagesTool(BusinessTool):
    @property
    def name(self) -> str:
        return "list_service_packages"

    @property
    def description(self) -> str:
        return "Satıştaki hizmet paketlerini (seans sayısı, içerdiği hizmetler, fiyat, indirim, geçerlilik süresi, taksit imkânı) listeler."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs) -> ToolResult:
        from app.shared.enums.package import PackageStatus

        packages = _package_service(self.db).list_packages(self.business_id, size=50, status=PackageStatus.ACTIVE)
        if not packages:
            return ToolResult(success=True, output="Satışta aktif paket yok.")
        lines = []
        for p in packages[:MAX_ROWS]:
            services = ", ".join(f"{s.get('service_name', '?')} x{s.get('session_count', '?')}" for s in (p.services or []))
            installment = f", {p.max_installments} taksite kadar" if p.is_installment_allowed and p.max_installments > 1 else ""
            discount = f", %{float(p.discount_percentage):g} indirim" if float(p.discount_percentage or 0) > 0 else ""
            lines.append(
                f"- {p.name}: {p.total_sessions} seans ({services}), {money(p.price)}{discount}, "
                f"{p.validity_days} gün geçerli{installment}"
            )
        return ToolResult(success=True, output="Aktif paketler:\n" + "\n".join(lines))


class GetCustomerPackagesTool(BusinessTool):
    @property
    def name(self) -> str:
        return "get_customer_packages"

    @property
    def description(self) -> str:
        return "Bir müşterinin satın aldığı paketleri, kalan seans sayısını ve bitiş tarihini gösterir."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {"customer_name": {"type": "string", "description": "CRM'de kayıtlı müşteri adı"}},
            "required": ["customer_name"],
        }

    def execute(self, **kwargs) -> ToolResult:
        from app.modules.packages.models import ServicePackage

        customer, error = find_customer(self.db, self.business_id, kwargs.get("customer_name", ""))
        if error:
            return ToolResult(success=False, output=error)
        cps = _package_service(self.db).list_customer_packages(self.business_id, size=50, customer_id=customer.id)
        if not cps:
            return ToolResult(success=True, output=f"{customer.name} adına satın alınmış paket yok.")
        names = dict(self.db.query(ServicePackage.id, ServicePackage.name).filter(
            ServicePackage.id.in_({cp.package_id for cp in cps}), ServicePackage.business_id == self.business_id,
        ).all())
        lines = [f"{customer.name} — paketler:"]
        for cp in cps:
            status = getattr(cp.status, "value", cp.status)
            expires = cp.expires_at.date().isoformat() if cp.expires_at else "-"
            pay = f", ödenen {money(cp.paid_amount)} / {money(cp.total_price)}" if self.can_view_finance else ""
            lines.append(
                f"- {names.get(cp.package_id, 'Paket')} [{status}]: {cp.remaining_sessions}/{cp.total_sessions} seans kaldı, "
                f"bitiş {expires}{pay}"
            )
        return ToolResult(success=True, output="\n".join(lines))
