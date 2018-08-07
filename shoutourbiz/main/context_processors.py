from django.utils import timezone

def uses_num(request):
    user = request.user
    uses_num = 0
    if user.is_authenticated():
        uses = user.buyeruses_set.all()
        if uses.exists():
            uses = uses[0]
            count_ends = uses.count_end
            if count_ends and count_ends > timezone.now():
                uses_num = uses.uses
    return {'num_uses': uses_num}



