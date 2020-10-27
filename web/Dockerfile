# this is our first build stage, it will not persist in the final image
FROM ubuntu as intermediate

MAINTAINER Artem Kunashev <artem.kunashev@gmail.com>

# install git
RUN apt-get update
RUN apt-get install -y git

# add credentials on build
ARG SSH_PRIVATE_KEY
RUN mkdir /root/.ssh/
COPY private_horizon /root/.ssh/id_rsa
RUN chmod 0400 /root/.ssh/id_rsa

# make sure your domain is accepted
RUN touch /root/.ssh/known_hosts
RUN ssh-keyscan github.com >> /root/.ssh/known_hosts


RUN git clone git@github.com:lanitgithub/horizon.git
# TODO Ветку выбирать от тега
WORKDIR /horizon
RUN git checkout dev
RUN rm -R /horizon/.git

FROM python:3.8

MAINTAINER Artem Kunashev <artem.kunashev@gmail.com>

RUN apt-get update \
    && rm -rf /var/lib/apt/lists/*

# copy the repository form the previous image
COPY --from=intermediate /horizon/web /horizon-web


WORKDIR /horizon-web
ENV PYTHONPATH $PYTHONPATH:/horizon-web

RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]