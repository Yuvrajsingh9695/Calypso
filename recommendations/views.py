from django.shortcuts import render

from .services.recommendation import recommend, movies


def recommendation_home(request):

    selected_movie = None
    recommendations = []

    # Get movie titles ONLY from ML dataset
    movie_titles = movies["title"].dropna().drop_duplicates().sort_values().tolist()

    if request.method == "POST":

        selected_movie = request.POST.get("movie", "").strip()

        if selected_movie:

            recommendations = recommend(selected_movie, n=10)

    context = {
        "movie_titles": movie_titles,
        "selected_movie": selected_movie,
        "recommendations": recommendations,
    }

    return render(request, "recommendations/recommendation.html", context)
