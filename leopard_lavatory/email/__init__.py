#!/usr/bin/env python3
import os
import smtplib
from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import make_msgid

import yaml
from jinja2 import Environment, PackageLoader, select_autoescape

FROM_ADDRESS = Address('Display Name From', 'from@example.com')
SMTP_SERVER = 'localhost'
DEBUG_DRYRUN = True

ENV = Environment(
    loader=PackageLoader('leopard_lavatory.email'),
    autoescape=select_autoescape(default=True)
)


def _read_templates():
    """Reads the available templates from the template directory and stores them in
    the global TEMPLATES variable, a list of template names
    (without file endings and excluding index).

    Makes sure that there exists exactly one txt email template for every html email template.

    It also tries to read yml files with default values for each of the html templates
    and if found, stores them in the DEFAULT_DATA dictionary.

    Returns:
        Tuple[List[str],dict]: a list of template strings (without file endings) and a default value
          dictionary
    """
    current_file_path = os.path.dirname(os.path.abspath(__file__))
    templates_path = os.path.join(current_file_path, 'templates')
    template_files = os.listdir(templates_path)
    txt_templates = []
    html_templates = []
    default_data = {}
    for file in template_files:
        if file in ['index.html']:
            continue
        if file.endswith('.html'):
            html_templates.append(file[:-5])
        elif file.endswith('.txt'):
            txt_templates.append(file[:-4])
        if file.endswith('.yml'):
            default_data[file[:-4]] = yaml.safe_load(open(os.path.join(templates_path, file)))

    assert set(html_templates) == set(txt_templates), 'For every html email template there must ' \
                                                      'be exactly one txt email template.'

    return html_templates, default_data


TEMPLATES, DEFAULT_DATA = _read_templates()


def send_email(template_name, to_address, data=None):
    """Send an email to the recipient `to_address` using the given template that will be rendered
    with the default values (read from <template_name.yml>) updated with the optionally provided
    data dict. The email subject will be read from the 'subject' value in the data (or default
    data, in case it is not present in the `data` dict).

    If `DEBUG_DRYRUN` is set to True, no email will be sent, but the message will be written to
    a file instead.

    Args:
        template_name (str): name of the template (without file ending)
        to_address (str): email address of the recipient
        data (dict): additional key-value pairs of data to pass on to the template (overrides
          default values if they have the same name (key)
    """
    if data and 'subject' in data:
        subject = data['subject']
    else:
        subject = DEFAULT_DATA[template_name]['subject']
    txt_body, html_body = create_email_bodies(template_name, data)

    msg = _create_message(to_address, subject, txt_body, html_body)

    if DEBUG_DRYRUN:
        # Make a local copy of what we would have sent.
        with open('outgoing.msg', 'wb') as f:
            f.write(bytes(msg))
    else:
        # Send the message via the SMTP server.
        with smtplib.SMTP(SMTP_SERVER) as smtp_server:
            smtp_server.send_message(msg)


def create_email_bodies(template_name, data=None):
    """Create the txt and html email bodies based on a template and additional data.
    The template will have the default values (read from <template_name>.yml), updated
    with the optionally provided values in the `data` dict available.

    Args:
        template_name (str): name of the template (without file ending)
        data (dict): additional key-value pairs of data to pass on to the template (overrides
          default values if they have the same name (key)

    Returns:
        Tuple[str, str]: a tuple of the text body and the html body as strings
    """
    complete_data = DEFAULT_DATA.get(template_name, {})
    if data:
        complete_data.update(data)
    txt_template = ENV.get_template(f'{template_name}.txt')
    txt_body = txt_template.render(complete_data)
    html_template = ENV.get_template(f'{template_name}.html')
    html_body = html_template.render(complete_data)
    return txt_body, html_body


def _create_message(to_address, subject, txt_body, html_body=None):
    """Create an email message object from the given arguments.

    Args:
        to_address (str): email address string of the recipient
        subject (str): email subject
        txt_body (str): the text part of the message
        html_body (str): the html part of the message

    Returns:
        email.message.EmailMessage: the final email message object
    """
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = FROM_ADDRESS
    msg['To'] = Address(addr_spec=to_address)
    msg.set_content(txt_body)

    if html_body:
        # Add the html version.  This converts the message into a multipart/alternative
        # container, with the original text message as the first part and the new html
        # message as the second (preferred) part.
        msg.add_alternative(html_body, subtype='html')

    return msg
