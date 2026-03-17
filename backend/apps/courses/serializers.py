"""
Serializers для курсов, модулей и уроков.
"""
from rest_framework import serializers
from .models import Category, Course, Module, Lesson


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор категорий"""
    courses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 
            'created_at', 'courses_count'
        ]
        read_only_fields = ['slug', 'created_at']
    
    def get_courses_count(self, obj) -> int:
        return obj.courses.filter(status='published').count()


class CategoryListSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для списка категорий"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class LessonListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка уроков"""
    content_type_display = serializers.CharField(
        source='get_content_type_display', 
        read_only=True
    )
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'content_type', 'content_type_display',
            'order_index', 'is_free_preview', 'duration_seconds'
        ]
        read_only_fields = ['order_index']


class LessonDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации об уроке"""
    content_type_display = serializers.CharField(
        source='get_content_type_display', 
        read_only=True
    )
    embed_url = serializers.SerializerMethodField()
    has_next = serializers.SerializerMethodField()
    has_previous = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'content_type', 'content_type_display',
            'kinescope_video_id', 'kinescope_embed_code',
            'text_content', 'order_index', 'is_free_preview',
            'duration_seconds', 'attachment',
            'embed_url', 'has_next', 'has_previous',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'order_index', 'created_at', 'updated_at', 'embed_url'
        ]
    
    def get_embed_url(self, obj) -> str:
        """Генерация безопасного embed URL"""
        request = self.context.get('request')
        return obj.get_embed_url(request)
    
    def get_has_next(self, obj) -> bool:
        return obj.get_next_lesson() is not None
    
    def get_has_previous(self, obj) -> bool:
        return obj.get_previous_lesson() is not None


class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления урока"""
    
    class Meta:
        model = Lesson
        fields = [
            'title', 'content_type', 'kinescope_video_id',
            'kinescope_embed_code', 'text_content',
            'order_index', 'is_free_preview', 'duration_seconds',
            'attachment'
        ]
    
    def validate_kinescope_video_id(self, value):
        """Проверка ID видео Kinescope"""
        if value and len(value) > 100:
            raise serializers.ValidationError(
                "Некорректный ID видео Kinescope"
            )
        return value


class ModuleSerializer(serializers.ModelSerializer):
    """Сериализатор модулей"""
    lessons_count = serializers.SerializerMethodField()
    lessons = LessonListSerializer(many=True, read_only=True)
    
    class Meta:
        model = Module
        fields = [
            'id', 'title', 'description', 'order_index',
            'lessons_count', 'lessons', 'created_at'
        ]
        read_only_fields = ['order_index', 'created_at']
    
    def get_lessons_count(self, obj) -> int:
        return obj.lessons.count()


class ModuleCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления модуля"""
    
    class Meta:
        model = Module
        fields = ['title', 'description', 'order_index']


class CourseListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка курсов"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    lessons_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'short_description',
            'cover_image', 'price', 'category', 'category_name',
            'author', 'author_name', 'status', 'status_display',
            'lessons_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
    
    def get_lessons_count(self, obj) -> int:
        return obj.get_lessons_count()


class CourseDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации о курсе"""
    category = CategorySerializer(read_only=True)
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    author_avatar = serializers.ImageField(source='author.avatar', read_only=True)
    modules = ModuleSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField()
    duration_seconds = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'cover_image', 'price', 'category', 'author', 'author_name',
            'author_avatar', 'status', 'status_display',
            'modules', 'lessons_count', 'duration_seconds',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
    
    def get_lessons_count(self, obj) -> int:
        return obj.get_lessons_count()
    
    def get_duration_seconds(self, obj) -> int:
        return obj.get_duration()


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления курса"""
    
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'short_description',
            'cover_image', 'price', 'category', 'status'
        ]
    
    def validate_price(self, value):
        """Проверка цены"""
        if value < 0:
            raise serializers.ValidationError("Цена не может быть отрицательной")
        return value


class CoursePublicSerializer(serializers.ModelSerializer):
    """Публичный сериализатор курса (для витрины)"""
    category = CategoryListSerializer(read_only=True)
    lessons_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'short_description', 'description',
            'cover_image', 'price', 'category',
            'lessons_count', 'created_at'
        ]
    
    def get_lessons_count(self, obj) -> int:
        return obj.get_lessons_count()
