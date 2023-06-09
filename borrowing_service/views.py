from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from borrowing_service.models import Borrowing
from borrowing_service.serializers import (
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingCreateSerializer,
    BorrowingReturnSerializer,
)
from rest_framework import serializers


class BorrowingPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Borrowing.objects.select_related("book")
    serializer_class = BorrowingSerializer
    pagination_class = BorrowingPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset
        if self.request.user.is_staff:
            user_id = self.request.query_params.get("user_id")

            if user_id:
                queryset = queryset.filter(user_id=int(user_id))

        else:
            queryset = Borrowing.objects.filter(user=self.request.user)

        is_active = self.request.query_params.get("is_active")

        if is_active:
            if is_active == "true":
                queryset = queryset.filter(actual_return_date__isnull=True)
            if is_active == "false":
                queryset = queryset.filter(actual_return_date__isnull=False)

        return queryset

    def get_serializer_class(self) -> type[serializers.Serializer]:
        if self.action == "list":
            return BorrowingListSerializer

        if self.action == "retrieve":
            return BorrowingDetailSerializer

        if self.action == "create":
            return BorrowingCreateSerializer

        if self.action == "return_book":
            return BorrowingReturnSerializer

        return BorrowingSerializer

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.request.user)

    @action(
        methods=["POST"],
        detail=True,
        url_path="return-book",
        permission_classes=[IsAuthenticated],
    )
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        book = borrowing.book
        serializer = self.get_serializer(borrowing, data=request.data)

        if borrowing.actual_return_date is not None:
            raise ValidationError("This book has been already returned")

        if serializer.is_valid():
            Borrowing.validated_date(
                borrowing.borrow_date,
                borrowing.expected_return_date,
                serializer.validated_data["actual_return_date"],
                ValidationError,
            )
            with transaction.atomic():
                serializer.save()
                book.inventory += 1
                book.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.STR,
                description="Filter by active borrowings",
                required=False,
            ),
            OpenApiParameter(
                "user_id",
                type=OpenApiTypes.INT,
                description="Filter by user id if user is_stuff",
                required=False,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
