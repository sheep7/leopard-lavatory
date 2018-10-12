"""Testing the utils package."""

from leopard_lavatory.utils import create_token, valid_email, valid_address, log_safe


class TestUtils:

    def test_create_token(self):
        assert len(create_token()) > 20

    def test_valid_email(self):
        assert valid_email('test@example.com')
        assert valid_email('test.Uppercase@and.Subdomain.example.com')
        assert valid_email('test+plus@example.com')
        assert valid_email('a'*240 + '@maxlength.com')
        assert not valid_email('a'*243 + '@toolong.com')
        assert not valid_email('')
        assert not valid_email('noatsign%example.com')
        assert not valid_email('white space@in.address.com')
        assert not valid_email('illegal:character@in.address.com')
        assert not valid_email('illegal"character@in.address.com')
        assert not valid_email("ends-with-dot@example.com.")

    def test_valid_address(self):
        assert valid_address('Drottninggatan 30')
        assert valid_address('Värmdövägen 1b')
        assert not valid_address('illegal character !')
        assert not valid_address('illegal character "')
        assert not valid_address("illegal character '")

    def test_log_safe(self):
        # test that long input is cut and that dots are added when cut
        assert len(log_safe('a'*2000)) == 1003
        assert log_safe('a'*2000).endswith('...')
        # test unsafe character conversion
        assert "'" not in log_safe("'")
        # test that common mail address is preserved
        assert log_safe('test@example.com') == 'test@example.com'
