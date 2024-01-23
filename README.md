# My Inventory
#### Description: A web page to save your favourite music and series/movies

For this project I have used Python, HTML and CSS.

Some important packages you will probably have to install:

For music 'musicbrainz':
`pip install musicbrainzngs`

For movies: 'imdb':
`pip install IMDbPY`

To run the project use in the command line `flask run`

To see the database you can use sqlite3 and the `.open FILENAME`

To be able to have a session in my website I used the resources given in the problem set of week 09, in addition to taking it a little bit as a model to develop
my website.

A general problem I encountered was to put back buttons, I was thinking about putting a back button whe you are seasrching for something, wether is a song or a
movie. But because I'm using forms it's not really possible, and more because I'm using the POST method. So because I'm not saving any cache information I would
say it is impossible to go back as I wanted, so if you want to get some other information you have to do the whole search again, unless you use the back button
of the browser itself and then relaod the page.

## Music ##
You have a main page for music where you can see the songs you have already saved. Then you have a button that allows you to find new music and add it to your
inventory. In this search page you have two text boxes, one where you can put the artist name and another one to put the title whether it is an album or a
song. The search will depend on which field you fill in: If you put the artist it will of course give you the artist, if you only fill in the titlethen,
**IMPORTANT REMARK**, it will search for the name of the album, not the song. If you put both, artist and title then by default it will look for the aritstalbum,
if it doesn't find any match then it will look for the song itself.

Once you have found the song you wanted you can add it to your inventory clicking 'add', if you already had the song saved you will see that it has a different
button saying 'added'.

#### Problems faced:
Working with this database has been a challenge, because the tables were a little confusing for me. It has this table called 'release-groups' which is to get
the albums/EP/singles/etc., that one was fine, but then you get the 'releases' table, which I assumed would be the songs itself, but no, it's more like the CDs,
what you can find physically in a store. If you search by it, you will get numerous titles with the same name, what changes is the year of release and the
country, which I would have loved skipping that step, but to find the songs you need it.

The next table is 'recordings', which I think are the songs, I'm not even 100% sure if it is like that, but at this point I used that as songs. Once you have
gotten to this point, you should be able to add the song to your inventory, the problem I had here is that a recording can be in multiple releases. There is
no way or easy way to get then the album to which that song is from, so what I do is simply take the first release that appears in its list and put it as the
album, but sometimes the name can be weird and in some way you could say it doesn't look as a correct title, because is from something pretty different like a
concert (if you were saving the studio recording) or things like that, the same happens with the cover.

Another thing that also happened, is that I had to stick using the search function in the database, because if I used get or browse it would give me some
slightly different information from the search function, in the sense of for example the artist missing in that information, and I basically need the same
information all the time because I reuse some templates. So that was annoying but easy to fix.

Basically it took time to get used to this database, and there are some stuff I'm not totally happy with, but it works.

## Movies ##
Movies is similar to what I did with music. You have the main page to see your saved movies and from there you can add more titles, you can search by title of
the movie, actor or director. If you look directly for the title you can already add it to your inventory, if you are looking for actor/director, first you
have to choose the person you want to look for. If you chose actor then it will show the movies where they have appeared, if you chose director it will show
you movies that they have directed. Notice, that both, actor and director work in the same way to be searched, in the sense of it's exactly the same function,
that means that if you put that you're looking for a director but instead if you put an actor name it will still show you the person as a director, but unless
they have actually directed something, it won't show you any result.

Notice too that in the main page you have a button called 'details', here you can get some information about the movies you have save, like the plot, stars,
and more.

#### Problems faced:
This database was even worse than the one for the music. It doesn't give you a lot of freedom to get the information. YOu can get useful information by using
the function search but not a lot, I would have liked being able to have some more, the way I found to do it is using get with the ID, but I realized it takes
a lot of time to get the data, so at the end I couldn't really use it unless it was only for one entry (and still, it takes a lot of time, so imagine being 20
for example).

I wanted to get the filmography of an actor, and it's easy to do it, the problem is again the information, it doesn't give you as much as if you were using the
normal search. For my program I'm putting the covers of the titles, but when you get the information of the titles in the filmography, you don't get the covers,
and the kind is always movie even if it is a tv series or anything else plus sometimes the years are wrong, so that's a big problem. The solution I thought
about is use the search function in each title to get the information I wanted or the update one, but again it takes too much, so I had to discard that solution
and just put less information.

## Index ##
For the index I was thinking about getting the global top 20 of movies and artists/songs and show them, but I was looking for ways to do that and couldn't find
anything that I liked or could actually work. I know there is a function in IMDB to get the top 250 movies, but at the moment is not working, some users,
including myself, have already reported the problem so they can fix it, but at the moment I can use that.

At the end what I though I could do is instead put your top artists and instead of movies, because it doesn't make sense, put you top genres in movies. To be
able to do this, I can just use my own database, the tables will have some other columns to be able to save the information I need to achieve this.

At first I was thinking about showing the top artist in a table where you could also be able to see the picture of the artist, but that hasn't been possible,
it would have been useful if musicbrainz had something to get their pictures, but it doesn't so I thought it was going to be too much work to get their pictures.

## Database ##
I have my own database called inventory.db, feel free to use sqlite3 in the terminal to open it and see its contents. As an overview, it has 7 tables:

**users:** Information for the user's sessions, saving their username and password, plus an ID.

**music:** Save useful information about your saved songs.

**movies:** Save useful information about your saved movies.

**genres:** To save all genres, each one will have a unique ID and its name.

**movie_genres:** To save the genres of each movie.

**artists:** To save all artists, each one will have a unique ID and their name.

**song_artists:** To save the artists of each song.
