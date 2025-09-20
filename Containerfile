FROM registry.access.redhat.com/ubi8/python-311
WORKDIR /app/

# Switch to root for package installation
USER root

# Install Azure CLI
RUN rpm --import https://packages.microsoft.com/keys/microsoft.asc && \
    echo -e "[azure-cli]\nname=Azure CLI\nbaseurl=https://packages.microsoft.com/yumrepos/azure-cli\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/azure-cli.repo && \
    yum install -y azure-cli && \
    yum clean all

# Install Python dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY ./app.py /app/app.py
COPY ./aws-logo.svg /app/aws-logo.svg
COPY ./azure-logo.svg /app/azure-logo.svg

# Set environment variables
ENV BASE_DIR="/app"
ENV PYTHONUNBUFFERED=1

# Switch back to the default user (1001)
USER 1001

EXPOSE 9001

ENTRYPOINT ["python", "/app/app.py"]
