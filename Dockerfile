# DOCKER-VERSION 1.1.2
FROM python
COPY . /src
CMD ["python", “bot.py"]