FROM yml-api as web
WORKDIR /opt/app
EXPOSE 8000
RUN pip install pywebpush==1.14.0 openai==1.3.8
ADD . .
ENTRYPOINT ["python", "manage.py", "startserver", "gv"]

FROM yml-api-test as test
WORKDIR /opt/app
ADD . .
ENTRYPOINT ["sh", "-c", "cp -r /opt/git .git && git pull origin $BRANCH && python manage.py test"]
