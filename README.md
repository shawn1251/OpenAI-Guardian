# OpenAI Guardian Service

This project implements a service that acts as an intermediary between an application and the OpenAI API. It utilizes `mitmproxy` for message interception and IBM Granite Guardian to assess the content for harmful material. If harmful content is detected, the service will block the response.

## Architecture

The project is structured using Docker Compose, which allows for easy management of multiple services. The architecture consists of the following components:

- **Nginx**: Acts as a reverse proxy to route requests to the appropriate service.
- **App**: The main application that interacts with the OpenAI API.
- **Guardian**: The IBM Granite Guardian service that evaluates the content for harmful material.
- **Mitmproxy**: Intercepts requests and responses between the App and the OpenAI API for analysis.

## Docker Compose Configuration

The project uses Docker Compose to define and run the services. Below is the `docker-compose.yml` configuration:

```yaml
version: '3.1'

services:
    nginx:
        image: nginx:alpine
        volumes:
            - ./nginx.conf:/etc/nginx/conf.d/default.conf
        ports:
            - "80:80"
        depends_on:
            - app

    app:
        image: openaigurad
        build: ./OpenAI-Guardian
        ports:
            - "8000:8000"
        depends_on:
            - guardian
        volumes:
            - ./config.yml:/code/config.yml

    guardian:
        image: guardian
        build: ./Granite-Guardian
        ports:
            - "8001:8000"

    mitmproxy:
        image: my_mitmproxy
        build: ./mitmproxy
        ports:
            - "8080:8080"
        depends_on:
            - guardian
            - app
        command: mitmdump -s /code/intercept_openai.py --mode reverse:https://api.openai.com
        volumes:
            - ./mitmproxy/code/intercept_openai.py:/code/intercept_openai.py
            - ~/.mitmproxy:/home/mitmproxy/.mitmproxy
```

## Getting Started

### Prerequisites

- Docker
- Docker Compose
- huggingface-cli

### Installation

1. Clone the repository:
        ```bash
        git clone https://github.com/shawn1251/OpenAI-Guardian.git
        cd OpenAI-Guardian
        ```
2. Download the model manully (because the size is too big)`huggingface-cli download ibm-granite/granite-guardian-3.0-2b --local-dir ./Granite-Guardian/model`

3. Fill in your API details in `config.example.yml` and rename it to `config.yml`.

4. Build and start the services:
        ```bash
        docker-compose up --build
        ```

5. Access the FastAPI OpenAPI interface at [http://localhost/docs](http://localhost:80/docs) to interact with the application.

### Notes

- The first execution may take longer than usual due to the large size of the Guardian model.
- Ensure that you have the correct API keys and configurations set in `config.yml`.

## Usage

- The application will intercept requests to the OpenAI API.
- The intercepted messages will be analyzed by the IBM Granite Guardian service.
- If harmful content is detected, the response will be blocked.

## Acknowledgments

- mitmproxy for providing the interception capabilities.
- IBM Granite Guardian for content evaluation.