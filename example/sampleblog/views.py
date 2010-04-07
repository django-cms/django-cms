from django.shortcuts import render_to_response
from sampleblog.models import BlogPost

def blog_post(request, post_id):
    return render_to_response('blog/post.html', {'post': BlogPost.objects.get(pk=post_id)})
