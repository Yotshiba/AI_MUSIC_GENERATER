from django.db import models

from .user import User


class TokenRecord(models.Model):
    """Records token transactions (earned or spent) for a User."""

    class TokenType(models.TextChoices):
        EARNED = 'Earned', 'Earned'
        SPENT = 'Spent', 'Spent'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='token_records')
    amount = models.IntegerField()
    type = models.CharField(max_length=10, choices=TokenType.choices)

    def __str__(self):
        return f"{self.type} {self.amount} tokens – {self.user.name}"
