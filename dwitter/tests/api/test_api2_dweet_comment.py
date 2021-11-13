from django.test import Client, TransactionTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from dwitter.models import Comment, Dweet
import json

APIV2_PATH = '/apiv2beta'


class Api2DweetAndCommentDeletionTestCase(TransactionTestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='user1Pass',
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='user2Pass',
        )
        self.mod = User.objects.create_user(
            username='mod',
            email='mod@example.com',
            password='banHammer69',
            is_staff=True  # set the mod flag
        )
        self.dweet1 = Dweet.objects.create(id=1,
                                           code="dweet code",
                                           posted=timezone.now(),
                                           author=self.user1)

        # log in with both users
        token = self.login('user1', 'user1Pass')
        self.authUser1 = 'token ' + token

        token = self.login('user2', 'user2Pass')
        self.authUser2 = 'token ' + token

        token = self.login('mod', 'banHammer69')
        self.authMod = 'token ' + token

    def login(self, username, password):
        response = self.client.post(f'{APIV2_PATH}/api-token-auth/',
                                    {'username': username, 'password': password})
        self.assertEquals(response.status_code, 200)
        token = json.loads(response.content)['token']
        return token

    def test_dweet_deletion(self):
        self.dweet2 = Dweet.objects.create(id=2,
                                           code="dweet code",
                                           posted=timezone.now(),
                                           author=self.user2)

        self.dweetmod = Dweet.objects.create(id=3,
                                             code="dweet code",
                                             posted=timezone.now(),
                                             author=self.mod)

        self.assertEqual(Dweet.objects.count(), 3)
        # Without authentication
        response = self.client.delete(f'{APIV2_PATH}/dweets/{str(self.dweet1.id)}/')
        self.assertEqual(response.status_code, 403)

        # Delete other user's dweet with authentication should fail
        response = self.client.delete(
            f'{APIV2_PATH}/dweets/{str(self.dweet1.id)}/', HTTP_AUTHORIZATION=self.authUser2)
        self.assertEqual(response.status_code, 403)

        # Delete mod's dweet with authentication should fail for other users
        response = self.client.delete(
            f'{APIV2_PATH}/dweets/{str(self.dweetmod.id)}/', HTTP_AUTHORIZATION=self.authUser1)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Dweet.objects.count(), 3)

        # Delete self should work
        response = self.client.delete(
            f'{APIV2_PATH}/dweets/{str(self.dweet1.id)}/', HTTP_AUTHORIZATION=self.authUser1)
        self.assertEqual(response.status_code, 204)

        # Delete other's dweet should work if you're a moderator
        response = self.client.delete(
            f'{APIV2_PATH}/dweets/{str(self.dweet2.id)}/', HTTP_AUTHORIZATION=self.authMod)
        self.assertEqual(response.status_code, 204)

        # Delete mod self dweet should work
        response = self.client.delete(
            f'{APIV2_PATH}/dweets/{str(self.dweetmod.id)}/', HTTP_AUTHORIZATION=self.authMod)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Dweet.objects.count(), 0)

    def test_comment_deletion(self):
        self.comment1 = Comment.objects.create(id=1,
                                               posted=timezone.now(),
                                               reply_to=self.dweet1,
                                               author=self.user1)
        self.comment2 = Comment.objects.create(id=2,
                                               posted=timezone.now(),
                                               reply_to=self.dweet1,
                                               author=self.user2)
        self.commentMod = Comment.objects.create(id=3,
                                                 posted=timezone.now(),
                                                 reply_to=self.dweet1,
                                                 author=self.mod)

        self.assertEqual(Comment.objects.count(), 3)

        # Without authentication
        response = self.client.delete(f'{APIV2_PATH}/comments/{str(self.comment1.id)}/')
        self.assertEqual(response.status_code, 403)

        # Delete other user's comment with authentication should fail
        response = self.client.delete(
            f'{APIV2_PATH}/comments/{str(self.comment1.id)}/', HTTP_AUTHORIZATION=self.authUser2)
        self.assertEqual(response.status_code, 403)

        # Delete mod's comment with authentication should fail for other users
        response = self.client.delete(
            f'{APIV2_PATH}/comments/{str(self.commentMod.id)}/', HTTP_AUTHORIZATION=self.authUser2)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Comment.objects.count(), 3)

        # Delete self should work
        response = self.client.delete(
            f'{APIV2_PATH}/comments/{str(self.comment1.id)}/', HTTP_AUTHORIZATION=self.authUser1)
        self.assertEqual(response.status_code, 204)

        # Delete other's dweet should work if you're a moderator
        response = self.client.delete(
            f'{APIV2_PATH}/comments/{str(self.comment2.id)}/', HTTP_AUTHORIZATION=self.authMod)
        self.assertEqual(response.status_code, 204)

        # Delete mod self dweet should work
        response = self.client.delete(
            f'{APIV2_PATH}/comments/{str(self.commentMod.id)}/', HTTP_AUTHORIZATION=self.authMod)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Comment.objects.count(), 0)
