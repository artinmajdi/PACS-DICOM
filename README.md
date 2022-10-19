# Connecting to a PACS server and downloading DICOM files

[![GitHub.io](https://img.shields.io/badge/GitHub.io-artinmajdi)](https://artinmajdi.github.io/Data7.PACS_DICOM/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://artinmajdi-data7-pacs-dicom-app-id280r.streamlitapp.com/)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/artinmajdi/Data7.PACS_DICOM.git/main?labpath=other%2Fd7.pacs.ipynb)
[![DockerHub](https://img.shields.io/badge/DockerHub-artinmajdi%2Fconnect--to--pacs-blue)](https://hub.docker.com/r/artinmajdi/connect_to_pacs)

## Installation

`pip install -r requirements.txt`



### Building the docker container

1. Building the image using Dockerfile
```bash
docker build . -t artinmajdi/connect_to_pacs
```

2. Pulling from docker hub
```bash
docker pull artinmajdi/connect_to_pacs
```
### Run the container
```bash
docker run --rm -i -v ~/Documents/projects/D7.PACS/code:/code artinmajdi/connect_to_pacs:latest python download_from_pacs.py --output_dir /code/data --csv_dir /code/other/test.csv --env /code/config.env
```

docker build --build-arg some_variable_name=a_value
docker run -e "env_var_name=another_value" alpine env

 docker build . -t artinmajdi/connect_to_pacs --build-arg output_dir=/data --build-arg csv_dir=/code/other/test.csv --build-arg env=/code/config.env

## Usage

`streamlit run app.py`

## License

[MIT](https://choosealicense.com/licenses/mit/)
