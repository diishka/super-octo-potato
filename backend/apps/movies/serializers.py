from rest_framework import serializers

from .models import Genre, LinkVote, Movie, MovieLink, UserMovie


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name", "slug")


class MovieSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    community_rating = serializers.SerializerMethodField()
    watched_by_count = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = (
            "id",
            "tmdb_id",
            "media_type",
            "title",
            "original_title",
            "description",
            "release_year",
            "poster_url",
            "backdrop_url",
            "tmdb_vote_average",
            "genres",
            "community_rating",
            "watched_by_count",
        )

    def get_community_rating(self, obj: Movie) -> float | None:
        value = getattr(obj, "community_rating", None)
        if value is None:
            return None
        return round(float(value), 1)

    def get_watched_by_count(self, obj: Movie) -> int:
        value = getattr(obj, "watched_by_count", None)
        if value is None:
            return 0
        return int(value)


class UserMovieSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)

    class Meta:
        model = UserMovie
        fields = (
            "id",
            "movie",
            "status",
            "rating",
            "review",
            "recommended_to_followers",
            "watched_at",
            "created_at",
            "updated_at",
        )


class UserMovieWriteSerializer(serializers.Serializer):
    movie_id = serializers.PrimaryKeyRelatedField(queryset=Movie.objects.all(), source="movie")
    status = serializers.ChoiceField(choices=UserMovie.Status.choices)
    rating = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    review = serializers.CharField(required=False, allow_blank=True)
    recommended_to_followers = serializers.BooleanField(required=False, default=False)
    watched_at = serializers.DateField(required=False, allow_null=True)

    def create(self, validated_data):
        user = self.context["request"].user
        movie = validated_data.pop("movie")
        defaults = {
            "status": validated_data["status"],
            "rating": validated_data.get("rating"),
            "review": validated_data.get("review", ""),
            "recommended_to_followers": validated_data.get("recommended_to_followers", False),
            "watched_at": validated_data.get("watched_at"),
        }
        entry, created = UserMovie.objects.update_or_create(
            user=user,
            movie=movie,
            defaults=defaults,
        )
        entry._was_created = created
        return entry


class MovieLinkSerializer(serializers.ModelSerializer):
    added_by = serializers.CharField(source="added_by.username", read_only=True)
    my_vote = serializers.SerializerMethodField()

    class Meta:
        model = MovieLink
        fields = ("id", "source_name", "url", "added_by", "score", "my_vote", "created_at")

    def get_my_vote(self, obj: MovieLink) -> int | None:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        vote = obj.votes.filter(user=request.user).values_list("value", flat=True).first()
        return vote


class MovieLinkWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieLink
        fields = ("source_name", "url")


class LinkVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkVote
        fields = ("value",)


class UserMovieUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMovie
        fields = ("status", "rating", "review", "recommended_to_followers", "watched_at")


class MovieDetailSerializer(MovieSerializer):
    my_entry = serializers.SerializerMethodField()
    links = serializers.SerializerMethodField()

    class Meta(MovieSerializer.Meta):
        fields = MovieSerializer.Meta.fields + ("my_entry", "links")

    def get_my_entry(self, obj: Movie):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        entry = obj.user_entries.filter(user=request.user).select_related("movie").first()
        if not entry:
            return None
        return UserMovieSerializer(entry, context=self.context).data

    def get_links(self, obj: Movie):
        links = obj.streaming_links.select_related("added_by").all()
        return MovieLinkSerializer(links, many=True, context=self.context).data
