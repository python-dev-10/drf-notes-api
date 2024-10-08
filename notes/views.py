from rest_framework import viewsets, filters, status, exceptions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response

from .models import Category, Tag, Note
from .serializers import CategorySerializer, TagSerializer, NoteSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['name']
    search_fields = ['name']

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['name']
    search_fields = ['name']

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_favorite', 'category__name', 'tags__name']
    search_fields = ['title', 'content']

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'is_favorite']
    ordering = ['created_at']

    def get_queryset(self):
        queryset = Note.objects.filter(user=self.request.user)
        is_favorite = self.request.query_params.get('is_favorite', None)
        if is_favorite:
            if is_favorite.lower() == 'true':
                queryset = queryset.filter(is_favorite=True)
            elif is_favorite.lower() == 'false':
                queryset = queryset.filter(is_favorite=False)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        note = self.get_object()
        note.is_favorite = not note.is_favorite
        note.save()
        return Response({'status': 'favorite status updated', 'is_favorite': note.is_favorite})

    def get_object(self):
        queryset = self.get_queryset()
        lookup_value = self.kwargs.get('pk')

        # Tenta buscar por ID primeiro
        if lookup_value.isdigit():
            return queryset.get(pk=lookup_value)

        # Se não for um dígito, tenta buscar pelo slug
        try:
            return queryset.get(slug=lookup_value)
        except Note.DoesNotExist:
            raise exceptions.NotFound("Note not found.")


class NoteHistoryViewSet(viewsets.ViewSet):

    def list(self, request, pk=None):
        try:
            note = Note.objects.get(pk=pk, user=request.user)
            history = note.history.all()

            history_data = []
            for record in history:
                history_data.append({
                    'history_id': record.history_id,
                    'title': record.title,
                    'content': record.content,
                    'created_at': record.created_at,
                    'updated_at': record.updated_at,
                    'is_favorite': record.is_favorite,
                    'history_date': record.history_date,
                    'history_change_reason': record.history_change_reason,
                    'history_type': record.history_type,
                    'history_user_id': record.history_user_id,
                })

            return Response(history_data, status=status.HTTP_200_OK)
        except Note.DoesNotExist:
            return Response({"detail": "Nota não encontrada."}, status=status.HTTP_404_NOT_FOUND)
