import datetime

import imdb
import musicbrainzngs as mbz

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required

# Configure application
app = Flask(__name__)

# Set user agent
mbz.set_useragent("TheRecordIndustry.io", "0.1")

# Creating an instance of the IMDB
ia = imdb.IMDb()

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///inventory.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


""" Index """


@app.route("/")
@login_required
def index():
    # Favourite movie genres
    genres = db.execute(
        "SELECT name, COUNT(movie_id) AS count FROM genres JOIN movie_genres ON id = genre_id WHERE movie_id IN "
        + "(SELECT imdb_id FROM movies WHERE user_id = ?) GROUP BY genre_id ORDER BY count DESC",
        session["user_id"],
    )

    # Favourite artists
    artists = db.execute(
        "SELECT name, COUNT(song_id) AS count FROM artists JOIN song_artists ON id = artist_id WHERE song_id IN "
        + "(SELECT mbz_id FROM music WHERE user_id = ?) GROUP BY artist_id ORDER BY count DESC",
        session["user_id"],
    )

    return render_template("index.html", genres=genres, artists=artists)


# User stuff


"""Log user in"""


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", invalid="Fill in username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", invalid="Fill in password")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["password"], request.form.get("password")
        ):
            return render_template("login.html", invalid="Wrong username or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


"""Register user"""


@app.route("/register", methods=["GET", "POST"])
def register():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("register.html", invalid="Fill in username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("register.html", invalid="Fill in password")

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return render_template("register.html", invalid="Fill in confirmation")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username doesn't exist in the database
        if len(rows) != 0:
            return render_template("register.html", invalid="Username already exists")

        # Ensure confimration is the same as password
        if request.form.get("password") != request.form.get("confirmation"):
            return render_template("register.html", invalid="Passowrds don't match")

        # Hash the user's password
        password = generate_password_hash(request.form.get("password"))

        # Query database for id just created
        id = db.execute(
            "INSERT INTO users (username, password) VALUES(?, ?)",
            request.form.get("username"),
            password,
        )

        # Save id as the current one
        session["user_id"] = int(id)

        # Redirect user to login page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


"""Log user out"""


@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


# Music stuff


""" Main page for music where you can see your saved songs """


@app.route("/music", methods=["GET", "POST"])
@login_required
def music():
    music = db.execute("SELECT * FROM music WHERE user_id = ?", session["user_id"])
    for i in range(len(music)):
        music[i]["my_id"] = "{0:0=3d}".format(i + 1)

    return render_template("/music/music.html", music=music)


""" Delete songs from the main page in the table """


@app.route("/deleteMusic", methods=["GET", "POST"])
@login_required
def deleteMusic():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        button = request.form.get("button")

        if button:
            db.execute(
                "DELETE FROM music WHERE user_id = ? AND mbz_id = ?",
                session["user_id"],
                button,
            )
            return redirect("/music")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/music/music.html")


""" Main page to search for music """


@app.route("/musicSearch", methods=["GET", "POST"])
@login_required
def musicSearch():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        artist = request.form.get("artist")
        title = request.form.get("title")

        # Check there is at least one field
        if not artist and not title:
            return render_template("/music/musicSearch.html", invalid=True)

        if artist and not title:
            return onlyArtist(artist)
        if artist and title:
            return artistTitle(artist, title)
        if title and not artist:
            return onlyTitle(title)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/music/musicSearch.html")


""" If only artsit is filled in """


def onlyArtist(artist):
    artists = mbz.search_artists(query=artist)["artist-list"]

    #  Format genres
    for artist in artists:
        genres = ""
        try:
            for genre in artist["tag-list"]:
                genres += str(genre["name"]) + " / "
            artist["genres"] = genres[:-2]
        except:
            genres = ""

    return render_template("/music/musicSearch.html", artists=artists, search="Artists")


""" If artist and title are filled in """


def artistTitle(artist, title):
    titles = mbz.search_release_groups(
        query=title, status="official", artist=artist, strict=True
    )["release-group-list"]

    # If a release-group wasnt found the look into the recordings
    if len(titles) == 0:
        recordings = mbz.search_recordings(
            query=title, artist=artist, status="official", strict=True
        )["recording-list"]
        music = db.execute("SELECT * FROM music WHERE user_id = ?", session["user_id"])

        for i in range(len(recordings)):
            recordings[i]["my_id"] = "{0:0=3d}".format(i + 1)
            recordings[i]["add"] = True
            for song in music:
                if song["mbz_id"] == recordings[i]["id"]:
                    recordings[i]["add"] = False

        return render_template(
            "/music/musicSearch.html", recordings=recordings, search="Recordings"
        )

    for i in range(len(titles)):
        titles[i]["my_id"] = "{0:0=3d}".format(i + 1)

    return render_template("/music/musicSearch.html", titles=titles, search="Titles")


""" If only title filled in """


def onlyTitle(title):
    titles = mbz.search_release_groups(query=title, status="official")[
        "release-group-list"
    ]
    for i in range(len(titles)):
        titles[i]["my_id"] = "{0:0=3d}".format(i + 1)

    return render_template("/music/musicSearch.html", titles=titles, search="Titles")


""" Search for release groups via artist and title """


@app.route("/musicSearch2", methods=["GET", "POST"])
@login_required
def searchTitlesByArtist():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        button = request.form.get("button")
        if button:
            titles = mbz.search_release_groups(
                arid=button, status="official", strict=True, limit=100
            )["release-group-list"]
            for i in range(len(titles)):
                titles[i]["my_id"] = "{0:0=3d}".format(i + 1)
            if len(titles) == 100:
                return render_template(
                    "/music/musicSearch.html",
                    id=button,
                    titles=titles,
                    more=True,
                    search="Titles",
                )

        return render_template(
            "/music/musicSearch.html", titles=titles, search="Titles"
        )

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/music/musicSearch.html")


""" Get more release groups """


@app.route("/more", methods=["GET", "POST"])
@login_required
def moreTitles():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        more = request.form.get("more")

        if more:
            titles = mbz.search_release_groups(
                arid=more, status="official", strict=True, limit=100, offset=100
            )["release-group-list"]
            i = 100
            for title in titles:
                title["my_id"] = "{0:0=3d}".format(i + 1)
                i += 1

            return render_template(
                "/music/musicSearch.html", titles=titles, search="Titles"
            )

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/music/musicSearch.html")


""" Search for releases given a release group id"""


@app.route("/releases", methods=["GET", "POST"])
@login_required
def releasesSearch():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        button = request.form.get("button")

        if button:
            releases = mbz.search_releases(
                rgid=button, status="official", strict=True, limit=100
            )["release-list"]
            for i in range(len(releases)):
                releases[i]["my_id"] = "{0:0=3d}".format(i + 1)

            return render_template(
                "/music/musicSearch.html", releases=releases, search="Releases"
            )

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/music/musicSearch.html")


""" Search for recordings given the release id"""


@app.route("/recordings", methods=["GET", "POST"])
@login_required
def recordingsSearch():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        button = request.form.get("button")

        if button:
            recordings = mbz.search_recordings(
                reid=button, status="official", strict=True, limit=100
            )["recording-list"]
            music = db.execute(
                "SELECT * FROM music WHERE user_id = ?", session["user_id"]
            )

            for i in range(len(recordings)):
                recordings[i]["my_id"] = "{0:0=3d}".format(i + 1)
                recordings[i]["add"] = True
                for song in music:
                    if song["mbz_id"] == recordings[i]["id"]:
                        recordings[i]["add"] = False

            return render_template(
                "/music/musicSearch.html", recordings=recordings, search="Recordings"
            )

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/music/musicSearch.html")


""" Add new music or delete songs if you alredady have them in your saved ones """


@app.route("/addSong", methods=["GET", "POST"])
@login_required
def addMusic():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        add = request.form.get("add")

        if add:
            recording = mbz.search_recordings(rid=add)["recording-list"]

            # If for some reason the recording doesn't exist
            if len(recording) == 0:
                return redirect("/music")

            recording = recording[0]

            # Get cover
            cover = ""
            group = mbz.search_release_groups(reid=recording["release-list"][0]["id"])[
                "release-group-list"
            ]
            try:
                cover = mbz.get_release_group_image_list(group[0]["id"])
                cover = cover["images"][0]["thumbnails"]["small"]
            except:
                cover = ""

            # Insert song in database
            db.execute(
                "INSERT INTO music (user_id, mbz_id, cover, title, artist, album) VALUES(?, ?, ?, ?, ?, ?)",
                session["user_id"],
                recording["id"],
                cover,
                recording["title"],
                recording["artist-credit-phrase"],
                group[0]["title"],
            )

            # Put artists in table 'artists' if there are new ones
            search1 = db.execute("SELECT * FROM artists")
            artists = []
            for a in search1:
                artists.append(a["id"])

            for artist in recording["artist-credit"]:
                try:
                    if artist["artist"]["id"] not in artists:
                        db.execute(
                            "INSERT INTO artists (id, name) VALUES(?, ?)",
                            artist["artist"]["id"],
                            artist["artist"]["name"],
                        )
                except:
                    pass

            # Match artists with songs in song_artists if it wasn't already matched
            search2 = db.execute("SELECT * FROM song_artists")
            songs = []
            for p in search2:
                songs.append(p["song_id"])

            if recording["id"] not in songs:
                for artist in recording["artist-credit"]:
                    try:
                        db.execute(
                            "INSERT INTO song_artists (song_id, artist_id) VALUES(?, ?)",
                            recording["id"],
                            artist["artist"]["id"],
                        )
                    except:
                        pass

            return redirect("/music")

        # Basically if there was any error (mostly because someone changed the values in the inspect of the browser)
        return render_template("failure.html", failure="Something went wrong")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/music/musicSearch.html")


# Movie stuff


MOVIE_OPTIONS = ["Title", "Actor", "Director"]


""" Main page for movies where you can see your saved movies/series """


@app.route("/movies", methods=["GET", "POST"])
@login_required
def movies():
    movies = db.execute("SELECT * FROM movies WHERE user_id = ?", session["user_id"])
    for i in range(len(movies)):
        movies[i]["my_id"] = "{0:0=3d}".format(i + 1)

    return render_template("/movies/movies.html", movies=movies)


""" Delete movies from the main page in the table """


@app.route("/deleteMovie", methods=["GET", "POST"])
@login_required
def deleteMovies():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        button = request.form.get("button")

        if button:
            db.execute(
                "DELETE FROM movies WHERE user_id = ? AND imdb_id = ?",
                session["user_id"],
                button,
            )
            db.execute(
                "DELETE FROM movies WHERE user_id = ? AND imdb_id = ?",
                session["user_id"],
                button,
            )
            return redirect("/movies")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/movies/movies.html")


""" Main page to search for movies """


@app.route("/movieSearch", methods=["GET", "POST"])
@login_required
def movieSearch():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        query = request.form.get("query")
        option = request.form.get("option")

        if not query or not option:
            return render_template(
                "/movies/movieSearch.html",
                options=MOVIE_OPTIONS,
                invalid="Invalid input",
            )

        if option in MOVIE_OPTIONS:
            if option == "Title":
                return movieTitlesSearch(query)
            if option == "Actor":
                return actorsSearch(query)
            if option == "Director":
                return directorsSearch(query)

        return render_template("/movies/movieSearch.html", options=MOVIE_OPTIONS)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/movies/movieSearch.html", options=MOVIE_OPTIONS)


""" Search titles """


def movieTitlesSearch(title):
    movies = ia.search_movie(title)
    titles = db.execute("SELECT * FROM movies WHERE user_id = ?", session["user_id"])

    for i in range(len(movies)):
        movies[i]["my_id"] = "{0:0=3d}".format(i + 1)
        movies[i]["add"] = True
        for title in titles:
            if int(title["imdb_id"]) == int(movies[i].movieID):
                movies[i]["add"] = False

    return render_template(
        "/movies/movieSearch.html",
        options=MOVIE_OPTIONS,
        movies=movies,
        search="Titles",
    )


""" Search actors """


def actorsSearch(actor):
    people = ia.search_person(actor)
    for i in range(len(people)):
        people[i]["my_id"] = "{0:0=3d}".format(i + 1)

    return render_template(
        "/movies/movieSearch.html",
        options=MOVIE_OPTIONS,
        people=people,
        search="Actors",
    )


""" Search directors """


def directorsSearch(director):
    people = ia.search_person(director)
    for i in range(len(people)):
        people[i]["my_id"] = "{0:0=3d}".format(i + 1)

    return render_template(
        "/movies/movieSearch.html",
        options=MOVIE_OPTIONS,
        people=people,
        search="Directors",
    )


""" Add movie to inventory """


@app.route("/addMovie", methods=["GET", "POST"])
@login_required
def addMovie():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        add = request.form.get("add")
        info = ""

        if add:
            movie = ia.get_movie(add)

            # If for some reason the movie doesn't exist
            if not movie:
                return redirect("/")

            # To get the length of a movie
            if (
                movie["kind"] == "movie"
                or movie["kind"] == "tv movie"
                or movie["kind"] == "short"
                or movie["kind"] == "video movie"
            ):
                try:
                    ia.update(movie, info="runtimes")
                    runtime = int(movie.get("runtimes")[0])
                    info = "Duration: " + str(datetime.timedelta(minutes=runtime))
                except:
                    info = ""

            # To get the number of seasons a series has
            elif movie["kind"] == "tv series" or movie["kind"] == "tv mini series":
                try:
                    ia.update(movie, info="number of seasons")
                    seasons = movie.get("number of seasons")
                    info = "Seasons: " + str(seasons)
                except:
                    info = ""

            # If the movie doesn't have a cover
            if not movie.get("cover url"):
                movie["cover url"] = ""

            db.execute(
                "INSERT INTO movies (user_id, imdb_id, cover, title, type, info) VALUES(?, ?, ?, ?, ?, ?)",
                session["user_id"],
                movie.movieID,
                movie["cover url"],
                movie["title"],
                movie["kind"],
                info,
            )

            # Put genres in table 'genres' if there are new ones
            search1 = db.execute("SELECT * FROM genres")
            genres = []
            for g in search1:
                genres.append(g["name"])

            for genre in movie["genres"]:
                if genre not in genres:
                    db.execute("INSERT INTO genres (name) VALUES(?)", genre)

            # Match genres with movie in movie_genres if it wasn't already matched
            search2 = db.execute("SELECT * FROM movie_genres")
            movies = []
            for m in search2:
                movies.append(m["movie_id"])

            if movie.movieID not in movies:
                for genre in movie["genres"]:
                    search3 = db.execute("SELECT id FROM genres WHERE name = ?", genre)
                    id = search3[0]["id"]
                    db.execute(
                        "INSERT INTO movie_genres (movie_id, genre_id) VALUES(?, ?)",
                        movie.movieID,
                        id,
                    )

            return redirect("/movies")

        # Basically if there was any error (mostly because someone changed the values in the inspect of the browser)
        return render_template("failure.html", failure="Something went wrong")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/movies/movieSearch.html", options=MOVIE_OPTIONS)


""" Give movies where an actor appears """


@app.route("/movieSearchByActor", methods=["GET", "POST"])
@login_required
def movieSearchByActor():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        button = request.form.get("button")
        movies = []

        if button:
            person = ia.get_person_filmography(button)
            movie = db.execute(
                "SELECT * FROM movies WHERE user_id = ?", session["user_id"]
            )

            if "actress" in person["data"]["filmography"]:
                movies = person["data"]["filmography"]["actress"]
            elif "actor" in person["data"]["filmography"]:
                movies = person["data"]["filmography"]["actor"]
            else:
                return render_template(
                    "/movies/movieSearch.html",
                    options=MOVIE_OPTIONS,
                    invalid="Not an actor",
                )

            for i in range(len(movies)):
                movies[i]["my_id"] = "{0:0=3d}".format(i + 1)
                movies[i]["add"] = True
                for title in movie:
                    if movies[i].movieID == title["imdb_id"]:
                        movies[i]["add"] = False

            return render_template(
                "/movies/movieSearch.html",
                options=MOVIE_OPTIONS,
                movies=movies,
                search="Titles",
            )

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/movies/movieSearch.html", options=MOVIE_OPTIONS)


""" Give movies from a specific director """


@app.route("/movieSearchByDirector", methods=["GET", "POST"])
@login_required
def movieSearchByDirector():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        button = request.form.get("button")
        movies = []

        if button:
            person = ia.get_person_filmography(button)
            movie = db.execute(
                "SELECT * FROM movies WHERE user_id = ?", session["user_id"]
            )

            try:
                movies = person["data"]["filmography"]["director"]
            except:
                return render_template(
                    "/movies/movieSearch.html",
                    options=MOVIE_OPTIONS,
                    invalid="Not a director",
                )

            for i in range(len(movies)):
                movies[i]["my_id"] = "{0:0=3d}".format(i + 1)
                movies[i]["add"] = True
                for title in movie:
                    if movies[i].movieID == title["imdb_id"]:
                        movies[i]["add"] = False

            return render_template(
                "/movies/movieSearch.html",
                options=MOVIE_OPTIONS,
                movies=movies,
                search="Titles",
            )

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/movies/movieSearch.html", options=MOVIE_OPTIONS)


""" Get more details about a movie """


@app.route("/movieDetails", methods=["GET", "POST"])
@login_required
def movieDetails():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        button = request.form.get("button")

        if button:
            movie = ia.get_movie(button)

            # To get the info we already had in the database
            info = db.execute(
                "SELECT info FROM movies WHERE user_id = ? AND imdb_id = ?",
                session["user_id"],
                button,
            )
            movie["info"] = info[0]["info"]

            # Format genres better
            genres = ""
            for genre in movie["genres"]:
                genres += str(genre) + ", "
            movie["genres"] = genres[:-2]

            # Format director better
            if (
                movie["kind"] == "movie"
                or movie["kind"] == "tv movie"
                or movie["kind"] == "short"
                or movie["kind"] == "video game"
                or movie["kind"] == "video movie"
            ):
                directors = ""
                for director in movie["director"]:
                    directors += str(director["name"]) + ", "
                movie["director"] = directors[:-2]

            # Format creators better
            if movie["kind"] == "tv series" or movie["kind"] == "tv mini series":
                creators = ""
                ids = []
                for creator in movie["writer"]:
                    if creator.personID not in ids:
                        creators += str(creator["name"]) + ", "
                        ids.append(creator.personID)
                movie["creator"] = creators[:-2]

            # Format cast better
            cast = ""
            for i in range(3):
                try:
                    cast += str(movie["cast"][i]["name"]) + ", "
                except:
                    break
            movie["cast"] = cast[:-2]

            return render_template("/movies/details.html", movie=movie)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return redirect("/movies")
