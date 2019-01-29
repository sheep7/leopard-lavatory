"""Test storage package."""
import json

from leopard_lavatory.storage.database import *


class TestDatabase:
    email_a = 'a@example.com'

    def test_add_user_watchjobs(self):
        with database_session() as dbs:
            user_a, wj_a = add_user_watchjob(dbs, TestDatabase.email_a, {'street': 'a-street'})
            user_b, wj_b = add_user_watchjob(dbs, 'b@example.com', {'street': 'b-street'})
            user_c, wj_c = add_user_watchjob(dbs, 'c@example.com', {'street': 'c-street'})

            assert len(user_b.watchjobs) == 1

            user_b.watchjobs.append(wj_a)

            # user b should now have two watchjobs, wj_b and wj_b (because we related that one above)
            assert len(user_b.watchjobs) == 2

            # get all watchjobs and confirm values
            watchjobs = get_all_watchjobs(dbs)
            assert len(watchjobs) == 3
            assert json.loads(watchjobs[0].query)['street'] == 'a-street'

            # clean up database
            dbs.delete(user_a)
            dbs.delete(wj_a)
            dbs.delete(user_b)
            dbs.delete(wj_b)
            dbs.delete(user_c)
            dbs.delete(wj_c)

    def test_confirm_request(self):
        with database_session() as dbs:
            confirm_token = add_request(dbs, TestDatabase.email_a, {'street': 'a-street'})

            # make sure it's not None or empty
            assert confirm_token

            returned_user = confirm_request(dbs, confirm_token)

            assert returned_user.email == TestDatabase.email_a

            # make sure user exists in User
            user_in_database = dbs.query(User).filter(User.email == TestDatabase.email_a).one_or_none()

            assert user_in_database is not None
            assert user_in_database.email == TestDatabase.email_a

            # clean up database
            user_request = dbs.query(UserRequest).filter(UserRequest.email == user_in_database.email).delete()

            for watchjob in user_in_database.watchjobs:
                dbs.delete(watchjob)
            dbs.delete(user_in_database)


    def test_delete_user(self):
        with database_session() as dbs:
            user_a, wj_a = add_user_watchjob(dbs, TestDatabase.email_a, {'street': 'a-street'})

            users = dbs.query(User).all()

            assert len(users) == 1

            delete_token = user_a.delete_token

            delete_user(dbs, delete_token)

            deleted_user = dbs.query(User).filter(User.email == TestDatabase.email_a).one_or_none()

            assert deleted_user == None

            # no other cleanup required
            dbs.delete(wj_a)
