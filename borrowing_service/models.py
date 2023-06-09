from django.contrib.auth import get_user_model
from django.db import models

from django.core.exceptions import ValidationError
from book_service.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=False)
    expected_return_date = models.DateField(auto_now_add=False)
    actual_return_date = models.DateField(auto_now_add=False, blank=True, null=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="borrowings"
    )

    @staticmethod
    def validated_date(
        borrow_date, expected_return_date, actual_return_date, error_to_raise
    ):
        if borrow_date > expected_return_date:
            raise error_to_raise(
                f"Borrow date {borrow_date} should be less than Expected return date"
            )

        if actual_return_date and actual_return_date < borrow_date:
            raise error_to_raise(
                f"Borrow date {borrow_date} should be less than Actual return date"
            )

    def clean(self):
        self.validated_date(
            self.borrow_date,
            self.expected_return_date,
            self.actual_return_date,
            ValidationError,
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ["borrow_date"]

    def __str__(self):
        return f"{self.user} borrow {self.book} at {self.borrow_date}"
