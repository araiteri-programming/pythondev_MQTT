Some brief instructions on how to run the project:

All tasks (including the MQTT broker) have been deployed as containers.

For the MQTT broker, you must install the rabbitmq image and deploy. The rabbitmq image is already installed on the EC2 Ubuntu server, 
but instructions are provided below to install and deploy a RabbitMQ instance with appropriate settings below in case the image is lost:
`docker run -d --hostname rabbitmq1 --name rabbitmq1 -e RABBITMQ_DEFAULT_USER=ayootuser -e RABBITMQ_DEFAULT_PASS=ayootpassword rabbitmq`

Containers map to the tasks as follows:
Task 1 - "rng_publisher"
Task 3 - "grapher"
Task 4 - "console"
Each image and container is already deployed to the server, but the Dockerfile and associated contents to build each image are available in this repo's files.
I have been naming the images as the containers are named above. 

If you wish to skip container deployment, skip to the section below that discusses connecting to the containers and running the Python scripts.

Command to build images:
`docker build ./ -t <image-name>` (use names from above)
For container name + hostname, I've been appending <name>1, <name>2 to number the containers.

To run the containers, you can use the following commands:

"rng_publisher"
`docker run -d --hostname rng_publisher1 --name rng_publisher1 -e LOGGING_LEVEL='error' -e CLIENT_ID='rng_publisher1' --env-file '/home/ubuntu/vars.txt' rng_publisher`

"grapher"
`docker run -d --hostname grapher1 --name grapher1 -e LOGGING_LEVEL='error' -e CLIENT_ID='grapher1' --env-file '/home/ubuntu/vars.txt' grapher`

"console"
`docker run -d --hostname console1 --name console1 -e LOGGING_LEVEL='error'  -e CLIENT_ID='console1' --env-file '/home/ubuntu/vars.txt' console`

If you want verbose logging for any of these containers to STDOUT, replace 'error' with 'info' in the container's `docker run` command.

Each container is passed an env file on launch. This file can be found on the EC2 Ubuntu server.

The containers are not currently configured to run their respective Python script on container launch. You must `docker exec -it <container-name> bash` into 
the container and then run the Python script found in the working directory.

Recommended order to start each container's script:
1. RabbitMQ
2. "rng_publisher"
3. "grapher"
4. "console"

The Ansible playbook 'install_mqtt_containers_remote.yaml' can be run from the Ansible server to automate cleaning up the old/not working solution setup on the Ansible client and build the solution from scratch (automated application deployment).
