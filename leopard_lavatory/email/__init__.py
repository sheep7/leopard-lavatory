#!/usr/bin/env python3
import os
import smtplib
from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import make_msgid

import yaml
from flask import render_template
from jinja2 import Environment, PackageLoader, select_autoescape

FROM_ADDRESS = Address('Display Name From', 'from@example.com')
SMTP_SERVER = 'localhost'
DEBUG_OUTPUT = True

ENV = Environment(
    loader=PackageLoader('leopard_lavatory.email'),
    autoescape=select_autoescape(default=True)
)

TEMPLATES = []
DEFAULT_DATA = {}


def _read_templates():
    """Reads the available templates from the template directory and stores them in
    the global TEMPLATES variable, a list of template names
    (without file endings and excluding index).

    Makes sure that there exists exactly one txt email template for every html email template.

    It also tries to read yml files with default values for each of the html templates
    and if found, stores them in the DEFAULT_DATA dictionary.
    """
    current_file_path = os.path.dirname(os.path.abspath(__file__))
    templates_path = os.path.join(current_file_path, 'templates')
    template_files = os.listdir(templates_path)
    txt_templates = []
    for file in template_files:
        if file in ['index.html']:
            continue
        if file.endswith('.html'):
            TEMPLATES.append(file[:-5])
        elif file.endswith('.txt'):
            txt_templates.append(file[:-4])
        if file.endswith('.yml'):
            DEFAULT_DATA[file[:-4]] = yaml.safe_load(open(os.path.join(templates_path, file)))

    assert set(TEMPLATES) == set(txt_templates), 'For every html email template there must be ' \
                                                 'exactly one txt email template.'


_read_templates()


def send_email(template_name, to_address, data):
    if 'subject' in data:
        subject = data['subject']
    else:
        subject = DEFAULT_DATA[template_name]['subject']
    txt_body, html_body = create_email_bodies(template_name, data)

    _send_email(to_address, subject, txt_body, html_body)


def create_email_bodies(template_name, data=None):
    complete_data = DEFAULT_DATA.get(template_name, {})
    if data:
        complete_data.update(data)
    txt_body = render_template(f'{template_name}.txt', **complete_data)
    html_body = render_template(f'{template_name}.html', **complete_data)
    return txt_body, html_body


def _send_email(to_address, subject, txt_body, html_body):
    msg = _create_message(to_address, subject, txt_body, html_body)

    if DEBUG_OUTPUT:
        # Make a local copy of what we are going to send.
        with open('outgoing.msg', 'wb') as f:
            f.write(bytes(msg))

    # Send the message via local SMTP server.
    with smtplib.SMTP(SMTP_SERVER) as smtp_server:
        smtp_server.send_message(msg)


def _create_message(to_address, subject, txt_body, html_body=None):
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
