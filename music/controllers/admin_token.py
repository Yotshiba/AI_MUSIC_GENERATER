"""
UC-03: Admin Token Management.

Business rules encoded here (from SRS Appendix D, §10.4):
- E1 guard: token balance cannot be set negative (§10.4.6).
- Cap: balance must not exceed 9999 to prevent integer overflow (§10.4.7).
- Audit trail: every admin adjustment creates a TokenRecord for the log.
"""

from django.shortcuts import get_object_or_404

from ..models import Profile, TokenRecord, User


class AdminTokenController:
    """Controls the admin token management use case (UC-03)."""

    MAX_TOKEN_BALANCE = 9999

    @staticmethod
    def get_user_profile(user_id):
        """Fetch a user and their profile for admin review."""
        user = get_object_or_404(User, pk=user_id)
        profile = get_object_or_404(Profile, user=user)
        return user, profile

    @staticmethod
    def set_token_balance(user_id, new_balance):
        """
        Overwrite a user's token balance.

        Raises ValueError for negative values or values exceeding the cap.
        Creates a TokenRecord to maintain an audit trail of the adjustment.
        """
        if new_balance < 0:
            raise ValueError("Ensure this value is greater than or equal to 0.")
        if new_balance > AdminTokenController.MAX_TOKEN_BALANCE:
            raise ValueError(
                f"Token balance cannot exceed {AdminTokenController.MAX_TOKEN_BALANCE}."
            )

        profile = get_object_or_404(Profile, user_id=user_id)
        delta = new_balance - profile.token_balance
        profile.token_balance = new_balance
        profile.save(update_fields=["token_balance"])

        if delta != 0:
            token_type = (
                TokenRecord.TokenType.EARNED if delta > 0 else TokenRecord.TokenType.SPENT
            )
            TokenRecord.objects.create(
                user_id=user_id, amount=abs(delta), type=token_type
            )

        return profile

    @staticmethod
    def list_users(**filters):
        """List users with optional filters; prefetches profile to avoid N+1 queries."""
        return User.objects.filter(**filters).select_related("profile")
