from categories.models import Category

def get_nodes(request):
    cats = list(Category.objects.all())
    res = []
    all_cats = cats[:]
    childs = []
    for cat in cats:
        if cat.parent_id:
            childs.append(cat)
        else:
            res.append(cat)
    for cat in all_cats:
        cat.childrens = []
        for child in childs:
            if child.parent_id == cat.pk:
                cat.childrens.append(child)
    return res