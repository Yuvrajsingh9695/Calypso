
from django.db.models import Q

MIN_TV_VOTES = 1000
JAPANESE_ANIMATION_MIN_VOTES = 40

BLOCKED_TV_TERMS = [
    "hentai",
    "ecchi",
    "porn",
    "pornographic",
    "sexually explicit",
    "explicit sexual",
    "adult animation",
    "adult anime",
    "erotic animation",
    "erotic anime",
    "erotic",
    "xxx",
    "sexual content",
    "sexual intercourse",
    "sex slave",
    "sex slavery",
    "incest",
    "nudity",
    "sexual violence",
]


def clean_tv_queryset(queryset):
    """Apply shared filters to TV-show querysets."""

    queryset = queryset.filter(
        vote_count__gte=MIN_TV_VOTES,
        is_adult=False,
    )

    queryset = queryset.exclude(
        Q(original_language="ja")
        & Q(genres__icontains="animation")
        & Q(vote_count__lt=JAPANESE_ANIMATION_MIN_VOTES)
    )

    for term in BLOCKED_TV_TERMS:
        queryset = queryset.exclude(
            Q(name__icontains=term)
            | Q(original_name__icontains=term)
            | Q(overview__icontains=term)
            | Q(genres__icontains=term)
        )

    return queryset
