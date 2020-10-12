#adding Django dependencies
FROM django

#adding Python 3.7 dependencies
FROM python:3.7

#creating working directory
ADD . /django-cms

#switching to woring directory
WORKDIR /django-cms

#RUN pip3 install --upgrade virtualenv

# RUN virtualenv env

# RUN source env/bin/activate

#installing djangocms-installer
RUN pip3 install djangocms-installer

#creating and switching to working directory
WORKDIR /django-cms/my-project

#running djangocms
RUN  djangocms -f -p . my_project

#opening tpc/8000 port
EXPOSE 8000
