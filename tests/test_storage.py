"""Test storage package."""
import json

from leopard_lavatory.storage.database import add_user_watchjob, get_all_watchjobs, database_session


class TestDatabase:

    def test_add_user_watchjobs(self):
        with database_session() as dbs:
            user_a, wj_a = add_user_watchjob(dbs, 'a@example.com', {'street': 'a-street'})
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
