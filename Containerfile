FROM registry.access.redhat.com/ubi8/nodejs-22
WORKDIR /app/
USER root
USER ${USER_UID}


ENV BASE_DIR="/app"
COPY ./index.js /app/index.js
COPY ./aws-logo.svg /app/aws-logo.svg
COPY ./azure-logo.svg /app/azure-logo.svg

EXPOSE 9001

ENTRYPOINT ["node", "/app/index.js"]
