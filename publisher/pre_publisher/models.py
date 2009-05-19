"""Install publisher first
"""
from django.db import models

# install publisher support
from publisher.pre_publisher.utils import install_publisher
install_publisher()
