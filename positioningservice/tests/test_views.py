import base64
from json import loads
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from rest_framework.test import APITestCase
from rest_framework import status
from oauth2_provider.models import Application

from ..models import Position, Event


class UserAPITestCase(APITestCase):

    """
    Base API test class so we can have logged in user
    """

    user1 = {'username': 'test', 'password': 'asdasd'}

    def setUp(self):
        """
        Here we set up our test objects for the tests
        """
        self.user_obj = User.objects.create_user(
            self.user1['username'], "asd@asd.se", self.user1['password'])

        self.client_obj = Application.objects.create(
            user=self.user_obj,
            name='clientname',
            redirect_uris='http://app.com/ http://app.com/?callback',
            client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_PASSWORD
        )

        self.position = Position.objects.create(
            name="Kalmar",
            address="Kalmar, Sweden",
            longitude=56,
            latitude=19
        )

        self.position2 = Position.objects.create(
            name="Stockholm",
            address="Stockholm, Sweden",
            longitude=12.344,
            latitude=39.919
        )

        self.event = Event.objects.create(
            name='Guldveckan Kalmar',
            position=self.position,
            user=self.user_obj
        )

        self.event2 = Event.objects.create(
            name='DjangoCon Europe',
            position=self.position2,
            user=self.user_obj
        )

    def tearDown(self):
        self.user_obj.delete()
        self.client_obj.delete()
        self.position.delete()

    def get_token(self, user, client):
        """
        Method for getting oauth token
        """
        data = {
            'grant_type': 'password', 'username': user['username'],
            'password': user['password'], 'client_id': client.client_id,
            'client_secret': client.client_secret,
        }

        # Post our data to the oauth access point
        response = self.client.post(reverse('oauth2_provider:token'), data)

        # Check that our response is fine
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Parse the content
        response_data = loads(response.content.decode("utf-8"))

        # Check if access_token is in our response_data
        self.assertTrue('access_token' in response_data)

        # Get the token
        token = response_data['access_token']

        # Send it!
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)


class PositionTest(UserAPITestCase):
    """
    API tests for the Positions API
    """

    def test_get_positions_requires_login(self):
        """
        Test method for checking that to get positions
        requires user to be logged in
        """
        # Send request to the positions API
        response = self.client.get(reverse('positioningservice:positions_list'))

        # Check that our response is "Unauthorized"
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Check for error message
        self.assertEqual(
            response.data['detail'], "Authentication credentials were not provided.")

    def test_can_retrieve_positions(self):
        """
        Test method for checking that authorized users can
        get a list of positions
        """
        # Get our access_token
        self.get_token(self.user1, self.client_obj)

        # Send request to the positions API
        response = self.client.get(reverse('positioningservice:positions_list'))

        # Check that our response is fine
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Parse our response
        response_data = loads(response.content.decode('utf-8'))

        # Check that our data is what it should be
        self.assertEqual(response_data[0]['name'], "Kalmar")
        self.assertEqual(response_data[0]['address'], "Kalmar, Sweden")
        self.assertEqual(response_data[0]['longitude'], '56.000')
        self.assertEqual(response_data[0]['latitude'], '19.000')
        self.assertEqual(response_data[1]['name'], "Stockholm")
        self.assertEqual(response_data[1]['address'], "Stockholm, Sweden")
        self.assertEqual(response_data[1]['longitude'], '12.344')
        self.assertEqual(response_data[1]['latitude'], '39.919')

        # Check events
        self.assertEqual(response_data[0]['events'][0]['name'], "Guldveckan Kalmar")


    def test_can_retrieve_a_single_position(self):
        """
        Test for checking that authorized users can
        get a SINGLE position
        """
        # Get our access_token
        self.get_token(self.user1, self.client_obj)

        # Send request to the positions API
        response = self.client.get(reverse('positioningservice:positions_detail', kwargs={'pk': 1}))

        # Check that our response is fine
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Parse our response
        response_data = loads(response.content.decode('utf-8'))

        # Check that our data is what it should be
        self.assertEqual(response_data['name'], "Kalmar")
        self.assertEqual(response_data['address'], "Kalmar, Sweden")
        self.assertEqual(response_data['longitude'], '56.000')
        self.assertEqual(response_data['latitude'], '19.000')

        # Send a new request to the positions API to get pk id 2
        response = self.client.get(reverse('positioningservice:positions_detail', kwargs={'pk': 2}))

        # Check that our response is fine
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Parse our response
        response_data = loads(response.content.decode('utf-8'))

        # Check that our data is what it should be
        self.assertEqual(response_data['name'], "Stockholm")
        self.assertEqual(response_data['address'], "Stockholm, Sweden")
        self.assertEqual(response_data['longitude'], '12.344')
        self.assertEqual(response_data['latitude'], '39.919')

        # Check events
        self.assertEqual(response_data['events'][0]['name'], "DjangoCon Europe")


class EventTest(UserAPITestCase):
    """
    API tests for the Events API
    """

    def test_can_retrieve_events(self):

        # Get our access_token
        self.get_token(self.user1, self.client_obj)

        # Send request to the positions API
        response = self.client.get(reverse('positioningservice:events_list'))

        # Check that our response is fine
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Parse our response
        response_data = loads(response.content.decode('utf-8'))

        # Check that our data is what it should be
        self.assertEqual(response_data[0]['name'], "Guldveckan Kalmar")


class TagTest(UserAPITestCase):
    """
    API tests for the Tag API
    """