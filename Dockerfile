# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /code
# COPY . /code

EXPOSE  11112

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /code
USER appuser

# ENTRYPOINT [  "--output_dir" , "--csv_dir" , "--env"]
ARG output_dir=/code/data
ARG csv_dir=/code/other/test.csv
ARG env=/code/config.env

# ENTRYPOINT [ --output_dir ,, ${output_dir} , --csv_dir , ${csv_dir} , --env , ${env} ]

CMD [bash]
# [python,  download_from_pacs.py]
# --output_dir $output_dir --csv_dir $csv_dir --env $env