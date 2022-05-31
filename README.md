# web-pip-show

web-pip-show is a simple python webserver used to display gitlab CI/CD pipelines status.

![Image](./img/web-pip-show-example.png)

Each line represent a pipeline, each case a stage.

| Color                                            | Description                      |
| ------------------------------------------------ | -------------------------------- |
| ![Yellow](https://img.shields.io/badge/--f8961e) | Created                          |
| ![Blue](https://img.shields.io/badge/--007bff)   | Pending, Started, Build, Running |
| ![Green](https://img.shields.io/badge/--28a745)  | Success                          |
| ![Grey](https://img.shields.io/badge/--6c757d)   | Skipped, Cancelled               |
| ![Red](https://img.shields.io/badge/--dc3545)    | Failed                           |


## Configure

Edit `config.json` file

```json
{
  "config": {
    "token": "<gitlab_token>",
    "url": "https://gitlab/",
    "id": "<id_project>",
    "size": "<size>",
    "port": "8003"
  }
}
```

| Parameters | Description                               |
| ---------- | ----------------------------------------- |
| token      | Gitlab token used to retrieve information |
| url        | Gitlab url                                |
| id         | Id of project                             |
| size       | Number of lines to display                |
| port       | Server port                               |

## Run

```shell
python server.py
```

Then visit [localhost:8003](http://localhost:8003/)