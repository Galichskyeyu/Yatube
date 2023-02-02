from django.contrib import admin

from .models import Comment, Follow, Group, Post


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
        'slug',
        'description',)
    empty_value_display = '-пусто-'


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    list_display = ("text", "author", "created")
    search_fields = ("text", "author", "created")


class FollowAdmin(admin.ModelAdmin):
    list_display = ("user", "author")
    search_fields = ("user", "author")


admin.site.register(Group, GroupAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
