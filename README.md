# Projeto Medway

Este repositório contém uma solução para o desafio proposto pela **Medway** para a vaga de **Sr. Backend Developer**. O desafio consiste em criar endpoints em um sistema Django que permitam a estudantes responder avaliações e consultar seus resultados.

## Sumário
- [Projeto Medway](#projeto-medway)
  - [Sumário](#sumário)
  - [Visão Geral](#visão-geral)
  - [Tecnologias e dependências](#tecnologias-e-dependências)
  - [Instalação e configuração](#instalação-e-configuração)
  - [Endpoints](#endpoints)
    - [Endpoint 1 - Respondendo a avaliação](#endpoint-1---respondendo-a-avaliação)
    - [Endpoint 2 - Consultando o resultado](#endpoint-2---consultando-o-resultado)
  - [Testes](#testes)
  - [Documentação](#documentação)

## Visão Geral
O desafio da Medway envolve a implementação de duas rotas em uma aplicação Django:

1. Um endpoint para que o usuário submeta suas respostas a uma prova (avaliação).
2. Um endpoint para que o usuário obtenha o resultado final de sua prova.

No código serão encontrados comentários `# NOTE:` onde busquei apresentar meu ponto de vista e soluções alternativas.

## Tecnologias e dependências
O projeto foi configurado inicialmente com:
- Python 3.11
- Django 5
- Rest Framework
- Django filters

Adicionalmente, para implementar uma solução robusta e escalável, foram utilizadas as seguintes ferramentas:
- Sentry
- Celery
- Redis
- Docker

Também foram adicionadas as seguintes dependências:
- `django-celery-results` para armazenar resultados.
- `python-decouple` para carregar variáveis de ambiente.
- `drf-yasg` para documentação com Swagger.

## Instalação e configuração
O projeto inicialmente dispunha de um docker-compose com um banco de dados PostgreSQL e um container para a aplicação. Buscando a construção de uma aplicação robusta, escalável e mais alinhada com um projeto real, foram adicionados os containers do Redis, RabbitMQ e Celery.

Para executar o projeto, basta clonar o repositório e executar o comando `docker-compose up --build` na raiz do projeto. O docker-compose irá construir os containers e executar a aplicação que estará rodando na porta padrão `8000`.

## Endpoints

### Endpoint 1 - Respondendo a avaliação

Esse endpoint deve permitir que um usuário responda ao *Exam*. O *Exam* é composto por *Questions* de múltipla escolha. O endpoint deve receber um JSON com o id do *Student* e com suas *Answers*, retornando um id de submissão da prova.


```json
// POST /api/v1/exams/{id}/answer

// BODY
{
  "student_id": 0,
  "question_responses": [
    {
      "question_id": 0,
      "selected_alternative_id": 0
    }
  ]
}

// RESPONSE
{
  "message": "Exam submitted successfully",
  "id": 15
}
```

>  💡 **Observações Importantes**
> - A correção não é imediata. O sistema enfileira a correção da prova e retorna um identificador para futura consulta do resultado.
> - Caso a prova seja longa ou existam vários usuários submetendo avaliações ao mesmo tempo, o sistema assíncrono lida melhor com essa carga, tornando a experiência mais rápida para quem envia as respostas.

### Endpoint 2 - Consultando o resultado

Esse endpoint deve permitir que um usuário consulte o resultado de um *Exam* previamente submetido. O endpoint deve receber o id do *Exam* no path e o id do *Student* como parâmetro de query, retornando o resultado da prova.


```json
// GET /api/v1/exams/{id}/results/?student_id={student_id}

// RESPONSE
{
  "summary": {
    "total_questions": 5,
    "correct_questions": 2,
    "percentage": "40.00"
  },
  "question_answers": [
    {
      "question": {
        "id": 1,
        "content": "Qual parte do corpo usamos para ouvir?"
      },
      "selected_alternative": {
        "id": 3,
        "content": "Ouvidos",
        "option": 3
      },
      "correct_alternative": {
        "id": 3,
        "content": "Ouvidos",
        "option": 3
      },
      "is_correct": true
    }
    ...
  ]
}
```

>  💡 **Observações Importantes**
> - O endpoint utiliza uma solução de cache para armazenar os resultados das provas. Isso permite que o sistema responda mais rapidamente a consultas frequentes.
> - Foi optado por calcular os acertos e percentual de acertos no momento da consulta de resultados, evitando a necessidade de armazenar esses dados no banco de dados e recalcular caso haja alguma alteração nas respostas do aluno.


## Testes

Foi implementada uma suite de testes para os 2 endpoints implementados. Os testes podem ser executados com o comando `docker-compose exec app python manage.py test`. Os testes cobrem os casos de sucesso e falha para os endpoints, garantindo que a aplicação se comporta conforme o esperado.

Foram escritos:

- **Testes unitários:** Para os serializers e para o service, garantindo que os dados são serializados e processados corretamente.
- **Testes de integração:** Para as integrações com o banco de dados, async worker e cache, garantindo que os dados são armazenados e recuperados corretamente.

```bash
$ docker exec -it medway-api python manage.py test


Found 7 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.......
----------------------------------------------------------------------
Ran 7 tests in 0.145s

OK
Destroying test database for alias 'default'...
```

## Documentação

Foi criada uma documentação para os endpoints utilizando o Swagger. A documentação pode ser acessada em `http://localhost:8000/swagger/` após a aplicação ser iniciada.