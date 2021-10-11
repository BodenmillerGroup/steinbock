# Contributing

Pull requests are welcome. Please make sure to update tests and documentation as appropriate.

For major changes, please open an issue first to discuss what you would like to change.

## Development

*steinbock* is developed using [Visual Studio Code](https://code.visualstudio.com).

For convenience, the following [Docker Compose](https://docs.docker.com/compose) services are available:
  - `steinbock` for running *steinbock*
  - `steinbock-debug` for debugging *steinbock* using [debugpy](https://github.com/microsoft/debugpy)
  - `pytest` for running unit tests with [pytest](https://pytest.org)
  - `pytest-debug` for debugging unit tests with [pytest](https://pytest.org) and [debugpy](https://github.com/microsoft/debugpy)

Matching Visual Studio Code launch configurations are provided for debugging:
  - `Docker: Python General` for debugging *steinbock* using [Docker](https://www.docker.com) directly
  - `Python: Remote Attach (steinbock-debug)` for debugging *steinbock* using [Docker Compose](https://docs.docker.com/compose)
  - `Python: Remote Attach (pytest-debug)` for debugging unit tests with [pytest](https://pytest.org) using [Docker Compose](https://docs.docker.com/compose)

Launch configurations may have to be invoked multiple times. To debug specific *steinbock* commands using the `Python: Remote Attach (steinbock-debug)` launch configuration, adapt the `command` in the [docker-compose.yml](https://github.com/BodenmillerGroup/steinbock/blob/main/docker-compose.yml) file (e.g. add `--version` after `-m steinbock`). To debug unit tests on the host system (i.e., not within the Docker container), run `pytest tests` in the project root folder or use the "Testing" tab in Visual Studio Code.
