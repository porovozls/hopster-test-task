import json
import unittest

from google.appengine.ext import testbed

import main
import webapp2
from backend.models import Movie, User


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.user = User(email="test@email.com", password="password")
        self.user.put()

    def tearDown(self):
        self.testbed.deactivate()


class TestAuthHandler(BaseTestCase):

    def setUp(self):
        super(TestAuthHandler, self).setUp()

    def test_login_email_blank(self):
        post_data = {"password": "fgkgjfdklgjkdfjgk"}
        request = webapp2.Request.blank("/api/auth/login/", POST=post_data)
        response = request.get_response(main.app)
        response_body = json.loads(response.body)
        self.assertEqual(400, response.status_int)
        self.assertEqual("Credentials cannot be blank", response_body["message"])

    def test_login_password_blank(self):
        post_data = {"password": "fgkgjfdklgjkdfjgk"}
        request = webapp2.Request.blank("/api/auth/login/", POST=post_data)
        response = request.get_response(main.app)
        response_body = json.loads(response.body)
        self.assertEqual(400, response.status_int)
        self.assertEqual("Credentials cannot be blank", response_body["message"])

    def test_login_invalid_password(self):
        post_data = {"email": "test@email.com", "password": "fgkgjfdklgjkdfjgk"}
        request = webapp2.Request.blank("/api/auth/login/", POST=post_data)
        response = request.get_response(main.app)
        response_body = json.loads(response.body)
        self.assertEqual(401, response.status_int)
        self.assertEqual("Invalid password", response_body["message"])

    def test_login_success(self):
        post_data = {"email": "test@email.com", "password": "password"}
        request = webapp2.Request.blank("/api/auth/login/", POST=post_data)
        response = request.get_response(main.app)
        headers = response.headers
        self.assertEqual(200, response.status_int)
        self.assertTrue("JWT" in headers)


class TestMovieHandler(BaseTestCase):

    def setUp(self):
        super(TestMovieHandler, self).setUp()
        # create several movies
        for i in range(3):
            movie = Movie(name="movie%i" % i, description="description%i" % i)
            movie.put()
            self.movie = movie.key()

        post_data = {"email": "test@email.com", "password": "password"}
        request = webapp2.Request.blank("/api/auth/login/", POST=post_data)
        response = request.get_response(main.app)
        self.jwt_token = response.headers["JWT"]

    def test_get_all_movies(self):
        request = webapp2.Request.blank("/api/movie/", headers={"Authorization": "Bearer {}".format(self.jwt_token)})
        response = request.get_response(main.app)
        movies = json.loads(response.body)

        self.assertEqual(3, len(movies))
        # check movies are present with correct ordering
        self.assertEqual("movie2", movies[0]["name"])
        self.assertEqual("movie1", movies[1]["name"])
        self.assertEqual("movie0", movies[2]["name"])

    def test_get_movie(self):
        request = webapp2.Request.blank("/api/movie/%i/" % self.movie.id(), headers={"Authorization": "Bearer {}".format(self.jwt_token)})
        response = request.get_response(main.app)
        movie = json.loads(response.body)

        # check movies are present with correct ordering
        self.assertEqual("movie2", movie["name"])

    def test_update_movie_success(self):
        request = webapp2.Request.blank("/api/movie/%i/" % self.movie.id(),
                                        headers={"Authorization": "Bearer {}".format(self.jwt_token)},
                                        POST={"name": "name2"})
        response = request.get_response(main.app)

        # check movies are present with correct ordering
        self.assertEqual(204, response.status_int)

    def test_update_movie_no_such_movie(self):
        request = webapp2.Request.blank("/api/movie/1234/",
                                        headers={"Authorization": "Bearer {}".format(self.jwt_token)},
                                        POST={"name": "name2", "description": "description2"})
        response = request.get_response(main.app)
        body = json.loads(response.body)

        # check movies are present with correct ordering
        self.assertEqual(404, response.status_int)
        self.assertEqual("No such movie", body["message"])

    def test_update_movie_no_fields_are_provided(self):
        request = webapp2.Request.blank("/api/movie/%i/" % self.movie.id(),
                                        headers={"Authorization": "Bearer {}".format(self.jwt_token)},
                                        POST={})
        response = request.get_response(main.app)

        self.assertEqual(204, response.status_int)

    def test_delete_movie_no_such_movie(self):
        request = webapp2.Request.blank("/api/movie/1234/",
                                        headers={"Authorization": "Bearer {}".format(self.jwt_token)})
        request.method = "DELETE"
        response = request.get_response(main.app)
        body = json.loads(response.body)

        # check movies are present with correct ordering
        self.assertEqual(404, response.status_int)
        self.assertEqual("No such movie", body["message"])

    def test_delete_movie_success(self):
        request = webapp2.Request.blank("/api/movie/%i/" % self.movie.id(),
                                        headers={"Authorization": "Bearer {}".format(self.jwt_token)})
        request.method = "DELETE"
        response = request.get_response(main.app)

        self.assertEqual(204, response.status_int)

    def test_create_movie_success(self):
        request = webapp2.Request.blank("/api/movie/",
                                        headers={"Authorization": "Bearer {}".format(self.jwt_token)},
                                        POST={"name": "name2", "description": "description2"})
        response = request.get_response(main.app)
        body = json.loads(response.body)

        # check movies are present with correct ordering
        self.assertEqual(201, response.status_int)
        self.assertEqual("name2", body["name"])
        self.assertEqual("description2", body["description"])

    def test_create_movie_name_is_not_provided(self):
        request = webapp2.Request.blank("/api/movie/",
                                        headers={"Authorization": "Bearer {}".format(self.jwt_token)},
                                        POST={"description": "description2"})
        response = request.get_response(main.app)
        body = json.loads(response.body)

        # check movies are present with correct ordering
        self.assertEqual(400, response.status_int)
        self.assertEqual("Name and description fields must be filled", body["message"])

    def test_create_movie_description_is_not_provided(self):
        request = webapp2.Request.blank("/api/movie/",
                                        headers={"Authorization": "Bearer {}".format(self.jwt_token)},
                                        POST={"name": "name2"})
        response = request.get_response(main.app)
        body = json.loads(response.body)

        # check movies are present with correct ordering
        self.assertEqual(400, response.status_int)
        self.assertEqual("Name and description fields must be filled", body["message"])

