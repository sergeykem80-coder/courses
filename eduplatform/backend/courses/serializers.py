"""
Serializers for the courses app.
"""
from rest_framework import serializers
from .models import Category, Course, Module, Lesson


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']
        read_only_fields = ['slug']


class CourseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for course listing."""
    category = CategorySerializer(read_only=True)
    total_lessons = serializers.SerializerMethodField()
    total_modules = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'short_description', 'cover_image',
            'price', 'category', 'status', 'total_lessons', 'total_modules',
            'created_at'
        ]
        read_only_fields = ['slug', 'created_at']
    
    def get_total_lessons(self, obj):
        return obj.get_total_lessons()
    
    def get_total_modules(self, obj):
        return obj.get_total_modules()


class CourseDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for course detail view with modules and lessons."""
    category = CategorySerializer(read_only=True)
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    modules = serializers.SerializerMethodField()
    total_lessons = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'cover_image', 'price', 'category', 'author', 'author_name',
            'status', 'modules', 'total_lessons', 'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
    
    def get_modules(self, obj):
        modules = obj.modules.prefetch_related('lessons').all()
        return ModuleSerializer(modules, many=True).data
    
    def get_total_lessons(self, obj):
        return obj.get_total_lessons()


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating courses (admin)."""
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'cover_image', 'price', 'category', 'status', 'author',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'author', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Author is set in view's perform_create
        return super().create(validated_data)


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer for Module model."""
    lessons_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = ['id', 'course', 'title', 'order_index', 'lessons_count']
        read_only_fields = ['id']
    
    def get_lessons_count(self, obj):
        return obj.lessons.count()


class LessonSerializer(serializers.ModelSerializer):
    """Serializer for Lesson model."""
    content_type_display = serializers.CharField(
        source='get_content_type_display', 
        read_only=True
    )
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'module', 'title', 'content_type', 'content_type_display',
            'kinescope_video_id', 'kinescope_embed_code', 'text_content',
            'order_index', 'is_free_preview', 'duration_seconds', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
