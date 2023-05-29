# Lunar Data Engineering Challenge: Rockets 🚀

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

As a first step, you should clone the repository:
```bash
git clone git@github.com:CarlosRecoder/rockets-lunar.git
```

And navigate to the project directory:
```bash
cd rockets-lunar
```

The service can be then run using Docker Compose. Assuming Docker and Docker Compose are installed, you can start the service with the following command from the root directory of the project:

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
http://localhost:8081
```

This port hosts the MongoDB Express interface, a web-based MongoDB admin interface, which provides a convenient way to interact with the data. Here, you can inspect the documents and make sure that the data is being stored correctly. You can also perform CRUD (Create, Read, Update, Delete) operations directly through this interface if needed.

## CI Pipeline

The project includes a CI pipeline configured using GitHub Actions. This pipeline runs two checks for every push or pull request to the repository:

1. Linting with flake8: This ensures that the code follows the Python PEP8 style guide.
2. Unit tests with pytest: This verifies that individual units of the main code are working as expected (`test_producer.py` and `test_consumer.py`)


## Design Decisions and Potential Improvements

Given the 6-hour limit for the challenge, the focus was on implementing a simple and functional pipeline that could handle the key requirements. The decision to use Python was due to its readability and robust support for working with JSON and HTTP requests. Kafka was chosen for its capabilities in handling real-time, distributed message streams, and MongoDB for its ease of use with JSON-like documents.

### Handling Message Order and Duplicates

The Rocket Data Pipeline is designed to handle the complexities of streaming data such as out-of-order messages and message duplication (at-least-once guarantee). These are key aspects to ensure reliable data processing, especially for time-based event data.

#### **At-Least-Once Delivery and Duplicates Handling:**
The pipeline already perfectly handles the at-least-once guarantee and potential message duplication issues. The combination of Kafka and MongoDB is key to achieving this:

1. **Kafka** is used as the message broker. Kafka provides built-in support for message offsets. An offset is a unique identifier assigned to each message in Kafka, and consumers use these offsets to keep track of the messages they have consumed. In this case, the consumer commits the offset of each message to Kafka after processing it, providing a robust mechanism to ensure that each message is processed at least once.

2. **MongoDB** is used as the database to store the rocket messages. Before inserting a new message into the database, a check is made to see if a message with the same number already exists in the corresponding channel. If such a message exists, it is considered as a duplicate and skipped, ensuring that the database does not store duplicate messages.


#### **Out-of-Order Messages Handling:**

The pipeline doesn't explicitly handle the out-of-order issue due to the complexity that it would introduce to the system. After extensive testing, it was noticed that the messages, while possibly arriving out of order to the system, were never out of order within their own channels. Given this observation and the constraints on time and resources, the pragmatic decision to not add additional logic to handle out-of-order messages was made.

That said, specific mechanisms to handle out-of-order messages could be introduced if necessary:

1. **Buffering:** Using a buffer would be the first and most straightforward approach to deal with out-of-order messages in this scenario. In this strategy, messages are temporarily stored as they arrive, rather than being immediately processed. Each message is associated with a unique `MessageNumber` per channel, and this number is used to determine the correct sequence of messages. The buffer would operate based on a defined 'maximum `MessageNumber`'. When a message arrives, its message number is checked against this maximum. If the arriving message's number is higher than the current maximum, the system recognizes that one or more preceding messages are yet to arrive. Consequently, this message is held in the buffer until all of its predecessors have been received and processed. Once the missing messages arrive and their processing is completed in their correct order, the buffered message (with the higher number) would be released from the buffer and processed. This ensures that all messages are processed in the correct sequence, even if they arrive out of order.

2. **Windowing and Watermarking:** A more sophisticated approach would be to use windowing and watermarking. Windowing is a technique where the incoming messages are divided into discrete time windows and the messages within each window are processed separately. This allows for handling out-of-order messages by delaying the processing of each window until all or most of the messages for that window have been received.

### Scalability

The system has been designed keeping scalability in mind. Kafka and MongoDB, the key components of the system, are known for their scalability. Kafka can handle high volume real-time data feeds through its distributed nature, and MongoDB supports horizontal scaling through sharding. However, as the scale of the system grows, there may be areas that need additional consideration:

1. **Producer Application:** Currently, the producer application (`producer.py`) is designed to run on a single machine and push messages to Kafka. As data volume grows, this single application may become a bottleneck. This can be resolved by creating multiple instances of the producer application running in parallel, each pushing a portion of the data.

2. **Consumer Application:** The consumer application (`consumer.py`) is also designed to run on a single machine. If the data inflow increases beyond its processing capacity, this can cause a backlog of messages in Kafka. Implementing horizontal scaling strategies, such as running multiple instances of the consumer application, would help address this issue. Load balancing strategies could be introduced to distribute the data evenly among multiple consumer instances.

3. **MongoDB:** While MongoDB supports horizontal scaling via sharding, the system currently does not implement sharding. As the data grows, especially across different channels, implementing sharding strategies to distribute the data across multiple MongoDB instances could be beneficial.

4. **Infrastructure:** Currently, all components are set to run on individual Docker containers, which are typically deployed on a single machine. To truly scale, you would need to leverage Kubernetes or a similar service for orchestrating multiple machines and distributing the Docker containers across them. Additionally, by deploying this system on a cloud service provider like AWS, Google Cloud, or Azure, we could leverage the cloud's elastic infrastructure to easily scale up or down based on the workload.

5. **Message processing:** The expected data flow, one message every 500ms, is quite manageable for Kafka. However, for extremely high data volumes, the processing capability of our Python-based consumer may not suffice, even with multiple instances. In such cases, Apache Spark could be a better choice for processing the Kafka messages. Spark's in-memory computation capabilities and its ability to distribute processing tasks across a cluster make it well suited for high-volume, high-velocity data.

### Other areas

There are several other areas that could be improved with more time:

1. **Error Handling and Recovery:** The current implementation does not include extensive error handling or recovery mechanisms. For example, if the Kafka or MongoDB service goes down, the pipeline would stop working. A more robust system would have strategies to recover from these failures. Additionally, implementing retry mechanisms in case of temporary service disruptions can greatly improve the robustness of the system. 

2. **Data Retrieval:** Although MongoDB provides a flexible query language, in a production environment, there might be a need for more complex data retrieval capabilities. This could be achieved by adding a service to expose the data via a REST API or by integrating with a data warehouse or analytics platform.

3. **Continuous Deployment:** A CD pipeline could be set up to automatically deploy changes whenever there is a push or pull request in the repo. This would allow for quicker and more reliable deployments. In a production environment, it would be beneficial to use a container orchestration system like Kubernetes for deployment. This would offer benefits such as scalability, self-healing (automatic restarts), and automated rollouts and rollbacks. Due to the complexity and time constraints of the project, this wasn't implemented, but should be considered for production-grade deployment.

4. **Monitoring and Logging:** Implement a comprehensive monitoring and logging system, which would be crucial for debugging and maintaining a healthy production system. Tools like Prometheus for monitoring and the ELK (Elasticsearch, Logstash, and Kibana) Stack for logging could be used.

5. **Enhanced Testing:** While the current project includes core unit tests to verify the basic functionality, there is significant room for improvement in the testing arena. A more thorough and robust test suite would offer increased confidence in the solution's stability and effectiveness. Some solutions for extending test coverage could be adding integration tests, end-to-end tests, load and performance tests, fault tolerance and recovery tests, or security tests.

6. **Data Transformation:** Currently, the data is stored in MongoDB as it arrives, without any additional processing. However, in a real-world scenario, there might be a need for additional processing, transformation, or aggregation of the data. For instance, it could be beneficial to calculate the averages or max/min values of some metrics, categorize the events, or detect specific patterns. This could be achieved by adding a data processing component to the pipeline, like Apache Spark or Apache Flink.

7. **Security:** Currently, there are no security measures implemented. In a production environment, it would be crucial to secure the communication between the services and protect the stored data. This could include measures such as encryption, authentication, and access control.

In summary, the solution developed for this challenge provides a solid foundation for building a robust data platform capable of ingesting and storing event data from rockets. However, to be truly production-ready, it would need additional improvements in areas such as error handling, scaling, data processing, data retrieval, security, CD, monitoring, logging, and testing.