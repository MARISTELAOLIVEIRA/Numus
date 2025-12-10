from .models import UserProfile


def user_profile(request):
    """Add user_profile to all templates, creating it if missing for authenticated users."""
    profile = None
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return {'user_profile': profile}
