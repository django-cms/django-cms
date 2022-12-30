.. _release-notes:

###################################
Release notes & upgrade information
###################################

Some versions of django CMS present more complex upgrade paths than others, and
some **require** you to take action. It is strongly recommended to read the
release notes carefully when upgrading.

It goes without saying that you should **backup your database** before embarking
on any process that makes changes to your database.

********************************************
How to upgrade django CMS to a newer version
********************************************

While it can be a complex process at times, upgrading to the latest django CMS
version has several benefits:

- New features and improvements are added.
- Bugs are fixed.
- Older version of django CMS will eventually no longer receive security updates.
- Upgrading as each new django CMS release is available makes future upgrades less
  painful by keeping your code base up to date.

Here are some things to consider to help make your upgrade process as smooth as
possible:

- Read the release notes for each major release from the one after your current
  django CMS version, up to and including the version to which you plan to
  upgrade.
- Check the versions of the django CMS packages such as djangocms-versioning
  that you are using in your project. Read their release notes.
- Pay particular attention to backwards incompatible changes to get a clear
  idea of what will be needed for a successful upgrade.
- Consider upgrading through more than one major version (e.g., 3.0 to 3.2),
  it is usually easier to upgrade through each major release incrementally, i.e.,
  3.0 to 3.1 to 3.2. For each major release use the latest patch release.
- Before upgrading `resolve any deprecation
  warnings <https://docs.djangoproject.com/en/dev/howto/upgrade-version/>`_ raised
  by your project while using your current version of django CMS


.. toctree::
    :maxdepth: 1

    4.1.0
    4.0
    3.8
    3.7.4
    3.7.3
    3.7.2
    3.7.1
    3.7
    3.6.1
    3.6
    3.5.4
    3.5.3
    3.5.2
    3.5.1
    3.5
    3.4.7
    3.4.6
    3.4.5
    3.4.4
    3.4.3
    3.4.2
    3.4.1
    3.4
    3.3
    3.2.5
    3.2.4
    3.2.3
    3.2.2
    3.2.1
    3.2
    3.1.5
    3.1.4
    3.1.3
    3.1.2
    3.1.1
    3.1
    3.0.16
    3.0.15
    3.0.14
    3.0.13
    3.0.12
    3.0.11
    3.0.10
    3.0.9
    3.0.8
    3.0.7
    3.0.6
    3.0.3
    3.0
    2.4
    2.3.4
    2.3.3
    2.3.2
    2.3
    2.2
    2.1
