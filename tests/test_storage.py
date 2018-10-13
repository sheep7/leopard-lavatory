"""Test storage package."""
import json

from leopard_lavatory.storage.database import add_user_watchjob, relate_user_watchjob, \
    delete_user, delete_watchjob, get_all_watchjobs


class TestDatabase:

    def test_add_user_watchjobs(self):
        user_a, wj_a = add_user_watchjob('a@example.com', {'street': 'a-street'})
        user_b, wj_b = add_user_watchjob('b@example.com', {'street': 'b-street'})
        user_c, wj_c = add_user_watchjob('c@example.com', {'street': 'c-street'})

        assert len(user_b.watchjobs) == 1

        relate_user_watchjob(user_b, wj_a)

        # user b should now have two watchjobs, wj_b and wj_b (because we related that one above)
        assert len(user_b.watchjobs) == 2

        # get all watchjobs and confirm values
        watchjobs = get_all_watchjobs()
        assert len(watchjobs) == 3
        assert json.loads(watchjobs[0].query)['street'] == 'a-street'

        # clean up database
        delete_user(user_a)
        delete_watchjob(wj_a)
        delete_user(user_b)
        delete_watchjob(wj_b)
        delete_user(user_c)
        delete_watchjob(wj_c)
