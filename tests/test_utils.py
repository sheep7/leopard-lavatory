"""Testing the utils package."""

from leopard_lavatory.utils import create_token, valid_email, valid_address, log_safe


class TestUtils:

    def test_create_token(self):
        assert len(create_token()) > 20, 'token must have more than 20 characters'
        token_a = create_token()
        token_b = create_token()
        assert token_a != token_b, 'two tokens must be different'

    def test_valid_email(self):
        assert valid_email('test@example.com')
        assert valid_email('test.Uppercase@and.Subdomain.example.com')
        assert valid_email('test+plus@example.com')
        assert valid_email('a'*240 + '@maxlength.com'), 'a 254 character email is valid'
        assert not valid_email('a'*243 + '@toolong.com'), 'a 255 character email is not valid'
        assert not valid_email(''), 'the empty string is not a valid email'
        assert not valid_email('noatsign%example.com'), 'a string without @ is not a valid email'
        assert not valid_email('white space@in.address.com')
        assert not valid_email('illegal:character@in.address.com')
        assert not valid_email('illegal"character@in.address.com')
        assert not valid_email("ends-with-dot@example.com.")

    def test_valid_address(self):
        assert valid_address('Drottninggatan 30')
        assert valid_address('Värmdövägen 1b')
        assert valid_address('a'*255), 'a 255 character string is valid'
        assert not valid_address('a'*256), 'a 256 character string is too long'
        assert not valid_address('illegal character !')
        assert not valid_address('illegal character "')
        assert not valid_address("illegal character '")

    def test_log_safe(self):
        assert len(log_safe('a'*2000)) <= 1003, 'long inputs must be cut short'
        assert log_safe('a'*2000).endswith('...'), 'cut inputs must end in ...'
        assert "'" not in log_safe("'"), 'unsafe characters like single quotes must be removed'
        assert log_safe('test@te.st') == 'test@te.st', 'simple email addresses must be preserved'
