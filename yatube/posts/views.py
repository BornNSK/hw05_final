from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CommentForm, PostForm
from .models import Group, Post, User, Comment, Follow
from core.utils import posts_paginator
from django.views.decorators.cache import cache_page


NUMBER_OF_POSTS = 10
KACHE_TIMER = 20


@cache_page(KACHE_TIMER, key_prefix='index_page')
def index(request):
    """Главная страница"""
    template = "posts/index.html"
    title = "Последние обновления на сайте"
    post_list = Post.objects.all()
    page_obj = posts_paginator(request, post_list, NUMBER_OF_POSTS)
    context = {
        'posts': post_list,
        'page_obj': page_obj,
        'title': title,
    }
    return render(request, template, context)


def group_posts(request, slug):
    """Страница группы"""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    title = f"Записи сообщества {group.title}"
    post_list = group.grouped_posts.all()
    page_obj = posts_paginator(request, post_list, NUMBER_OF_POSTS)

    context = {
        'title': title,
        'text': slug,
        'group': group,
        'posts': post_list,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    """Профаил пользователя"""
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.authored_posts.all()
    page_obj = posts_paginator(request, posts, NUMBER_OF_POSTS)
    following = (request.user.is_authenticated
                 and Follow.objects.filter(user=request.user,
                                           author=author,
                                           ).exists()
                 )
    context = {
        'posts': posts,
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    """Детали поста"""
    template = 'posts/post_detail.html'
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    author = post.author
    comments = Comment.objects.filter(post=post)
    posts_num = Post.objects.filter(author=author).count()
    context = {
        'post_num': posts_num,
        'post': post,
        'form': form,
        'author': author,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Создание поста."""
    template = 'posts/create_post.html'
    user = get_user(request)
    if request.method == 'POST':
        form = PostForm(request.POST or None,
                        files=request.FILES or None
                        )
        if form.is_valid():
            frm = form.save(commit=False)
            frm.author = user
            frm.save()
            return redirect(f'/profile/{user.username}/')
    form = PostForm()
    context = {
        'form': form,
        'is_edit': False,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    """Редактирование поста."""
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post
                    )
    if request.method == 'POST':
        if form.is_valid:
            form.save()
            return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    """Добавить комментарии"""
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Страница подписок"""
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = posts_paginator(request, posts, NUMBER_OF_POSTS)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на пользователя"""
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        Follow.objects.get_or_create(
            user=user,
            author=author
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Отписаться от пользователя"""
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=user,
        author=author,
    ).delete()
    return redirect('posts:profile', username)
