import stripe
from django.core.management.base import BaseCommand
from django.conf import settings
from payment_gateway.models import Plan, PlanPricing


class Command(BaseCommand):
    help = "Seed localstripe with Products/Prices and create Plan records (Day Pass, Premium, Free)"

    def add_arguments(self, parser):
        parser.add_argument("--currency", default="usd")
        parser.add_argument("--day_pass_amount", type=int, default=5, help="USD amount for Day Pass")
        parser.add_argument("--premium_amount", type=int, default=200, help="USD amount for Premium monthly")
        parser.add_argument("--free_amount", type=int, default=0, help="USD amount for Free plan")

    def handle(self, *args, **opts):
        currency = opts["currency"].lower()
        # Convert USD dollars to cents
        amt_day_pass_cents = int(round(opts["day_pass_amount"] * 100))
        amt_premium_cents = int(round(opts["premium_amount"] * 100))
        amt_free_cents = int(round(opts["free_amount"] * 100))

        # Ensure stripe is pointed at localstripe and has api_key
        if settings.USE_LOCALSTRIPE:
            stripe.api_key = settings.STRIPE_API_KEY
            try:
                stripe.api_base = settings.LOCALSTRIPE_URL  # type: ignore[attr-defined]
            except Exception:
                pass
        else:
            stripe.api_key = settings.STRIPE_API_KEY

        self.stdout.write(self.style.MIGRATE_HEADING("Seeding products and prices/plans"))

        # 1) Day Pass: daily, non auto-renew (we will cancel at period end at subscribe time)
        day_pass_name = "Day Pass"
        day_pass_desc = "Unlimited time and traffic (1 day access)"
        day_pass_product = self._get_or_create_product(day_pass_name, day_pass_desc)
        if settings.USE_LOCALSTRIPE:
            day_pass_price = self._get_or_create_recurring_plan(
                product_id=day_pass_product["id"],
                unit_amount=amt_day_pass_cents,
                currency=currency,
                interval="day",
            )
        else:
            day_pass_price = self._get_or_create_recurring_price(
                product_id=day_pass_product["id"],
                unit_amount=amt_day_pass_cents,
                currency=currency,
                interval="day",
            )
        day_pass_plan = self._upsert_plan(
            name=day_pass_name,
            description=day_pass_desc,
            default=False,
            available=True,
            requires_payment=True,
            requires_invoice=True,
            auto_renew=False,
            daily_time_minutes=None,
            daily_data_mb=None,
            stripe_product_id=day_pass_product["id"],
        )
        self._upsert_pricing(
            plan=day_pass_plan,
            amount=opts["day_pass_amount"],
            currency=currency.upper(),
            interval="day",
            trial_period_days=0,
            stripe_price_id=day_pass_price["id"],
        )

        # 2) Premium: monthly $200
        premium_name = "Premium"
        premium_desc = "Unlimited time and traffic (monthly)"
        premium_product = self._get_or_create_product(premium_name, premium_desc)
        if settings.USE_LOCALSTRIPE:
            premium_price = self._get_or_create_recurring_plan(
                product_id=premium_product["id"],
                unit_amount=amt_premium_cents,
                currency=currency,
                interval="month",
            )
        else:
            premium_price = self._get_or_create_recurring_price(
                product_id=premium_product["id"],
                unit_amount=amt_premium_cents,
                currency=currency,
                interval="month",
            )
        premium_plan = self._upsert_plan(
            name=premium_name,
            description=premium_desc,
            default=False,
            available=True,
            requires_payment=True,
            requires_invoice=True,
            auto_renew=True,
            daily_time_minutes=None,
            daily_data_mb=None,
            stripe_product_id=premium_product["id"],
        )
        self._upsert_pricing(
            plan=premium_plan,
            amount=opts["premium_amount"],
            currency=currency.upper(),
            interval="month",
            trial_period_days=0,
            stripe_price_id=premium_price["id"],
        )

        # 3) Free: monthly $0, limits 3 hours/day, 300 MB/day
        free_name = "Free"
        free_desc = "3 hours per day, 300 MB per day"
        free_product = self._get_or_create_product(free_name, free_desc)
        if settings.USE_LOCALSTRIPE:
            free_price = self._get_or_create_recurring_plan(
                product_id=free_product["id"],
                unit_amount=amt_free_cents,
                currency=currency,
                interval="month",
            )
        else:
            free_price = self._get_or_create_recurring_price(
                product_id=free_product["id"],
                unit_amount=amt_free_cents,
                currency=currency,
                interval="month",
            )
        free_plan = self._upsert_plan(
            name=free_name,
            description=free_desc,
            default=True,
            available=True,
            requires_payment=False,
            requires_invoice=False,
            auto_renew=True,
            daily_time_minutes=180,
            daily_data_mb=300,
            stripe_product_id=free_product["id"],
        )
        self._upsert_pricing(
            plan=free_plan,
            amount=opts["free_amount"],
            currency=currency.upper(),
            interval="month",
            trial_period_days=0,
            stripe_price_id=free_price["id"],
        )

        self.stdout.write(self.style.SUCCESS("Seeded plans and prices successfully."))

    def _get_or_create_product(self, name: str, description: str):
        # Try to find by exact name
        prods = stripe.Product.list(active=True, limit=100)
        for p in prods.auto_paging_iter():
            if p["name"] == name:
                return p
        return stripe.Product.create(name=name, description=description)

    def _get_or_create_recurring_price(self, product_id: str, unit_amount: int, currency: str, interval: str):
        prices = stripe.Price.list(product=product_id, active=True, limit=100)
        for pr in prices.auto_paging_iter():
            if (
                pr.get("unit_amount") == unit_amount
                and pr.get("currency") == currency
                and pr.get("recurring")
                and pr["recurring"].get("interval") == interval
            ):
                return pr
        return stripe.Price.create(
            product=product_id,
            unit_amount=unit_amount,
            currency=currency,
            recurring={"interval": interval},
        )

    def _get_or_create_recurring_plan(self, product_id: str, unit_amount: int, currency: str, interval: str):
        """Legacy Plan API for localstripe compatibility.
        Stores the returned plan object (with 'id') analogous to Price, so callers can access ['id'].
        """
        plans = stripe.Plan.list(product=product_id, active=True, limit=100)
        for pl in plans.auto_paging_iter():
            if (
                pl.get("amount") == unit_amount
                and pl.get("currency") == currency
                and pl.get("interval") == interval
            ):
                return pl
        return stripe.Plan.create(
            product=product_id,
            amount=unit_amount,
            currency=currency,
            interval=interval,
        )

    def _upsert_plan(
        self,
        *,
        name: str,
        description: str,
        default: bool,
        available: bool,
        requires_payment: bool,
        requires_invoice: bool,
        auto_renew: bool,
        daily_time_minutes,
        daily_data_mb,
        stripe_product_id: str,
    ) -> Plan:
        plan, _ = Plan.objects.update_or_create(
            name=name,
            defaults={
                "description": description,
                "default": default,
                "available": available,
                "requires_payment": requires_payment,
                "requires_invoice": requires_invoice,
                "auto_renew": auto_renew,
                "daily_time_minutes": daily_time_minutes,
                "daily_data_mb": daily_data_mb,
                "stripe_product_id": stripe_product_id,
            },
        )
        if default:
            Plan.objects.exclude(pk=plan.pk).filter(default=True).update(default=False)
        return plan

    def _upsert_pricing(
        self,
        *,
        plan: Plan,
        amount: int,
        currency: str,
        interval: str,
        trial_period_days: int,
        stripe_price_id: str,
    ) -> PlanPricing:
        # amount saved in Decimal dollars in DB
        pricing, _ = PlanPricing.objects.update_or_create(
            plan=plan,
            currency=currency,
            interval=interval,
            amount=amount,
            defaults={
                "active": True,
                "trial_period_days": trial_period_days,
                "stripe_price_id": stripe_price_id,
            },
        )
        return pricing
