def wallet_context(request):
    if request.user.is_authenticated:
        try:
            return {'wallet': request.user.wallet}
        except:
            return {'wallet': None}
    return {'wallet': None}