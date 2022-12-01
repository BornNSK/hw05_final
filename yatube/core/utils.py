from django.core.paginator import Paginator


def posts_paginator(request, post_list, number_posts):
    paginator = Paginator(post_list, number_posts)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
