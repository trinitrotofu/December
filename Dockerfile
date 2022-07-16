FROM nginx:1.21.5

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /December

RUN apt-get update && \
    apt-get install python3 python3-pip cron -y && \
    pip3 install pipenv

COPY clearsessions_cron /etc/cron.d/

COPY Pipfile Pipfile.lock uwsgi_params docker-run.sh default.conf /December/

RUN cat /December/default.conf > /etc/nginx/conf.d/default.conf && \    
    pipenv install --system && \
    rm /December/Pipfile /December/Pipfile.lock /December/default.conf && \
    chmod +x /December/docker-run.sh && \
    chmod 0644 /etc/cron.d/clearsessions_cron

COPY December /December/December/

CMD ["bash", "/December/docker-run.sh"]
