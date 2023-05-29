# Lunar Data Engineering Challenge: Rockets **🚀

## Overview

The task was to build a data platform capable of ingesting data from a service and making it available in a chosen format. The service produces event data for rockets in the form of JSON messages. These messages arrive out of order and could be duplicated due to the "at-least-once" delivery guarantee.

This documentation provides an overview of the solution developed for the challenge, detailing the architecture, instructions for running the service, and some key design decisions. It also covers the use of continuous integration (CI) to ensure code quality and automated testing.

## Architecture

The solution was implemented using Python and relies heavily on Docker for easy setup and distribution. The primary components are a message producer, a message consumer, and two key technologies - Kafka and MongoDB.

Kafka was chosen due to its capabilities for handling real-time, distributed message streaming. It also helps to deal with the out-of-order delivery and potential message duplication.

MongoDB was selected as a NoSQL database due to its strong support for storing JSON-like documents, allowing for flexible and straightforward data modeling.

Here is the flow:

1. The service sends JSON messages about rocket events to a REST endpoint hosted by a FastAPI application (`producer.py`). This application serves as the message producer.
2. The producer publishes these messages to a Kafka topic.
3. A separate Kafka consumer application (`consumer.py`) reads these messages from the Kafka topic.
4. The consumer processes the messages and stores them into MongoDB. 
5. The stored data in MongoDB can be easily accessed and used for further processing or analysis, as each channel's data is stored in separate documents within the database, allowing for a more efficient data organization, easier querying, better scalability and data integrity as each channel's data can be updated or retrieved independently without affecting the others.
6. This pipeline is deployed using Docker Compose, which orchestrates the setup and interaction between Kafka, MongoDB, and the Python applications.

## Running the Service
The service can be run using Docker Compose. Assuming Docker and Docker Compose are installed, you can start the service with the following command from the root directory of the project:

```bash
docker-compose up --build -d
```

This command will build the Docker images for the producer and consumer applications and start all the services. Once everything is deployed, you can start posting messages to the API by executing the command:

```bash
./rockets launch "http://localhost:8088/messages" --message-delay=500ms --concurrency-level=1
```

Make sure to include the `rockets` executable that works for your system in the root directory when you do so.

## Visualize the data

To check the database and observe the stored data, navigate to MongoDB Express by entering the following address in your web browser:

```bash
http://0.0.0.0:8081
```

This port hosts the MongoDB Express interface, a web-based MongoDB admin interface, which provides a convenient way to interact with the data. Here, you can inspect the documents and make sure that the data is being stored correctly. You can also perform CRUD (Create, Read, Update, Delete) operations directly through this interface if needed.

## CI Pipeline

The project includes a CI pipeline configured using GitHub Actions. This pipeline runs two checks for every push or pull request to the repository:

1. Linting with flake8: This ensures that the code follows the Python PEP8 style guide.
2. Unit tests with pytest: This verifies that individual units of the main code are working as expected (`test_producer.py` and `test_consumer.py`)


## Design Decisions and Potential Improvements

Given the 6-hour limit for the challenge, the focus was on implementing a simple and functional pipeline that could handle the key requirements. The decision to use Python was due to its readability and robust support for working with JSON and HTTP requests. Kafka was chosen for its capabilities in handling real-time, distributed message streams, and MongoDB for its ease of use with JSON-like documents.

However, there are several areas that could be improved with more time:

1. **Error Handling and Recovery:** The current implementation does not include extensive error handling or recovery mechanisms. For example, if the Kafka or MongoDB service goes down, the pipeline would stop working. A more robust system would have strategies to recover from these failures.

2. **Scaling:** While Kafka and MongoDB can handle a large volume of data, the Python applications might become a bottleneck when dealing with a huge influx of messages. Implementing horizontal scaling strategies, such as running multiple instances of the applications, would help address this issue.

3. **Data Processing:** Currently, the data is stored in MongoDB as it arrives, without any additional processing. However, in a real-world scenario, there might be a need for additional processing, transformation, or aggregation of the data. For instance, it could be beneficial to calculate the averages or max/min values of some metrics, categorize the events, or detect specific patterns. This could be achieved by adding a data processing component to the pipeline.

4. **Data Retrieval:** Although MongoDB provides a flexible query language, in a production environment, there might be a need for more complex data retrieval capabilities. This could be achieved by adding a service to expose the data via a REST API or by integrating with a data warehouse or analytics platform.

5. **Security:** Currently, there are no security measures implemented. In a production environment, it would be crucial to secure the communication between the services and protect the stored data. This could include measures such as encryption, authentication, and access control.

6. **Message Delivery Guarantees:** While Kafka does provide "at-least-once" delivery, there could be scenarios where "exactly-once" delivery would be necessary to avoid potential duplication or loss of data. This could be addressed by implementing idempotency or using a transactional approach to message handling.

In summary, the solution developed for this challenge provides a solid foundation for building a robust data platform capable of ingesting and storing event data from rockets. However, to be truly production-ready, it would need additional improvements in areas such as error handling, scaling, data processing, data retrieval, security, and message delivery guarantees.