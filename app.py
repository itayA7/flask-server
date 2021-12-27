from flask import Flask,send_file
import requests
import flask.scaffold
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from flask_restful import Api,Resource,reqparse,marshal_with,fields,abort
from  flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

API_KEY="6073dee017e4bfeb41c29456aa4ccb06"
BASE_URL_IMAGES="https://image.tmdb.org/t/p/w500"
app = Flask(__name__)
api = Api(app)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///web.db'
db = SQLAlchemy(app)


def average(ratings_of_movie):
    score_sum=0
    counter=0
    for current_rating in ratings_of_movie:
        score_sum+=current_rating.score
        counter=counter+1
    average_score=score_sum/counter
    return average_score

#data base functions
def get_actor_name_by_actorId(actor_id):
    actor_by_actorId = Actor.query.filter_by(actorId=actor_id).first()
    if not actor_by_actorId:
        return None
    actor_name=actor_by_actorId.actorName
    return actor_name

def get_movie_id_by_movie_name(movie_name):
    movie_by_movie_name = Movies.query.filter_by(movieName=movie_name).first()
    if not movie_by_movie_name:
        return False
    movie_id = movie_by_movie_name.movieId
    return movie_id


#tmdb api functions
def insert_movie_by_movie_info(movie_info,language="en"):#main function for insert movies with all details (actors,trailer,poster)
    movie_tmdb_id = str(movie_info['id'])
    movie_title = movie_info['title']
    movie_tmdb_genre_id = movie_info['genre_ids'][0]
    movie_genre_id=check_genreId_by_genreAPI_id(movie_tmdb_genre_id)
    movie_description = movie_info['overview']
    print(movie_title)
    is_movie_exist = Movies.query.filter_by(movieName=movie_title).first()
    if is_movie_exist:
        print("movie already exist")
        return movie_title
    new_movie = Movies(movieName=movie_title, movieIdAPI=movie_tmdb_id, description=movie_description,genreId=movie_genre_id)
    db.session.add(new_movie)
    db.session.commit()
    # insert poster to Poster table
    current_movie = Movies.query.filter_by(movieName=movie_title, movieIdAPI=movie_tmdb_id,description=movie_description, genreId=movie_genre_id).first()
    movie_id = current_movie.movieId
    movie_poster_link = BASE_URL_IMAGES + movie_info['poster_path']
    new_poster = Posters(movieId=movie_id, posterLink=movie_poster_link)
    db.session.add(new_poster)
    db.session.commit()
    # insert the actors of the movie for Actor table and Movie-Actor table
    crew = requests.get("https://api.themoviedb.org/3/movie/" + str(movie_tmdb_id) + "/credits?api_key=" + API_KEY+"&language="+language).json()
    actors_list = crew['cast']
    for x in range(5):
        current_actor_name = actors_list[x]['name']
        is_current_actor_exsist = Actor.query.filter_by(actorName=current_actor_name).first()
        if not is_current_actor_exsist:
            new_actor = Actor(actorName=current_actor_name)
            db.session.add(new_actor)
            db.session.commit()
        current_actor_key = Actor.query.filter_by(actorName=current_actor_name).first().actorId
        new_actor_movie = Actor_Movies(actorId=current_actor_key, movieId=movie_id)
        db.session.add(new_actor_movie)
        db.session.commit()
    # insert trailer for Trailers table
    search_trailer = requests.get("https://api.themoviedb.org/3/movie/"+movie_tmdb_id+"/videos?api_key=" + API_KEY+"&language="+language).json()
    search_trailer_results = search_trailer['results']
    if not search_trailer_results:
        print("no trailer")
        return
    for current_trailer in search_trailer_results:
        trailer_site = current_trailer['site']
        trailer_key = current_trailer['key']
        if trailer_site == "YouTube":
            youtube_link = "https://www.youtube.com/embed/" + trailer_key
            new_trailer = Trailers(trailerLink=youtube_link, movieId=movie_id)
            db.session.add(new_trailer)
            db.session.commit()
            break
def insert_movie_by_movie_name(movie_name,language="en"):
    search_movie = requests.get("https://api.themoviedb.org/3/search/movie?api_key=" + API_KEY + "&query="+movie_name+"&language="+language).json()
    search_movie_results = search_movie['results']
    if not search_movie_results:
        print("no results")
        return False
    movie_info=0
    for current_movie in search_movie_results:
        if current_movie['original_language']==language:
                movie_info=current_movie
                break
    if movie_info==0:
        print("no movie with this lang")
        return False
    return insert_movie_by_movie_info(movie_info,language)
def check_genreId_by_genreAPI_id(genre_api_id):
    genre_by_genreAPI_id=Genre.query.filter_by(genreAPIId=genre_api_id).first()
    if not genre_by_genreAPI_id:
        print("no such genre")
        return
    genre_id=genre_by_genreAPI_id.genreId
    return genre_id


class Users(db.Model):
    userId = db.Column(db.Integer, primary_key=True,autoincrement=True)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)


class Rating(db.Model):
    ratingId = db.Column(db.Integer, primary_key=True,autoincrement=True)
    userId = db.Column(db.Integer, nullable=False)
    score=db.Column(db.Integer,nullable=False)
    movieId = db.Column(db.Integer, nullable=False)
    comment=db.Column(db.String(500),nullable=True)


class Movies(db.Model):
    movieId = db.Column(db.Integer, primary_key=True,autoincrement=True)
    movieName = db.Column(db.String(30), nullable=False)
    movieIdAPI=db.Column(db.String,nullable=False)
    description = db.Column(db.String(200), nullable=False)
    genreId=db.Column(db.Integer,nullable=False)

class Genre(db.Model):
    genreId=db.Column(db.Integer, primary_key=True,autoincrement=True)
    genreName = db.Column(db.String(15), nullable=False)
    genreAPIId = db.Column(db.Integer, nullable=False)


class Posters(db.Model):
    posterId=db.Column(db.Integer, primary_key=True,autoincrement=True)
    movieId=db.Column(db.Integer, nullable=False)
    posterLink=db.Column(db.Integer,nullable=False)


class History(db.Model):
    eventId=db.Column(db.Integer, primary_key=True,autoincrement=True)
    userId = db.Column(db.Integer, nullable=False)
    eventType=db.Column(db.Integer,nullable=False)


class Actor(db.Model):
    actorId=db.Column(db.Integer, primary_key=True,autoincrement=True)
    actorName=db.Column(db.String(20), nullable=False)

class Actor_Movies(db.Model):
    actorMovieId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    actorId=db.Column(db.Integer,nullable=False)
    movieId=db.Column(db.Integer,nullable=False)

class Trailers(db.Model):
    trailerId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trailerLink = db.Column(db.String(100), nullable=False)
    movieId = db.Column(db.Integer, nullable=False)


rating_get_args=reqparse.RequestParser()
rating_get_args.add_argument("kind",type=str,help="rating kind is required",required=True)


rating_put_args=reqparse.RequestParser()
rating_put_args.add_argument("userId",type=int,help="userId is required",required=True)
rating_put_args.add_argument("score",type=int,help="score is required",required=True)
rating_put_args.add_argument("comment",type=str,required=False)



resource_fields = {
    'ratingId': fields.Integer,
    'userId': fields.String,
    'score': fields.Integer,
    'movieId': fields.Integer
}


class home_page(Resource):
    def get(self):
        return send_file("javascript_files/learn.html","javascript")

class ratings(Resource):
    def get(self,movie_id):
        args=rating_get_args.parse_args()
        ratings_by_movieId = Rating.query.filter_by(movieId=movie_id).all()
        if not ratings_by_movieId:
            abort(404, message="Could not find review for this movie")

        if args['kind']=='average':
            return average(ratings_by_movieId)
        else:
            abort(404,message="rating kind is incorrect")

    def put(self,movie_id):
        args=rating_put_args.parse_args()
        user_id=args['userId']
        score=args['score']
        if not args['comment']:
            new_rating=Rating(userId=user_id,score=score,movieId=movie_id)
        else:
            rating_comment=args['comment']
            new_rating=Rating(userId=user_id,score=score,movieId=movie_id,comment=rating_comment)
        db.session.add(new_rating)
        db.session.commit()
        return "success"

class posters(Resource):
    def get(self,movie_id):
        poster_by_movieId=Posters.query.filter_by(movieId=movie_id).first()
        if not poster_by_movieId:
            abort(404,message="could not find poster for this movie")
        poster_by_movieId = Posters.query.filter_by(movieId=movie_id).first()
        if not poster_by_movieId:
            print("no poster for this movie id")
            return
        poster_link =poster_by_movieId.posterLink
        return poster_link

class actors_in_movie(Resource):
    def get(self,movie_id):
        all_actors_in_movie=[]
        actors_by_movieId=Actor_Movies.query.filter_by(movieId=movie_id).all()
        if not actors_by_movieId:
            abort(404,message="error")
        for actor_in_movie in actors_by_movieId:
            actor_name=get_actor_name_by_actorId(actor_in_movie.actorId)
            all_actors_in_movie.append(actor_name)
        return all_actors_in_movie

class movies_with_actor(Resource):
    def get(self,actor_id):
        all_movies=[]
        movies_by_actorId=Actor_Movies.query.filter_by(actorId=actor_id).all()
        if not movies_by_actorId:
            abort(404,message="error ")
        for movie in movies_by_actorId:
            movie_id=movie.movieId
            current_movie=Movies.query.filter_by(movieId=movie_id).first()
            current_movie_name=current_movie.movieName
            all_movies.append(current_movie_name)
        return all_movies

class trailer(Resource):
    def get(self,movie_id):
        trailer_link_by_movieId=Trailers.query.filter_by(movieId=movie_id).first()
        if not trailer_link_by_movieId:
            abort(404,message="no trailer for this movie")
        link=trailer_link_by_movieId.trailerLink
        return link

class movie(Resource):
    def get(self,movie_name):#search title
        movie_title_search=Movies.query.filter_by(movieName=movie_name).first()
        if movie_title_search!=None:
            print("didnt work hard")
            return movie_title_search.movieId
        movie_title=insert_movie_by_movie_name(movie_name)
        if movie_title==None:
            movie_title=insert_movie_by_movie_name(movie_name)
        movie_id=get_movie_id_by_movie_name(movie_title)
        return movie_id

class movie_title(Resource):
    def get(self,movie_id):
        movietitle_by_movieId=Movies.query.filter_by(movieId=movie_id).first()
        if movietitle_by_movieId==None:
            return False
        movie_title=movietitle_by_movieId.movieName
        return movie_title
class movie_description(Resource):
    def get(self,movie_id):
        movie_description_by_movieId=Movies.query.filter_by(movieId=movie_id).first()
        if movie_description_by_movieId==None:
            return False
        movie_description=movie_description_by_movieId.description
        return movie_description

api.add_resource(home_page,"/")
api.add_resource(ratings,"/rating/<int:movie_id>")
api.add_resource(posters,"/poster/<int:movie_id>")
api.add_resource(actors_in_movie,"/movie_actors/<int:movie_id>")
api.add_resource(movies_with_actor,"/actor/<int:actor_id>")
api.add_resource(trailer,"/trailer/<int:movie_id>")
api.add_resource(movie,"/search/<string:movie_name>")
api.add_resource(movie_title,"/title/<int:movie_id>")
api.add_resource(movie_description,"/description/<int:movie_id>")

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')
