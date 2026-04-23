from django.db import models

from .user import User


class InsufficientTokensError(Exception):
    pass


class Profile(models.Model):
    """One-to-one profile for a User, holding token balance."""

    MAX_BALANCE = 9999

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    token_balance = models.IntegerField(default=0)

    def __str__(self):
        return f"Profile of {self.user.name}"

    # ── Information Expert: token domain logic lives here ─────────────────

    def can_afford(self, cost: int) -> bool:
        """Return True if the user has enough tokens to cover cost."""
        return self.token_balance >= cost

    def deduct(self, cost: int) -> None:
        """
        Deduct tokens and record the transaction.
        Raises InsufficientTokensError if balance is too low.
        """
        from .token_record import TokenRecord  # local import avoids circular dep

        if not self.can_afford(cost):
            raise InsufficientTokensError(
                "Insufficient credits. Please contact the Administrator."
            )
        self.token_balance -= cost
        self.save(update_fields=["token_balance"])
        TokenRecord.objects.create(
            user=self.user,
            amount=cost,
            type=TokenRecord.TokenType.SPENT,
        )

    def refund(self, cost: int) -> None:
        """Refund tokens and record the transaction (called on generation failure)."""
        from .token_record import TokenRecord

        self.token_balance = min(self.token_balance + cost, self.MAX_BALANCE)
        self.save(update_fields=["token_balance"])
        TokenRecord.objects.create(
            user=self.user,
            amount=cost,
            type=TokenRecord.TokenType.EARNED,
        )
